# Tools & External APIs

Every external tool or API used in this project — what it does, why it was chosen, and how it's integrated.

---

## anthropic (Claude SDK)
- **What:** Python SDK for calling Claude models via the Anthropic API.
- **Why chosen:** This project is built around Claude as the AI brain. Official SDK.
- **Used by:** All agents — they all call Claude to make decisions.
- **Docs:** https://docs.anthropic.com
- **Added:** Phase 1

## python-dotenv
- **What:** Loads variables from a `.env` file into the environment.
- **Why chosen:** Keeps secrets out of code. Industry standard for local development.
- **Used by:** `src/config.py` at startup.
- **Added:** Phase 1

---

## ddgs (DuckDuckGo Search)
- **What:** Python library for searching the web via DuckDuckGo.
- **Why chosen:** Free, no API key required, sufficient for finding trending topics.
  Can be swapped for a paid provider (Serper, Tavily) later without changing agents.
- **Used by:** `src/tools/search_tool.py` → called by Research Agent via tool use.
- **Added:** Phase 3

---

## ElevenLabs
- **What:** AI text-to-speech API with 1000+ voices and multiple accents.
- **Why chosen:** Best voice quality and variety available. Industry standard for YouTube automation. Natural sounding, barely detectable as AI.
- **Used by:** `src/tools/elevenlabs_tool.py` → called by Voice Agent.
- **Voice used:** George (ID: JBFqnCBsd6RMkjVDRZzb) — clear, neutral accent, natural delivery.
- **Model:** eleven_multilingual_v2 — best quality, supports multiple languages.
- **Cost:** Free tier 10k chars/month. $5/month for 30k chars (~6 videos). $22/month for 100k chars (~20 videos).
- **Added:** Phase 4

---

## fal.ai + Flux Schnell
- **What:** AI image generation API hosting the Flux family of models.
- **Why chosen:** Single platform for both images (Flux) and video (Kling) under one API key. Flux Schnell is cheapest at ~$0.003/image with good quality.
- **Upgrade path:** Set `FAL_IMAGE_MODEL=fal-ai/flux-pro/v1.1` in `.env` for best quality (~$0.05/image). No code changes needed.
- **Used by:** `src/tools/image_tool.py` → called by Visual Agent.
- **Cost:** ~$0.003/image (Schnell). 6 images per video = ~$0.02/video.
- **Added:** Phase 5

---

---

## fal.ai + Kling v3 (AI video clips)
- **What:** Text-to-video / image-to-video generation via fal.ai hosting Kling v3 standard.
- **Why chosen:** Same API key as Flux. Kling v3 produces smooth, realistic motion from a still image.
- **Used by:** `src/agents/visual_agent.py` (when `FAL_VIDEO_DISABLED` is not set).
- **Cost:** ~$0.42 per 5-second clip. Disabled by default via `FAL_VIDEO_DISABLED=true` to save cost.
- **Added:** Phase 6

---

## Flask (web portal)
- **What:** Lightweight Python web framework.
- **Why chosen:** FastAPI + Jinja2 is broken on Python 3.14 (LRU cache incompatibility). Flask works cleanly on 3.14.
- **Used by:** `web/app.py` — the local web portal for reviewing prompts/images and configuring the pipeline.
- **Start:** `poetry run python -m web.app` → http://localhost:8000
- **Added:** Phase 7

---

## Pillow (image processing)
- **What:** Python Imaging Library fork — reads, modifies, and saves image files.
- **Why chosen:** Used for professional text rendering on thumbnails and scene images. Supports Impact font, stroke outlines, gradient overlays.
- **Used by:** `src/tools/thumbnail_tool.py` — `add_text_to_thumbnail()`, `make_vertical_cover()`, `burn_overlay_text()`.
- **Added:** Phase 7

---

| Phase | Tool | Purpose |
|---|---|---|
| Phase 3 | ElevenLabs | Text-to-speech voiceover generation |
| Phase 5 | fal.ai + Flux Pro | AI image generation |
| Phase 6 | fal.ai + Kling v3 | AI video clip generation |
| Phase 6 | MoviePy + FFmpeg | Video editing and compilation |
| Phase 7 | Flask | Local web portal |
| Phase 7 | Pillow | Thumbnail and overlay text rendering |
