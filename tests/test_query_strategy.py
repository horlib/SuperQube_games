"""Tests for query strategy."""

from unittest.mock import Mock, patch

from ptm.query_strategy import QueryStrategy
from ptm.schemas import ProductInput, TavilySource
from ptm.tavily_client import TavilyClient


def test_build_product_pricing_query() -> None:
    """Test building product pricing query."""
    client = TavilyClient(api_key="test_key")
    strategy = QueryStrategy(client)

    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )

    query = strategy._build_product_pricing_query(product)
    assert "Test Product" in query
    assert "pricing" in query.lower()


def test_build_competitor_pricing_query() -> None:
    """Test building competitor pricing query."""
    client = TavilyClient(api_key="test_key")
    strategy = QueryStrategy(client)

    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )

    query = strategy._build_competitor_pricing_query(product)
    assert "Test Product" in query
    assert "alternatives" in query.lower() or "competitors" in query.lower()


@patch.object(TavilyClient, "search")
def test_discover_pricing_sources(mock_search: Mock) -> None:
    """Test discovering pricing sources."""
    # Mock Tavily search results
    mock_search.return_value = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Price: $99/month",
        ),
        TavilySource(
            url="https://other.com",
            title="Other",
            content="Some content",
        ),
    ]

    client = TavilyClient(api_key="test_key")
    strategy = QueryStrategy(client)

    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )

    sources = strategy.discover_pricing_sources(product)

    # Should have executed multiple queries
    assert mock_search.call_count >= 2
    # Should return sources (pricing URLs prioritized)
    assert len(sources) > 0


def test_filter_pricing_urls() -> None:
    """Test filtering pricing URLs."""
    client = TavilyClient(api_key="test_key")
    strategy = QueryStrategy(client)

    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Price: $99/month",
        ),
        TavilySource(
            url="https://other.com/about",
            title="About",
            content="Some content",
        ),
        TavilySource(
            url="https://test.com/plans",
            title="Plans",
            content="Plans content",
        ),
    ]

    seen_urls = set()
    filtered = strategy._filter_pricing_urls(sources, seen_urls)

    # Pricing URLs should be prioritized (at the beginning)
    assert len(filtered) == 3
    assert "/pricing" in str(filtered[0].url) or "/plans" in str(filtered[0].url)


def test_filter_pricing_urls_deduplication() -> None:
    """Test that filter_pricing_urls deduplicates."""
    client = TavilyClient(api_key="test_key")
    strategy = QueryStrategy(client)

    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Price: $99/month",
        ),
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing Duplicate",
            content="Price: $99/month",
        ),
    ]

    seen_urls = set()
    filtered = strategy._filter_pricing_urls(sources, seen_urls)

    # Should deduplicate
    assert len(filtered) == 1
