"""
Pipeline runner — runs each step only if not already cached for this topic.

Each topic's outputs are saved under output/topics/{slug}/.
Re-running with the same topic skips completed steps automatically.

Usage:
    poetry run python run.py
"""

from src.agents.research_agent import ResearchAgent
from src.agents.script_agent import ScriptAgent
from src.agents.voice_agent import VoiceAgent
from src.agents.visual_agent import VisualAgent
from src.agents.editor_agent import EditorAgent
from src.pipeline.state import PipelineState


def run_pipeline(niche: str) -> None:

    # Step 1: Research — find today's topic
    print(f"[1/5] Research Agent finding topic for niche: '{niche}'...")
    research_agent = ResearchAgent()
    topic = research_agent.run(niche)
    print(f"      Topic: {topic}\n")

    # Initialise state — creates output/topics/{slug}/
    state = PipelineState(topic)
    print(f"      State folder: {state.dir}\n")

    # Step 2: Script — skip if cached
    if state.has_script():
        print("[2/5] Script already exists — loading from cache.")
        script = state.get_script()
    else:
        print("[2/5] Script Agent generating script...")
        script = ScriptAgent().run(topic)
        state.save_script(script)
        print(f"      Script saved ({len(script)} characters).")
    print()

    # Step 3: Voice — skip if cached
    if state.has_audio():
        print("[3/5] Audio already exists — skipping ElevenLabs call.")
    else:
        print("[3/5] Voice Agent converting script to audio...")
        VoiceAgent().run(script, state)
    print()

    # Step 4: Images — skip if cached
    if state.has_images():
        print("[4/5] Images already exist — skipping fal.ai calls.")
        image_paths = state.get_image_paths()
    else:
        print("[4/5] Visual Agent generating images...")
        image_paths = VisualAgent().run(script, state)
    print()

    # Step 5: Video — skip if cached
    if state.has_video():
        print("[5/5] Video already exists — skipping render.")
        video_path = str(state.video_path)
    else:
        print("[5/5] Editor Agent assembling final video...")
        video_path = EditorAgent().run(state)
    print()

    # Summary
    print("=" * 60)
    print("Pipeline complete.")
    print(f"Topic:   {topic}")
    print(f"Script:  {state.script_path}")
    print(f"Audio:   {state.audio_path}")
    print(f"Images:  {len(state.get_image_paths())} files")
    print(f"Video:   {video_path}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline(niche="educational science")
