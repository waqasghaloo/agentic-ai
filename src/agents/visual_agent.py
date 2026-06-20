"""
Visual Agent — builds a mixed media sequence of Flux Pro images and Kling AI video clips.

How it works:
    1. Split the script into paragraphs (~20-25 chunks)
    2. One Claude call: for each paragraph decide "image" or "video" and write TWO prompts:
       - image_prompt: cinematic Flux Pro still image description
       - motion_prompt: short Kling animation instruction (for "video" type only)
    3. For all paragraphs: generate the Flux Pro image (start frame / standalone)
    4. For "video" paragraphs: also animate the image with Kling i2v → 5s clip
    5. Clip fails → fall back to the already-generated image (no extra API call needed)
    6. Save the ordered media list to PipelineState for the editor

Cost per video (~21 paragraphs, 30% video):
    ~15 images × $0.05 = $0.75
    ~6 clips  × $0.42 = $2.52  (Flux Pro base + Kling animation)
    Total ≈ $3.27/video
"""

import json
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.image_tool import generate_image
from src.tools.video_tool import animate_image
from src.pipeline.state import PipelineState


_VISUAL_SYSTEM_PROMPT = """
You are a visual director for a YouTube educational channel.

You will receive a script split into numbered paragraphs.
For each paragraph, decide whether it should be visualised as:

  "image" — a Flux Pro AI still image
             Best for: concepts, data, close-ups, abstract ideas, narration beats
  "video" — a Kling AI video clip that STARTS from a Flux Pro still frame and adds motion
             Best for: action, flowing motion, space, nature, particles, camera moves

Rules:
- Aim for 65-70% images and 30-35% video clips
- Both types: NO text, logos, watermarks, or human faces
- Both types: visually match what is being said in that paragraph

For "image" entries provide:
  image_prompt: rich, cinematic description. Style: "photorealistic, dramatic cinematic lighting, ultra detail, 16:9"

For "video" entries provide TWO prompts:
  image_prompt: description of the start frame (same style as image)
  motion_prompt: ONE sentence describing the motion. Examples:
    "camera slowly zooms into the centre of a glowing nebula"
    "DNA helix gently rotates, particles drifting outward in slow motion"
    "time-lapse clouds race over a mountain peak, shadows sweeping across valleys"

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "media": [
    {"index": 0, "type": "image", "image_prompt": "..."},
    {"index": 1, "type": "video", "image_prompt": "...", "motion_prompt": "..."},
    {"index": 2, "type": "image", "image_prompt": "..."}
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

    For all paragraphs: generates a Flux Pro base image.
    For ~30% paragraphs: also animates the image with Kling i2v to produce a clip.
    Falls back to the base image if clip generation fails (no extra cost).
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
        print(f"  [Visual Agent] Plan: {img_planned} images + {vid_planned} AI clips. Generating...")

        state.images_dir.mkdir(parents=True, exist_ok=True)
        state.clips_dir.mkdir(parents=True, exist_ok=True)

        media_list = []
        img_counter = 0
        vid_counter = 0

        for item in media_plan:
            idx = item["index"]
            media_type = item["type"]
            image_prompt = item["image_prompt"]
            img_path = state.images_dir / f"{idx + 1:02d}-para.png"

            # Always generate the Flux Pro base image first
            img_counter += 1
            label = "image" if media_type == "image" else f"base frame for clip {vid_counter + 1}"
            print(f"  [Visual Agent] Image {img_counter}/{img_planned + vid_planned} ({label}, para {idx + 1})...")
            generate_image(prompt=image_prompt, output_path=img_path)

            if media_type == "video":
                vid_counter += 1
                motion_prompt = item.get("motion_prompt", "camera slowly zooms in")
                clip_path = state.clips_dir / f"{idx + 1:02d}-clip.mp4"
                print(f"  [Visual Agent] Animating clip {vid_counter}/{vid_planned}...")
                success = animate_image(
                    image_path=img_path,
                    motion_prompt=motion_prompt,
                    output_path=clip_path,
                )
                if success:
                    media_list.append({"type": "video", "path": str(clip_path)})
                else:
                    print(f"  [Visual Agent] Clip failed — using base image for para {idx + 1}")
                    media_list.append({"type": "image", "path": str(img_path)})
            else:
                media_list.append({"type": "image", "path": str(img_path)})

        state.save_media_list(media_list)

        final_imgs = sum(1 for m in media_list if m["type"] == "image")
        final_vids = sum(1 for m in media_list if m["type"] == "video")
        print(f"  [Visual Agent] Done: {len(media_list)} items ({final_imgs} images + {final_vids} AI clips)")
