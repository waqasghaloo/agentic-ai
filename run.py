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
from src.pipeline.state import PipelineState


def run_pipeline(niche: str) -> None:

    # Step 1: Research — find today's topic
    print(f"[1/4] Research Agent finding topic for niche: '{niche}'...")
    research_agent = ResearchAgent()
    topic = research_agent.run(niche)
    print(f"      Topic: {topic}\n")

    # Initialise state for this topic — creates output/topics/{slug}/
    state = PipelineState(topic)
    print(f"      State folder: {state.dir}\n")

    # Step 2: Script — skip if already generated
    if state.has_script():
        print("[2/4] Script already exists — loading from cache.")
        script = state.get_script()
    else:
        print("[2/4] Script Agent generating script...")
        script_agent = ScriptAgent()
        script = script_agent.run(topic)
        state.save_script(script)
        print(f"      Script saved ({len(script)} characters).")
    print()

    # Step 3: Voice — skip if already generated
    if state.has_audio():
        print("[3/4] Audio already exists — skipping ElevenLabs call.")
        audio_path = str(state.audio_path)
    else:
        print("[3/4] Voice Agent converting script to audio...")
        voice_agent = VoiceAgent()
        audio_path = voice_agent.run(script, state)
    print()

    # Step 4: Images — skip if already generated
    if state.has_images():
        print("[4/4] Images already exist — skipping fal.ai calls.")
        image_paths = state.get_image_paths()
    else:
        print("[4/4] Visual Agent generating images...")
        visual_agent = VisualAgent()
        image_paths = visual_agent.run(script, state)
    print()

    # Summary
    print("=" * 60)
    print("Pipeline complete.")
    print(f"Topic:   {topic}")
    print(f"Folder:  {state.dir}")
    print(f"Script:  {state.script_path}")
    print(f"Audio:   {audio_path}")
    print(f"Images:  {len(image_paths)} files in {state.images_dir}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline(niche="educational science")
