# Phase 6 — Editor Agent (Video Assembly)

## Goal
Combine the voiceover audio and generated images into a final MP4 video
using the Ken Burns effect, making still images feel dynamic and professional.

## What Was Achieved
- `src/tools/editor_tool.py` — assembles images + audio into MP4 with Ken Burns effect
- `src/agents/editor_agent.py` — simple Transform Agent wrapping the editor tool
- `src/pipeline/state.py` — updated with video_path tracking and has_video() check
- `run.py` updated — full 5-step pipeline: Research → Script → Voice → Images → Video
- First complete MP4 video produced end to end

## Steps Taken

### 1. Installed ffmpeg and MoviePy
- ffmpeg: system-level video processing engine (installed via Homebrew)
- moviepy 1.0.3: Python wrapper around ffmpeg for programmatic video editing
- Pillow: image processing library used for the Ken Burns zoom calculations

### 2. Created `src/tools/editor_tool.py`
Two functions:
- `_make_ken_burns_clip()` — applies slow zoom to a single image using VideoClip
  with a custom make_frame function that crops/resizes at each timestamp
- `assemble_video()` — loads audio, calculates clip duration per image,
  builds all clips, concatenates, attaches audio, exports MP4

Key technical detail: Used `VideoClip(make_frame)` not `ImageClip` because
moviepy's ImageClip expects a numpy array, not a frame function.

### 3. Ken Burns Effect Implementation
```
For each image clip of duration D:
  At time t (0 → D):
    progress = t / D                     # 0.0 → 1.0
    zoom = 1.0 + 0.10 * progress         # 100% → 110% (zoom in)
    crop to zoom region (centre crop)
    resize back to 1920×1080
```
Alternates zoom in / zoom out between clips for visual variety.

### 4. EditorAgent — another Transform Agent
No Claude reasoning needed. Reads from PipelineState, calls assemble_video(),
returns the final video path. Third example of the Transform Agent pattern
(alongside Voice Agent).

### 5. Caching prevents re-renders
`state.has_video()` checks if final.mp4 already exists.
Video rendering is CPU-intensive (minutes of compute). Caching means
a failed upload in Phase 7 won't trigger a full re-render.

## Full Pipeline After Phase 6

```
ResearchAgent  → finds trending topic         (text)
ScriptAgent    → writes full script           (text, cached)
VoiceAgent     → converts to audio            (MP3, cached)
VisualAgent    → generates 6 images           (PNG × 6, cached)
EditorAgent    → assembles final video        (MP4, cached)
```

## Sample Output
- Topic: "Scientists just discovered a brand-new color the human eye can see"
- Audio: 440 seconds (7.3 minutes)
- Video: 6 clips × 73.4 seconds each, alternating zoom in/out

## What This Unlocks for Phase 7
With a finished MP4 ready, Phase 7 (Upload Agent) connects to the YouTube
Data API to upload the video with title, description, and tags automatically.
This is the final step that makes the pipeline fully automated end to end.
