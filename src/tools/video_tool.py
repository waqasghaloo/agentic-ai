"""
Video Tool — generates a short AI video clip from a text prompt via fal.ai.

Why AI video clips:
    Still images with Ken Burns effects are engaging but AI video clips add
    real motion — camera moves, physics, flowing water, space, fire — that
    makes the video feel alive. Mixing ~30% AI clips with 70% Flux Pro images
    balances quality and cost (~$0.03-0.05 per 5s clip with WAN 2.1).

Model choice:
    Default: WAN 2.1 (fal-ai/wan/v2.1/t2v) — good quality, cost effective
    Premium: Kling 2.0 (fal-ai/kling-video/v2.0/standard/text-to-video) — cinematic
    Set FAL_VIDEO_MODEL in .env to switch.

Prompt tips for video:
    - Describe motion explicitly: "camera slowly panning", "particles floating"
    - Keep scenes simple — complex multi-subject prompts confuse video models
    - 5 seconds is ideal: enough for one strong visual moment
"""

import requests
from pathlib import Path
import fal_client
from src.config import FAL_VIDEO_MODEL


def generate_clip(prompt: str, output_path: Path, duration: int = 5) -> bool:
    """
    Generate a short video clip from a text prompt and save to disk.

    Args:
        prompt:      Motion scene description (e.g. "DNA helix slowly rotating in blue light")
        output_path: Where to save the downloaded MP4 file.
        duration:    Clip length in seconds (5 or 10). Default 5.

    Returns:
        True if the clip was generated and saved, False on any failure.
    """
    try:
        result = fal_client.run(
            FAL_VIDEO_MODEL,
            arguments={
                "prompt": prompt,
                "duration": str(duration),
                "resolution": "720p",
                "aspect_ratio": "16:9",
            },
        )

        # fal.ai video models return {"video": {"url": "..."}}
        video_url = result["video"]["url"]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(video_url, timeout=120, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        print(f"  [Video Tool] Clip generation failed: {e}")
        return False
