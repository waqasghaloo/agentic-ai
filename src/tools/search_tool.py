"""
Search Tool — wraps DuckDuckGo search for use by agents.

Why DuckDuckGo:
    Free, no API key required, sufficient for finding trending topics.
    Can be swapped for Google/Serper/Tavily later without changing the agents
    — because agents call this tool, not the search library directly.

Why this is a tool (not inside the agent):
    Tools are stateless functions that call external services.
    Agents are decision-makers. Keeping them separate means:
    - This tool can be used by multiple agents
    - Easy to swap the search provider without touching agent logic
    - Easy to test independently
"""

from ddgs import DDGS


# This is the tool DEFINITION — a JSON schema that tells Claude what the tool
# does, what arguments it accepts, and which are required.
# Claude reads this and decides when and how to call it.
SEARCH_TOOL_DEFINITION = {
    "name": "search_web",
    "description": (
        "Search the web for recent information on a topic. "
        "Use this to find trending YouTube topics, recent news, or popular content."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up.",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of results to return. Default is 5.",
            },
        },
        "required": ["query"],
    },
}


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo and return results as a formatted string.

    Args:
        query:       The search query.
        max_results: How many results to return (default 5).

    Returns:
        Search results as a plain text string, ready to pass back to Claude.
    """
    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                f"Title: {r['title']}\n"
                f"URL: {r['href']}\n"
                f"Summary: {r['body']}"
            )

    if not results:
        return "No results found."

    # Join results with a separator so Claude can clearly distinguish each one
    return "\n---\n".join(results)
