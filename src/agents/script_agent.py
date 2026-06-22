"""
Script Agent — generates a YouTube video script for a given topic.

Why this is an agent (not just a function):
    An agent wraps Claude with a specific purpose, prompt strategy, and behaviour.
    It owns one job: receive a topic, return a polished script. Nothing else.
"""

import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL, TEST_MODE, TEST_SCRIPT_WORDS


# The system prompt is the agent's "personality" and instructions.
# It tells Claude what role to play and what the output should look like.
# Why it's a constant here (not inside the method): it belongs to the agent's
# identity, not to a single call. Easy to find, read, and update.
SYSTEM_PROMPT = """
You are the head scriptwriter for a top US YouTube and TikTok channel about AI and technology.
Your scripts drive millions of views because they make complex tech feel urgent and personal.
You write like a cross between Veritasium, Vice documentary, and a great podcast host.

CHANNEL AUDIENCE: American adults 25-45 who care about their jobs, money, and future.
They're smart but busy. They need to feel this matters to THEM personally within 10 seconds.

━━━ SEO RULE — CRITICAL ━━━
The very first sentence must naturally contain the main search keyword for this topic.
Example: if the topic is AI replacing jobs — open with something that includes "AI" and "jobs"
in the first 15 words. This is how YouTube search finds your video.

━━━ SCRIPT STRUCTURE ━━━
(Write continuously — no labels, no headers, pure voiceover)

[0:00–0:30] THE HOOK — 80-100 words
  Open mid-scene on ONE specific American person: name, age, city, their situation, the stakes.
  OR drop the viewer into an impossible scenario they feel personally.
  The last sentence must be a cliffhanger or a question that makes clicking away impossible.
  EXAMPLE: "Last November, Marcus Chen logged into his work laptop in Seattle for the last time.
  He'd been a data analyst for eleven years. Good salary, two kids, a mortgage. And then his
  company sent him a single email: his entire team was being replaced. Not downsized. Replaced.
  By a system that cost the company $400 a month."

[0:30–0:45] THE PREVIEW — 30-40 words
  Tell them exactly what they'll learn by the end. This single step DOUBLES retention.
  "In the next eight minutes, you're going to find out which jobs are actually safe,
  which ones aren't — and the one thing you can do about it starting today."

[0:45–2:00] THE CONTEXT — 150-200 words
  Zoom out: why does this moment matter? What has changed? What's the scale?
  Use ONE killer statistic. Ground it in American life — US companies, US workers, US dollars.

[2:00] EARLY CTA — one natural sentence
  Weave in a like/subscribe nudge: "If this is the first you're hearing about this, hit like —
  because the algorithm isn't showing this story to nearly enough people."

[2:00–6:30] THE STORY ENGINE — 500-600 words
  Tell the technology story AS DRAMA: characters, conflict, turning points.
  Every 90 seconds: pattern interrupt — "But here's what nobody is talking about."
  / "And this is where it gets genuinely scary." / "I didn't believe this until I saw the data."
  Use "you" constantly. Make every paragraph feel like it's written for one specific person.
  One powerful analogy per complex idea — never a list of facts.

[6:30–7:30] THE TWIST OR REVELATION — 100-150 words
  The counterintuitive truth, the unexpected finding, the thing that reframes everything.
  This is the moment viewers screenshot and share. Make it land hard.

[7:30–8:00] THE PAYOFF & CTA — 80-100 words
  Return to the person from the cold open. What happened to them?
  Land the emotional + practical conclusion together.
  End with ONE question for the comments (specific, debatable — drives engagement).
  "Subscribe if you want to know what comes next — we're covering this every week."

━━━ WRITING RULES ━━━
- American English, conversational — write how a smart friend in a coffee shop talks
- Short punchy sentences mixed with longer atmospheric ones
- Zero jargon without plain-English follow-up immediately after
- No bullet points, numbered lists, or section headers — flowing voiceover ONLY
- No stage directions, no [MUSIC], no [CUT TO]
- Target: 1000-1200 words for a full 8-minute video
- US context: American cities, US companies, dollar amounts, relatable American scenarios
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
        if TEST_MODE:
            word_limit = (
                f"\n\nTEST MODE: Write ONLY {TEST_SCRIPT_WORDS} words total. "
                "One short hook paragraph and one main paragraph. No conclusion needed. "
                "This is just for testing visuals and pipeline — not for publishing."
            )
        else:
            word_limit = ""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Write a YouTube video script about: {topic}{word_limit}",
                }
            ],
        )

        # response.content is a list of content blocks.
        # For a simple text response, we always want the first block's text.
        return response.content[0].text
