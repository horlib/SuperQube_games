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
    
    # Get current product price - try to extract from key_reasons first (most reliable)
    current_price = None
    key_reasons = verdict.get("key_reasons", [])
    
    # Extract from key_reasons if available (e.g., "Current price ($4.00/month)")
    if key_reasons:
        import re
        for reason in key_reasons:
            match = re.search(r'\$([\d.]+)/month', reason)
            if match:
                try:
                    current_price = float(match.group(1))
                    break
                except ValueError:
                    pass
    
    # Fallback: parse from current_price string
    if current_price is None:
        current_price_str = product_input.get("current_price", "")
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


def calculate_price_statistics(comparison_df: pd.DataFrame, current_price: float | None) -> dict[str, Any]:
    """Calculate price statistics for competitors.
    
    Args:
        comparison_df: DataFrame with price comparison data
        current_price: Current product price (optional)
        
    Returns:
        Dictionary with statistics
    """
    competitor_prices = comparison_df[comparison_df["Is Product"] == False]["Price (USD/month)"]
    
    if competitor_prices.empty:
        return {}
    
    stats = {
        "count": len(competitor_prices),
        "mean": competitor_prices.mean(),
        "median": competitor_prices.median(),
        "min": competitor_prices.min(),
        "max": competitor_prices.max(),
        "std": competitor_prices.std(),
    }
    
    # Add quartiles
    quartiles = competitor_prices.quantile([0.25, 0.5, 0.75])
    stats["q25"] = quartiles[0.25]
    stats["q75"] = quartiles[0.75]
    
    # Calculate position of current price if available
    if current_price is not None:
        stats["current_price"] = current_price
        stats["current_vs_mean"] = current_price - stats["mean"]
        stats["current_vs_mean_pct"] = ((current_price - stats["mean"]) / stats["mean"]) * 100 if stats["mean"] > 0 else 0
        stats["current_percentile"] = (competitor_prices < current_price).sum() / len(competitor_prices) * 100
    
    return stats
