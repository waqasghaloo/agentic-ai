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

*(More tools added here as each phase introduces them)*

| Phase | Tool | Purpose |
|---|---|---|
| Phase 3 | ElevenLabs | Text-to-speech voiceover generation |
| Phase 3 | DALL-E 3 / Flux | AI image generation for visuals |
| Phase 3 | MoviePy + FFmpeg | Video editing and compilation |
| Phase 5 | YouTube Data API v3 | Uploading videos to YouTube |
