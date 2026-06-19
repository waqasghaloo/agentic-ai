"""
Editor Agent — combines audio and images into a final MP4 video.

Like the Voice Agent, this is a Transform Agent — no Claude reasoning needed.
It has one job: take the pipeline's media files and assemble the final video.
"""

from src.tools.editor_tool import assemble_video
from src.pipeline.state import PipelineState


class EditorAgent:
    """
    Agent responsible for assembling the final YouTube video.

    Reads audio and images from PipelineState, produces a final MP4,
    and skips if the video already exists (cached).
    """

    def run(self, state: PipelineState) -> str:
        """
        Assemble the final video from cached audio and images.

        Args:
            state: PipelineState for this topic — source of all media files.

        Returns:
            Path to the finished MP4 file.
        """
        image_paths = state.get_image_paths()
        audio_path = str(state.audio_path)

        print(f"  [Editor Agent] Assembling {len(image_paths)} images + audio → MP4")

        assemble_video(
            image_paths=image_paths,
            audio_path=audio_path,
            output_path=state.video_path,
        )

        print(f"  [Editor Agent] Video ready: {state.video_path}")
        return str(state.video_path)
