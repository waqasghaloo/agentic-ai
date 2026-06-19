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
