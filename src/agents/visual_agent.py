"""
Visual Agent — builds a mixed media sequence of Flux Pro images and Kling AI video clips.

How it works:
    1. Split the script into paragraphs (~25-35 chunks)
    2. One Claude call: for each paragraph decide "image" or "video" and write TWO prompts:
       - image_prompt: cinematic Flux Pro still image description
       - motion_prompt: short Kling animation instruction (for "video" type only)
    3. For all paragraphs: generate the Flux Pro image (start frame / standalone)
    4. For "video" paragraphs: also animate the image with Kling i2v → 5s clip
    5. Clip fails → fall back to the already-generated image (no extra API call needed)
    6. Save the ordered media list to PipelineState for the editor

Cost per video (~30 paragraphs, images only at $0.05):
    ~30 images × $0.05 = $1.50
    With clips: ~10 clips × $0.42 = $4.20 extra
"""

import json
import re
import anthropic
from pathlib import Path
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, FAL_VIDEO_DISABLED, TEST_MODE, TEST_MAX_PARAGRAPHS
from src.tools.image_tool import generate_image
from src.tools.video_tool import animate_image
from src.tools.thumbnail_tool import burn_overlay_text
from src.pipeline.state import PipelineState


_VISUAL_SYSTEM_PROMPT = """
You are a world-class cinematographer and visual director — think Roger Deakins meets documentary
filmmaking. You shoot for a US YouTube/TikTok channel about AI and technology. Every frame you
design must make someone stop scrolling within 2 seconds.

CHANNEL: American adults 25-45. Style: HBO documentary × Vice × Kurzgesagt.
The audience must see THEMSELVES in every frame — diverse Americans in real American environments.

━━━ MEDIA TYPES ━━━
  "image" — Flux Pro AI photorealistic still (use for: emotional close-ups, tension moments,
             quiet devastation, data reveals, wide establishing shots, environment scenes)
  "video" — Kling v3 animated clip (use for: movement, transformation, camera pushes,
             moments of physical reaction, anything with kinetic energy)

TARGET: 70% images, 30% video clips when clips enabled. Images only when disabled.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL COVERAGE RULE — READ THIS FIRST  ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST return EXACTLY one item for EVERY paragraph provided.
If you receive 28 paragraphs, your JSON MUST have 28 items: index 0 through 27.
NEVER skip a paragraph. NEVER merge two paragraphs into one item.
NEVER return fewer items than paragraphs. COUNT THEM before responding.
Missing a paragraph = blank screen in the video = unacceptable.

━━━ RULE 1: PARAGRAPH 0 IS ALWAYS A VIDEO CLIP ━━━
  The first paragraph MUST be type "video". It is the viewer's very first impression.
  Motion in the opening 3 seconds signals high production value and stops the scroll.
  It must also serve as the YouTube thumbnail (extreme shock face, person fills 60%+ of frame).

━━━ RULE 2: FACES DRIVE ENGAGEMENT ━━━
  60% of shots must feature a HUMAN FACE as the primary subject.
  The face communicates before the brain processes words. Show EXTREME emotion:
  — Jaw literally dropped, eyes wide, hand flying to mouth in shock
  — Forehead creased, eyes scanning with growing dread
  — Quiet devastation: the face that has just understood something terrible
  NEVER show neutral or pleasant expressions. NEVER show stock-photo smiles.
  The other 40% can be: DATA scenes, ENVIRONMENT shots, ABSTRACT/conceptual, TEXT CARDS.

━━━ RULE 3: VISUAL VARIETY — NOT JUST FACES ━━━
  Mix your shots like a real documentary:
  — FACE SHOTS: emotional reactions, realizations, tension (60%)
  — ENVIRONMENT SHOTS: empty offices, factory floors, city streets at night (15%)
  — DATA/CONCEPT SHOTS: a stat on a screen, a chart, an empty desk, a layoff notice (15%)
  — ABSTRACT SHOTS: hands typing, a phone notification, a paycheck, a resignation letter (10%)
  Back-to-back face shots with the same character → split with an environment or concept shot.

━━━ RULE 4: NARRATIVE CONTINUITY — SCENES MUST CONNECT ━━━
  This is a story, not a slideshow of random images. Each scene must feel like the next chapter.
  — Introduce your MAIN CHARACTER in paragraph 0. Follow them for the first half.
  — When the script shifts topic or location, you may change subject.
  — COLOR PALETTE stays consistent within scene clusters.
  — Same office, different angles → not same angle twice in a row.

━━━ RULE 5: OVERLAY TEXT FOR KEY MOMENTS ━━━
  For select images (max 30% of total), add "overlay_text" to reinforce a key stat or hook.
  overlay_text must be:
  — SHORT: 2-5 words maximum, ALL CAPS
  — PUNCHY: a number, a stat, a shocking phrase
  — NO company names, no logos, no proper nouns that cause copyright issues

  GOOD examples: "40% INCOME GAP", "11.7M JOBS AT RISK", "YOUR BOSS KNOWS",
                 "THE DATA IS CLEAR", "$27,000 STOLEN", "THEY KNEW"
  BAD examples: "Amazon replacing workers" (too long, company name),
                "Technology is changing jobs" (too vague, not punchy)

  Use overlay_text on: stats reveals, hook moments, chapter transitions, emotional peaks.
  DO NOT use on every image — only where it adds shock or clarity.

━━━ CINEMATOGRAPHY LANGUAGE (use these in every prompt) ━━━

  LENS & CAMERA STYLE (pick one per shot):
    "shot on ARRI Alexa, anamorphic lens, subtle lens flare at frame edge"
    "documentary handheld feel, slight camera breathing, intimate proximity"
    "medium close-up, 85mm portrait lens, background compressed to soft bokeh"
    "extreme close-up of face, 135mm telephoto, every pore visible"
    "wide establishing shot, 24mm, deep focus, foreground detail sharp"

  LIGHTING (pick one per shot):
    "single practical lamp casting deep amber shadows, Rembrandt lighting ratio"
    "blue-white monitor glow as only light source, hard shadows falling away from face"
    "golden hour backlight rimming the silhouette, face in cooler shadow"
    "fluorescent office overhead, harsh and unflattering — feels institutional, trapped"
    "neon city light bleed through rain-streaked window, teal and magenta color split"
    "interrogation-style single overhead light, 90% of frame in deep shadow"

  COLOR GRADING (end most prompts with one):
    "teal-and-orange color grade, shadows pushed cool, skin tones warm"
    "desaturated muted palette, only the face retains color warmth"
    "high contrast monochromatic blue, cold and clinical"
    "deep shadows crushed to black, highlights burning warm — cinematic noir"

  COMPOSITION:
    "rule of thirds, subject at left third, negative space right suggests isolation"
    "symmetrical framing, subject dead-center, feels authoritative and unsettling"
    "foreground object partially obscuring — voyeuristic, like we shouldn't be watching"
    "Dutch angle tilt 8 degrees — psychological unease"

━━━ ABSOLUTE RULES ━━━
  ✗ ZERO text IN the image_prompt — no words, labels, signs, screen text in the actual image
    (overlay_text is SEPARATE — it is burned on AFTER generation, not part of the scene)
  ✗ ZERO logos — no Apple, Google, Amazon, Meta, Microsoft visual identity
  ✗ ZERO watermarks
  ✗ ZERO unrealistic anatomy — no extra fingers, fused hands, floating limbs
  ✗ ZERO stock photo energy — no handshakes, no thumbs up, no staged smiles

━━━ PROMPT STRUCTURE (mandatory for every shot) ━━━
  [WHO: age/gender/ethnicity/appearance] + [WHERE: specific US environment] +
  [WHAT: specific action/micro-expression] + [LENS/CAMERA] + [LIGHTING] +
  [COLOR GRADE] + [COMPOSITION]

  EXPERT EXAMPLE (copy this quality):
  "a 42-year-old Latino male office worker in a rumpled blue dress shirt, tie loosened,
  sits alone in a fluorescent-lit cubicle late at night, staring at his laptop screen
  with hollow eyes, the blue-white glow etching deep shadows under his cheekbones,
  one hand pressed flat against his mouth holding back whatever he's about to say —
  documentary handheld feel, slight camera breathing, 85mm portrait lens,
  background cubicle farm compressed to soft bokeh, desaturated muted palette
  only face retains warmth, teal-and-orange grade, rule of thirds subject left,
  negative space right suggesting the weight of an empty office around him,
  photorealistic, ARRI Alexa quality, ultra-sharp, 16:9"

  ENVIRONMENT EXAMPLE (for non-face shots):
  "a row of empty office desks in a downtown Chicago high-rise at dusk, monitors
  dark and powered down, coffee mugs still on desks as if abandoned mid-day,
  motion-blurred commuters visible through the floor-to-ceiling windows behind,
  wide establishing shot 24mm deep focus, the warm amber glow of the city contrasting
  the cold grey office interior, teal-and-orange color grade, symmetrical composition,
  photorealistic, ARRI Alexa quality, ultra-sharp, 16:9"

━━━ EFFECT ASSIGNMENT (every image must have one) ━━━
  "zoom_in"   — TENSION, REVELATION, DREAD — slowly pushes into subject
  "zoom_out"  — SCALE, ISOLATION, BIGGER PICTURE — pulls back
  "pan_left"  — FORWARD PROGRESSION, TIMELINE, SCANNING
  "pan_right" — REVERSAL, PIVOT, CONTRAST — against natural flow

━━━ VIDEO MOTION PROMPTS ━━━
  The image_prompt IS the first frame. Motion prompt = what changes over 5 seconds.
  Describe what the PERSON does and what we FEEL.

Return ONLY valid JSON. No explanation. No markdown. Format:
{
  "media": [
    {"index": 0, "type": "video", "image_prompt": "...", "motion_prompt": "..."},
    {"index": 1, "type": "image", "image_prompt": "...", "effect": "zoom_in"},
    {"index": 2, "type": "image", "image_prompt": "...", "effect": "pan_left", "overlay_text": "40% INCOME GAP"},
    {"index": 3, "type": "image", "image_prompt": "...", "effect": "zoom_out"}
  ]
}
"""

