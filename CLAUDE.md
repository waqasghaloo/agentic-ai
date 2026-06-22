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

## Channel Strategy

- **Niche**: AI and technology impact on American jobs, money, and everyday life
- **Target audience**: US adults 25-45, YouTube + TikTok + Instagram
- **Voice**: Adam (ElevenLabs) — deep American male, authoritative
- **Video length**: 8-10 minutes (unlocks mid-roll ads, 3-4 ad breaks per video)
- **Monetization path**: YouTube Partner Program (1,000 subs + 4,000 watch hours)
- **Platforms**: YouTube (long-form + Shorts) + TikTok + Instagram Reels + Facebook Reels

## Open TODOs

### Planned features not yet built:
- **Burned-in captions** — word-level subtitles on video using ElevenLabs timestamps (boosts retention + accessibility)
- **Trending sound suggestions** — recommend viral TikTok sounds for Shorts cuts
- **YouTube auto-upload agent** — Phase 7, YouTube Data API (title, description, tags, thumbnail)
- **A/B thumbnail testing** — generate 2-3 thumbnail variants, track CTR
