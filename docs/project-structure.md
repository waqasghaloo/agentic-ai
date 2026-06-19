# Project Structure

Every folder and file explained — including why it exists and where new code goes.

---

## Root Level

```
agentic-ai/
├── CLAUDE.md           → Rules and context for Claude. Read at every session start.
├── pyproject.toml      → Project metadata and all dependencies (managed by Poetry).
├── poetry.lock         → Exact locked versions of every dependency. Always committed.
├── .env                → Your actual secrets. NEVER committed to git.
├── .env.example        → Template showing which secrets are needed. Safe to commit.
├── .gitignore          → Files git should never track (.env, __pycache__, etc.)
├── README.md           → Project overview for anyone visiting the repo.
├── docs/               → All documentation lives here.
├── src/                → All source code lives here.
└── tests/              → All tests live here, mirroring src/ structure.
```

---

## `src/` — Source Code

```
src/
├── config.py           → Loads all environment variables in one place.
│                         Why: fail early if a key is missing, not mid-pipeline.
│
├── agents/             → One file per agent. Each agent has exactly one responsibility.
│   ├── orchestrator.py → Coordinates all other agents. Does not do the work itself.
│   ├── research_agent.py
│   ├── script_agent.py
│   ├── voice_agent.py
│   ├── visual_agent.py
│   ├── editor_agent.py
│   ├── metadata_agent.py
│   └── upload_agent.py
│
├── tools/              → Wrappers around external APIs. Called by agents via tool use.
│                         Why separate from agents: tools are stateless API calls;
│                         agents are decision-makers. Keeping them apart makes each
│                         independently testable.
│
├── skills/             → Reusable capabilities shared across multiple agents.
│                         Why separate from tools: skills use Claude internally;
│                         tools call external APIs.
│
└── pipeline/           → Pipeline-level concerns separate from agents and tools.
    └── state.py        → Tracks completed steps per topic. Caches all outputs
                          so nothing is regenerated unnecessarily (cost saving).
```

---

## `docs/` — Documentation

```
docs/
├── concepts.md         → Agentic AI concepts explained + where they appear in project.
├── architecture.md     → System design, agent map, data flow diagram.
├── tools.md            → Every external tool/API: what, why chosen, how it works.
├── skills.md           → Every skill built: purpose, inputs, outputs, when to use.
├── hooks.md            → Every hook: what triggers it, what it does, why it was added.
├── project-structure.md→ This file.
└── phases/
    ├── phase1.md       → Phase 1 journal: goal, steps, decisions, what was learned.
    └── ...
```

---

## `tests/` — Tests

```
tests/
├── agents/             → Tests for each agent (mirrors src/agents/)
├── tools/              → Tests for each tool (mirrors src/tools/)
└── skills/             → Tests for each skill (mirrors src/skills/)
```

**Rule:** Every agent, tool, and skill gets a corresponding test file.

---

## Where Does New Code Go?

| What you're building | Where it goes |
|---|---|
| New agent | `src/agents/your_agent.py` |
| New external API wrapper | `src/tools/your_tool.py` |
| Reusable Claude capability | `src/skills/your_skill.py` |
| New config variable | `src/config.py` + `.env.example` |
| Tests for any of the above | `tests/` mirroring the same path |
