"""
Image Tool — generates an image using Flux via fal.ai and saves to a given path.

Why fal.ai + Flux:
    fal.ai hosts the best open image models under one API.
    Default: Flux Pro v1.1 (~$0.05/image) — cinematic, photorealistic quality.
    Budget mode: set FAL_IMAGE_MODEL=fal-ai/flux/schnell in .env (~$0.003/image).
"""

import requests
from pathlib import Path
import fal_client
from src.config import FAL_IMAGE_MODEL


def generate_image(prompt: str, output_path: Path) -> None:
    """
    Generate an image from a text prompt and save it to the given path.

    Args:
        prompt:      Detailed description of the image to generate.
        output_path: Full path where the image should be saved.
    """
    result = fal_client.run(
        FAL_IMAGE_MODEL,
        arguments={
            "prompt": prompt,
            # Negative prompt prevents the most common Flux failures:
            # text/logos cause platform copyright strikes, anatomy issues look unprofessional
            "negative_prompt": (
                "text, letters, words, numbers, watermark, logo, brand name, "
                "NASA logo, ESA logo, company name, label, caption, subtitle, "
                "unrealistic anatomy, distorted hands, extra fingers, deformed face, "
                "blurry, low quality, oversaturated, cartoon, illustration, painting"
            ),
            "image_size": "landscape_16_9",  # 16:9 — perfect for YouTube
            "num_images": 1,
            "enable_safety_checker": True,
        },
    )

    image_url = result["images"][0]["url"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(image_url, timeout=30)
    response.raise_for_status()
    output_path.write_bytes(response.content)
