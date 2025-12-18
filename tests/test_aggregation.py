"""Tests for competitor pricing aggregation."""

from ptm.aggregation import (
    aggregate_competitor_pricing,
    get_comparable_competitors,
)
from ptm.schemas import TavilySource


def test_aggregate_competitor_pricing_single_domain() -> None:
    """Test aggregation with single competitor domain."""
    sources = [
        TavilySource(
            url="https://competitor.com/pricing",
            title="Pricing",
            content="Our pricing starts at $99 per month for the basic plan.",
        )
    ]

    competitors = aggregate_competitor_pricing(sources)

    assert len(competitors) == 1
    assert competitors[0].domain == "competitor.com"
    assert len(competitors[0].extracted_price_texts) > 0
    assert len(competitors[0].evidence_snippets) > 0


def test_aggregate_competitor_pricing_multiple_domains() -> None:
    """Test aggregation with multiple competitor domains."""
    sources = [
        TavilySource(
            url="https://competitor1.com/pricing",
            title="Pricing",
            content="Price: $99/month",
        ),
        TavilySource(
            url="https://competitor2.com/plans",
            title="Plans",
            content="Starting at €50 per month",
        ),
    ]

    competitors = aggregate_competitor_pricing(sources)

    # Should have 2 competitors
    assert len(competitors) == 2
    domains = {c.domain for c in competitors}
    assert "competitor1.com" in domains
    assert "competitor2.com" in domains


def test_aggregate_competitor_pricing_deduplication() -> None:
    """Test that sources from same domain are grouped."""
    sources = [
        TavilySource(
            url="https://competitor.com/pricing",
            title="Pricing",
            content="Price: $99/month",
        ),
        TavilySource(
            url="https://www.competitor.com/plans",
            title="Plans",
            content="Premium: $199/month",
        ),
    ]

    competitors = aggregate_competitor_pricing(sources)

    # Should group by domain (www. removed)
    assert len(competitors) == 1
    assert competitors[0].domain == "competitor.com"
    assert len(competitors[0].extracted_price_texts) >= 2


def test_aggregate_competitor_pricing_no_content() -> None:
    """Test aggregation with sources that have no content."""
    sources = [
        TavilySource(
            url="https://competitor.com/pricing",
            title="Pricing",
            content="",
        )
    ]

    competitors = aggregate_competitor_pricing(sources)

    assert len(competitors) == 1
    assert len(competitors[0].extracted_price_texts) == 0
    assert len(competitors[0].gaps) > 0
    assert "No pricing content" in " ".join(competitors[0].gaps)


def test_aggregate_competitor_pricing_normalization() -> None:
    """Test that normalization is attempted when possible."""
    sources = [
        TavilySource(
            url="https://competitor.com/pricing",
            title="Pricing",
            content="Price: $99 per month",
        )
    ]

    competitors = aggregate_competitor_pricing(sources)

    assert len(competitors) == 1
    # Should have normalized price if all data available
    if competitors[0].normalized_monthly_usd is not None:
        assert competitors[0].normalized_monthly_usd > 0


def test_aggregate_competitor_pricing_gaps() -> None:
    """Test that gaps are recorded when normalization fails."""
    sources = [
        TavilySource(
            url="https://competitor.com/pricing",
            title="Pricing",
            content="Price: $99",  # Missing cadence
        )
    ]

    competitors = aggregate_competitor_pricing(sources)

    assert len(competitors) == 1
    if competitors[0].normalized_monthly_usd is None:
        assert len(competitors[0].gaps) > 0


def test_get_comparable_competitors() -> None:
    """Test filtering comparable competitors."""
    from ptm.schemas import CompetitorPricing

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["€50/month"],
            normalized_monthly_usd=None,  # Not normalized
            gaps=["Missing FX rate"],
        ),
        CompetitorPricing(
            domain="competitor3.com",
            extracted_price_texts=["$199/month"],
            normalized_monthly_usd=199.0,
        ),
    ]

    comparable = get_comparable_competitors(competitors)

    assert len(comparable) == 2
    domains = {c.domain for c in comparable}
    assert "competitor1.com" in domains
    assert "competitor3.com" in domains
    assert "competitor2.com" not in domains
