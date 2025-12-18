"""Tests for JSON output generator."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ptm.json_output import generate_json_report
from ptm.schemas import (
    EvidenceBundle,
    PricingVerdict,
    ProductInput,
    VerdictStatus,
)


def test_generate_json_report() -> None:
    """Test JSON report generation."""
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
        gaps=["Missing FX rate"],
        citations=["https://example.com/source1"],
        competitor_count=2,
        evidence_bundle=bundle,
    )

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.json"
        generate_json_report(verdict, output_path)

        assert output_path.exists()

        # Load and validate JSON
        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Check structure
        assert "verdict" in data
        assert "metadata" in data

        # Check verdict data
        verdict_data = data["verdict"]
        assert verdict_data["status"] == "FAIR"
        assert verdict_data["confidence"] == 0.8
        assert len(verdict_data["key_reasons"]) > 0
        assert len(verdict_data["gaps"]) > 0
        assert len(verdict_data["citations"]) > 0
        assert verdict_data["competitor_count"] == 2


def test_generate_json_report_validates_schema() -> None:
    """Test that generated JSON validates against schema."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    verdict = PricingVerdict(
        status=VerdictStatus.UNDETERMINABLE,
        confidence=0.0,
        competitor_count=0,
        evidence_bundle=bundle,
    )

    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.json"
        generate_json_report(verdict, output_path)

        # Should be able to load and parse
        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Should have stable keys
        assert "verdict" in data
        assert "status" in data["verdict"]
        assert "confidence" in data["verdict"]
        assert "competitor_count" in data["verdict"]
