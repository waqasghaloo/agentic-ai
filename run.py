"""
Temporary runner to test agents manually during development.

Why this exists: lets us run a single agent in isolation to verify it works
before wiring everything into the full pipeline.

Usage:
    poetry run python run.py
"""

from src.agents.script_agent import ScriptAgent


def main() -> None:
    print("Initialising Script Agent...")
    agent = ScriptAgent()

    topic = "5 surprising facts about black holes"
    print(f"Generating script for topic: '{topic}'\n")
    print("-" * 60)

    script = agent.run(topic)
    print(script)

    print("-" * 60)
    print("\nScript Agent ran successfully.")


if __name__ == "__main__":
    main()
