# Phase 4 — Voice Agent (ElevenLabs)

## Goal
Convert the generated script into a real MP3 audio file using ElevenLabs.
First phase to produce a media file output (not just text).

## What Was Achieved
- `src/tools/elevenlabs_tool.py` — wraps ElevenLabs API, saves MP3 to disk
- `src/agents/voice_agent.py` — converts script to audio, returns file path
- `output/audio/` — directory where all generated audio files are saved
- `run.py` updated — full 3-agent pipeline: Research → Script → Voice
- First real MP3 generated and verified working

## Steps Taken

### 1. Added ElevenLabs SDK via Poetry
`poetry add elevenlabs` — official SDK, handles API communication and audio streaming.

### 2. Updated `src/config.py` with ElevenLabs settings
Three new config values:
- `ELEVENLABS_API_KEY` — required, loaded from .env
- `ELEVENLABS_VOICE_ID` — defaults to George voice, overridable via .env
- `ELEVENLABS_MODEL` — defaults to eleven_multilingual_v2 (best quality)

Why make voice and model overridable via .env:
Switching voices without touching code. Different niches may suit different voices.

### 3. Created `output/audio/` directory
Why a dedicated output directory:
All generated files go in one place. Easy to find, easy to clear, easy to gitignore.
MP3 and MP4 files added to .gitignore — media files are too large for git.

### 4. Created `src/tools/elevenlabs_tool.py`
The tool does one thing: text in → MP3 file out.
Uses today's date as default filename so daily videos are automatically organised.
Audio streamed in chunks (generator pattern) — efficient for large scripts.

### 5. Created `src/agents/voice_agent.py` — no agentic loop
Key lesson: this agent has NO while loop, NO tool use, NO Claude API call.
Why: the Voice Agent has nothing to decide. It receives text and transforms it.
Not every agent needs Claude reasoning — sometimes an agent is just a clean
wrapper that gives a consistent interface to an external service.

## Key Concept: Two Agent Patterns

**Pattern 1 — Decision Agent (Research Agent):**
Uses Claude + tool use + agentic loop.
Claude decides what to do, when to use tools, how many times.
Use when: the task requires reasoning and judgement.

**Pattern 2 — Transform Agent (Voice Agent):**
No Claude, no loop. Just calls a tool and returns the result.
Use when: the task is a straight conversion with no decisions needed.

Both are valid agents. Choose the pattern that fits the job.

## Pipeline State After Phase 4

```
ResearchAgent  →  finds trending topic        (text)
ScriptAgent    →  writes full script          (text)
VoiceAgent     →  converts to audio           (MP3 file)
```

## What This Unlocks for Phase 5
With audio ready, Phase 5 adds the Visual Agent — generating images for the video.
This introduces image generation APIs (DALL-E or Flux) and produces our second
media output type. Together with the audio, we'll have the raw materials needed
for the Editor Agent to assemble the final video.
