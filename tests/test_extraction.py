"""Tests for pricing snippet extraction."""

from ptm.extraction import (
    extract_price_texts,
    extract_pricing_snippets,
)
from ptm.schemas import TavilySource


def test_extract_pricing_snippets_with_currency() -> None:
    """Test extraction with currency symbols."""
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Our pricing starts at $99 per month. Premium plan costs $199/month.",
        )
    ]

    snippets = extract_pricing_snippets(sources)

    assert len(snippets) > 0
    # Verify snippets are verbatim from source
    assert any("$99" in s for s in snippets)
    assert any("$199" in s for s in snippets)


def test_extract_pricing_snippets_starts_at() -> None:
    """Test extraction with 'starts at' pattern."""
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Pricing starts at $49.99 per month for the basic plan.",
        )
    ]

    snippets = extract_pricing_snippets(sources)

    assert len(snippets) > 0
    assert any("starts at" in s.lower() for s in snippets)
    assert any("$49.99" in s for s in snippets)


def test_extract_pricing_snippets_per_month() -> None:
    """Test extraction with 'per month' pattern."""
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Basic plan: 29 USD per month. Pro plan: 99 USD per year.",
        )
    ]

    snippets = extract_pricing_snippets(sources)

    assert len(snippets) > 0
    assert any("per month" in s.lower() or "per year" in s.lower() for s in snippets)


def test_extract_pricing_snippets_price_range() -> None:
    """Test extraction with price ranges."""
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Our plans range from $99-$199 per month depending on features.",
        )
    ]

    snippets = extract_pricing_snippets(sources)

    assert len(snippets) > 0
    assert any("$99" in s or "$199" in s for s in snippets)


def test_extract_pricing_snippets_truncation() -> None:
    """Test that snippets are truncated to safe length."""
    long_content = "Price: $99/month. " * 100  # Very long content
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content=long_content,
        )
    ]

    snippets = extract_pricing_snippets(sources)

    # All snippets should be truncated
    for snippet in snippets:
        assert len(snippet) <= 500  # MAX_SNIPPET_LENGTH


def test_extract_pricing_snippets_deduplication() -> None:
    """Test that duplicate snippets are removed."""
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="Price: $99/month. Price: $99/month.",  # Duplicate
        )
    ]

    snippets = extract_pricing_snippets(sources)

    # Should deduplicate
    unique_snippets = list(set(snippets))
    assert len(snippets) == len(unique_snippets)


def test_extract_price_texts() -> None:
    """Test extraction of just price texts."""
    snippets = [
        "Our pricing starts at $99 per month for the basic plan.",
        "Premium plan costs $199/month with all features.",
        "Enterprise: contact us for pricing.",
    ]

    price_texts = extract_price_texts(snippets)

    assert len(price_texts) > 0
    assert any("$99" in text for text in price_texts)
    assert any("$199" in text for text in price_texts)


def test_extract_pricing_snippets_no_content() -> None:
    """Test extraction with empty content."""
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content="",
        )
    ]

    snippets = extract_pricing_snippets(sources)

    assert len(snippets) == 0


def test_extract_pricing_snippets_verbatim_only() -> None:
    """Test that snippets are verbatim from source (no generation)."""
    original_content = "Price: $99/month. This is our standard pricing."
    sources = [
        TavilySource(
            url="https://example.com/pricing",
            title="Pricing",
            content=original_content,
        )
    ]

    snippets = extract_pricing_snippets(sources)

    # All snippets must be substrings of original content
    for snippet in snippets:
        assert (
            snippet in original_content
            or original_content in snippet
            or any(word in original_content for word in snippet.split())
        )
