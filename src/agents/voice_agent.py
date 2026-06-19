"""
Voice Agent — converts a video script into an MP3 audio file.

No agentic loop needed here — straight conversion, no decisions required.
Saves audio via PipelineState so the path is consistent and cacheable.
"""

from src.tools.elevenlabs_tool import text_to_speech
from src.pipeline.state import PipelineState


class VoiceAgent:
    """
    Agent responsible for converting video scripts to audio.

    Reads from and writes to PipelineState so outputs are cached
    and never regenerated unnecessarily.
    """

    def run(self, script: str, state: PipelineState) -> str:
        """
        Convert a video script to an MP3 audio file.

        Args:
            script: The full video script text to convert.
            state:  PipelineState for this topic — used to save the audio.

        Returns:
            Path to the saved MP3 file as a string.
        """
        print(f"  [Voice Agent] Converting {len(script)} characters to audio...")
        audio_bytes = text_to_speech(text=script)
        state.save_audio(audio_bytes)
        print(f"  [Voice Agent] Audio saved to: {state.audio_path}")
        return str(state.audio_path)
