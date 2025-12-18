# -*- coding: utf-8 -*-
"""Load and validate JSON report data."""

import json
from pathlib import Path
from typing import Any

import streamlit as st


def load_report_json(file_path: Path | str) -> dict[str, Any] | None:
    """Load and parse report.json file.
    
    Args:
        file_path: Path to report.json file
        
    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        path = Path(file_path)
        if not path.exists():
            st.error(f"File not found: {file_path}")
            return None
            
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Validate structure
        if "verdict" not in data:
            st.error("Invalid report format: missing 'verdict' key")
            return None
            
        if "metadata" not in data:
            st.warning("Report missing metadata")
            
        return data
        
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
        return None
    except Exception as e:
        st.error(f"Error loading report: {e}")
        return None


def validate_report_structure(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate that report has required fields for visualization.
    
    Args:
        data: Parsed report JSON
        
    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []
    
    if "verdict" not in data:
        return False, ["Missing 'verdict' key"]
        
    verdict = data["verdict"]
    
    required_fields = ["status", "confidence", "competitor_count"]
    for field in required_fields:
        if field not in verdict:
            warnings.append(f"Missing required field: {field}")
            
    if "evidence_bundle" not in verdict:
        warnings.append("Missing 'evidence_bundle' - some visualizations may not work")
    else:
        bundle = verdict["evidence_bundle"]
        if "product_input" not in bundle:
            warnings.append("Missing 'product_input' in evidence_bundle")
        if "competitor_pricing" not in bundle:
            warnings.append("Missing 'competitor_pricing' in evidence_bundle")
            
    return len([w for w in warnings if "Missing required" in w]) == 0, warnings
