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

# fal.ai — image generation
# FAL_KEY is also read automatically by fal_client from os.environ
FAL_KEY: str = _require("FAL_KEY")
# Flux Schnell: fastest and cheapest (~$0.003/image), good quality
# Upgrade to "fal-ai/flux-pro/v1.1" for best quality (~$0.05/image)
FAL_IMAGE_MODEL: str = os.getenv("FAL_IMAGE_MODEL", "fal-ai/flux/schnell")
