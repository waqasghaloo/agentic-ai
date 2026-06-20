"""
Editor Tool — assembles images and stock clips + audio into a final MP4 video.

How it works:
    1. Loads the audio and measures its total duration
    2. Divides duration equally across all media items
    3. For each item:
       - Image → applies one of 4 Ken Burns / pan effects
       - Video clip → trims to the required duration
    4. Concatenates everything into one video
    5. Attaches the audio track
    6. Exports as MP4

Effects on images (rotate through 4 for variety):
    zoom_in  — slow zoom from 100% to 110% (classic Ken Burns)
    zoom_out — slow zoom from 110% to 100%
    pan_left — slow pan left to right across a slightly wider image
    pan_right — slow pan right to left across a slightly wider image

Why MoviePy:
    Pure Python video editing library built on top of ffmpeg.
    No GUI needed — fully scriptable, perfect for automated pipelines.
"""

from pathlib import Path
import numpy as np
from PIL import Image as PILImage
from moviepy.editor import (
    AudioFileClip,
    VideoClip,
    VideoFileClip,
    concatenate_videoclips,
)

# Output video settings
VIDEO_FPS = 24
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Cycle through these effects to keep the video visually varied
_EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

# How much wider the image is made for panning (20% gives smooth travel room)
_PAN_SCALE = 1.20


def _make_image_clip(image_path: str, duration: float, effect: str) -> VideoClip:
    """
    Create a video clip from a still image using a Ken Burns or pan effect.

    Args:
        image_path: Path to the source image.
        duration:   How long this clip should play in seconds.
        effect:     One of "zoom_in", "zoom_out", "pan_left", "pan_right".

    Returns:
        A MoviePy VideoClip with the effect applied.
    """
    img = PILImage.open(image_path).convert("RGB")

    if effect in ("pan_left", "pan_right"):
        # For panning, make the image 20% wider so there's room to travel
        wider_w = int(VIDEO_WIDTH * _PAN_SCALE)
        img = img.resize((wider_w, VIDEO_HEIGHT), PILImage.LANCZOS)
        img_array = np.array(img)

        def make_frame(t: float) -> np.ndarray:
            progress = t / duration  # 0.0 → 1.0
            travel = wider_w - VIDEO_WIDTH  # pixels available to pan

            if effect == "pan_left":
                x_start = int(travel * progress)       # starts left, moves right
            else:
                x_start = int(travel * (1 - progress))  # starts right, moves left

            return img_array[:, x_start:x_start + VIDEO_WIDTH]

    else:
        # Zoom effects — image stays at base size, we crop a shrinking/growing region
        img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), PILImage.LANCZOS)
        img_array = np.array(img)

        def make_frame(t: float) -> np.ndarray:
            progress = t / duration

            zoom = 1.0 + 0.10 * progress if effect == "zoom_in" else 1.10 - 0.10 * progress

            crop_h = int(VIDEO_HEIGHT / zoom)
            crop_w = int(VIDEO_WIDTH / zoom)
            y1 = (VIDEO_HEIGHT - crop_h) // 2
            x1 = (VIDEO_WIDTH - crop_w) // 2

            cropped = img_array[y1:y1 + crop_h, x1:x1 + crop_w]
            return np.array(
                PILImage.fromarray(cropped).resize((VIDEO_WIDTH, VIDEO_HEIGHT), PILImage.LANCZOS)
            )

    clip = VideoClip(make_frame, duration=duration)
    return clip.set_fps(VIDEO_FPS)


def _make_video_clip(clip_path: str, duration: float) -> VideoFileClip:
    """
    Load a stock video clip and trim it to the required duration.

    Args:
        clip_path: Path to the MP4 file.
        duration:  Target duration in seconds.

    Returns:
        A MoviePy VideoFileClip trimmed and resized to 1920×1080.
    """
    clip = VideoFileClip(clip_path)

    # Trim to target duration (clip may be shorter — loop if needed, else take as-is)
    if clip.duration >= duration:
        clip = clip.subclip(0, duration)
    # else: use the whole clip even if shorter; concatenation handles gaps

    # Resize using Pillow LANCZOS directly — MoviePy's .resize() uses the
    # deprecated PIL.Image.ANTIALIAS which was removed in Pillow 10+
    if clip.size != (VIDEO_WIDTH, VIDEO_HEIGHT):
        clip = clip.fl_image(
            lambda img: np.array(
                PILImage.fromarray(img).resize((VIDEO_WIDTH, VIDEO_HEIGHT), PILImage.LANCZOS)
            )
        )

    return clip.set_fps(VIDEO_FPS)


def assemble_video(
    media_list: list[dict],
    audio_path: str,
    output_path: Path,
) -> None:
    """
    Assemble a mixed sequence of images and video clips into a final MP4.

    Args:
        media_list:  Ordered list of {"type": "image"|"video", "path": "..."} dicts.
        audio_path:  Path to the voiceover MP3 file.
        output_path: Where to save the finished MP4.
    """
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    clip_duration = total_duration / len(media_list)

    print(f"  [Editor] Audio duration: {total_duration:.1f}s")
    print(f"  [Editor] {len(media_list)} clips × {clip_duration:.1f}s each")

    clips = []
    effect_index = 0  # track separately so video clips don't consume an effect slot

    for i, item in enumerate(media_list):
        item_type = item["type"]
        item_path = item["path"]

        if item_type == "video":
            clip = _make_video_clip(item_path, clip_duration)
            label = "stock clip"
        else:
            effect = _EFFECTS[effect_index % len(_EFFECTS)]
            clip = _make_image_clip(item_path, clip_duration, effect)
            label = effect
            effect_index += 1

        clips.append(clip)
        print(f"  [Editor] {i + 1}/{len(media_list)}: {item_type} ({label})")

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  [Editor] Rendering to {output_path} ...")
    video.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    audio.close()
    video.close()
