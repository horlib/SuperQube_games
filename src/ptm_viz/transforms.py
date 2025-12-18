# -*- coding: utf-8 -*-
"""Transform report data into chart-ready formats."""

from typing import Any

import pandas as pd


def build_competitor_table(data: dict[str, Any]) -> pd.DataFrame:
    """Build competitor comparison table from report data.
    
    Args:
        data: Parsed report JSON
        
    Returns:
        DataFrame with columns: Competitor, Source URL, Price Evidence, Normalized Monthly USD, Notes
    """
    verdict = data.get("verdict", {})
    evidence_bundle = verdict.get("evidence_bundle", {})
    competitor_pricing = evidence_bundle.get("competitor_pricing", [])
    
    rows = []
    for cp in competitor_pricing:
        domain = cp.get("domain", "Unknown")
        
        # Get source URL from tavily_sources if available
        source_url = ""
        tavily_sources = evidence_bundle.get("tavily_sources", [])
        for source in tavily_sources:
            if domain in str(source.get("url", "")):
                source_url = str(source.get("url", ""))
                break
        
        # Price evidence (verbatim)
        price_texts = cp.get("extracted_price_texts", [])
        price_evidence = " | ".join(price_texts[:3]) if price_texts else "No explicit price found"
        
        # Normalized price
        normalized = cp.get("normalized_monthly_usd")
        normalized_str = f"${normalized:.2f}" if normalized is not None else "N/A"
        
        # Notes
        gaps = cp.get("gaps", [])
        notes = "; ".join(gaps[:2]) if gaps else ""
        
        rows.append({
            "Competitor": domain,
            "Source URL": source_url,
            "Price Evidence (verbatim)": price_evidence,
            "Normalized Monthly USD": normalized_str,
            "Normalized Value": normalized,  # For sorting/filtering
            "Notes": notes,
            "All Price Texts": price_texts,  # For expander
            "Evidence Snippets": cp.get("evidence_snippets", []),
        })
    
    return pd.DataFrame(rows)


def build_price_comparison_data(data: dict[str, Any]) -> tuple[pd.DataFrame, float | None]:
    """Build data for price comparison chart.
    
    Args:
        data: Parsed report JSON
        
    Returns:
        Tuple of (DataFrame with competitor prices, current product price or None)
    """
    verdict = data.get("verdict", {})
    evidence_bundle = verdict.get("evidence_bundle", {})
    product_input = evidence_bundle.get("product_input", {})
    competitor_pricing = evidence_bundle.get("competitor_pricing", [])
    
    # Get current product price
    current_price_str = product_input.get("current_price", "")
    current_price = None
    
    # Try to parse current price using ptm.parsing if available, otherwise use simple regex
    if current_price_str:
        try:
            # Try using ptm.parsing module (more robust)
            from ptm.parsing import normalize_to_monthly_usd, parse_price
            
            parsed = parse_price(current_price_str)
            if parsed:
                normalized = normalize_to_monthly_usd(parsed)
                if normalized.monthly_usd and normalized.monthly_usd > 0:
                    current_price = normalized.monthly_usd
        except (ImportError, AttributeError, ValueError):
            # Fallback to simple regex extraction
            try:
                import re
                # Look for $X/month pattern
                match = re.search(r'\$([\d.]+)/month', current_price_str, re.IGNORECASE)
                if match:
                    current_price = float(match.group(1))
            except (ValueError, AttributeError):
                pass
    
    # Build competitor data (only with normalized prices)
    rows = []
    for cp in competitor_pricing:
        normalized = cp.get("normalized_monthly_usd")
        if normalized is not None:
            rows.append({
                "Competitor": cp.get("domain", "Unknown"),
                "Price (USD/month)": normalized,
                "Is Product": False,
            })
    
    # Add current product if we have a price
    if current_price is not None:
        product_name = product_input.get("name", "Your Product")
        rows.append({
            "Competitor": product_name,
            "Price (USD/month)": current_price,
            "Is Product": True,
        })
    
    df = pd.DataFrame(rows)
    
    # Sort by price
    if not df.empty:
        df = df.sort_values("Price (USD/month)", ascending=True)
    
    return df, current_price


def get_product_info(data: dict[str, Any]) -> dict[str, Any]:
    """Extract product information from report.
    
    Args:
        data: Parsed report JSON
        
    Returns:
        Dictionary with product name, URL, current_price
    """
    verdict = data.get("verdict", {})
    evidence_bundle = verdict.get("evidence_bundle", {})
    product_input = evidence_bundle.get("product_input", {})
    
    return {
        "name": product_input.get("name", "Unknown Product"),
        "url": product_input.get("url", ""),
        "current_price": product_input.get("current_price", "N/A"),
    }
