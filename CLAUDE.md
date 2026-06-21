# agentic-ai — YouTube Automation Project

## What This Project Is
A fully automated YouTube channel pipeline built with Claude and agentic AI patterns.
It researches trending topics, writes scripts, generates voiceovers, creates visuals,
edits videos, and uploads to YouTube — daily, without manual intervention.

This is a personal learning and portfolio project.

---

## Hard Rules (Never Break These)

- **NEVER push to Tarabut/company GitHub** — this is a personal project only
- **NEVER commit secrets** — all API keys go in `.env`, never in code
- **NEVER use `requirements.txt`** — this project uses Poetry exclusively
- **NEVER skip documentation** — every phase ends with docs updated before committing

---

## Project Standards

### Python
- Follow PEP8 for all Python code
- Every function must have a docstring explaining what it does and why
- Use type hints on all function signatures
- No hardcoded values — use `src/config.py` for all configuration

### Git
- Commit messages must be clear and descriptive
- One logical change per commit
- Always push to personal GitHub (`github.com` with `id_ed25519`)
- Branch naming: `phase/N-description` or `feature/description`

### Dependencies
- Use Poetry for all dependency management
- Separate dev dependencies (testing, linting) from production dependencies
- Always commit `poetry.lock`

---

## Project Structure Rules

- New agents → `src/agents/`
- External API integrations → `src/tools/`
- Reusable Claude skills → `src/skills/`
- Configuration and env loading → `src/config.py`
- Tests mirror src structure → `tests/agents/`, `tests/tools/`

---

## Architecture Principles

- **Orchestrator coordinates** — it does not do the work itself
- **Agents specialise** — each agent has one job only
- **Tools are external** — anything calling an external API is a tool
- **Skills are reusable** — if two agents need the same thing, it's a skill

---

## Documentation Rules

- `docs/concepts.md` — update when a new agentic AI concept is introduced
- `docs/tools.md` — update when a new tool/API is added
- `docs/skills.md` — update when a new skill is built
- `docs/hooks.md` — update when a new hook is added
- `docs/phases/phaseN.md` — completed before the phase is committed
- `docs/project-structure.md` — update when folder structure changes

---

## Commit Cadence
- Commit after every meaningful change — do not batch unrelated changes
- Each commit = one logical unit of work
- Push immediately after every commit

## Before Every Commit Checklist
1. Are secrets in `.env` and not in code?
2. Are docs updated for anything new added?
3. Does the code follow PEP8?
4. Is the commit message descriptive?

---

## Open TODOs

### When ready to go full quality (remove test limits):
1. `.env` — set `TEST_MODE=false`
2. `.env` — set `FAL_IMAGE_MODEL=fal-ai/flux-pro/v1.1` (was schnell during testing)
3. `.env` — set `FAL_VIDEO_DISABLED=false` (re-enable Kling AI clips)
4. That's it — no code changes needed, config drives everything

### Planned features not yet built:
- **Shorts/Reels agent** — crop best 60s from final video to 9:16 vertical, add bold captions, export for YouTube Shorts / Instagram Reels / TikTok
- **Captions/subtitles** — burn word-level captions onto video using ElevenLabs timestamps
- **YouTube upload agent** — Phase 7, auto-upload with title, description, tags via YouTube Data API
