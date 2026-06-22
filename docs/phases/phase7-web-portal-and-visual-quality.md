# Phase 7 — Web Portal, Visual Quality & Platform Agents

## Goal
Three parallel improvements to make the pipeline production-ready:
1. A local web portal so configuration and review happen through a UI, not code edits
2. Dramatic visual quality improvements — professional text overlays, context-aware effects, full script coverage
3. Platform agents for TikTok, Instagram, Facebook, and YouTube Shorts metadata

---

## Web Portal (`web/`)

### Why
Previously, every config change (niche, voice, model, video toggle) required editing `.env` directly and reviewing generated image prompts required opening files manually. This made iteration slow and opaque.

### What was built
A Flask app (`web/app.py`) served at `http://localhost:8000` with four pages:

| Route | Purpose |
|---|---|
| `/` | Dashboard grid of all topics with thumbnails and status badges |
| `/topic/<folder>` | Topic detail: image prompts side-by-side with generated images, script, YouTube/platform captions |
| `/config` | Edit key pipeline settings (niche, model, voice, video toggle) without touching `.env` |
| `/api/run` | POST to start a new pipeline run as a background subprocess |
| `/api/status` | Poll pipeline run state (idle / running / finished + exit code) |

### Key implementation details
- **Static output serving**: `/output/<path>` route serves all generated files (images, thumbnails, videos) directly so the browser can display them
- **Thumbnail fallback**: If `thumbnail.png` doesn't exist yet, falls back to the first scene image (`images/01-para.png`) so every topic card has a visual
- **Platform covers section**: topic detail page renders YouTube thumbnail, TikTok/Instagram/Facebook covers, and Shorts thumbnail inline
- **Prompts + images side-by-side**: the Prompts tab shows `image_prompt`, `effect`, and `overlay_text` for each scene alongside the generated image — this is the primary quality review surface
- **Run button with status polling**: JS polls `/api/status` every 10s and updates the button label live

### Why Flask over FastAPI
Python 3.14 broke FastAPI/Jinja2 due to an LRU cache change that made `dict` unhashable as a cache key. Flask has no such issue on 3.14.

---

## Visual Quality Improvements (`src/agents/visual_agent.py`)

### Problem
Long scripts (8+ minutes, 48 paragraphs) were producing only 13 images because the chunk size was too large and Claude's output was being truncated at the 8192 token ceiling.

### Smaller chunks → more visuals
| Setting | Old | New |
|---|---|---|
| `_TARGET_CHUNK_WORDS` | 60 | 35 |
| `_MAX_CHUNK_WORDS` | 90 | 50 |
| Result | ~13 images | ~48 images |
| Seconds per image | ~38s | ~10s |

Smaller chunks mean one image per paragraph — the visual changes every 10 seconds, matching the pace of speech.

### Batching to avoid token truncation
Claude's output is capped at 8192 tokens. A 48-item JSON response exceeds this and gets cut mid-array, causing a JSON parse error.

Fix: `_MAX_BATCH = 24`. Any script with more than 24 paragraphs is split into batches, each called separately via `_call_claude_for_batch(client, model, paragraphs, offset)`. Results are merged and sorted by index.

### Safety net: `_fill_missing_paragraphs()`
Even with batching, if Claude skips an index the editor would have a gap. `_fill_missing_paragraphs()` checks every paragraph index 0..N-1 and inserts a fallback image prompt for any that are missing. This guarantees full coverage.

### Context-aware effects
Previously, all images cycled through effects blindly. Now Claude assigns an `effect` field per scene based on the narrative:

| Effect | When to use |
|---|---|
| `zoom_in` | Tension, urgency, close-up reveal |
| `zoom_out` | Scale, context, stepping back |
| `pan_left` | Forward motion, progress |
| `pan_right` | Reversal, looking back |

The editor uses `item.get("effect", fallback)` — if Claude provides one, it's used; otherwise the cycling fallback applies.

