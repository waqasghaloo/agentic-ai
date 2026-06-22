"""
Pipeline runner — cost-efficient, never regenerates completed work.

Priority on every run:
  1. Resume any topic that has audio but no final video (finish before starting new)
  2. Only run the Research Agent when there is truly no incomplete work

Each step checks its own cache — skip if done, generate if not.
Individual images and clips are also skipped if the file already exists,
so a mid-run failure resumes from where it stopped.

Usage:
    poetry run python run.py               # auto-resume or research new topic
    poetry run python run.py "My Topic"    # force a specific topic (skip research)
"""

from src.config import CHANNEL_NICHE
from src.agents.research_agent import ResearchAgent
from src.agents.script_agent import ScriptAgent
from src.agents.voice_agent import VoiceAgent
from src.agents.visual_agent import VisualAgent
from src.agents.editor_agent import EditorAgent
from src.agents.youtube_agent import YouTubeMetaAgent
from src.agents.shorts_agent import ShortsAgent
from src.agents.platform_agent import PlatformAgent
from src.pipeline.state import PipelineState, find_incomplete_state


def _run_steps(state: PipelineState) -> None:
    """Run all pipeline steps for a given state, skipping completed ones."""

    topic = state.topic
    print(f"      Topic:  {topic}")
    print(f"      Folder: {state.dir}\n")

    # Step 2: Script
    if state.has_script():
        print("[2/5] Script already exists — loading from cache.")
        script = state.get_script()
    else:
        print("[2/5] Script Agent generating script...")
        script = ScriptAgent().run(topic)
        state.save_script(script)
        print(f"      Script saved ({len(script)} characters).")
    print()

    # Step 3: Voice
    if state.has_audio():
        print("[3/5] Audio already exists — skipping ElevenLabs call.")
    else:
        print("[3/5] Voice Agent converting script to audio...")
        VoiceAgent().run(script, state)
    print()

    # Step 4: Images + clips
    if state.has_media():
        print("[4/5] Media already complete — skipping generation.")
    else:
        print("[4/5] Visual Agent generating images and clips...")
        VisualAgent().run(script, state)
    print()

    # Step 5: Video
    if state.has_video():
        print("[5/5] Video already exists — skipping render.")
        video_path = str(state.video_path)
    else:
        print("[5/5] Editor Agent assembling final video...")
        video_path = EditorAgent().run(state)
    print()

    # Step 6: YouTube metadata + thumbnail
    print("[6/7] YouTube Agent generating title, description, tags, thumbnail...")
    yt_meta = YouTubeMetaAgent().run(state)
    print()

    # Step 7: Platform cuts + optimised captions (TikTok / Instagram / Shorts)
    print("[7/7] Platform Agent creating Shorts cuts and platform captions...")
    ShortsAgent().run(state)
    PlatformAgent().run(state)
    print()

    media_list = state.get_media_list()
    img_count = sum(1 for m in media_list if m["type"] == "image")
    vid_count = sum(1 for m in media_list if m["type"] == "video")

    print("=" * 60)
    print("Pipeline complete.")
    print(f"Folder:    {state.dir}")
    print(f"Topic:     {topic}")
    print(f"Video:     {video_path}")
    print(f"Title:     {yt_meta['title']}")
    print(f"Media:     {img_count} images + {vid_count} clips")
    print(f"Platforms: {state.platforms_dir}")
    print("=" * 60)


def run_pipeline(niche: str) -> None:

    # Always check for incomplete work first — never waste money starting fresh
    # when a half-finished topic is waiting
    incomplete = find_incomplete_state()
    if incomplete:
        print(f"[Resume] Found incomplete topic — finishing before researching new one.")
        print(f"         Folder: {incomplete.dir}\n")
        _run_steps(incomplete)
        return

    # No incomplete work — research a new topic
    print(f"[1/5] Research Agent finding topic for niche: '{niche}'...")
    topic = ResearchAgent().run(niche)
    print(f"      Topic: {topic}\n")

    state = PipelineState(topic)
    _run_steps(state)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Direct topic mode: skips research, resumes from cache
        # Usage: poetry run python run.py "My Topic Here"
        topic = sys.argv[1]
        print(f"[Direct mode] Topic: {topic}\n")
        state = PipelineState(topic)
        _run_steps(state)
    else:
        run_pipeline(niche=CHANNEL_NICHE)