_MIN_PARA_LEN = 60
_TARGET_CHUNK_WORDS = 35   # ~7-9 seconds of speech per visual at 130wpm
_MAX_CHUNK_WORDS = 50      # hard cap


def _split_paragraphs(script: str) -> list[str]:
    """
    Split script into short chunks suitable for one image/clip each.

    Strategy:
      1. Split on double newlines first (paragraph boundaries)
      2. Any paragraph longer than _TARGET_CHUNK_WORDS gets split further
         on sentence boundaries (period/exclamation/question mark)
      3. Group short sentences so no chunk is under 30 words
    Target: one visual change every 10-15 seconds → 30-40 chunks per 8-min video.
    """
    raw_paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    chunks = []

    for para in raw_paragraphs:
        words = para.split()
        if len(words) <= _MAX_CHUNK_WORDS:
            if len(para) >= _MIN_PARA_LEN:
                chunks.append(para)
            continue

        # Split long paragraph into sentences
        sentences = re.split(r'(?<=[.!?])\s+', para)
        current = []
        current_words = 0

        for sent in sentences:
            sent_words = len(sent.split())
            if current_words + sent_words > _TARGET_CHUNK_WORDS and current:
                chunk_text = " ".join(current)
                if len(chunk_text) >= _MIN_PARA_LEN:
                    chunks.append(chunk_text)
                current = [sent]
                current_words = sent_words
            else:
                current.append(sent)
                current_words += sent_words

        if current:
            chunk_text = " ".join(current)
            if len(chunk_text) >= _MIN_PARA_LEN:
                chunks.append(chunk_text)

    return chunks


