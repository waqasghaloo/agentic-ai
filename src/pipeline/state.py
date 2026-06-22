"""
Pipeline State — tracks progress of a single video pipeline run per topic.

Why this exists:
    Every agent call costs money (Claude API, ElevenLabs, fal.ai).
    If a pipeline run fails halfway, or we want to re-run for any reason,
    we should not regenerate content that already exists.

    This class is the single source of truth for what has been completed
    for a given topic. Each step checks state before spending money.

How it works:
    Each topic gets its own numbered folder under output/topics/{NNN}-{slug}/.
    A metadata.json file tracks which steps are done and the ordered media list.
    Agents read paths from state and write paths back to state.

Output structure per topic:
    output/topics/001-topic-slug/
        metadata.json   ← progress tracker + media order
        script.txt      ← generated script (cached)
        audio.mp3       ← generated voiceover (cached)
        images/
            01-para.png
            02-para.png
            ...
        clips/
            01-clip.mp4
            02-clip.mp4
            ...
        final.mp4
"""

import json
import re
from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path("output/topics")


def _slugify(text: str, max_len: int = 60) -> str:
    """
    Convert a topic string into a safe, readable folder name.

    Example: "5 Facts About Black Holes!" → "5-facts-about-black-holes"
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)   # remove special chars
    text = re.sub(r"\s+", "-", text.strip())    # spaces to hyphens
    return text[:max_len].rstrip("-")


def _next_number() -> int:
    """Scan existing folders and return the next run number (e.g. 3 if 001 and 002 exist)."""
    if not OUTPUT_DIR.exists():
        return 1
    numbers = []
    for d in OUTPUT_DIR.iterdir():
        if d.is_dir():
            m = re.match(r"^(\d+)-", d.name)
            if m:
                numbers.append(int(m.group(1)))
    return (max(numbers) + 1) if numbers else 1


def find_incomplete_state() -> "PipelineState | None":
    """
    Scan all topic folders and return the first one that has audio but no final video.

    This lets the pipeline finish existing work before starting new topics,
    which avoids spending money on research/script/audio for a new topic when
    a half-finished one is already sitting there waiting.

    Returns None if all existing topics are complete (or none exist yet).
    """
    if not OUTPUT_DIR.exists():
        return None
    for d in sorted(OUTPUT_DIR.iterdir()):  # sorted = lowest number first
        if not d.is_dir():
            continue
        meta_path = d / "metadata.json"
        if not meta_path.exists():
            continue
        audio_exists = (d / "audio.mp3").exists()
        video_exists = (d / "final.mp4").exists()
        if audio_exists and not video_exists:
            try:
                data = json.loads(meta_path.read_text())
                topic = data.get("topic", "")
                if topic:
                    return PipelineState(topic)
            except (json.JSONDecodeError, OSError):
                continue
    return None


def _find_existing_by_slug(slug: str) -> Path | None:
    """
    Search all existing topic folders for a matching slug stored in metadata.json.

    Returns the folder Path if found, None otherwise. This is how we detect
    that a topic has already been started and resume from its cached state
    rather than creating a new numbered folder.
    """
    if not OUTPUT_DIR.exists():
        return None
    for d in OUTPUT_DIR.iterdir():
        if not d.is_dir():
            continue
        meta_path = d / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            data = json.loads(meta_path.read_text())
            if data.get("slug") == slug:
                return d
        except (json.JSONDecodeError, OSError):
            continue
    return None


class PipelineState:
    """
    Manages cached state for one topic's video pipeline.

    Folder naming: output/topics/001-topic-slug/, 002-next-topic/, etc.
    New topics get the next available number. Same topic reuses its folder.

    Usage:
        state = PipelineState(topic)

        if state.has_script():
            script = state.get_script()      # load from cache
        else:
            script = agent.run(topic)        # generate (costs money)
            state.save_script(script)        # cache it
    """

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.slug = _slugify(topic)

        existing = _find_existing_by_slug(self.slug)
        if existing:
            self.dir = existing
        else:
            num = _next_number()
            self.dir = OUTPUT_DIR / f"{num:03d}-{self.slug}"

        self.dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.dir / "metadata.json"
        self._meta = self._load()

    # ── Paths ────────────────────────────────────────────────────────────────

    @property
    def script_path(self) -> Path:
        return self.dir / "script.txt"

    @property
    def audio_path(self) -> Path:
        return self.dir / "audio.mp3"

    @property
    def images_dir(self) -> Path:
        return self.dir / "images"

    @property
    def clips_dir(self) -> Path:
        return self.dir / "clips"

    @property
    def video_path(self) -> Path:
        return self.dir / "final.mp4"

    @property
    def youtube_path(self) -> Path:
        return self.dir / "youtube.json"

    @property
    def thumbnail_path(self) -> Path:
        return self.dir / "thumbnail.png"

    @property
    def platforms_dir(self) -> Path:
        return self.dir / "platforms"

    # ── Metadata ─────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        """Load existing metadata or create fresh."""
        if self.metadata_path.exists():
            with open(self.metadata_path) as f:
                return json.load(f)
        return {
            "topic": self.topic,
            "slug": self.slug,
            "created_at": datetime.now().isoformat(),
            "completed_steps": [],
        }

    def _save(self) -> None:
        with open(self.metadata_path, "w") as f:
            json.dump(self._meta, f, indent=2)

    def _mark_done(self, step: str) -> None:
        if step not in self._meta["completed_steps"]:
            self._meta["completed_steps"].append(step)
        self._save()

    # ── Script ───────────────────────────────────────────────────────────────

    def has_script(self) -> bool:
        return self.script_path.exists()

    def get_script(self) -> str:
        return self.script_path.read_text()

    def save_script(self, script: str) -> None:
        self.script_path.write_text(script)
        self._mark_done("script")

    # ── Audio ─────────────────────────────────────────────────────────────────

    def has_audio(self) -> bool:
        return self.audio_path.exists()

    def save_audio(self, audio_bytes: bytes) -> None:
        self.audio_path.write_bytes(audio_bytes)
        self._mark_done("audio")

    # ── Images ───────────────────────────────────────────────────────────────

    def has_images(self) -> bool:
        return (
            self.images_dir.exists()
            and len(list(self.images_dir.glob("*.png"))) > 0
        )

    def get_image_paths(self) -> list[str]:
        return sorted(str(p) for p in self.images_dir.glob("*.png"))

    # ── Media plan (Claude's per-paragraph image/video decisions) ────────────────

    def has_media_plan(self) -> bool:
        """True if Claude has already produced the media plan for this topic."""
        return bool(self._meta.get("media_plan"))

    def get_media_plan(self) -> list[dict]:
        """Return Claude's per-paragraph media decisions (type + prompts)."""
        return self._meta.get("media_plan", [])

    def save_media_plan(self, plan: list[dict]) -> None:
        """Persist Claude's media plan immediately after it's received."""
        self._meta["media_plan"] = plan
        self._save()

    # ── Media list (images + video clips interleaved) ─────────────────────────

    def has_media(self) -> bool:
        """True if the VisualAgent has finished and saved the full media list."""
        return bool(self._meta.get("media_list"))

    def get_media_list(self) -> list[dict]:
        """
        Return the ordered media sequence for the editor.

        Each item is {"type": "image"|"video", "path": "..."}.
        Images get Ken Burns / pan effects; video clips are trimmed to fit duration.
        """
        return self._meta.get("media_list", [])

    def save_media_list(self, media_list: list[dict]) -> None:
        """Save the interleaved media sequence after VisualAgent completes."""
        self._meta["media_list"] = media_list
        self._mark_done("media")

    # ── Video ─────────────────────────────────────────────────────────────────

    def has_video(self) -> bool:
        return self.video_path.exists()

    # ── YouTube metadata ──────────────────────────────────────────────────────

    def has_youtube_meta(self) -> bool:
        return self.youtube_path.exists()

    def get_youtube_meta(self) -> dict:
        return json.loads(self.youtube_path.read_text())

    def save_youtube_meta(self, meta: dict) -> None:
        self.youtube_path.write_text(json.dumps(meta, indent=2))
        self._mark_done("youtube_meta")
