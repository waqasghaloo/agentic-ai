"""
Shorts Agent — creates vertical 9:16 video cuts for TikTok, Instagram Reels,
and YouTube Shorts from the finished 16:9 long-form video.

Strategy:
    Always take the FIRST 60 seconds — that's where the hook lives.
    The script is written with a cold open that grabs attention immediately,
    so the first minute is always the strongest 60 seconds to share.

Output per topic:
    platforms/tiktok/video.mp4      ← 60s max, 9:16
    platforms/instagram/video.mp4   ← 90s max, 9:16 (Reels allows longer)
    platforms/shorts/video.mp4      ← 60s max, 9:16 (YouTube Shorts limit)

All three are center-cropped from the 16:9 final.mp4.
TikTok and Shorts share the same 60s cut; Instagram gets up to 90s.
"""

import numpy as np
from pathlib import Path
from moviepy.editor import VideoFileClip
from PIL import Image as PILImage

from src.pipeline.state import PipelineState

_TIKTOK_DURATION = 60    # seconds — TikTok / YouTube Shorts limit
_INSTAGRAM_DURATION = 90  # seconds — Instagram Reels limit


def _crop_to_vertical(clip: VideoFileClip) -> VideoFileClip:
    """
    Center-crop a 16:9 clip to 9:16 aspect ratio.

    From a 1920x1080 source: takes a 608x1080 center slice → 9:16.
    Then scales up to 1080x1920 standard vertical resolution.
    """
    src_w, src_h = clip.size
    target_w = int(src_h * 9 / 16)
    x_center = src_w / 2

    cropped = clip.crop(
        x1=x_center - target_w / 2,
        x2=x_center + target_w / 2,
    )

    # Scale to standard 1080x1920 using Pillow LANCZOS (Pillow 10+ compatible)
    resized = cropped.fl_image(
        lambda frame: np.array(
            PILImage.fromarray(frame).resize((1080, 1920), PILImage.LANCZOS)
        )
    )
    return resized


class ShortsAgent:
    """
    Generates vertical short-form video cuts for all major social platforms.

    Skips any platform cut that already exists on disk (resume-safe).
    """

    def run(self, state: PipelineState) -> None:
        """
        Create TikTok, Instagram, and YouTube Shorts cuts from final.mp4.

        Args:
            state: PipelineState for the completed topic (must have final.mp4).
        """
        if not state.video_path.exists():
            print("  [Shorts Agent] No final.mp4 found — skipping.")
            return

        tiktok_path = state.platforms_dir / "tiktok" / "video.mp4"
        instagram_path = state.platforms_dir / "instagram" / "video.mp4"
        shorts_path = state.platforms_dir / "shorts" / "video.mp4"
        facebook_path = state.platforms_dir / "facebook" / "video.mp4"

        all_exist = (tiktok_path.exists() and instagram_path.exists()
                     and shorts_path.exists() and facebook_path.exists())
        if all_exist:
            print("  [Shorts Agent] All platform cuts already exist — skipping.")
            return

        print("  [Shorts Agent] Loading video and cropping to 9:16...")
        source = VideoFileClip(str(state.video_path))
        vertical = _crop_to_vertical(source)

        write_opts = {
            "codec": "libx264",
            "audio_codec": "aac",
            "temp_audiofile": "/tmp/shorts_tmp_audio.m4a",
            "remove_temp": True,
            "verbose": False,
            "logger": None,
        }

        # TikTok / Shorts — 60 seconds
        if not tiktok_path.exists() or not shorts_path.exists():
            cut_60 = vertical.subclip(0, min(_TIKTOK_DURATION, vertical.duration))

            if not tiktok_path.exists():
                tiktok_path.parent.mkdir(parents=True, exist_ok=True)
                print(f"  [Shorts Agent] Rendering TikTok cut ({int(cut_60.duration)}s)...")
                cut_60.write_videofile(str(tiktok_path), **write_opts)

            if not shorts_path.exists():
                shorts_path.parent.mkdir(parents=True, exist_ok=True)
                print(f"  [Shorts Agent] Rendering YouTube Shorts cut ({int(cut_60.duration)}s)...")
                cut_60.write_videofile(str(shorts_path), **write_opts)

        # Instagram Reels — 90 seconds
        if not instagram_path.exists():
            cut_90 = vertical.subclip(0, min(_INSTAGRAM_DURATION, vertical.duration))
            instagram_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"  [Shorts Agent] Rendering Instagram Reels cut ({int(cut_90.duration)}s)...")
            cut_90.write_videofile(str(instagram_path), **write_opts)

        # Facebook Reels — 90 seconds (same format as Instagram)
        if not facebook_path.exists():
            cut_fb = vertical.subclip(0, min(_INSTAGRAM_DURATION, vertical.duration))
            facebook_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"  [Shorts Agent] Rendering Facebook Reels cut ({int(cut_fb.duration)}s)...")
            cut_fb.write_videofile(str(facebook_path), **write_opts)

        source.close()
        vertical.close()
        print("  [Shorts Agent] Done — TikTok, Instagram, Facebook, YouTube Shorts cuts ready.")
