# -*- coding: utf-8 -*-
"""Competitor pricing aggregation."""

from urllib.parse import urlparse

from ptm.extraction import extract_price_texts, extract_pricing_snippets
from ptm.parsing import normalize_to_monthly_usd, parse_price
from ptm.schemas import CompetitorPricing, TavilySource


def aggregate_competitor_pricing(
    sources: list[TavilySource],
    fx_rates: dict[str, float] | None = None,
    seat_count: int | None = None,
) -> list[CompetitorPricing]:
    """Aggregate competitor pricing from sources.

    Groups sources by domain and extracts pricing information.
    Does NOT fill in missing data with assumptions.

    Args:
        sources: List of TavilySource objects
        fx_rates: Optional FX rates for normalization
        seat_count: Optional seat count for per-seat pricing

    Returns:
        List of CompetitorPricing objects
    """
    # Group sources by domain
    domain_sources: dict[str, list[TavilySource]] = {}

    for source in sources:
        try:
            domain = urlparse(str(source.url)).netloc
            if not domain:
                continue

            # Remove www. prefix for consistency
            domain = domain.replace("www.", "")

            if domain not in domain_sources:
                domain_sources[domain] = []
            domain_sources[domain].append(source)
        except Exception:
            # Skip invalid URLs
            continue

    # Build competitor pricing records
    competitor_pricing_list: list[CompetitorPricing] = []

    for domain, domain_source_list in domain_sources.items():
        # Extract all content from this domain's sources
        all_content = " ".join([s.content for s in domain_source_list if s.content])

        if not all_content:
            # No content, but still create record to flag as gap
            competitor_pricing = CompetitorPricing(
                domain=domain,
                extracted_price_texts=[],
                evidence_snippets=[],
                gaps=["No pricing content found in sources"],
            )
            competitor_pricing_list.append(competitor_pricing)
            continue

        # Extract pricing snippets
        snippets = extract_pricing_snippets(domain_source_list)

        # Extract price texts
        price_texts = extract_price_texts(snippets)

        # Try to parse and normalize prices
        normalized_monthly_usd = None
        gaps = []

        # Try to normalize first valid price
        for price_text in price_texts:
            parsed = parse_price(price_text)
            if parsed:
                normalized = normalize_to_monthly_usd(
                    parsed, fx_rates=fx_rates, seat_count=seat_count
                )
                if normalized.gaps:
                    gaps.extend(normalized.gaps)
                else:
                    normalized_monthly_usd = normalized.monthly_usd
                    break  # Use first successfully normalized price

        # If no normalized price, collect all gaps
        if normalized_monthly_usd is None and not gaps:
            gaps.append("Could not normalize any price (missing cadence, FX rate, or seat count)")

        # Create competitor pricing record
        competitor_pricing = CompetitorPricing(
            domain=domain,
            extracted_price_texts=price_texts,
            evidence_snippets=snippets[:10],  # Limit to first 10 snippets
            normalized_monthly_usd=normalized_monthly_usd,
            gaps=gaps,
        )

        competitor_pricing_list.append(competitor_pricing)

    return competitor_pricing_list


def get_comparable_competitors(
    competitor_pricing_list: list[CompetitorPricing],
) -> list[CompetitorPricing]:
    """Get competitors with comparable pricing (normalized monthly USD available).

    Args:
        competitor_pricing_list: List of CompetitorPricing objects

    Returns:
        List of competitors with normalized_monthly_usd set
    """
    return [cp for cp in competitor_pricing_list if cp.normalized_monthly_usd is not None]
