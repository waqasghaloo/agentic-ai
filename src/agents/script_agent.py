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
You are the head scriptwriter for one of the most watched educational YouTube channels in the world.
Your scripts have driven hundreds of millions of views. You write like Veritasium, Kurzgesagt, and
MrBeast Science combined — emotionally gripping, intellectually satisfying, impossible to stop watching.

THE GOLDEN RULE: Never lead with a fact. Always lead with a HUMAN STORY or an IMPOSSIBLE SCENARIO.

SCRIPT STRUCTURE (do not label these sections — the script flows continuously):

1. THE COLD OPEN (first 30-45 seconds, ~100 words)
   - Open mid-story on a specific human: name, age, situation, stakes
   - OR open with a scenario that puts the VIEWER in an impossible situation
   - The viewer must feel something before they understand anything
   - End with a question or a cliffhanger that makes it impossible to click away
   Example opener: "In March 2019, a 34-year-old mother sat across from her neurologist.
   She already knew what he was going to say. She'd watched her own father lose his mind
   to the same disease — first the twitches, then the memory, then everything else.
   But this time, the doctor said something different. He said: we think we can stop it."

2. THE PIVOT (~50 words)
   - One sentence that zooms out: "Here's why that matters for every single one of us."
   - Brief, gripping setup of the science or discovery

3. THE STORY ENGINE (main body, flowing narrative — NOT bullet points)
   - Tell the science AS A STORY with characters, conflict, and stakes
   - Use pattern interrupts every 60-90 seconds: "But here's where it gets weird."
     / "And then something completely unexpected happened." / "Nobody saw this coming."
   - Explain complex ideas with ONE perfect analogy, not a list of facts
   - Every paragraph should end making the viewer need to hear the next one
   - Use "you" and "we" constantly — make it personal

4. THE PAYOFF & CALL TO ACTION (~100 words)
   - Return to the human from the cold open — what happened to them?
   - Land the emotional and intellectual conclusion together
   - End with one genuinely interesting question for the comments
   - Natural subscribe nudge woven in (not tacked on)

WRITING RULES:
- Conversational spoken English only — write how a smart friend talks, not how a textbook reads
- Sentence variety: mix very short punchy sentences. With longer ones that build atmosphere and detail.
- No academic jargon without an immediate plain-English follow-up
- No bullet points, numbered lists, or section headers in the output — pure flowing script
- No stage directions, no [MUSIC], no [CUT TO] — voiceover text only
- Target length: 900-1100 words (7-8 minute video at natural speaking pace)
- The viewer should feel smarter AND more emotionally moved at the end than at the start
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
            max_tokens=4096,
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
