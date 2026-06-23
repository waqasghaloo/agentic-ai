# Agentic AI — Automated YouTube Channel Pipeline

A fully automated video pipeline that researches trending topics, writes scripts, generates voiceovers, creates AI images, edits videos, and produces platform-ready content for YouTube, TikTok, Instagram, and Facebook — daily, without manual intervention.

Built with Claude (Anthropic), fal.ai (Flux Pro + Kling), and ElevenLabs.

---

## What It Does

1. **Research** — finds trending topics in your niche using DuckDuckGo
2. **Script** — writes an 8-10 minute documentary-style YouTube script
3. **Voice** — converts the script to audio via ElevenLabs (Adam voice)
4. **Visuals** — generates ~48 AI images (Flux Pro) with context-aware effects and text overlays
5. **Edit** — assembles images + audio into a final MP4 with Ken Burns effects
6. **Platform** — generates YouTube metadata, TikTok/Instagram/Facebook captions, Shorts cut points
7. **Thumbnails** — creates professional thumbnails and vertical covers with Impact font text

---

## Web Portal

A local web portal for reviewing and configuring everything without touching code.

```bash
poetry run python -m web.app
```

Open `http://localhost:8000` to:
- Review every image prompt side-by-side with its generated image
- Edit pipeline settings (niche, model, voice, video toggle)
- Trigger new pipeline runs and monitor status
- See YouTube/platform captions and platform covers per topic

---

## Setup

### Prerequisites
- Python 3.11+ with [Poetry](https://python-poetry.org/)
- FFmpeg installed (`brew install ffmpeg` on Mac)

### Install
```bash
git clone https://github.com/waqasghaloo/agentic-ai.git
cd agentic-ai
poetry install
cp .env.example .env
# Fill in your API keys in .env
```

### API Keys needed (in `.env`)
| Key | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `FAL_KEY` | fal.ai/dashboard |
| `ELEVENLABS_API_KEY` | elevenlabs.io |

### Run the pipeline
```bash
poetry run python run.py
```

The pipeline is resume-safe — if it stops mid-run, re-running picks up where it left off.

---

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `CHANNEL_NICHE` | AI and tech impact on American jobs | Topic focus for research |
| `FAL_IMAGE_MODEL` | `fal-ai/flux-pro/v1.1` | Image model ($0.05/image) |
| `FAL_VIDEO_DISABLED` | `true` | Set `false` to enable Kling video clips |
| `ELEVENLABS_VOICE_ID` | Adam | ElevenLabs voice ID |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model for all agents |
| `TEST_MODE` | `false` | Limits audio to 1 min for cheap test runs |

All settings can also be changed through the web portal at `/config`.

---

## Output

Each topic is saved to `output/topics/<NNN>-<slug>/`:

```
001-topic-slug/
├── script.txt          → Full video script
├── audio.mp3           → ElevenLabs voiceover
├── images/             → Generated Flux Pro images (01-para.png, 02-para.png, ...)
├── final.mp4           → Edited video
├── thumbnail.png       → YouTube 16:9 thumbnail
├── youtube.json        → Title, description, tags
├── metadata.json       → Pipeline state (used for resume)
└── platforms/
    ├── tiktok/         → Caption, vertical cover
    ├── instagram/      → Caption, vertical cover
    ├── facebook/       → Caption, vertical cover
    └── shorts/         → Clip points, Shorts thumbnail
```

---

## Cost per Video (approximate)

| Item | Cost |
|---|---|
| 48 AI images (Flux Pro) | ~$2.40 |
| ElevenLabs audio (~7,000 chars) | ~$0.07 |
| Claude API calls | ~$0.30 |
| **Total** | **~$2.77/video** |

Add ~$18 if Kling video clips are enabled (`FAL_VIDEO_DISABLED=false`).

---

## Project Structure

```
src/agents/     → One agent per pipeline step
src/tools/      → External API wrappers (fal.ai, ElevenLabs, etc.)
src/pipeline/   → State management and resume logic
web/            → Flask web portal
docs/           → Full documentation per phase
```

See `docs/project-structure.md` for the full breakdown.

---

## Tech Stack

| Component | Technology |
|---|---|
| AI brain | Claude (Anthropic) |
| Image generation | Flux Pro v1.1 via fal.ai |
| Video clips | Kling v3 via fal.ai |
| Text-to-speech | ElevenLabs |
| Video editing | MoviePy + FFmpeg |
| Image processing | Pillow |
| Web portal | Flask |
| Dependency management | Poetry |