### Text overlays on images (`overlay_text` field)
Claude now optionally adds an `overlay_text` field (2-5 words, ALL CAPS) to ~30% of scenes where a punchline or stat would add impact. Rules:
- No company names or logos
- Only where the text adds emotional punch
- After image generation, `burn_overlay_text()` in `thumbnail_tool.py` modifies the PNG in-place

### Visual variety rule
Claude's system prompt enforces: 60% human faces (close-ups), 15% environment/location, 15% data/concept, 10% abstract. This prevents the "all faces" or "all graphics" monotony from earlier runs.

---

## Professional Text Rendering (`src/tools/thumbnail_tool.py`)

Complete rewrite replacing Arial Bold + drop shadow with:

- **Font**: Impact (`/System/Library/Fonts/Supplemental/Impact.ttf`) with Arial Bold fallback
- **Stroke**: 8-direction outline (`_draw_stroked_text()`), not just a shadow
- **Gradient backing**: semi-transparent dark gradient behind text zone (`_add_gradient_backing()`) so text is readable over any image
- **Color**: yellow-gold `(255, 224, 0)` for overlays, white for covers
- **`burn_overlay_text(image_path, text)`**: modifies image in-place; gradient bottom 28%, centered Impact text

This applies to:
- `add_text_to_thumbnail()` — YouTube 16:9 thumbnail
- `make_vertical_cover()` — TikTok/Instagram/Facebook/Shorts 9:16 cover
- `burn_overlay_text()` — in-scene text overlays

---

## Platform Agents

### `src/agents/platform_agent.py`
Generates platform-specific captions and metadata for TikTok, Instagram, Facebook. Outputs to `output/topics/<folder>/platforms/<platform>/caption.txt` and `growth_tips.txt`.

### `src/agents/shorts_agent.py`
Identifies the strongest 60-second moment in the script for a YouTube Shorts cut. Outputs timestamps and a Shorts-optimized title/description.

### `src/agents/youtube_agent.py`
Generates YouTube metadata: title (optimised for CTR), description (SEO + timestamps), tags, and category. Outputs to `output/topics/<folder>/youtube.json`.

---

## Configuration: CHANNEL_NICHE (`src/config.py`, `.env`)

Previously, the channel niche was hardcoded in `run.py`. Now it's an environment variable:

```
CHANNEL_NICHE=AI and technology impact on American jobs, money, and everyday life
```

Set via the web portal's Config page or directly in `.env`. The research agent uses it to find relevant trending topics.

---

## FAL_VIDEO_DISABLED Flag

Set `FAL_VIDEO_DISABLED=true` in `.env` to generate images only (no Kling video clips). The visual agent and editor both check this flag. Kling clip infrastructure is kept so switching back requires only changing the env var.

Cost implication: images-only mode costs ~$2.40/video (48 × $0.05 Flux Pro) vs ~$22/video with clips.

---

## Summary of Files Changed

| File | Change |
|---|---|
| `web/app.py` | New — Flask portal |
| `web/templates/*.html` | New — dashboard, topic detail, config, base layout |
| `web/__init__.py` | New — makes web/ a Python package |
| `src/agents/visual_agent.py` | Batching, smaller chunks, overlay_text, context-aware effects, variety rules |
| `src/tools/thumbnail_tool.py` | Complete rewrite — Impact font, 8-direction stroke, gradient, burn_overlay_text |
| `src/tools/editor_tool.py` | Effect-aware: uses item's "effect" field, falls back to cycling |
| `src/agents/platform_agent.py` | New — TikTok/Instagram/Facebook captions |
| `src/agents/shorts_agent.py` | New — Shorts clip identification |
| `src/agents/youtube_agent.py` | New — YouTube metadata generation |
| `src/config.py` | Added CHANNEL_NICHE |
| `run.py` | Uses CHANNEL_NICHE, resume-first logic |
| `.env` | Added CHANNEL_NICHE, FAL_VIDEO_DISABLED |
