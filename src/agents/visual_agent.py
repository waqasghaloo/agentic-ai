"""
Visual Agent — generates images and sources stock clips for each paragraph of a script.

How it works:
    1. Split the script into paragraphs (~20-25 chunks)
    2. Ask Claude for an image prompt per paragraph + 4 Pexels search queries
    3. Generate one AI image per paragraph via fal.ai (paragraph-level alignment
       means the visual matches exactly what is being said at that moment)
    4. If PEXELS_API_KEY is set: download 4 free stock clips from Pexels
    5. Interleave: every 5th item in the sequence is replaced by a stock clip
    6. Save the ordered media list to PipelineState for the editor to consume
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PEXELS_API_KEY
from src.tools.image_tool import generate_image
from src.tools.pexels_tool import search_and_download_clip
from src.pipeline.state import PipelineState


_IMAGE_SYSTEM_PROMPT = """
You are a visual director for YouTube educational videos.

You will receive a script split into numbered paragraphs.
For each paragraph, write one image generation prompt that:
- Depicts a specific, concrete visual scene matching what is being said
- Uses style: "photorealistic, cinematic lighting, 16:9 format, high detail"
- Contains NO text, logos, watermarks, or human faces

Also provide 4 short Pexels video search queries for stock footage variety.
Choose search terms that would find visually rich, topic-relevant clips
(e.g. "space telescope orbit", "underwater coral reef", "city time lapse").

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "image_prompts": [
    {"index": 0, "prompt": "..."},
    {"index": 1, "prompt": "..."}
  ],
  "pexels_queries": ["query one", "query two", "query three", "query four"]
}
"""

# Minimum paragraph length to generate an image for — skips section headers, short lines
_MIN_PARA_LEN = 80

# Insert a stock clip after every Nth image
_CLIP_EVERY_N = 5


def _split_paragraphs(script: str) -> list[str]:
    """Split script into non-trivial paragraphs suitable for image generation."""
    paragraphs = [p.strip() for p in script.split("\n\n")]
    return [p for p in paragraphs if len(p) >= _MIN_PARA_LEN]


class VisualAgent:
    """
    Agent that builds the full visual media list for one video.

    Generates one AI image per script paragraph for tight voiceover alignment,
    then mixes in free Pexels stock clips every few images for motion variety.
    The final ordered media list is saved to PipelineState for the editor.
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def run(self, script: str, state: PipelineState) -> None:
        """
        Generate all visual media for the script and save to state.

        Args:
            script: The full video script text.
            state:  PipelineState for this topic — media list saved here.
        """
        paragraphs = _split_paragraphs(script)
        print(f"  [Visual Agent] {len(paragraphs)} paragraphs → requesting prompts from Claude...")

        # Step 1: Ask Claude for image prompts + Pexels search terms
        numbered = "\n\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs))
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=_IMAGE_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Script paragraphs:\n\n{numbered}",
                }
            ],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if Claude wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        data = json.loads(raw)
        image_prompts = data["image_prompts"]
        pexels_queries = data.get("pexels_queries", [])

        print(f"  [Visual Agent] {len(image_prompts)} image prompts ready. Generating...")

        # Step 2: Generate AI images (one per paragraph)
        state.images_dir.mkdir(parents=True, exist_ok=True)
        image_paths = []

        for item in image_prompts:
            idx = item["index"]
            prompt = item["prompt"]
            output_path = state.images_dir / f"{idx + 1:02d}-para.png"

            print(f"  [Visual Agent] Image {idx + 1}/{len(image_prompts)}...")
            generate_image(prompt=prompt, output_path=output_path)
            image_paths.append(str(output_path))

        # Step 3: Download Pexels stock clips (only if API key is configured)
        clip_paths = []
        if PEXELS_API_KEY and pexels_queries:
            print(f"  [Visual Agent] Downloading {len(pexels_queries)} Pexels clips...")
            state.clips_dir.mkdir(parents=True, exist_ok=True)

            for i, query in enumerate(pexels_queries[:4]):
                clip_path = state.clips_dir / f"{i + 1:02d}-clip.mp4"
                success = search_and_download_clip(query, clip_path)
                if success:
                    clip_paths.append(str(clip_path))
                    print(f"  [Visual Agent] Clip {i + 1}: '{query}' ✓")
                else:
                    print(f"  [Visual Agent] Clip {i + 1}: '{query}' — not found, skipping")
        else:
            if not PEXELS_API_KEY:
                print("  [Visual Agent] PEXELS_API_KEY not set — using AI images only")

        # Step 4: Interleave — insert a stock clip after every Nth image
        media_list = []
        clip_index = 0

        for i, img_path in enumerate(image_paths):
            media_list.append({"type": "image", "path": img_path})

            if (i + 1) % _CLIP_EVERY_N == 0 and clip_index < len(clip_paths):
                media_list.append({"type": "video", "path": clip_paths[clip_index]})
                clip_index += 1

        state.save_media_list(media_list)

        total = len(media_list)
        img_count = sum(1 for m in media_list if m["type"] == "image")
        vid_count = sum(1 for m in media_list if m["type"] == "video")
        print(f"  [Visual Agent] Media ready: {total} items ({img_count} images, {vid_count} clips)")
