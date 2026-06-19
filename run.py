"""
Temporary runner to test agents manually during development.

Usage:
    poetry run python run.py
"""

from src.agents.research_agent import ResearchAgent
from src.agents.script_agent import ScriptAgent


def main() -> None:
    niche = "educational science"

    # Step 1: Research Agent finds today's best topic
    print(f"Research Agent searching for trending topics in: '{niche}'...")
    research_agent = ResearchAgent()
    topic = research_agent.run(niche)
    print(f"Topic found: {topic}\n")

    # Step 2: Script Agent writes a script about that topic
    print("Script Agent generating script...")
    print("-" * 60)
    script_agent = ScriptAgent()
    script = script_agent.run(topic)
    print(script)
    print("-" * 60)
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
