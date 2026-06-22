"""
YouTube Meta Agent — generates everything needed to publish a video.

For each completed topic it produces:
    youtube.json   — title, description, tags, hashtags, thumbnail_prompt
    thumbnail.png  — Flux Pro image designed for YouTube thumbnail (1280x720)

Why thumbnails matter: CTR (click-through rate) is the #1 factor YouTube's
algorithm uses to promote videos. A great thumbnail + title is worth more
than the video quality itself in the first 24 hours.

Thumbnail formula:
    - One dramatic human face (extreme emotion: shock, awe, curiosity)
    - High contrast background (deep space, lab glow, bright colours)
    - No text in the image — text is overlaid separately in editing
    - 16:9, cinematic, ultra-sharp
"""

import json
import anthropic
from pathlib import Path

from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.image_tool import generate_image
from src.pipeline.state import PipelineState


_SYSTEM_PROMPT = """
You are a YouTube SEO and growth expert for a US-market AI/technology channel.
Your metadata is what gets the video discovered and clicked. This is your only job.

Given a video script, produce a JSON object with these fields:

"title"
  - 55-65 characters max (longer gets cut in search results)
  - FORMULA: [Specific shocking number or fact] + [What it means for the viewer]
  - The main keyword must appear in the FIRST 3 words
  - Use parentheses for the emotional hook: "AI Replaced 40,000 Jobs Last Month (Yours Could Be Next)"
  - Power words: "Just", "Finally", "They Won't Tell You", "Exposed", "The Truth About"
  - The title must be 100% deliverable by the script — no misleading claims
  - Target US search terms Americans actually type into YouTube

"description"
  - First 2 lines (150 chars) are shown before "show more" — make them land hard
  - 350-450 words total
  - Structure: Hook (2 lines) | What you'll discover | Chapter timestamps | Keywords | CTA
  - Chapter timestamps format:
    00:00 [Topic cold open]
    00:30 What this means for you
    02:00 The full story
    06:30 The twist nobody expected
    07:30 What to do about it
  - End with: "Subscribe — we cover AI and tech stories that affect YOUR money and career, daily."
  - Naturally embed 4-6 high-volume keywords

"tags"
  - Array of 28-32 strings
  - Include: 5 broad (AI, technology, jobs, future, money), 10 topic-specific,
    5 US-specific (american jobs, US economy, united states), 5 question-format
    ("will AI take my job", "how to survive AI"), 3-5 trending related terms
  - Each tag: 1-6 words, no hashtag symbol

"hashtags"
  - Array of 7-9 strings WITH # symbol
  - Mix: viral (#AI #tech #fyp #viral), topic-specific, US-market (#USJobs #AmericanTech)

"thumbnail_prompt"
  This single image determines 70% of whether someone clicks. Study what gets clicked.

  THE VIRAL THUMBNAIL FORMULA:
    - ONE face, front-facing, eyes wide, expression is MAXIMUM SHOCK or DISBELIEF
    - Face occupies 65-75% of the total frame — not a headshot, not a full body
    - Mouth slightly open, eyes wide enough to show white above the iris
    - One hand raised near face (pointing, covering mouth, or pressed to cheek) — adds drama
    - Background: ONE strong contrasting color (deep red, electric blue, or pure black)
      that makes the face pop — the background itself should feel like something is WRONG
    - Subject: relatable American — office worker, regular person in their 30s-40s,
      NOT a celebrity, NOT a scientist, NOT someone unrelatable
    - Lighting: dramatic split lighting OR strong rim light — NOT flat, NOT even
    - The image must feel like the person just learned something that changed everything

  WRITE IT LIKE THIS (copy this quality):
  "a 39-year-old white woman with shoulder-length brown hair, wearing a simple grey
  office shirt, stares directly into the lens with jaw dropped and eyes wide —
  pupils dilated, whites visible above the iris — right hand pressed to the side of
  her face in shock, left hand pointing slightly downward at something off-frame,
  face filling 70% of frame, lit by a single dramatic side key light leaving the
  other half of her face in deep shadow, background pure deep crimson red creating
  maximum contrast, shot on 85mm portrait lens with shallow depth of field,
  background completely blurred, ultra-sharp focus on her face, cinematic,
  photorealistic, 16:9, thumbnail quality, no text, no logos"

Return ONLY valid JSON. No markdown fences. No explanation.
"""


class YouTubeMetaAgent:
    """
    Generates YouTube-ready metadata and a thumbnail image for a completed topic.

    Checks for existing youtube.json and thumbnail.png — skips if already done.
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(self, state: PipelineState) -> dict:
        """
        Generate and save YouTube metadata + thumbnail for the given topic.

        Args:
            state: PipelineState for the completed topic.

        Returns:
            The youtube metadata dict.
        """
        if state.has_youtube_meta():
            print("  [YouTube Agent] Metadata already exists — loading from cache.")
            return state.get_youtube_meta()

        script = state.get_script()
        print("  [YouTube Agent] Generating title, description, tags, hashtags...")

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Video script:\n\n{script}"}],
        )

        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()

        meta = json.loads(raw)
        state.save_youtube_meta(meta)

        print(f"  [YouTube Agent] Title: {meta['title']}")
        print(f"  [YouTube Agent] Tags: {len(meta['tags'])} tags, {len(meta['hashtags'])} hashtags")

        # Generate thumbnail if it doesn't exist
        if not state.thumbnail_path.exists():
            print("  [YouTube Agent] Generating thumbnail image...")
            generate_image(
                prompt=meta["thumbnail_prompt"],
                output_path=state.thumbnail_path,
            )
            print(f"  [YouTube Agent] Thumbnail saved: {state.thumbnail_path}")
        else:
            print("  [YouTube Agent] Thumbnail already exists — skipping.")

        return meta
