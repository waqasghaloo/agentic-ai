"""
Editor Agent — combines audio and mixed media (images + stock clips) into a final MP4.

Like the Voice Agent, this is a Transform Agent — no Claude reasoning needed.
It has one job: take the pipeline's media files and assemble the final video.
"""

from src.tools.editor_tool import assemble_video
from src.pipeline.state import PipelineState


class EditorAgent:
    """
    Agent responsible for assembling the final YouTube video.

    Reads audio and the ordered media list from PipelineState, produces a
    final MP4, and skips if the video already exists (cached).
    """

    def run(self, state: PipelineState) -> str:
        """
        Assemble the final video from cached audio and media list.

        Args:
            state: PipelineState for this topic — source of all media files.

        Returns:
            Path to the finished MP4 file.
        """
        media_list = state.get_media_list()
        audio_path = str(state.audio_path)

        img_count = sum(1 for m in media_list if m["type"] == "image")
        vid_count = sum(1 for m in media_list if m["type"] == "video")
        print(f"  [Editor Agent] Assembling {img_count} images + {vid_count} clips + audio → MP4")

        assemble_video(
            media_list=media_list,
            audio_path=audio_path,
            output_path=state.video_path,
        )

        print(f"  [Editor Agent] Video ready: {state.video_path}")
        return str(state.video_path)
