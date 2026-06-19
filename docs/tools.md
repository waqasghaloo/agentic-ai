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

*(More tools added here as each phase introduces them)*

| Phase | Tool | Purpose |
|---|---|---|
| Phase 3 | ElevenLabs | Text-to-speech voiceover generation |
| Phase 3 | DALL-E 3 / Flux | AI image generation for visuals |
| Phase 3 | MoviePy + FFmpeg | Video editing and compilation |
| Phase 5 | YouTube Data API v3 | Uploading videos to YouTube |
