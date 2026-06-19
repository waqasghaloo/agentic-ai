# Architecture

System design, agent map, and data flow for the YouTube automation pipeline.

---

## Overview

A multi-agent pipeline where an Orchestrator coordinates specialist sub-agents.
Each agent has one job. External APIs are wrapped as tools. Everything is triggered daily.

---

## Agent Map

```
Daily Trigger (Hook)
        │
        ▼
  Orchestrator Agent
  (coordinates all below)
        │
        ├──▶ Research Agent ──▶ [Web Search Tool]
        │         │ topic + research
        │         ▼
        ├──▶ Script Agent ──▶ [Claude: write script]
        │         │ script
        │         ▼
        ├──▶ Voice Agent ──▶ [ElevenLabs Tool]
        │         │ audio file
        │         ▼
        ├──▶ Visual Agent ──▶ [DALL-E / Flux Tool]
        │         │ image/video files
        │         ▼
        ├──▶ Editor Agent ──▶ [MoviePy/FFmpeg Tool]
        │         │ final video file
        │         ▼
        ├──▶ Metadata Agent ──▶ [Claude: write title/desc/tags]
        │         │ title, description, tags
        │         ▼
        └──▶ Upload Agent ──▶ [YouTube API Tool]
                              uploaded ✓
```

---

## Data Flow

| Step | Input | Output |
|---|---|---|
| Research | Nothing (uses today's date/trends) | Topic + research notes |
| Script | Topic + research notes | Full video script |
| Voice | Script | Audio file (.mp3) |
| Visual | Script (for context) | Images/clips |
| Editor | Audio + visuals | Final video (.mp4) |
| Metadata | Script + topic | Title, description, tags |
| Upload | Video + metadata | YouTube video URL |

---

## Key Design Decisions

**Why separate agents instead of one big script?**
Each agent can be developed, tested, and replaced independently.
If ElevenLabs goes down, only the Voice Agent changes — nothing else.

**Why does the Orchestrator not do the work?**
Separation of concerns. The Orchestrator's only job is sequencing and error handling.
If it also wrote scripts, a script bug would break the whole coordinator.

**Why are tools separate from agents?**
Tools are stateless API calls. Agents are decision-makers.
A tool can be reused by multiple agents without duplication.
