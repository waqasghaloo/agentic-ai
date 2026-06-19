# Agentic AI Concepts

A living document — updated as each new concept is introduced in the project.
Each concept is explained in plain language, then mapped to where it appears in THIS project.

---

## Agent
**What it is:** A program that uses an AI model to decide what to do next, rather than following fixed steps.

**In this project:** Each specialist (Script Agent, Voice Agent, etc.) is an agent — it receives a task, thinks about it using Claude, and decides how to complete it.

---

## Orchestrator
**What it is:** The "manager" agent that breaks a big goal into smaller tasks and delegates them to specialist agents. It does not do the work itself.

**In this project:** `src/agents/orchestrator.py` — receives "make a video today" and coordinates all other agents in the right order.

---

## Sub-agent
**What it is:** A specialist agent that is called by the orchestrator. It has one job and does it well.

**In this project:** Script Agent, Voice Agent, Visual Agent, Editor Agent, Upload Agent — each is a sub-agent.

---

## Tool (Tool Use)
**What it is:** A function that an agent can call to interact with the outside world — an API, a file, a database. The agent decides when to use it.

**In this project:** ElevenLabs API (voiceover), DALL-E (images), YouTube API (upload) — all wrapped as tools in `src/tools/`.

---

## Skill
**What it is:** A reusable capability that multiple agents can use. Avoids repeating the same logic across agents.

**In this project:** e.g. a "format_script" skill used by both the Script Agent and Metadata Agent.

---

## Memory
**What it is:** How an agent remembers things — either within one run (short-term) or across runs (long-term).

**In this project:** *(to be added when we implement memory in a later phase)*

---

## Hook
**What it is:** An automatic action triggered by an event — before/after a tool runs, on a schedule, on failure.

**In this project:** Daily upload trigger, error notification hook — defined in `.claude/settings.json`.

---

## Multi-agent Workflow
**What it is:** Multiple agents working together, each contributing their specialty, coordinated by an orchestrator.

**In this project:** The entire pipeline is a multi-agent workflow — research → script → voice → visual → edit → upload.
