"""
Video Tool — animates a Flux Pro image into a short AI video clip using Kling image-to-video.

Why image-to-video instead of text-to-video:
    Text-to-video (e.g. Seedance) generates from scratch at ~$1.21/5s clip.
    Image-to-video (Kling) starts from a Flux Pro frame and adds motion at ~$0.42/5s.
    The result is higher quality AND 3× cheaper because the start frame is already
    a professional Flux Pro image.

Flow per "video" paragraph:
    1. VisualAgent generates a Flux Pro image (the start frame)
    2. This tool uploads that image to fal.ai's CDN to get a URL
    3. Kling v3 Standard animates it using a short motion description
    4. The resulting MP4 is saved to the clips/ folder

Model choice (set FAL_VIDEO_MODEL in .env):
    Default: fal-ai/kling-video/v3/standard/image-to-video  (~$0.42/5s)
    Premium: fal-ai/kling-video/v3/pro/image-to-video        (~$0.63/5s, more cinematic)

Motion prompt tips:
    - Short and specific: "camera slowly orbits", "particles drift upward"
    - One clear motion per clip — video models struggle with complex multi-action prompts
    - 5 seconds is the sweet spot: full motion arc, not too expensive
"""

import requests
from pathlib import Path
import fal_client
from src.config import FAL_VIDEO_MODEL


def animate_image(image_path: Path, motion_prompt: str, output_path: Path, duration: int = 5) -> bool:
    """
    Animate a still image into a short video clip using Kling image-to-video.

    Args:
        image_path:    Path to the local Flux Pro start frame image.
        motion_prompt: Short description of what should move (e.g. "camera slowly zooms in")
        output_path:   Where to save the downloaded MP4 file.
        duration:      Clip length in seconds (5 or 10). Default 5.

    Returns:
        True if the clip was generated and saved, False on any failure.
    """
    try:
        # Upload the local image to fal.ai CDN — Kling needs a URL, not a local path
        image_url = fal_client.upload_file(str(image_path))

        result = fal_client.run(
            FAL_VIDEO_MODEL,
            arguments={
                "start_image_url": image_url,
                "prompt": motion_prompt,
                "duration": str(duration),
                "aspect_ratio": "16:9",
                "generate_audio": False,
            },
        )

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
