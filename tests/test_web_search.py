"""Tests for the (stubbed) web_search tool."""

from src.tools.web_search import web_search


def test_web_search_returns_stubbed_results() -> None:
    result = web_search("transformer architectures", num_results=2)
    assert result["stubbed"] is True
    assert result["query"] == "transformer architectures"
    assert len(result["results"]) <= 2
