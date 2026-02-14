"""Tests for web research tools."""

from __future__ import annotations
import asyncio

from src.tools.web_research import SearchResult, WebResearchTools

def test_search_without_api_key_returns_fallback() -> None:
    tools = WebResearchTools(brave_api_key="")
    results = asyncio.run(tools.search_web("test"))
    assert len(results) == 1
    title = results[0].title.lower()
    assert (
        "not configured" in title or "search error" in title
    ), f"Unexpected title: {results[0].title}"

def test_search_result_dataclass() -> None:
    r = SearchResult(title="Test", url="https://example.com", snippet="Snippet")
    assert r.title == "Test"
