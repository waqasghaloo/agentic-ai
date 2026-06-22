"""
Thumbnail Tool — professional text overlays for thumbnails, covers, and scene images.

Typography standards:
    Font: Impact (the YouTube thumbnail standard — condensed, ultra-bold)
    Text color: bright yellow-gold (#FFE000) for thumbnails, white for covers
    Stroke: 4px black outline on all sides — readable on ANY background
    Backing: semi-transparent dark gradient so text is always legible
    Sizing: aggressive — text fills 30-40% of image width
"""

import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
_ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
_YOUTUBE_SIZE = (1280, 720)
_VERTICAL_SIZE = (1080, 1920)


def _font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load Impact (preferred) or Arial Bold as fallback."""
    try:
        return ImageFont.truetype(_IMPACT, size)
    except OSError:
        return ImageFont.truetype(_ARIAL_BOLD, size)


def _draw_stroked_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    stroke_width: int = 5,
    stroke_fill: tuple = (0, 0, 0),
    anchor: str = "lm",
) -> None:
    """Draw text with a solid stroke/outline — readable on any background."""
    x, y = xy
    # Draw stroke by offsetting in 8 directions
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=stroke_fill, anchor=anchor)
    # Draw main text on top
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)


def _add_gradient_backing(
    img: Image.Image,
    zone_top: int,
    zone_bottom: int,
    alpha: int = 180,
) -> Image.Image:
    """Add a dark semi-transparent gradient over a vertical zone of the image."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    zone_height = zone_bottom - zone_top
    for y in range(zone_height):
        # Fade from 0 alpha at top of zone to `alpha` at bottom
        a = int(alpha * (y / zone_height))
        draw.rectangle([0, zone_top + y, img.width, zone_top + y + 1], fill=(0, 0, 0, a))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def add_text_to_thumbnail(
    source_path: Path,
    output_path: Path,
    hook_text: str,
    size: tuple[int, int] = _YOUTUBE_SIZE,
) -> None:
    """
    Resize source thumbnail to YouTube spec and add bold hook text overlay.

    Args:
        source_path: Flux Pro generated thumbnail image.
        output_path: Where to save the final thumbnail.
        hook_text:   Short 2-5 word hook in ALL CAPS (e.g. "THEY KNEW").
        size:        Output dimensions (width, height).
    """
    img = Image.open(source_path).convert("RGB")
    img = img.resize(size, Image.LANCZOS)
    w, h = size

    # Wrap text: max 10 chars per line so font stays huge
    lines = textwrap.wrap(hook_text.upper(), width=10)

    # Font size: aggressive — Impact at 1/7 of width
    font_size = max(100, w // 7)
    font = _font(font_size)

    line_h = int(font_size * 1.1)
    total_text_h = len(lines) * line_h
    pad = 55

    # Dark gradient in bottom 40% of image so text always pops
    gradient_top = int(h * 0.60)
    img = _add_gradient_backing(img, gradient_top, h, alpha=200)

    draw = ImageDraw.Draw(img)

    # Position: bottom-left, above padding
    y_start = h - total_text_h - pad

    for line in lines:
        _draw_stroked_text(
            draw, line,
            xy=(pad, y_start + line_h // 2),
            font=font,
            fill=(255, 224, 0),   # YouTube yellow-gold
            stroke_width=6,
            anchor="lm",
        )
        y_start += line_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")


def make_vertical_cover(
    source_path: Path,
    output_path: Path,
    hook_text: str,
) -> None:
    """
    Crop source thumbnail to 9:16 vertical and add professional text overlay.

    Used for TikTok / Instagram / Facebook Reels covers and YouTube Shorts thumbnail.
    Two-zone design: large hook text at top, platform secondary text reserved at bottom.
    """
    img = Image.open(source_path).convert("RGB")
    src_w, src_h = img.size

    # Center-crop to 9:16 aspect from landscape
    target_w = int(src_h * 9 / 16)
    x_start = (src_w - target_w) // 2
    cropped = img.crop((x_start, 0, x_start + target_w, src_h))
    vertical = cropped.resize(_VERTICAL_SIZE, Image.LANCZOS)

    vw, vh = _VERTICAL_SIZE

    # Wrap to max 10 chars per line — keeps font BIG
    lines = textwrap.wrap(hook_text.upper(), width=10)
    font_size = max(110, vw // 6)    # Impact at 1/6 of width = very large
    font = _font(font_size)
    line_h = int(font_size * 1.15)
    total_text_h = len(lines) * line_h
    pad = 70

    # Add gradient backing at bottom 35% of image
    gradient_top = int(vh * 0.65)
    vertical = _add_gradient_backing(vertical, gradient_top, vh, alpha=210)

    draw = ImageDraw.Draw(vertical)

    # Position: bottom center, above bottom padding
    y_start = vh - total_text_h - pad

    for line in lines:
        _draw_stroked_text(
            draw, line,
            xy=(vw // 2, y_start + line_h // 2),
            font=font,
            fill=(255, 255, 255),   # White on vertical covers — cleaner than yellow
            stroke_width=7,
            anchor="mm",            # center-anchor for vertical covers
        )
        y_start += line_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    vertical.save(str(output_path), "PNG")


def burn_overlay_text(image_path: Path, text: str) -> None:
    """
    Burn a punchline or stat as text overlay onto a generated scene image.

    Called by VisualAgent after image generation, only for images marked
    with overlay_text in the media plan. Modifies the image in-place.

    Design: dark gradient backing in bottom 25% + large Impact text centered.
    Text stays short (2-5 words) and punchy (stats, hooks, punchlines).
    """
    try:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size

        lines = textwrap.wrap(text.upper(), width=14)
        font_size = max(70, w // 11)
        font = _font(font_size)
        line_h = int(font_size * 1.15)
        total_text_h = len(lines) * line_h
        pad = 40

        # Gradient backing in bottom 28%
        gradient_top = int(h * 0.72)
        img = _add_gradient_backing(img, gradient_top, h, alpha=190)

        draw = ImageDraw.Draw(img)

        y_start = h - total_text_h - pad
        for line in lines:
            _draw_stroked_text(
                draw, line,
                xy=(w // 2, y_start + line_h // 2),
                font=font,
                fill=(255, 224, 0),  # Yellow-gold for scene images
                stroke_width=5,
                anchor="mm",
            )
            y_start += line_h

        img.save(str(image_path), "PNG")
    except Exception as e:
        print(f"  [Thumbnail] Warning: overlay text failed — {e}")
