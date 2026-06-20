# Phase 6b — Video Quality Improvements

## Goal
Make the output video significantly more engaging:
- More images with better voiceover alignment (20-25 instead of 6)
- Add pan left/right effects alongside zoom for visual variety
- Mix in free Pexels stock video clips for motion variety
- Number output folders so the latest run is easy to identify

## What Was Changed

### Numbered output folders (`src/pipeline/state.py`)
- Old: `output/topics/scientists-just-discovered.../`
- New: `output/topics/001-scientists-just-discovered.../`
- `_next_number()` scans existing folders for `NNN-` prefix, increments
- `_find_existing_by_slug()` searches metadata.json files so the same topic
  reuses its existing folder (doesn't create 002-same-topic/)
- Added `clips_dir` property and `has_media()` / `get_media_list()` / `save_media_list()`
  for tracking the interleaved image + video sequence

### Paragraph-level images (`src/agents/visual_agent.py`)
- Old: 6 fixed sections (hook, point-one...conclusion)
- New: one image per paragraph in the script (~20-25 total)
- Script is split on `\n\n`, paragraphs under 80 chars are skipped
- Single Claude call returns both image prompts (one per paragraph) AND
  4 Pexels search queries for stock footage
- Images are much more aligned to the voiceover — the visual matches
  exactly what is being said at that timestamp

### Pexels stock footage (`src/tools/pexels_tool.py`)
- New tool: searches Pexels Videos API and downloads the best 1280p+ MP4
- `search_and_download_clip(query, output_path) -> bool`
- Gracefully returns False if no API key, no result, or download fails
- Pipeline skips stock clips silently if PEXELS_API_KEY is not in .env
- Clips limited to 30 seconds to control file size

### Media interleaving logic (`src/agents/visual_agent.py`)
- After generating all images and clips, builds an ordered media_list
- Pattern: 5 images → 1 stock clip → 5 images → 1 stock clip → ...
- Saved to metadata.json so it's cached and never rebuilt on re-run

### 4 visual effects on images (`src/tools/editor_tool.py`)
- Old: 2 effects (zoom in, zoom out)
- New: 4 effects cycling in order — zoom_in, zoom_out, pan_left, pan_right
- Pan effects load the image at 120% width, then animate x-offset over time
- Effect index only advances for image clips — stock clips don't consume a slot

### Editor updated for mixed media (`src/tools/editor_tool.py`, `src/agents/editor_agent.py`)
- `assemble_video()` now takes `media_list: list[dict]` instead of `image_paths: list[str]`
- For type "image": applies `_make_image_clip()` with the next effect
- For type "video": loads via `VideoFileClip`, trims to clip_duration, resizes to 1920×1080
- `run.py` checks `state.has_media()` instead of `state.has_images()` to skip Step 4

## Sample Result (before vs after)
| Metric           | Before | After                      |
|------------------|--------|----------------------------|
| Image count      | 6      | ~22                        |
| Seconds/image    | 73s    | ~17s                       |
| Effects          | 2      | 4 (zoom in/out + pan L/R)  |
| Stock clips      | 0      | 4 (if Pexels key is set)   |
| Total media items| 6      | ~26                        |

## Pexels Setup
1. Sign up at https://www.pexels.com/api/ (free, no credit card)
2. Get your API key from the dashboard
3. Add to `.env`: `PEXELS_API_KEY=your_key_here`

If the key is not set, the pipeline uses AI images only — no errors.
