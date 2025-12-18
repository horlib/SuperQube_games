"""Tests for Pydantic schemas."""

import pytest
from ptm.schemas import (
    CompetitorPricing,
    EvidenceBundle,
    PricingVerdict,
    ProductInput,
    TavilySource,
    VerdictStatus,
)
from pydantic import ValidationError


def test_product_input_valid() -> None:
    """Test valid ProductInput."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com/product",
        current_price="$99/month",
    )
    assert product.name == "Test Product"
    assert str(product.url) == "https://example.com/product"
    assert product.current_price == "$99/month"


def test_product_input_invalid_url() -> None:
    """Test ProductInput with invalid URL."""
    with pytest.raises(ValidationError):
        ProductInput(
            name="Test Product",
            url="not-a-url",
            current_price="$99/month",
        )


def test_tavily_source_valid() -> None:
    """Test valid TavilySource."""
    source = TavilySource(
        url="https://example.com/pricing",
        title="Pricing Page",
        content="Price: $99/month",
    )
    assert str(source.url) == "https://example.com/pricing"
    assert source.title == "Pricing Page"
    assert source.content == "Price: $99/month"


def test_competitor_pricing_valid() -> None:
    """Test valid CompetitorPricing."""
    pricing = CompetitorPricing(
        domain="competitor.com",
        extracted_price_texts=["$99/month"],
        evidence_snippets=["Price: $99/month"],
        normalized_monthly_usd=99.0,
    )
    assert pricing.domain == "competitor.com"
    assert pricing.normalized_monthly_usd == 99.0


def test_competitor_pricing_invalid_price() -> None:
    """Test CompetitorPricing with invalid normalized price."""
    with pytest.raises(ValidationError):
        CompetitorPricing(
            domain="competitor.com",
            normalized_monthly_usd=-10.0,
        )


def test_evidence_bundle_valid() -> None:
    """Test valid EvidenceBundle."""
    product = ProductInput(
        name="Test",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    assert bundle.product_input == product
    assert bundle.tavily_sources == []
    assert bundle.competitor_pricing == []


def test_pricing_verdict_valid() -> None:
    """Test valid PricingVerdict."""
    product = ProductInput(
        name="Test",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    verdict = PricingVerdict(
        status=VerdictStatus.UNDETERMINABLE,
        confidence=0.5,
        competitor_count=0,
        evidence_bundle=bundle,
    )
    assert verdict.status == VerdictStatus.UNDETERMINABLE
    assert verdict.confidence == 0.5
    assert verdict.competitor_count == 0


def test_pricing_verdict_invalid_confidence() -> None:
    """Test PricingVerdict with invalid confidence."""
    product = ProductInput(
        name="Test",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    with pytest.raises(ValidationError):
        PricingVerdict(
            status=VerdictStatus.UNDETERMINABLE,
            confidence=1.5,  # Invalid: > 1.0
            competitor_count=0,
            evidence_bundle=bundle,
        )


def test_pricing_verdict_invalid_competitor_count() -> None:
    """Test PricingVerdict with invalid competitor count."""
    product = ProductInput(
        name="Test",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    with pytest.raises(ValidationError):
        PricingVerdict(
            status=VerdictStatus.UNDETERMINABLE,
            confidence=0.5,
            competitor_count=-1,  # Invalid: < 0
            evidence_bundle=bundle,
        )
