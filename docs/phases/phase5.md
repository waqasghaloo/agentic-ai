# Phase 5 — Visual Agent + Pipeline State (Cost Caching)

## Goal
Generate images for each section of the video script using Flux via fal.ai,
and introduce pipeline state management to avoid regenerating cached outputs.

## What Was Achieved
- `src/tools/image_tool.py` — wraps fal.ai Flux, saves image to given path
- `src/agents/visual_agent.py` — uses Claude for prompt generation, then fal.ai for images
- `src/pipeline/state.py` — tracks completed steps per topic, caches all outputs
- All agents updated to read/write via PipelineState
- `run.py` updated — each step checks cache before spending money
- `output/` fully gitignored — no media or pipeline data committed

## Key Pattern: Idempotent Pipeline

An idempotent pipeline can be run multiple times without changing the result.
If a step is already done, it skips it. This is a production best practice.

```
Run 1 (full run):
  research   → generates topic          → new
  script     → generates script         → new, saved to cache
  audio      → generates MP3            → new, saved to cache
  images     → generates 6 images       → new, saved to cache

Run 2 (same topic):
  research   → same topic found
  script     → already exists           → SKIPPED (free)
  audio      → already exists           → SKIPPED (free)
  images     → already exist            → SKIPPED (free)
```

**Why this matters:** Claude API, ElevenLabs, and fal.ai all charge per call.
A failed run at step 4 would waste steps 2 and 3 on every retry without caching.

## Steps Taken

### 1. Created `src/pipeline/state.py`
Central state manager per topic. Responsibilities:
- Creates a slug from the topic string (e.g. "5 Facts About Black Holes" → "5-facts-about-black-holes")
- Creates `output/topics/{slug}/` directory
- Writes `metadata.json` tracking completed steps
- Provides has/get/save methods for each pipeline output

Why a dedicated `src/pipeline/` package:
Pipeline concerns (state, orchestration) are separate from agents (AI decisions)
and tools (external APIs). This separation will matter when we add the Orchestrator.

### 2. Updated tools to be path-agnostic
- `elevenlabs_tool.py` now returns bytes — caller decides where to save
- `image_tool.py` now accepts an output_path — caller decides where to save

Why: tools should be stateless. State management belongs in PipelineState, not tools.

### 3. Updated agents to accept PipelineState
Both VoiceAgent and VisualAgent now receive a state object and save through it.
This means the save location is always consistent and trackable.

### 4. Gitignored `output/` entirely
Media files (MP3, PNG, MP4) and metadata must never be committed:
- Too large for git
- Contain generated content, not source code
- Regeneratable from the pipeline

## Output Structure Per Topic

```
output/topics/{slug}/
    metadata.json          ← completed steps, timestamps
    script.txt             ← generated script (plain text)
    audio.mp3              ← ElevenLabs voiceover
    images/
        01-hook.png
        02-point-one.png
        03-point-two.png
        04-point-three.png
        05-point-four.png
        06-conclusion.png
```

## What This Unlocks for Phase 6
With script, audio, and images all saved per topic, Phase 6 (Editor Agent)
can combine them into a final MP4 video. The Editor reads from the same
state directory and produces the final video file there too.
