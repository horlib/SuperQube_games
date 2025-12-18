"""Tests for Markdown report generator."""

from pathlib import Path
from tempfile import TemporaryDirectory

from ptm.reporting import generate_markdown_report
from ptm.schemas import (
    EvidenceBundle,
    PricingVerdict,
    ProductInput,
    VerdictStatus,
)


def test_generate_markdown_report() -> None:
    """Test Markdown report generation."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    verdict = PricingVerdict(
        status=VerdictStatus.FAIR,
        confidence=0.8,
        key_reasons=["Price is competitive"],
        gaps=["Missing FX rate for EUR"],
        citations=["https://example.com/source1"],
        competitor_count=2,
        evidence_bundle=bundle,
    )

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.md"
        generate_markdown_report(verdict, output_path)

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")

        # Check key sections
        assert "# Pricing Analysis Report" in content
        assert "Test Product" in content
        assert "$99/month" in content
        assert "FAIR" in content
        assert "80.0%" in content or "0.8" in content
        assert "Price is competitive" in content
        assert "Missing FX rate" in content
        assert "https://example.com/source1" in content
        assert "Disclaimer" in content


def test_generate_markdown_report_with_competitors() -> None:
    """Test report generation with competitor data."""
    from ptm.schemas import CompetitorPricing

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
            evidence_snippets=["Price: $95/month"],
        ),
        CompetitorPricing(
            domain="competitor2.com",
            extracted_price_texts=["$105/month"],
            normalized_monthly_usd=105.0,
            evidence_snippets=["Price: $105/month"],
        ),
    ]

    bundle = EvidenceBundle(
        product_input=product,
        competitor_pricing=competitors,
    )

    verdict = PricingVerdict(
        status=VerdictStatus.FAIR,
        confidence=0.8,
        competitor_count=2,
        evidence_bundle=bundle,
    )

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.md"
        generate_markdown_report(verdict, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check competitor table
        assert "Competitor Comparison" in content
        assert "competitor1.com" in content
        assert "competitor2.com" in content
        assert "$95.00" in content or "$95" in content
        assert "$105.00" in content or "$105" in content
