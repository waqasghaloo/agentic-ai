"""
Pipeline State — tracks progress of a single video pipeline run per topic.

Why this exists:
    Every agent call costs money (Claude API, ElevenLabs, fal.ai).
    If a pipeline run fails halfway, or we want to re-run for any reason,
    we should not regenerate content that already exists.

    This class is the single source of truth for what has been completed
    for a given topic. Each step checks state before spending money.

How it works:
    Each topic gets its own folder under output/topics/{slug}/.
    A metadata.json file tracks which steps are done and where files are saved.
    Agents read paths from state and write paths back to state.

Output structure per topic:
    output/topics/{slug}/
        metadata.json   ← progress tracker
        script.txt      ← generated script (cached)
        audio.mp3       ← generated voiceover (cached)
        images/
            01-hook.png
            02-point-one.png
            ...
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


class PipelineState:
    """
    Manages cached state for one topic's video pipeline.

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
        self.dir = OUTPUT_DIR / self.slug
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
