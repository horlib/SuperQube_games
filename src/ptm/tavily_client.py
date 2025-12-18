"""Tavily search client for real-time web data retrieval."""

from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ptm.config import get_tavily_api_key
from ptm.schemas import TavilySource

TAVILY_API_BASE_URL = "https://api.tavily.com"


class TavilyClientError(Exception):
    """Base exception for Tavily client errors."""


class TavilyAuthError(TavilyClientError):
    """Exception raised for authentication errors."""


class TavilyClient:
    """Client for Tavily search API."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Tavily client.

        Args:
            api_key: Tavily API key. If not provided, will be loaded from config.
        """
        self.api_key = api_key or get_tavily_api_key()
        self.base_url = TAVILY_API_BASE_URL
        self.timeout = 30.0

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 10,
        include_raw_content: bool = True,
    ) -> list[TavilySource]:
        """Search Tavily API for web content.

        Args:
            query: Search query string
            search_depth: Search depth ("basic" or "advanced")
            max_results: Maximum number of results to return
            include_raw_content: Whether to include raw page content

        Returns:
            List of TavilySource objects

        Raises:
            TavilyAuthError: If authentication fails
            TavilyClientError: For other API errors
        """
        url = f"{self.base_url}/search"
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise TavilyAuthError(
                    "Tavily API authentication failed. Please check your TAVILY_API_KEY."
                ) from e
            raise TavilyClientError(
                f"Tavily API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise TavilyClientError("Tavily API request timed out") from e
        except httpx.NetworkError as e:
            raise TavilyClientError(f"Network error connecting to Tavily API: {e}") from e

        # Parse response and deduplicate by URL
        sources = self._parse_response(data)
        return self._deduplicate_sources(sources)

    def _parse_response(self, data: dict) -> list[TavilySource]:
        """Parse Tavily API response into TavilySource objects.

        Args:
            data: Raw API response JSON

        Returns:
            List of TavilySource objects
        """
        sources = []
        results = data.get("results", [])

        for result in results:
            try:
                source = TavilySource(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    score=result.get("score"),
                    published_date=result.get("published_date"),
                )
                sources.append(source)
            except Exception:
                # Skip invalid results but continue processing
                continue

        return sources

    def _deduplicate_sources(self, sources: list[TavilySource]) -> list[TavilySource]:
        """Deduplicate sources by URL.

        Args:
            sources: List of TavilySource objects

        Returns:
            Deduplicated list of TavilySource objects
        """
        seen_urls = set()
        deduplicated = []

        for source in sources:
            # Normalize URL by removing query params and fragments for comparison
            parsed = urlparse(str(source.url))
            normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                deduplicated.append(source)

        return deduplicated
