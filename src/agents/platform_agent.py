"""
Platform Agent — generates optimised publish-ready content for each platform.

Why this matters for audience growth:
    Each platform has a different algorithm, audience behaviour, and content format.
    A caption that works on YouTube tanks on TikTok. This agent writes content
    natively for each platform — not repurposed copy-paste.

Output per topic (platforms/ folder):
    youtube/
        thumbnail_final.png   ← 1280x720 with bold hook text overlay
        description.txt       ← copy-paste ready YouTube description
        tags.txt              ← one tag per line, ready for YouTube
    tiktok/
        caption.txt           ← 150-char caption + trending hashtags
        cover.png             ← 9:16 thumbnail with text
    instagram/
        caption.txt           ← longer caption with storytelling hook
        cover.png             ← 9:16 thumbnail with text
    shorts/
        title.txt             ← punchy Shorts title (different from main)
        thumbnail.png         ← 9:16 thumbnail with text

Growth optimisation Claude provides:
    - Platform-specific hashtag sets (trending + niche mix)
    - Hook text optimised per platform attention span
    - Best posting time windows per platform
    - Content angle recommendations (what to emphasise per audience)
"""

import json
import anthropic
from pathlib import Path

from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.thumbnail_tool import add_text_to_thumbnail, make_vertical_cover
from src.pipeline.state import PipelineState


_SYSTEM_PROMPT = """
You are a viral social media strategist for science content with proven results
across YouTube, TikTok, and Instagram. You understand each platform's algorithm deeply.

Given a video title, description, tags, and script — produce platform-specific content
that maximises reach, saves, and shares on each platform.

Return ONLY valid JSON with these exact keys:

"hook_text"
  2-4 WORDS in ALL CAPS for the thumbnail text overlay.
  Must create intense curiosity or shock. Examples:
  "SCIENTISTS STUNNED", "IMPOSSIBLE FIND", "CHANGES EVERYTHING", "NEVER SEEN BEFORE"

"youtube_thumbnail_text"
  Same as hook_text but can be slightly longer (max 5 words).
  This will be burned into the YouTube thumbnail image.

"tiktok_caption"
  Max 150 characters STRICT — TikTok shows nothing beyond 150 before truncation.
  Formula: [SHOCKING STAT OR FACT]. [What it means for the viewer personally.] No questions.
  Must make someone stop mid-scroll. US-focused. Written like a text message from a smart friend.
  Example: "Amazon just automated 4,200 overnight jobs. The replacement system costs $400/month. This is how it happened."

"tiktok_hashtags"
  Array of 10-12 hashtag strings WITH # symbol.
  Formula: 3 mega tags (#fyp #viral #AI), 4 topic tags (#jobs #technology #AIjobs #future),
  2 US market tags (#USA #AmericanWorkers), 2-3 niche community tags (#techjobs #careeradvice).

"instagram_caption"
  250-350 words. Four parts:
    LINE 1: Hook — one sentence that stops the scroll (shocking stat or counterintuitive fact)
    LINE 2: Empty line (forces "more" click on mobile)
    PARAGRAPH 2: The story — make it personal and relatable to the US audience
    PARAGRAPH 3: The twist or what this really means
    FINAL LINE: "Save this. Share it with someone who needs to see it."
  Use line breaks and 1-2 emojis per paragraph. Instagram audience expects a human voice, not corporate.

"instagram_hashtags"
  Array of 28-30 hashtag strings WITH # symbol.
  Mix: broad reach (#AI #technology #jobs #money #career #future),
  US audience (#AmericaJobs #UStech #AmericanWorker),
  niche community (#AItools #techindustry #futureofwork #workplacetechnology),
  discovery tags (#learnontiktok #educationalcontent #mindblown).

"shorts_title"
  Under 55 characters. More emotionally urgent than the main YouTube title.
  Must work without thumbnail context — the title alone makes someone click.
  Use "..." at end to create open loop. Example: "The job AI can't replace yet…"

"facebook_caption"
  200-300 words. Facebook audience skews slightly older (30-55) vs TikTok.
  Structure:
    LINE 1: Bold declarative statement — the most shocking fact (Facebook shows first 3 lines)
    PARAGRAPH 2: The human story — make it relatable to someone with a job, family, mortgage
    PARAGRAPH 3: What they should do / what this means going forward
    FINAL LINE: "Share this with someone who needs to see it before it's too late."
  No hashtag spam — Facebook algorithm deprioritizes posts with many hashtags.
  1-2 emojis max. Tone: concerned friend, not news anchor.

"facebook_hashtags"
  Array of ONLY 3-5 hashtag strings WITH # symbol.
  Facebook penalizes hashtag stuffing. Pick only the highest-reach ones:
  (#AI #Technology #Jobs or topic-specific equivalents).

"best_posting_times"
  Object with keys "youtube", "tiktok", "instagram", "facebook".
  Base on US market (EST/PST friendly) AI/tech audience behaviour research.
  Format: "Mon/Wed/Fri 2-4pm EST" style.
  Facebook peak: weekdays 1-3pm EST (lunch scroll) or 7-9pm EST (evening).

"growth_tips"
  Array of 4-5 specific actionable tips for THIS specific video and topic.
  NOT generic advice. Think: what comment to pin, which community to share in,
  what angle to push in the first 3 hours to trigger the algorithm, what to say in
  Stories/Community tab. Example: "Pin a comment: 'Which job do YOU think is safe?
  Reply with your career below.' — AI anxiety drives insane comment rates on this topic."

Return ONLY valid JSON. No markdown. No explanation.
"""


