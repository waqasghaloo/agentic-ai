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
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, FAL_VIDEO_DISABLED
from src.tools.image_tool import generate_image
from src.tools.video_tool import animate_image
from src.pipeline.state import PipelineState


_VISUAL_SYSTEM_PROMPT = """
You are the lead visual director for a top-tier YouTube educational channel with 10M+ subscribers.
You think like a documentary filmmaker: every frame should evoke emotion AND communicate the idea.

You will receive a script split into numbered paragraphs.
For each paragraph, decide whether it should be visualised as:

  "image" — a Flux Pro cinematic still (best for: close-up emotions, data moments, quiet tension)
  "video" — a Kling animated clip starting from a Flux Pro frame (best for: motion, drama, action)

VISUAL PHILOSOPHY:
  - Humans are the most engaging subject on screen. Scientists, patients, children, families.
    Show people experiencing the science — not just the science floating in a void.
  - Every shot should answer: "what is the CHARACTER feeling right now?"
  - Mix intimate close-ups with epic wide shots — vary the visual scale constantly
  - Think: what would a Netflix documentary director put on screen here?

TARGET MIX: 60-65% images, 35-40% video clips

IMAGE PROMPT RULES:
  - Always describe a SPECIFIC scene: who is in it, where they are, what they're doing/feeling
  - Style suffix to ALWAYS include: "photorealistic, cinematic lighting, shallow depth of field,
    ultra detail, 16:9, no text, no logos, no watermarks"
  - Great image prompts: "a middle-aged female scientist staring at a glowing microscope screen,
    expression shifting from concentration to disbelief, dark lab background with blue equipment glow"
  - Avoid: generic "DNA helix on black background" — that's a screensaver, not a documentary frame

VIDEO MOTION PROMPT RULES:
  - The image_prompt describes the start FRAME (same rules as images)
  - The motion_prompt describes WHAT MOVES and HOW — one specific, cinematic sentence
  - Great motion prompts: "camera slowly pushes in on the scientist's face as her eyes widen,
    shallow focus, warm lab lights blurring in the background"
  - Great motion prompts: "extreme close-up of a syringe slowly depressing into a vial, hands
    slightly trembling, clinical blue light, camera holds then slowly pulls back"
  - Avoid: "camera zooms in" — that's not a motion prompt, that's a default

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

        # Reuse Claude's media plan if already saved — saves API cost on resume
        if state.has_media_plan():
            media_plan = state.get_media_plan()
            print(f"  [Visual Agent] Resuming from saved media plan ({len(media_plan)} items)...")
        else:
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
            state.save_media_plan(media_plan)  # persist immediately before generating anything

        img_planned = sum(1 for m in media_plan if m["type"] == "image")
        vid_planned = sum(1 for m in media_plan if m["type"] == "video")

        if FAL_VIDEO_DISABLED and vid_planned > 0:
            print(f"  [Visual Agent] FAL_VIDEO_DISABLED=true — treating all {vid_planned} clips as images")
            for item in media_plan:
                item["type"] = "image"
            img_planned += vid_planned
            vid_planned = 0

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

            # Generate base image — skip if it already exists on disk (resume safety)
            img_counter += 1
            label = "image" if media_type == "image" else f"base frame for clip {vid_counter + 1}"
            if img_path.exists():
                print(f"  [Visual Agent] Image {img_counter} already exists — skipping (para {idx + 1})")
            else:
                print(f"  [Visual Agent] Image {img_counter}/{img_planned + vid_planned} ({label}, para {idx + 1})...")
                generate_image(prompt=image_prompt, output_path=img_path)

            if media_type == "video":
                vid_counter += 1
                motion_prompt = item.get("motion_prompt", "camera slowly zooms in")
                clip_path = state.clips_dir / f"{idx + 1:02d}-clip.mp4"
                if clip_path.exists():
                    print(f"  [Visual Agent] Clip {vid_counter} already exists — skipping (para {idx + 1})")
                    media_list.append({"type": "video", "path": str(clip_path)})
                else:
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
