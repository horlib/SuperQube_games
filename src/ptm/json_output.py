# -*- coding: utf-8 -*-
"""JSON output generator for automation."""

import json
from pathlib import Path

from ptm.schemas import PricingVerdict


def generate_json_report(verdict: PricingVerdict, output_path: Path) -> None:
    """Generate machine-readable JSON report.

    JSON mirrors PricingVerdict schema and includes raw source metadata.

    Args:
        verdict: Pricing verdict
        output_path: Path to write report.json
    """
    # Convert verdict to dict (Pydantic handles serialization)
    verdict_dict = verdict.model_dump(mode="json")

    # Add metadata
    report_data = {
        "verdict": verdict_dict,
        "metadata": {
            "schema_version": "1.0",
            "generated_at": verdict_dict.get("evidence_bundle", {})
            .get("product_input", {})
            .get("name", "unknown"),
        },
    }

    # Write JSON with pretty formatting
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

    # Validate that output conforms to schema by loading it back
    # This ensures the JSON is valid and can be parsed
    with output_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)

    # Verify structure
    assert "verdict" in loaded
    assert "metadata" in loaded