class PlatformAgent:
    """
    Generates all platform-specific content and thumbnail overlays.

    Creates the full platforms/ folder structure with copy-paste ready
    captions, optimised hashtags, thumbnail images, and posting guidance.

    Skips any file that already exists (resume-safe).
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(self, state: PipelineState) -> dict:
        """
        Generate and save all platform content for the topic.

        Args:
            state: PipelineState for the completed topic.

        Returns:
            The platform metadata dict.
        """
        platform_meta_path = state.platforms_dir / "platform_meta.json"

        if platform_meta_path.exists():
            print("  [Platform Agent] Platform metadata exists — loading from cache.")
            platform_meta = json.loads(platform_meta_path.read_text())
        else:
            yt_meta = state.get_youtube_meta()
            script = state.get_script()

            print("  [Platform Agent] Generating platform-optimised content...")
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=3000,
                system=_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Title: {yt_meta['title']}\n\n"
                        f"Description: {yt_meta['description']}\n\n"
                        f"Script excerpt (first 500 words):\n{script[:2000]}"
                    ),
                }],
            )

            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()

            platform_meta = json.loads(raw)
            state.platforms_dir.mkdir(parents=True, exist_ok=True)
            platform_meta_path.write_text(json.dumps(platform_meta, indent=2))
            print(f"  [Platform Agent] Hook text: {platform_meta['hook_text']}")

        self._write_platform_files(state, platform_meta)
        self._generate_thumbnails(state, platform_meta)
        return platform_meta

    def _write_platform_files(self, state: PipelineState, meta: dict) -> None:
        """Write copy-paste ready text files for each platform."""
        yt_meta = state.get_youtube_meta()

        # YouTube
        yt_dir = state.platforms_dir / "youtube"
        yt_dir.mkdir(parents=True, exist_ok=True)

        desc_path = yt_dir / "description.txt"
        if not desc_path.exists():
            desc_path.write_text(
                f"TITLE:\n{yt_meta['title']}\n\n"
                f"DESCRIPTION:\n{yt_meta['description']}\n\n"
                f"HASHTAGS:\n{' '.join(yt_meta['hashtags'])}\n\n"
                f"Best time to post: {meta['best_posting_times']['youtube']}"
            )

        tags_path = yt_dir / "tags.txt"
        if not tags_path.exists():
            tags_path.write_text(", ".join(yt_meta["tags"]))

        # TikTok
        tt_dir = state.platforms_dir / "tiktok"
        tt_dir.mkdir(parents=True, exist_ok=True)
        caption_path = tt_dir / "caption.txt"
        if not caption_path.exists():
            caption_path.write_text(
                f"{meta['tiktok_caption']}\n\n"
                f"{' '.join(meta['tiktok_hashtags'])}\n\n"
                f"Best time to post: {meta['best_posting_times']['tiktok']}"
            )

        # Instagram
        ig_dir = state.platforms_dir / "instagram"
        ig_dir.mkdir(parents=True, exist_ok=True)
        ig_caption_path = ig_dir / "caption.txt"
        if not ig_caption_path.exists():
            ig_caption_path.write_text(
                f"{meta['instagram_caption']}\n\n"
                f"{' '.join(meta['instagram_hashtags'])}\n\n"
                f"Best time to post: {meta['best_posting_times']['instagram']}"
            )

        # YouTube Shorts
        shorts_dir = state.platforms_dir / "shorts"
        shorts_dir.mkdir(parents=True, exist_ok=True)
        shorts_title_path = shorts_dir / "title.txt"
        if not shorts_title_path.exists():
            shorts_title_path.write_text(meta["shorts_title"])

        # Facebook
        fb_dir = state.platforms_dir / "facebook"
        fb_dir.mkdir(parents=True, exist_ok=True)
        fb_caption_path = fb_dir / "caption.txt"
        if not fb_caption_path.exists():
            fb_caption_path.write_text(
                f"{meta.get('facebook_caption', meta['instagram_caption'])}\n\n"
                f"{' '.join(meta.get('facebook_hashtags', meta['instagram_hashtags'][:5]))}\n\n"
                f"Best time to post: {meta['best_posting_times'].get('facebook', 'Mon/Wed/Fri 1-3pm EST')}"
            )

        # Growth tips (shared)
        tips_path = state.platforms_dir / "growth_tips.txt"
        if not tips_path.exists():
            tips = "\n\n".join(f"• {tip}" for tip in meta.get("growth_tips", []))
            tips_path.write_text(f"GROWTH TIPS FOR THIS VIDEO:\n\n{tips}")

        print("  [Platform Agent] Caption files written for YouTube / TikTok / Instagram / Shorts.")

    def _generate_thumbnails(self, state: PipelineState, meta: dict) -> None:
        """Generate text-overlaid thumbnails for each platform."""
        if not state.thumbnail_path.exists():
            print("  [Platform Agent] Base thumbnail missing — skipping thumbnail generation.")
            return

        hook = meta.get("hook_text", "WATCH THIS")
        yt_hook = meta.get("youtube_thumbnail_text", hook)

        # YouTube thumbnail — 1280x720 landscape
        yt_thumb = state.platforms_dir / "youtube" / "thumbnail_final.png"
        if not yt_thumb.exists():
            print("  [Platform Agent] Generating YouTube thumbnail with text...")
            add_text_to_thumbnail(state.thumbnail_path, yt_thumb, yt_hook)

        # TikTok cover — 9:16 vertical
        tt_cover = state.platforms_dir / "tiktok" / "cover.png"
        if not tt_cover.exists():
            print("  [Platform Agent] Generating TikTok cover (9:16)...")
            make_vertical_cover(state.thumbnail_path, tt_cover, hook)

        # Instagram cover — same 9:16 format
        ig_cover = state.platforms_dir / "instagram" / "cover.png"
        if not ig_cover.exists():
            print("  [Platform Agent] Generating Instagram cover (9:16)...")
            make_vertical_cover(state.thumbnail_path, ig_cover, hook)

        # Shorts thumbnail — same 9:16 format
        shorts_thumb = state.platforms_dir / "shorts" / "thumbnail.png"
        if not shorts_thumb.exists():
            print("  [Platform Agent] Generating Shorts thumbnail (9:16)...")
            make_vertical_cover(state.thumbnail_path, shorts_thumb, hook)

        # Facebook cover — same 9:16 format (used for Facebook Reels)
        fb_cover = state.platforms_dir / "facebook" / "cover.png"
        if not fb_cover.exists():
            print("  [Platform Agent] Generating Facebook cover (9:16)...")
            make_vertical_cover(state.thumbnail_path, fb_cover, hook)

        print("  [Platform Agent] All thumbnails generated.")
