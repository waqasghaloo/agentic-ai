"""
Temporary runner to test agents manually during development.

Usage:
    poetry run python run.py
"""

from src.agents.research_agent import ResearchAgent
from src.agents.script_agent import ScriptAgent
from src.agents.voice_agent import VoiceAgent


def main() -> None:
    niche = "educational science"

    # Step 1: Research Agent — find today's best topic
    print(f"[1/3] Research Agent searching for trending topics in: '{niche}'...")
    research_agent = ResearchAgent()
    topic = research_agent.run(niche)
    print(f"      Topic: {topic}\n")

    # Step 2: Script Agent — write a script about that topic
    print("[2/3] Script Agent generating script...")
    script_agent = ScriptAgent()
    script = script_agent.run(topic)
    print(f"      Script: {len(script)} characters\n")

    # Step 3: Voice Agent — convert script to audio
    print("[3/3] Voice Agent converting to audio...")
    voice_agent = VoiceAgent()
    audio_path = voice_agent.run(script)

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    print(f"Topic:  {topic}")
    print(f"Audio:  {audio_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