_MAX_BATCH = 24  # safe upper bound — 24 × ~250 tokens per prompt ≈ 6000 tokens, under 8192 limit


def _parse_json(raw: str) -> dict:
    """Parse JSON from Claude response, stripping markdown code fences if present."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    return json.loads(raw)


def _call_claude_for_batch(
    client: anthropic.Anthropic,
    model: str,
    paragraphs: list[str],
    offset: int,
) -> list[dict]:
    """
    Ask Claude for a media plan for a single batch of paragraphs.

    Indices in the returned items are global (offset applied), so batches
    can be merged directly without index collisions.
    """
    n = len(paragraphs)
    end_idx = offset + n - 1
    numbered = "\n\n".join(f"[{i + offset}] {p}" for i, p in enumerate(paragraphs))
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=_VISUAL_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"This batch has {n} paragraphs with indices {offset} to {end_idx}. "
                f"Return exactly {n} items, one per paragraph, using indices {offset} to {end_idx}.\n\n"
                f"Script paragraphs:\n\n{numbered}"
            ),
        }],
    )
    data = _parse_json(response.content[0].text)
    return data["media"]


def _fill_missing_paragraphs(media_plan: list[dict], paragraphs: list[str]) -> list[dict]:
    """
    Ensure the media plan covers every paragraph index.

    If Claude skipped any indices, generate default image entries so the
    editor always has a visual for every segment of the audio.
    """
    covered = {item["index"] for item in media_plan}
    added = 0
    for i, para in enumerate(paragraphs):
        if i not in covered:
            # Default: zoom_in image with a basic fallback prompt
            media_plan.append({
                "index": i,
                "type": "image",
                "image_prompt": (
                    f"documentary-style close-up of a 35-year-old American professional, "
                    f"sitting alone in a modern US office at night, expression of deep concern, "
                    f"blue-white monitor glow, 85mm portrait lens, teal-and-orange color grade, "
                    f"photorealistic, ARRI Alexa quality, 16:9"
                ),
                "effect": "zoom_in",
            })
            added += 1
    if added:
        print(f"  [Visual Agent] Filled {added} missing paragraph(s) with default visuals")
    media_plan.sort(key=lambda x: x["index"])
    return media_plan


class VisualAgent:
    """
    Agent that builds the ordered visual media list for one video.

    For all paragraphs: generates a Flux Pro base image.
    For ~30% paragraphs: also animates the image with Kling i2v to produce a clip.
    Falls back to the base image if clip generation fails (no extra cost).
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def run(self, script: str, state: PipelineState) -> None:
        """
        Generate all visual media for the script and save to state.

        Args:
            script: The full video script text.
            state:  PipelineState for this topic — media list saved here.
        """
        paragraphs = _split_paragraphs(script)
        if TEST_MODE and len(paragraphs) > TEST_MAX_PARAGRAPHS:
            print(f"  [Visual Agent] TEST_MODE: capping at {TEST_MAX_PARAGRAPHS} paragraphs (was {len(paragraphs)})")
            paragraphs = paragraphs[:TEST_MAX_PARAGRAPHS]

        n = len(paragraphs)

        # Reuse Claude's media plan if already saved — saves API cost on resume
        if state.has_media_plan():
            media_plan = state.get_media_plan()
            print(f"  [Visual Agent] Resuming from saved media plan ({len(media_plan)} items)...")
        else:
            print(f"  [Visual Agent] {n} paragraphs → asking Claude for media plan...")

            # Batch calls to avoid hitting the 8192 output-token limit
            # (48 × ~250 token prompts = ~12k tokens, well over limit)
            media_plan = []
            num_batches = (n + _MAX_BATCH - 1) // _MAX_BATCH
            for batch_num in range(num_batches):
                start = batch_num * _MAX_BATCH
                end = min(start + _MAX_BATCH, n)
                batch = paragraphs[start:end]
                if num_batches > 1:
                    print(f"  [Visual Agent] Batch {batch_num + 1}/{num_batches} (paragraphs {start}-{end - 1})...")
                batch_plan = _call_claude_for_batch(self.client, self.model, batch, offset=start)
                media_plan.extend(batch_plan)

            media_plan.sort(key=lambda x: x["index"])

            # Safety: enforce paragraph 0 is always a video clip
            if media_plan and media_plan[0]["type"] == "image":
                media_plan[0]["type"] = "video"
                if "motion_prompt" not in media_plan[0]:
                    media_plan[0]["motion_prompt"] = (
                        "camera slowly pushes in toward the subject's face, "
                        "background losing focus, tension building in their expression"
                    )
                print("  [Visual Agent] Enforced: paragraph 0 → video clip (hook must open with motion)")

            # Safety: fill any paragraphs Claude skipped
            media_plan = _fill_missing_paragraphs(media_plan, paragraphs)

            state.save_media_plan(media_plan)

        img_planned = sum(1 for m in media_plan if m["type"] == "image")
        vid_planned = sum(1 for m in media_plan if m["type"] == "video")

        if FAL_VIDEO_DISABLED and vid_planned > 0:
            print(f"  [Visual Agent] FAL_VIDEO_DISABLED=true — treating all {vid_planned} clips as images")
            for item in media_plan:
                item["type"] = "image"
            img_planned += vid_planned
            vid_planned = 0

        print(f"  [Visual Agent] Plan: {img_planned} images + {vid_planned} AI clips. Generating...")

        state.images_dir.mkdir(parents=True, exist_ok=True)
        state.clips_dir.mkdir(parents=True, exist_ok=True)

        media_list = []
        img_counter = 0
        vid_counter = 0
        total = len(media_plan)

        for item in media_plan:
            idx = item["index"]
            media_type = item["type"]
            image_prompt = item["image_prompt"]
            overlay_text = item.get("overlay_text", "")
            img_path = state.images_dir / f"{idx + 1:02d}-para.png"

            # Generate base image — skip if it already exists on disk
            img_counter += 1
            label = "image" if media_type == "image" else f"base frame for clip {vid_counter + 1}"
            if img_path.exists():
                print(f"  [Visual Agent] Image {img_counter}/{total} already exists — skipping (para {idx + 1})")
            else:
                print(f"  [Visual Agent] Image {img_counter}/{total} ({label}, para {idx + 1})...")
                generate_image(prompt=image_prompt, output_path=img_path)

                # Burn overlay text onto image (only for image type, never on base frames for clips)
                if overlay_text and media_type == "image" and img_path.exists():
                    print(f"  [Visual Agent] Burning overlay: '{overlay_text}'")
                    burn_overlay_text(img_path, overlay_text)

            if media_type == "video":
                vid_counter += 1
                motion_prompt = item.get("motion_prompt", "camera slowly zooms in")
                clip_path = state.clips_dir / f"{idx + 1:02d}-clip.mp4"
                if clip_path.exists():
                    print(f"  [Visual Agent] Clip {vid_counter} already exists — skipping (para {idx + 1})")
                    media_list.append({"type": "video", "path": str(clip_path)})
                else:
                    print(f"  [Visual Agent] Animating clip {vid_counter}/{vid_planned}...")
                    success = animate_image(
                        image_path=img_path,
                        motion_prompt=motion_prompt,
                        output_path=clip_path,
                    )
                    if success:
                        media_list.append({"type": "video", "path": str(clip_path)})
                    else:
                        print(f"  [Visual Agent] Clip failed — using base image for para {idx + 1}")
                        media_list.append({"type": "image", "path": str(img_path), "effect": item.get("effect", "zoom_in")})
            else:
                media_list.append({
                    "type": "image",
                    "path": str(img_path),
                    "effect": item.get("effect", "zoom_in"),
                })

        state.save_media_list(media_list)

        final_imgs = sum(1 for m in media_list if m["type"] == "image")
        final_vids = sum(1 for m in media_list if m["type"] == "video")
        print(f"  [Visual Agent] Done: {len(media_list)} items ({final_imgs} images + {final_vids} AI clips)")
