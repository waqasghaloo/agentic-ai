"""
Script Agent — generates a YouTube video script for a given topic.

Why this is an agent (not just a function):
    An agent wraps Claude with a specific purpose, prompt strategy, and behaviour.
    It owns one job: receive a topic, return a polished script. Nothing else.
"""

import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL


# The system prompt is the agent's "personality" and instructions.
# It tells Claude what role to play and what the output should look like.
# Why it's a constant here (not inside the method): it belongs to the agent's
# identity, not to a single call. Easy to find, read, and update.
SYSTEM_PROMPT = """
You are an expert YouTube scriptwriter specialising in educational content.
Your scripts are engaging, clear, and structured for a general audience.

When given a topic, write a complete YouTube video script that includes:
1. Hook (first 15 seconds) — grab attention immediately
2. Introduction — what the viewer will learn
3. Main content — 3 to 5 key points, each explained simply
4. Conclusion — summarise and give a clear call to action

Rules:
- Write in a conversational tone, as if speaking directly to the viewer
- Keep sentences short and punchy
- Aim for a 5 to 7 minute video (approximately 750 to 1000 words)
- Do not include stage directions or camera notes
"""


class ScriptAgent:
    """
    Agent responsible for generating YouTube video scripts.

    Takes a topic string, calls Claude, returns a complete script string.
    Single responsibility: topic in, script out.
    """

    def __init__(self) -> None:
        # anthropic.Anthropic() is the client that talks to the Claude API.
        # We pass the API key from config (which loaded it from .env).
        # Why not hardcode the key here? Security — keys in code get accidentally
        # committed to git and exposed publicly.
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL

    def run(self, topic: str) -> str:
        """
        Generate a YouTube video script for the given topic.

        Args:
            topic: The subject of the video e.g. "how black holes form"

        Returns:
            A complete video script as a string.
        """
        # client.messages.create() is the core Claude API call.
        # Think of it as: "send this conversation to Claude, get a reply back."
        #
        # system: the agent's standing instructions (role + output format)
        # messages: the actual conversation — here just one user message
        # max_tokens: the maximum length of Claude's response
        #             (~750 words = ~1000 tokens, we give headroom with 2048
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Write a YouTube video script about: {topic}",
                }
            ],
        )

        # response.content is a list of content blocks.
        # For a simple text response, we always want the first block's text.
        return response.content[0].text
