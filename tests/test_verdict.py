"""Tests for evidence-only verdict logic."""

from ptm.schemas import (
    CompetitorPricing,
    EvidenceBundle,
    ProductInput,
    TavilySource,
    VerdictStatus,
)
from ptm.verdict import compute_verdict


def test_compute_verdict_underpriced() -> None:
    """Test verdict for underpriced product."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$50/month",
    )

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$100/month"],
            normalized_monthly_usd=100.0,
        ),
    ]

    bundle = EvidenceBundle(
        product_input=product,
        tavily_sources=[
            TavilySource(
                url="https://competitor1.com/pricing",
                title="Pricing",
                content="Price: $99/month",
            )
        ],
        competitor_pricing=competitors,
    )

    verdict = compute_verdict(product, bundle)

    assert verdict.status == VerdictStatus.UNDERPRICED
    assert verdict.confidence > 0.0
    assert verdict.competitor_count == 2


def test_compute_verdict_overpriced() -> None:
    """Test verdict for overpriced product."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$150/month",
    )

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$100/month"],
            normalized_monthly_usd=100.0,
        ),
    ]

    bundle = EvidenceBundle(
        product_input=product,
        competitor_pricing=competitors,
    )

    verdict = compute_verdict(product, bundle)

    assert verdict.status == VerdictStatus.OVERPRICED
    assert verdict.confidence > 0.0


def test_compute_verdict_fair() -> None:
    """Test verdict for fairly priced product."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$95/month"],
            normalized_monthly_usd=95.0,
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$105/month"],
            normalized_monthly_usd=105.0,
        ),
    ]

    bundle = EvidenceBundle(
        product_input=product,
        competitor_pricing=competitors,
    )

    verdict = compute_verdict(product, bundle)

    assert verdict.status == VerdictStatus.FAIR
    assert verdict.confidence > 0.0


def test_compute_verdict_undeterminable_insufficient_competitors() -> None:
    """Test verdict when insufficient competitors."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )

    competitors = [
        CompetitorPricing(
            domain="competitor1.com",
            extracted_price_texts=["$99/month"],
            normalized_monthly_usd=99.0,
        ),
    ]

    bundle = EvidenceBundle(
        product_input=product,
        competitor_pricing=competitors,
    )

    verdict = compute_verdict(product, bundle)

    assert verdict.status == VerdictStatus.UNDETERMINABLE
    assert "at least 2" in " ".join(verdict.key_reasons).lower()


def test_compute_verdict_undeterminable_unparseable_price() -> None:
    """Test verdict when current price cannot be parsed."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="Contact us for pricing",
    )

    bundle = EvidenceBundle(product_input=product)

    verdict = compute_verdict(product, bundle)

    assert verdict.status == VerdictStatus.UNDETERMINABLE
    assert "parse" in " ".join(verdict.key_reasons).lower()


def test_compute_verdict_confidence_calculation() -> None:
    """Test that confidence is calculated correctly."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )

    competitors = [
        CompetitorPricing(
            domain=f"competitor{i}.com",
            extracted_price_texts=[f"${99 + i}/month"],
            normalized_monthly_usd=99.0 + i,
        )
        for i in range(5)  # 5 competitors for high confidence
    ]

    bundle = EvidenceBundle(
        product_input=product,
        tavily_sources=[
            TavilySource(
                url=f"https://competitor{i}.com/pricing",
                title="Pricing",
                content=f"Price: ${99 + i}/month",
            )
            for i in range(10)  # 10 sources
        ],
        competitor_pricing=competitors,
    )

    verdict = compute_verdict(product, bundle)

    # Should have higher confidence with more competitors and sources
    assert verdict.confidence > 0.5
    assert 0.0 <= verdict.confidence <= 1.0
