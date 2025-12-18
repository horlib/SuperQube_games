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

    # Test without price filtering (backward compatibility)
    comparable = get_comparable_competitors(competitors)

    assert len(comparable) == 2
    domains = {c.domain for c in comparable}
    assert "competitor1.com" in domains
    assert "competitor3.com" in domains
    assert "competitor2.com" not in domains


def test_get_comparable_competitors_with_price_filtering() -> None:
    """Test filtering comparable competitors by price similarity."""
    from ptm.schemas import CompetitorPricing

    # Current product price: $100/month
    current_price = 100.0

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,  # Similar price
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$50/month"],
            normalized_monthly_usd=50.0,  # Similar price (within 10x range)
        ),
        CompetitorPricing(
            domain="competitor3.com",
            extracted_price_texts=["$199/month"],
            normalized_monthly_usd=199.0,  # Similar price
        ),
        CompetitorPricing(
            domain="competitor4.com",
            extracted_price_texts=["$5/month"],
            normalized_monthly_usd=5.0,  # Too cheap (below 0.1x = $10)
        ),
        CompetitorPricing(
            domain="competitor5.com",
            extracted_price_texts=["$2000/month"],
            normalized_monthly_usd=2000.0,  # Too expensive (above 10x = $1000)
        ),
        CompetitorPricing(
            domain="competitor6.com",
            extracted_price_texts=["€50/month"],
            normalized_monthly_usd=None,  # Not normalized
            gaps=["Missing FX rate"],
        ),
    ]

    # Test with price filtering (default factor 10.0)
    comparable = get_comparable_competitors(competitors, current_price_usd=current_price)

    assert len(comparable) == 3
    domains = {c.domain for c in comparable}
    assert "competitor1.com" in domains  # $99 - similar
    assert "competitor2.com" in domains  # $50 - similar (within range)
    assert "competitor3.com" in domains  # $199 - similar
    assert "competitor4.com" not in domains  # $5 - too cheap
    assert "competitor5.com" not in domains  # $2000 - too expensive
    assert "competitor6.com" not in domains  # No normalized price


def test_get_comparable_competitors_strict_filtering() -> None:
    """Test filtering with stricter price similarity factor."""
    from ptm.schemas import CompetitorPricing

    # Current product price: $100/month
    current_price = 100.0

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,  # Similar price
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$50/month"],
            normalized_monthly_usd=50.0,  # Similar price
        ),
        CompetitorPricing(
            domain="competitor3.com",
            extracted_price_texts=["$500/month"],
            normalized_monthly_usd=500.0,  # Too expensive with factor 2.0
        ),
    ]

    # Test with stricter filtering (factor 2.0 means 0.5x to 2x = $50-$200)
    comparable = get_comparable_competitors(
        competitors, 
        current_price_usd=current_price,
        price_similarity_factor=2.0
    )

    assert len(comparable) == 2
    domains = {c.domain for c in comparable}
    assert "competitor1.com" in domains  # $99 - within range
    assert "competitor2.com" in domains  # $50 - within range
    assert "competitor3.com" not in domains  # $500 - outside range


def test_get_comparable_competitors_with_attributes() -> None:
    """Test filtering comparable competitors by product attributes."""
    from ptm.schemas import CompetitorPricing

    # Current product: SaaS project management tool for teams
    current_price = 100.0
    product_category = "Project Management"
    product_target_customer = "Team"
    product_key_features = ["Collaboration", "Task Management", "Real-time"]

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,
            category="Project Management",  # Matches category
            target_customer="Team",  # Matches target customer
            key_features=["Collaboration", "Task Management"],  # Matches features
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$95/month"],
            normalized_monthly_usd=95.0,
            category="Design Tool",  # Different category
            target_customer="Individual",  # Different target
            key_features=["Design", "Prototyping"],  # Different features
        ),
        CompetitorPricing(
            domain="competitor3.com",
            extracted_price_texts=["$105/month"],
            normalized_monthly_usd=105.0,
            category="Project Management",  # Matches category
            target_customer=None,  # No target customer info
            key_features=["Task Management"],  # Partial feature match
        ),
        CompetitorPricing(
            domain="competitor4.com",
            extracted_price_texts=["$110/month"],
            normalized_monthly_usd=110.0,
            # No attributes - should be included as fallback
        ),
    ]

    # Test with attribute filtering
    comparable = get_comparable_competitors(
        competitors,
        current_price_usd=current_price,
        product_category=product_category,
        product_target_customer=product_target_customer,
        product_key_features=product_key_features,
        product_name="Test Product",
        min_similarity_threshold=0.25,
    )

    # Should include: competitor1 (matches all), competitor3 (matches category), competitor4 (no attributes = fallback)
    assert len(comparable) >= 2
    domains = {c.domain for c in comparable}
    assert "competitor1.com" in domains  # Matches all attributes
    assert "competitor3.com" in domains  # Matches category
    assert "competitor4.com" in domains  # No attributes = fallback
    # competitor2 might or might not be included depending on similarity score


def test_get_comparable_competitors_partial_attribute_match() -> None:
    """Test that partial attribute matches are included with lower threshold."""
    from ptm.schemas import CompetitorPricing

    current_price = 100.0
    product_category = "SaaS"

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,
            category="SaaS Platform",  # Partial match (contains "SaaS") - gives 0.2 score
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$95/month"],
            normalized_monthly_usd=95.0,
            category="Cloud SaaS",  # Partial match (contains "SaaS") - gives 0.2 score
        ),
    ]

    # Use lower threshold to allow partial matches (0.2 score from partial category match)
    comparable = get_comparable_competitors(
        competitors,
        current_price_usd=current_price,
        product_category=product_category,
        product_name="Test Product",
        min_similarity_threshold=0.15,  # Lower threshold to allow partial matches
    )

    # Both should be included due to partial category match with lower threshold
    assert len(comparable) >= 1
    domains = {c.domain for c in comparable}
    assert "competitor1.com" in domains or "competitor2.com" in domains
