"""
Central configuration loader for the project.

Why this exists: instead of every file calling os.getenv() directly,
all config is loaded here. If a key is missing, we catch it early
at startup rather than failing mid-pipeline.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Load a required environment variable, raising clearly if missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Add it to your .env file. See .env.example for reference."
        )
    return value


# Claude
ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# ElevenLabs
ELEVENLABS_API_KEY: str = _require("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # George — clear, natural, neutral accent
ELEVENLABS_MODEL: str = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# fal.ai — image + video generation
# FAL_KEY is also read automatically by fal_client from os.environ
FAL_KEY: str = _require("FAL_KEY")

# Image model — Flux Pro v1.1 gives cinematic quality (~$0.05/image)
# Downgrade to "fal-ai/flux/schnell" for budget runs (~$0.003/image)
FAL_IMAGE_MODEL: str = os.getenv("FAL_IMAGE_MODEL", "fal-ai/flux-pro/v1.1")

# Video model — Kling v3 Standard image-to-video (~$0.42 per 5s clip)
# Animates a Flux Pro start frame → higher quality than pure text-to-video
# Upgrade: "fal-ai/kling-video/v3/pro/image-to-video" (~$0.63 per 5s, more cinematic)
FAL_VIDEO_MODEL: str = os.getenv("FAL_VIDEO_MODEL", "fal-ai/kling-video/v3/standard/image-to-video")

# Pexels — free stock video clips (optional, kept as fallback)
# Sign up at https://www.pexels.com/api/ — free, no credit card needed
PEXELS_API_KEY: str | None = os.getenv("PEXELS_API_KEY") or None
