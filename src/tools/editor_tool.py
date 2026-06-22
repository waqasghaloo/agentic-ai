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

Effects on images (chosen per-scene by the Visual Agent based on emotional context):
    zoom_in  — tension, revelation, dread — slow push into subject
    zoom_out — scale, isolation, bigger picture — pull back
    pan_left — forward progression, scanning — natural eye movement
    pan_right — reversal, pivot, contrast — against natural flow

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

# Kling clips are 5s — editor slots may be 10-40s, so we loop them
_CLIP_LOOP_THRESHOLD = 5.5  # seconds; clips shorter than this get looped

# Output video settings
VIDEO_FPS = 24
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Fallback effect cycle used only when an image has no explicit effect assigned
_EFFECTS = ["zoom_in", "zoom_out", "pan_left", "pan_right"]

# How much wider the image is made for panning (20% gives smooth travel room)
_PAN_SCALE = 1.20


def _make_image_clip(
    duration: float,
    effect: str,
    image_path: str = None,
    image_array: np.ndarray = None,
) -> VideoClip:
    """
    Create a Ken Burns / pan clip from a still image file or numpy array.

    Args:
        duration:     How long this clip should play in seconds.
        effect:       One of "zoom_in", "zoom_out", "pan_left", "pan_right".
        image_path:   Path to the source image (provide this OR image_array).
        image_array:  Raw RGB numpy array (used when holding last video frame).
    """
    if image_array is not None:
        img = PILImage.fromarray(image_array.astype("uint8")).convert("RGB")
    else:
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
    Load a Kling clip and fill the full slot duration without repetition.

    Kling clips are 5s. Slots can be 15-30s. Old approach looped — causing
    the same animation to play 3-4x which felt cheap and repetitive.

    New approach: play the clip once, then hold the last frame with a subtle
    slow zoom for the remainder. Looks intentional and cinematic, not looped.
    """
    clip = VideoFileClip(clip_path)

    # Resize to target resolution first (Pillow 10+ safe)
    if clip.size != (VIDEO_WIDTH, VIDEO_HEIGHT):
        clip = clip.fl_image(
            lambda img: np.array(
                PILImage.fromarray(img).resize((VIDEO_WIDTH, VIDEO_HEIGHT), PILImage.LANCZOS)
            )
        )
    clip = clip.set_fps(VIDEO_FPS)

    if clip.duration >= duration:
        return clip.subclip(0, duration)

    # Clip is shorter than slot — play once, hold last frame with slow zoom
    remaining = duration - clip.duration
    last_frame = clip.get_frame(clip.duration - 0.05)
    hold = _make_image_clip(
        image_array=last_frame,
        duration=remaining,
        effect="zoom_in",
    )
    return concatenate_videoclips([clip, hold])


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
    _fallback_idx = 0  # used only when item has no explicit effect

    for i, item in enumerate(media_list):
        item_type = item["type"]
        item_path = item["path"]

        if item_type == "video":
            clip = _make_video_clip(item_path, clip_duration)
            label = "clip"
        else:
            # Use per-scene effect assigned by Visual Agent; fall back to cycling
            if "effect" in item:
                effect = item["effect"]
            else:
                effect = _EFFECTS[_fallback_idx % len(_EFFECTS)]
                _fallback_idx += 1
            clip = _make_image_clip(duration=clip_duration, effect=effect, image_path=item_path)
            label = effect

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
