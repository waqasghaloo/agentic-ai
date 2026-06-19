"""
Research Agent — finds the best trending YouTube topic for a given channel niche.

This agent demonstrates the core agentic AI pattern: tool use.
It gives Claude access to a web search tool and lets Claude decide
when to use it, what to search for, and how to interpret the results.
"""

import anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.tools.search_tool import SEARCH_TOOL_DEFINITION, search_web


SYSTEM_PROMPT = """
You are a YouTube content research specialist. Your job is to find the single best
topic for a YouTube video that will perform well today.

When given a channel niche:
1. Search for what is trending or popular in that niche right now
2. Evaluate the results for viewer interest and content potential
3. Return ONLY the chosen topic as a single clear sentence

Example output: "How NASA's new telescope is rewriting what we know about dark matter"

Do not explain your reasoning. Just return the topic sentence.
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
                    f"Find the best trending YouTube video topic for a channel about: {niche}. "
                    f"Search the web to see what is popular and trending right now."
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
                # Extract the text from the final response
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
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
