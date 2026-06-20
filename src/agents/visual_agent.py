"""
Visual Agent — builds a mixed media sequence of AI images and AI video clips per script.

How it works:
    1. Split the script into paragraphs (~20-25 chunks)
    2. One Claude call: for each paragraph, decide "image" or "video" + write the prompt
       - ~70% get a Flux Pro image (concepts, data, faces, objects)
       - ~30% get a WAN 2.1 video clip (motion scenes: space, water, fire, nature)
    3. Generate all media in order: images via image_tool, clips via video_tool
    4. Save the ordered media list to PipelineState for the editor

Why per-paragraph media type decisions:
    Claude knows which paragraphs describe action/motion (better as video)
    versus concepts/facts (better as a crisp still image). This produces
    a much better visual fit than mechanical every-Nth rotation.
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.image_tool import generate_image
from src.tools.video_tool import generate_clip
from src.pipeline.state import PipelineState


_VISUAL_SYSTEM_PROMPT = """
You are a visual director for a YouTube educational channel.

You will receive a script split into numbered paragraphs.
For each paragraph, decide whether it should be visualised as:

  "image" — a Flux Pro AI still image (best for: concepts, data, close-ups, portraits, diagrams)
  "video" — a WAN AI video clip (best for: motion, action, nature, space, flowing, cinematic)

Rules:
- Aim for roughly 65-70% images and 30-35% video clips
- For "image" prompts: be specific and cinematic. Style: "photorealistic, dramatic cinematic lighting, ultra detail, 16:9"
- For "video" prompts: describe motion clearly. Examples: "camera slowly orbiting a glowing DNA helix", "time-lapse of neurons firing in electric blue light"
- Both types: NO text, logos, watermarks, or human faces
- Both types: visually match what is being said in that paragraph

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "media": [
    {"index": 0, "type": "image", "prompt": "..."},
    {"index": 1, "type": "video", "prompt": "..."},
    {"index": 2, "type": "image", "prompt": "..."}
  ]
}
"""

_MIN_PARA_LEN = 80


def _split_paragraphs(script: str) -> list[str]:
    """Split script into non-trivial paragraphs. Skips short headers and blank lines."""
    paragraphs = [p.strip() for p in script.split("\n\n")]
    return [p for p in paragraphs if len(p) >= _MIN_PARA_LEN]


def _parse_json(raw: str) -> dict:
    """Parse JSON from Claude response, stripping markdown code fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)


class VisualAgent:
    """
    Agent that builds the ordered visual media list for one video.

    Makes per-paragraph image vs. video decisions, generates all media,
    and saves the result to PipelineState for the EditorAgent to assemble.
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
        print(f"  [Visual Agent] {len(paragraphs)} paragraphs → asking Claude for media plan...")

        numbered = "\n\n".join(f"[{i}] {p}" for i, p in enumerate(paragraphs))
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=_VISUAL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Script paragraphs:\n\n{numbered}"}],
        )

        data = _parse_json(response.content[0].text)
        media_plan = data["media"]

        img_planned = sum(1 for m in media_plan if m["type"] == "image")
        vid_planned = sum(1 for m in media_plan if m["type"] == "video")
        print(f"  [Visual Agent] Plan: {img_planned} images + {vid_planned} video clips. Generating...")

        state.images_dir.mkdir(parents=True, exist_ok=True)
        state.clips_dir.mkdir(parents=True, exist_ok=True)

        media_list = []
        img_counter = 0
        vid_counter = 0

        for item in media_plan:
            idx = item["index"]
            media_type = item["type"]
            prompt = item["prompt"]

            if media_type == "video":
                vid_counter += 1
                output_path = state.clips_dir / f"{idx + 1:02d}-clip.mp4"
                print(f"  [Visual Agent] Clip {vid_counter}/{vid_planned} (para {idx + 1})...")
                success = generate_clip(prompt=prompt, output_path=output_path)
                if success:
                    media_list.append({"type": "video", "path": str(output_path)})
                else:
                    # Fallback: generate an image instead if the clip fails
                    print(f"  [Visual Agent] Clip failed — falling back to image for para {idx + 1}")
                    img_counter += 1
                    img_path = state.images_dir / f"{idx + 1:02d}-para.png"
                    generate_image(prompt=prompt, output_path=img_path)
                    media_list.append({"type": "image", "path": str(img_path)})
            else:
                img_counter += 1
                output_path = state.images_dir / f"{idx + 1:02d}-para.png"
                print(f"  [Visual Agent] Image {img_counter}/{img_planned} (para {idx + 1})...")
                generate_image(prompt=prompt, output_path=output_path)
                media_list.append({"type": "image", "path": str(output_path)})

        state.save_media_list(media_list)

        total = len(media_list)
        final_imgs = sum(1 for m in media_list if m["type"] == "image")
        final_vids = sum(1 for m in media_list if m["type"] == "video")
        print(f"  [Visual Agent] Done: {total} items ({final_imgs} images + {final_vids} AI clips)")
