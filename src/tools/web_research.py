"""Web research tools — gives agents live web access."""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class SearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str


class WebResearchTools:
    """Web search and URL fetching for agents."""

    def __init__(self, brave_api_key: str = "") -> None:
        self.brave_api_key = brave_api_key or os.environ.get("BRAVE_API_KEY", "")

    async def search_web(self, query: str, count: int = 5) -> list[SearchResult]:
        """Search the web using Brave Search API."""
        if not self.brave_api_key:
            return [SearchResult(
                title="[Brave Search not configured]", url="",
                snippet=f"Set BRAVE_API_KEY in .env. Query was: {query}",
            )]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": self.brave_api_key,
                    },
                    params={"q": query, "count": str(count)},
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                    )
                    for item in data.get("web", {}).get("results", [])[:count]
                ]
        except Exception as e:
            return [SearchResult(title="[Search error]", url="", snippet=str(e))]

    async def fetch_url(self, url: str, max_chars: int = 5000) -> str:
        """Fetch text content from a URL."""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, timeout=15.0)
                return resp.text[:max_chars]
        except Exception as e:
            return f"[Fetch error: {e}]"
