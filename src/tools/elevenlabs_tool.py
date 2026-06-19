"""
ElevenLabs Tool — converts text to speech and returns audio bytes.

Why it returns bytes instead of saving directly:
    The caller (Voice Agent via PipelineState) decides where to save.
    This keeps the tool stateless and reusable.
"""

from elevenlabs.client import ElevenLabs
from src.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL


def text_to_speech(text: str) -> bytes:
    """
    Convert text to speech using ElevenLabs.

    Args:
        text: The script text to convert to audio.

    Returns:
        Raw MP3 audio as bytes. Caller is responsible for saving.
    """
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    audio = client.text_to_speech.convert(
        text=text,
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=ELEVENLABS_MODEL,
        output_format="mp3_44100_128",
    )

    return b"".join(chunk for chunk in audio)
