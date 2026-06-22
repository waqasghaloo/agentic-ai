"""
Research Agent — finds the best trending YouTube topic for a given channel niche.

This agent demonstrates the core agentic AI pattern: tool use.
It gives Claude access to a web search tool and lets Claude decide
when to use it, what to search for, and how to interpret the results.
"""

import re
import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.search_tool import SEARCH_TOOL_DEFINITION, search_web


def _extract_topic(text: str) -> str:
    """
    Extract the clean topic sentence from Claude's response.

    Claude often reasons before answering (scoring tables, analysis).
    The topic sentence is always the last line that:
    - Looks like a proper sentence (starts with capital letter or quote)
    - Is long enough to be a topic (>40 chars)
    - Is not a markdown element (table, header, bullet, emoji-tagged)
    """
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]

    # Exclude markdown artifacts
    def is_topic_line(line: str) -> bool:
        if line.startswith("|"):       return False  # table row
        if line.startswith("#"):       return False  # heading
        if line.startswith("**"):      return False  # bold label
        if line.startswith("- "):      return False  # bullet
        if line.startswith("* "):      return False  # bullet
        if line.startswith("---"):     return False  # divider
        if line.startswith("> "):      return False  # blockquote
        if "✅" in line or "⚠️" in line or "❌" in line:  return False  # scoring rows
        if len(line) < 40:             return False  # too short
        return True

    candidates = [l for l in lines if is_topic_line(l)]
    if candidates:
        return candidates[-1]

    # Fallback: last non-empty line
    return lines[-1] if lines else "Could not determine a topic."


SYSTEM_PROMPT = """
You are a viral content strategist for a YouTube/TikTok channel targeting the US market.
Your job is to find ONE topic that will get clicks, views, and shares TODAY.

CHANNEL IDENTITY:
This channel covers AI and technology stories that directly affect American people's money,
jobs, and everyday lives. Think Vice meets Veritasium — documentary urgency, real human stakes.

WHAT MAKES A WINNING TOPIC (all four must be true):
1. PERSONAL STAKE — the viewer can see how this directly affects THEM (their job, money, health, future)
2. SHOCK VALUE — there is a genuinely surprising or counterintuitive fact at the centre
3. SEARCH DEMAND — people are actively searching related keywords right now (recent news angle helps)
4. UNDERSERVED — not already covered this week by a channel with 1M+ subscribers with fresh content

SEARCH STRATEGY (run multiple searches before deciding):
- Search: what's trending on TikTok and YouTube about AI and jobs this week
- Search: latest AI news that affects American workers or money
- Search: viral technology stories US market [current week]
- Search: what people fear or are excited about regarding AI right now
- Pick the ONE topic with the strongest combination of all four winning criteria above

TOPIC FORMULA (follow this exactly):
"[Specific shocking development] — [specific impact on American viewer's life/money/job]"

STRONG EXAMPLES (notice: specific, personal, urgent):
- "The AI system Walmart just deployed that eliminated 4,200 overnight jobs — and which stores are next"
- "The one salary range economists say AI cannot touch for the next 10 years"
- "How a 26-year-old used a $20/month AI tool to replace his $85,000/year graphic design job"
- "The hidden clause in Apple's new AI terms that means they can use your photos to train models"

WEAK EXAMPLES (avoid these — too generic, no personal stake):
- "How AI is changing the world"
- "The latest developments in quantum computing"
- "Scientists discover new exoplanet"

OUTPUT: Return ONLY the topic sentence. No explanation, no options, no commentary.
"""


class ResearchAgent:
    """
    Agent that uses web search to find trending YouTube topics.

    Demonstrates tool use: Claude decides when to search, what to search for,
    and synthesises the results into a single best topic.
    """

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL
        # Pass the tool definition so Claude knows it can search the web
        self.tools = [SEARCH_TOOL_DEFINITION]

    def run(self, niche: str) -> str:
        """
        Find the best trending YouTube topic for the given channel niche.

        Args:
            niche: The channel's subject area e.g. "educational science"

        Returns:
            A single topic sentence ready to pass to the Script Agent.
        """
        # Start the conversation with the task
        messages = [
            {
                "role": "user",
                "content": (
                    f"Find the best viral YouTube/TikTok topic for this channel niche: {niche}. "
                    f"Run at least 3 different searches covering: trending AI/tech news, "
                    f"what's viral on TikTok this week, and what US audiences are worried about or excited about "
                    f"regarding technology right now. Then pick the single strongest topic."
                ),
            }
        ]

        # THE AGENTIC LOOP
        # We keep going until Claude stops requesting tools (stop_reason == "end_turn").
        # Each iteration: Claude thinks → maybe calls a tool → we run it → send result back.
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            # Claude is done — no more tools needed, final answer is ready
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return _extract_topic(block.text)
                return "Could not determine a topic."

            # Claude wants to use a tool — execute it and send results back
            if response.stop_reason == "tool_use":
                # Add Claude's response (including its tool request) to the conversation.
                # Why: Claude needs to see its own previous messages to continue reasoning.
                messages.append({"role": "assistant", "content": response.content})

                # Find and execute each tool Claude requested
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  [Research Agent] Searching: '{block.input['query']}'")

                        # Run the actual search function with Claude's chosen query
                        result = search_web(
                            query=block.input["query"],
                            max_results=block.input.get("max_results", 5),
                        )

                        # Package the result in the format Claude expects
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,  # links result to the request
                                "content": result,
                            }
                        )

                # Send the tool results back so Claude can continue
                messages.append({"role": "user", "content": tool_results})
