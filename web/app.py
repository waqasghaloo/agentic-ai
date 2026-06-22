"""
Local web portal for the video pipeline.

Start with:  poetry run python -m web.app
Then open:   http://localhost:8000

Pages:
    /            — dashboard: all topics with status + thumbnails
    /topic/<id>  — topic detail: script, image prompts side-by-side with generated images
    /config      — edit pipeline settings (niche, model, video toggle, test mode)
    /api/run     — POST to start a new pipeline run in the background
    /api/status  — GET current pipeline run status
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory

OUTPUT_DIR = Path("output/topics")
ENV_PATH = Path(".env")
_active_proc: subprocess.Popen | None = None

app = Flask(__name__, template_folder="templates", static_folder="static")


# ── Static output files ────────────────────────────────────────────────────────

@app.route("/output/<path:filename>")
def serve_output(filename: str):
    """Serve generated images, thumbnails, and videos."""
    return send_from_directory(Path("output").resolve(), filename)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _read_env() -> dict[str, str]:
    """Parse .env into a dict."""
    result: dict[str, str] = {}
    if not ENV_PATH.exists():
        return result
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        result[key.strip()] = val.strip()
    return result


def _write_env_key(key: str, value: str) -> None:
    """Update or append a single key=value line in .env."""
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    found = False
    new_lines = []
    for line in lines:
        if re.match(rf"^{re.escape(key)}\s*=", line):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(new_lines) + "\n")


def _get_topics() -> list[dict]:
    """Scan output/topics and return metadata for all topic folders."""
    topics = []
    if not OUTPUT_DIR.exists():
        return topics
    for d in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if not d.is_dir() or not (d / "metadata.json").exists():
            continue
        try:
            meta = json.loads((d / "metadata.json").read_text())
        except (json.JSONDecodeError, OSError):
            continue
        yt_meta: dict = {}
        if (d / "youtube.json").exists():
            try:
                yt_meta = json.loads((d / "youtube.json").read_text())
            except (json.JSONDecodeError, OSError):
                pass
        media_list = meta.get("media_list", [])

        # Prefer the generated thumbnail; fall back to the first scene image
        thumb_web = ""
        if (d / "thumbnail.png").exists():
            thumb_web = f"/output/topics/{d.name}/thumbnail.png"
        else:
            first_img = sorted((d / "images").glob("*.png")) if (d / "images").exists() else []
            if first_img:
                thumb_web = f"/output/topics/{d.name}/images/{first_img[0].name}"

        topics.append({
            "folder": d.name,
            "topic": meta.get("topic", ""),
            "title": yt_meta.get("title", ""),
            "has_video": (d / "final.mp4").exists(),
            "has_thumbnail": bool(thumb_web),
            "thumbnail_web": thumb_web,
            "media_count": len(media_list),
            "image_count": sum(1 for m in media_list if m.get("type") == "image"),
            "clip_count": sum(1 for m in media_list if m.get("type") == "video"),
            "steps_done": meta.get("completed_steps", []),
        })
    return topics


def _get_topic_detail(folder_name: str) -> dict:
    """Load full detail for a single topic folder."""
    folder = OUTPUT_DIR / folder_name
    meta = json.loads((folder / "metadata.json").read_text())
    yt_meta: dict = {}
    if (folder / "youtube.json").exists():
        yt_meta = json.loads((folder / "youtube.json").read_text())
    platform_meta: dict = {}
    pm_path = folder / "platforms" / "platform_meta.json"
    if pm_path.exists():
        platform_meta = json.loads(pm_path.read_text())

    script = ""
    if (folder / "script.txt").exists():
        script = (folder / "script.txt").read_text()

    media_plan = meta.get("media_plan", [])
    media_list = meta.get("media_list", [])

    # Build web-accessible image paths — always use the Flux Pro base image for display
    plan_with_images = []
    for item in media_plan:
        idx = item.get("index", -1)
        img_filename = f"{idx + 1:02d}-para.png"
        img_file = folder / "images" / img_filename
        web_path = f"/output/topics/{folder_name}/images/{img_filename}" if img_file.exists() else ""
        plan_with_images.append({**item, "web_image_path": web_path})

    # Platform captions
    captions: dict[str, str] = {}
    for platform in ("tiktok", "instagram", "facebook", "youtube", "shorts"):
        cap_path = folder / "platforms" / platform / "caption.txt"
        if not cap_path.exists():
            cap_path = folder / "platforms" / platform / "description.txt"
        if cap_path.exists():
            captions[platform] = cap_path.read_text()

    growth_tips = ""
    gt_path = folder / "platforms" / "growth_tips.txt"
    if gt_path.exists():
        growth_tips = gt_path.read_text()

    return {
        "folder_name": folder_name,
        "meta": meta,
        "yt_meta": yt_meta,
        "platform_meta": platform_meta,
        "script": script,
        "media_plan": plan_with_images,
        "media_list": media_list,
        "has_video": (folder / "final.mp4").exists(),
        "has_thumbnail": (folder / "thumbnail.png").exists(),
        "thumbnail_web_path": (
            f"/output/topics/{folder_name}/thumbnail.png"
            if (folder / "thumbnail.png").exists()
            else (
                f"/output/topics/{folder_name}/images/{sorted((folder/'images').glob('*.png'))[0].name}"
                if (folder / "images").exists() and sorted((folder / "images").glob("*.png"))
                else ""
            )
        ),
        "captions": captions,
        "growth_tips": growth_tips,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    topics = _get_topics()
    env = _read_env()
    return render_template("dashboard.html",
        topics=topics,
        niche=env.get("CHANNEL_NICHE", ""),
        video_disabled=env.get("FAL_VIDEO_DISABLED", "false").lower() == "true",
    )


@app.route("/topic/<folder_name>")
def topic_detail(folder_name: str):
    detail = _get_topic_detail(folder_name)
    return render_template("topic.html", **detail)


@app.route("/config", methods=["GET", "POST"])
def config_page():
    saved = False
    if request.method == "POST":
        _write_env_key("CHANNEL_NICHE", request.form.get("channel_niche", "").strip())
        # Checkbox sends "true" when checked, absent when unchecked
        _write_env_key("FAL_VIDEO_DISABLED", "true" if request.form.get("fal_video_disabled") else "false")
        _write_env_key("TEST_MODE", "true" if request.form.get("test_mode") else "false")
        _write_env_key("FAL_IMAGE_MODEL", request.form.get("fal_image_model", "fal-ai/flux-pro/v1.1"))
        voice_id = request.form.get("elevenlabs_voice_id_custom", "").strip()
        if not voice_id:
            voice_id = request.form.get("elevenlabs_voice_id", "pNInz6obpgDQGcFmaJgB")
        _write_env_key("ELEVENLABS_VOICE_ID", voice_id)
        _write_env_key("CLAUDE_MODEL", request.form.get("claude_model", "claude-sonnet-4-6").strip())
        saved = True
    env = _read_env()
    return render_template("config.html", env=env, saved=saved)


@app.route("/api/run", methods=["POST"])
def run_pipeline():
    global _active_proc
    if _active_proc and _active_proc.poll() is None:
        return jsonify({"status": "already_running", "pid": _active_proc.pid})
    _active_proc = subprocess.Popen(
        [sys.executable, "run.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=Path(".").resolve(),
    )
    return jsonify({"status": "started", "pid": _active_proc.pid})


@app.route("/api/status")
def pipeline_status():
    global _active_proc
    if _active_proc is None:
        return jsonify({"status": "idle"})
    code = _active_proc.poll()
    if code is None:
        return jsonify({"status": "running", "pid": _active_proc.pid})
    return jsonify({"status": "finished", "exit_code": code})


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)  # run from project root
    app.run(host="0.0.0.0", port=8000, debug=True)
