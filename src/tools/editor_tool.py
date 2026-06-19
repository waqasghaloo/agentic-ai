"""
Editor Tool — assembles images + audio into a final MP4 video.

How it works:
    1. Loads the audio and measures its total duration
    2. Divides duration equally across all images
    3. Applies Ken Burns effect (slow zoom) to each image
    4. Concatenates all image clips into one video
    5. Attaches the audio track
    6. Exports as MP4

Ken Burns effect:
    A slow zoom into a still image that creates the illusion of motion.
    Used by documentaries and faceless YouTube channels to make static
    images feel alive and engaging without needing real video footage.

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
    concatenate_videoclips,
)

# Output video settings
VIDEO_FPS = 24
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080


def _make_ken_burns_clip(image_path: str, duration: float, zoom_direction: str = "in") -> ImageClip:
    """
    Create a video clip from a still image with the Ken Burns zoom effect.

    Args:
        image_path:     Path to the source image.
        duration:       How long this clip should play in seconds.
        zoom_direction: "in" zooms in slowly, "out" zooms out slowly.
                        Alternating directions adds visual variety.

    Returns:
        A MoviePy ImageClip with zoom effect applied.
    """
    # Load and resize image to exact video dimensions
    img = PILImage.open(image_path).convert("RGB")
    img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), PILImage.LANCZOS)
    img_array = np.array(img)

    def make_frame(t: float) -> np.ndarray:
        """Generate one video frame at time t with zoom applied."""
        progress = t / duration  # 0.0 → 1.0 over the clip duration

        # Zoom from 100% to 110% (zoom in) or 110% to 100% (zoom out)
        # 10% zoom is subtle enough to look smooth, noticeable enough to add life
        if zoom_direction == "in":
            zoom = 1.0 + 0.10 * progress
        else:
            zoom = 1.10 - 0.10 * progress

        # Calculate the cropped region (centre crop to simulate zoom)
        crop_h = int(VIDEO_HEIGHT / zoom)
        crop_w = int(VIDEO_WIDTH / zoom)
        y1 = (VIDEO_HEIGHT - crop_h) // 2
        x1 = (VIDEO_WIDTH - crop_w) // 2

        # Crop and resize back to full dimensions
        cropped = img_array[y1:y1 + crop_h, x1:x1 + crop_w]
        result = PILImage.fromarray(cropped).resize(
            (VIDEO_WIDTH, VIDEO_HEIGHT), PILImage.LANCZOS
        )
        return np.array(result)

    clip = VideoClip(make_frame, duration=duration)
    return clip.set_fps(VIDEO_FPS)


def assemble_video(
    image_paths: list[str],
    audio_path: str,
    output_path: Path,
) -> None:
    """
    Assemble images and audio into a final MP4 video.

    Args:
        image_paths: Ordered list of image file paths (one per section).
        audio_path:  Path to the voiceover MP3 file.
        output_path: Where to save the finished MP4.
    """
    # Load audio to determine total video duration
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    # Each image gets an equal share of the total duration
    clip_duration = total_duration / len(image_paths)

    print(f"  [Editor] Audio duration: {total_duration:.1f}s")
    print(f"  [Editor] {len(image_paths)} images × {clip_duration:.1f}s each")

    # Build a clip for each image, alternating zoom direction for variety
    clips = []
    for i, img_path in enumerate(image_paths):
        direction = "in" if i % 2 == 0 else "out"
        clip = _make_ken_burns_clip(img_path, clip_duration, zoom_direction=direction)
        clips.append(clip)
        print(f"  [Editor] Clip {i + 1}/{len(image_paths)} ready (zoom {direction})")

    # Concatenate all image clips into one video
    video = concatenate_videoclips(clips, method="compose")

    # Attach the audio track
    video = video.set_audio(audio)

    # Export — libx264 is the standard H.264 codec for YouTube
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  [Editor] Rendering video to {output_path} ...")
    video.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        logger=None,  # suppress moviepy's verbose output
    )

    # Clean up open file handles
    audio.close()
    video.close()
