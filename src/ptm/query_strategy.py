# -*- coding: utf-8 -*-
"""Query strategy for pricing discovery via Tavily."""

from urllib.parse import urlparse

from ptm.schemas import ProductInput, TavilySource
from ptm.tavily_client import TavilyClient


class QueryStrategy:
    """Strategy for generating pricing-related search queries."""

    def __init__(self, tavily_client: TavilyClient) -> None:
        """Initialize query strategy.

        Args:
            tavily_client: Tavily client instance
        """
        self.client = tavily_client

    def discover_pricing_sources(
        self,
        product_input: ProductInput,
        max_results_per_query: int = 10,
    ) -> list[TavilySource]:
        """Discover pricing-related sources for product and competitors.

        Args:
            product_input: Product input with name, URL, and optional competitor URLs
            max_results_per_query: Maximum results per query

        Returns:
            List of TavilySource objects with pricing information
        """
        all_sources: list[TavilySource] = []
        seen_urls = set()

        # Query 1: Product pricing context
        product_query = self._build_product_pricing_query(product_input)
        sources = self._execute_query(product_query, max_results_per_query)
        all_sources.extend(self._filter_pricing_urls(sources, seen_urls))

        # Query 2: Competitors/alternatives pricing
        competitor_query = self._build_competitor_pricing_query(product_input)
        sources = self._execute_query(competitor_query, max_results_per_query)
        all_sources.extend(self._filter_pricing_urls(sources, seen_urls))

        # Query 3: Direct competitor URLs if provided
        if product_input.competitor_urls:
            for competitor_url in product_input.competitor_urls:
                domain = urlparse(str(competitor_url)).netloc
                if domain:
                    competitor_domain_query = f"{domain} pricing plans"
                    sources = self._execute_query(competitor_domain_query, max_results_per_query)
                    all_sources.extend(self._filter_pricing_urls(sources, seen_urls))

        return all_sources

    def _build_product_pricing_query(self, product_input: ProductInput) -> str:
        """Build query for product pricing context.

        Args:
            product_input: Product input

        Returns:
            Search query string
        """
        return f"{product_input.name} pricing plans"

    def _build_competitor_pricing_query(self, product_input: ProductInput) -> str:
        """Build query for competitor/alternative pricing.

        Args:
            product_input: Product input

        Returns:
            Search query string
        """
        return f"{product_input.name} alternatives competitors pricing"

    def _execute_query(self, query: str, max_results: int) -> list[TavilySource]:
        """Execute search query via Tavily.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of TavilySource objects
        """
        try:
            return self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_raw_content=True,
            )
        except Exception:
            # Log error but continue with other queries
            return []

    def _filter_pricing_urls(
        self, sources: list[TavilySource], seen_urls: set
    ) -> list[TavilySource]:
        """Filter sources to prefer pricing-related URLs.

        Args:
            sources: List of TavilySource objects
            seen_urls: Set of already seen URLs

        Returns:
            Filtered list of TavilySource objects
        """
        pricing_keywords = ["/pricing", "/plans", "price", "pricing"]
        filtered = []

        for source in sources:
            url_str = str(source.url).lower()

            # Check if URL contains pricing keywords
            is_pricing_url = any(keyword in url_str for keyword in pricing_keywords)

            # Check if we've seen this URL before
            if str(source.url) in seen_urls:
                continue

            seen_urls.add(str(source.url))

            # Prioritize pricing URLs, but include others too
            if is_pricing_url:
                filtered.insert(0, source)  # Add pricing URLs at the beginning
            else:
                filtered.append(source)

        return filtered
