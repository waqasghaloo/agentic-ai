"""
Pexels Tool — searches and downloads free stock video clips.

Why Pexels:
    Free, high-quality stock footage with a generous API tier.
    Mixing real video clips among AI images makes the final video
    feel more dynamic and professional — especially for action-heavy
    science topics where motion footage exists (space, nature, etc.).

How it works:
    1. Search Pexels Videos API with a keyword (e.g. "black hole space")
    2. Pick the best 1080p MP4 from the first result
    3. Download the clip and save to the topic's clips/ folder
    4. Return the local path, or None if no suitable clip is found

Fallback:
    If PEXELS_API_KEY is not set, every call returns None and the
    VisualAgent silently falls back to AI images for that slot.
"""

from pathlib import Path

import requests

from src.config import PEXELS_API_KEY

# Pexels API base URL for video search
_SEARCH_URL = "https://api.pexels.com/videos/search"

# Max clip download duration — longer clips cost more bandwidth
_MAX_CLIP_SECONDS = 30


def search_and_download_clip(query: str, output_path: Path) -> bool:
    """
    Search Pexels for a video matching the query and download the first result.

    Args:
        query:       Search term, e.g. "space telescope stars orbit"
        output_path: Where to save the downloaded MP4 file.

    Returns:
        True if a clip was downloaded successfully, False if not found
        or if PEXELS_API_KEY is not configured.
    """
    if not PEXELS_API_KEY:
        return False

    try:
        response = requests.get(
            _SEARCH_URL,
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query": query,
                "per_page": 3,
                "orientation": "landscape",
                "size": "medium",
            },
            timeout=15,
        )
        response.raise_for_status()
        videos = response.json().get("videos", [])
    except requests.RequestException:
        return False

    if not videos:
        return False

    # Try each result until we find a downloadable 1080p (or best available) MP4
    for video in videos:
        duration = video.get("duration", 9999)
        if duration > _MAX_CLIP_SECONDS:
            continue

        video_files = video.get("video_files", [])
        mp4_files = [
            f for f in video_files
            if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280
        ]
        if not mp4_files:
            continue

        # Pick highest resolution available
        best = max(mp4_files, key=lambda f: f.get("width", 0))
        clip_url = best.get("link")
        if not clip_url:
            continue

        try:
            clip_response = requests.get(clip_url, timeout=60, stream=True)
            clip_response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in clip_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True

        except requests.RequestException:
            continue

    return False
