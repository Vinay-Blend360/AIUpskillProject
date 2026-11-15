"""A web-search tool an agent can call via function/tool-calling.

Stubbed: no search API key is configured for this project. Returns a
clearly-marked placeholder so the function-calling loop can be exercised
and tested without a live dependency. Swap the body for a real provider
(e.g. Tavily, Brave Search, SerpAPI) when one is available.
"""

from __future__ import annotations

WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for recent information on a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "num_results": {
                    "type": "integer",
                    "description": "How many results to return.",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}


def web_search(query: str, num_results: int = 3) -> dict:
    """Stub search: no live provider is configured, so this returns a placeholder."""
    return {
        "query": query,
        "stubbed": True,
        "results": [
            {
                "title": f"[stub] No search provider configured for: {query}",
                "snippet": "Configure a real search provider to get live results.",
            }
        ][:num_results],
    }
