"""
ElevenLabs Tool — converts text to speech and saves as an MP3 file.

Why this is a tool (not inside the Voice Agent):
    The tool handles one thing: calling ElevenLabs API and saving the file.
    The agent handles one thing: deciding what to send and returning the result.
    If we switch from ElevenLabs to another provider later, only this file changes.
"""

from pathlib import Path
from elevenlabs.client import ElevenLabs
from src.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL

# Output directory for all generated audio files
AUDIO_OUTPUT_DIR = Path("output/audio")


def text_to_speech(text: str, filename: str) -> str:
    """
    Convert text to speech using ElevenLabs and save as an MP3 file.

    Args:
        text:     The script text to convert to audio.
        filename: The name for the output file (without extension).

    Returns:
        The full path to the saved MP3 file as a string.
    """
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # convert() returns a generator of audio bytes
    # We iterate over it and write each chunk to the file
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=ELEVENLABS_MODEL,
        output_format="mp3_44100_128",  # high quality MP3, 128kbps
    )

    # Ensure the output directory exists before writing
    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = AUDIO_OUTPUT_DIR / f"{filename}.mp3"

    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    return str(output_path)
