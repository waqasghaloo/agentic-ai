"""
Voice Agent — converts a video script into an MP3 audio file.

Why no agentic loop here:
    Unlike the Research Agent, the Voice Agent has no decisions to make.
    It receives text and transforms it to audio — a straight conversion.
    No Claude reasoning required. This is a valid and common agent pattern:
    an agent that wraps an external service with a clean, consistent interface.
"""

from datetime import datetime
from src.tools.elevenlabs_tool import text_to_speech


class VoiceAgent:
    """
    Agent responsible for converting video scripts to audio.

    Takes a script string, calls ElevenLabs, returns the path to the MP3 file.
    Single responsibility: script in, audio file path out.
    """

    def run(self, script: str, filename: str | None = None) -> str:
        """
        Convert a video script to an MP3 audio file.

        Args:
            script:   The full video script text to convert.
            filename: Optional custom filename. Defaults to today's date.

        Returns:
            Path to the saved MP3 file as a string.
        """
        # Default filename is today's date — useful for daily uploads
        # where each video corresponds to one day
        if not filename:
            filename = datetime.now().strftime("%Y-%m-%d")

        print(f"  [Voice Agent] Converting script to audio ({len(script)} characters)...")
        audio_path = text_to_speech(text=script, filename=filename)
        print(f"  [Voice Agent] Audio saved to: {audio_path}")

        return audio_path
