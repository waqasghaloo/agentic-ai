# Phase 1 — Foundation

## Goal
Set up the project professionally so every future phase builds cleanly on top of it.
No pipeline logic yet — just the skeleton, tooling, and first Claude API connection.

## What Was Achieved
- Professional Python project structure with Poetry
- Documentation skeleton covering all aspects of the project
- `CLAUDE.md` with hard rules and project standards
- `src/config.py` for safe, centralised secret loading
- First working Claude API call

## Steps Taken

### 1. Chose Poetry over requirements.txt
**Why:** Poetry provides a lock file (reproducible builds), separates dev from prod
dependencies, and has first-class CI/CD support. Requirements.txt requires manual
management and doesn't lock transitive dependencies reliably.

### 2. Created CLAUDE.md
**Why:** Every Claude Code session reads this file automatically. It acts as standing
instructions — hard rules (never push to Tarabut), coding standards (PEP8, docstrings),
and architecture principles. Without this, instructions would need to be repeated
every session.

### 3. Created `src/config.py` as the single config loader
**Why:** If every file loads its own env vars, a missing key fails silently mid-pipeline.
Centralising in `config.py` means the app fails immediately at startup with a clear
error message pointing to `.env.example`.

### 4. Separated `.env` from `.env.example`
**Why:** `.env` holds real secrets — never committed. `.env.example` is a safe template
showing collaborators (or future-you) what keys are needed.

### 5. Created full documentation skeleton upfront
**Why:** Documentation written after the fact is always incomplete. Creating the structure
in Phase 1 makes it a natural part of the workflow, not an afterthought.

### 6. Added dev dependencies separately (pytest, black, ruff)
**Why:** Dev tools should never end up in production. Poetry's `--group dev` flag keeps
them separate. CI/CD can install production deps only with `poetry install --only main`.

## What You Learned
- **Poetry** manages dependencies, virtual environments, and lock files in one tool
- **CLAUDE.md** is how you give Claude persistent, session-spanning instructions
- **`python-dotenv`** loads a `.env` file so secrets never appear in code
- **Separation of concerns** starts at the folder level — agents, tools, skills are distinct

## What This Unlocks for Phase 2
With the structure in place, Phase 2 can focus entirely on building the first agent
(Script Agent) without any setup overhead. The config, structure, and standards are
already established.
