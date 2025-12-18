# -*- coding: utf-8 -*-
"""Evidence-only verdict logic (NO LLM required)."""


from ptm.aggregation import get_comparable_competitors
from ptm.parsing import normalize_to_monthly_usd, parse_price
from ptm.schemas import (
    EvidenceBundle,
    PricingVerdict,
    ProductInput,
    VerdictStatus,
)


def compute_verdict(
    product_input: ProductInput,
    evidence_bundle: EvidenceBundle,
    fx_rates: dict[str, float] | None = None,
    seat_count: int | None = None,
) -> PricingVerdict:
    """Compute pricing verdict based on evidence only (no LLM).

    This is a deterministic, rule-based verdict computation that:
    - Compares current price vs competitor prices ONLY if comparable
    - Returns UNDETERMINABLE if fewer than 2 comparable competitors
    - Calculates confidence based on evidence count and consistency

    Args:
        product_input: Product input with current price
        evidence_bundle: Evidence bundle with competitor pricing
        fx_rates: Optional FX rates for normalization
        seat_count: Optional seat count for per-seat pricing

    Returns:
        PricingVerdict with status, confidence, and reasons
    """
    # Parse current price
    current_parsed = parse_price(product_input.current_price)
    if not current_parsed:
        return PricingVerdict(
            status=VerdictStatus.UNDETERMINABLE,
            confidence=0.0,
            key_reasons=["Could not parse current product price"],
            gaps=["Current price format not recognized"],
            citations=[],
            competitor_count=0,
            evidence_bundle=evidence_bundle,
        )

    # Normalize current price
    current_normalized = normalize_to_monthly_usd(
        current_parsed, fx_rates=fx_rates, seat_count=seat_count
    )

    if current_normalized.gaps:
        return PricingVerdict(
            status=VerdictStatus.UNDETERMINABLE,
            confidence=0.0,
            key_reasons=["Could not normalize current product price"],
            gaps=current_normalized.gaps,
            citations=[],
            competitor_count=0,
            evidence_bundle=evidence_bundle,
        )

    current_monthly_usd = current_normalized.monthly_usd

    # Get comparable competitors
    comparable_competitors = get_comparable_competitors(evidence_bundle.competitor_pricing)

    # Check if we have enough competitors
    if len(comparable_competitors) < 2:
        return PricingVerdict(
            status=VerdictStatus.UNDETERMINABLE,
            confidence=0.0,
            key_reasons=[
                f"Only {len(comparable_competitors)} comparable competitor(s) found. "
                "Need at least 2 for comparison."
            ],
            gaps=[
                "Insufficient competitor data for comparison",
                *[gap for cp in evidence_bundle.competitor_pricing for gap in cp.gaps],
            ],
            citations=[str(s.url) for s in evidence_bundle.tavily_sources[:10]],
            competitor_count=len(comparable_competitors),
            evidence_bundle=evidence_bundle,
        )

    # Compare prices
    competitor_prices = [
        cp.normalized_monthly_usd
        for cp in comparable_competitors
        if cp.normalized_monthly_usd is not None
    ]

    avg_competitor_price = sum(competitor_prices) / len(competitor_prices)
    min_competitor_price = min(competitor_prices)
    max_competitor_price = max(competitor_prices)

    # Calculate price difference
    price_diff_percent = (current_monthly_usd - avg_competitor_price) / avg_competitor_price * 100

    # Determine verdict status
    if price_diff_percent < -20:  # More than 20% cheaper
        status = VerdictStatus.UNDERPRICED
        key_reasons = [
            f"Current price (${current_monthly_usd:.2f}/month) is "
            f"{abs(price_diff_percent):.1f}% below average competitor price "
            f"(${avg_competitor_price:.2f}/month)"
        ]
    elif price_diff_percent > 20:  # More than 20% more expensive
        status = VerdictStatus.OVERPRICED
        key_reasons = [
            f"Current price (${current_monthly_usd:.2f}/month) is "
            f"{price_diff_percent:.1f}% above average competitor price "
            f"(${avg_competitor_price:.2f}/month)"
        ]
    else:  # Within 20% of average
        status = VerdictStatus.FAIR
        key_reasons = [
            f"Current price (${current_monthly_usd:.2f}/month) is within "
            f"reasonable range of competitor prices "
            f"(${min_competitor_price:.2f}-${max_competitor_price:.2f}/month)"
        ]

    # Calculate confidence
    confidence = _calculate_confidence(
        competitor_count=len(comparable_competitors),
        price_consistency=competitor_prices,
        evidence_count=len(evidence_bundle.tavily_sources),
    )

    # Collect gaps from competitors
    all_gaps = [gap for cp in evidence_bundle.competitor_pricing for gap in cp.gaps]

    # Collect citations
    citations = [str(s.url) for s in evidence_bundle.tavily_sources[:20]]

    return PricingVerdict(
        status=status,
        confidence=confidence,
        key_reasons=key_reasons,
        gaps=all_gaps,
        citations=citations,
        competitor_count=len(comparable_competitors),
        evidence_bundle=evidence_bundle,
    )


def _calculate_confidence(
    competitor_count: int,
    price_consistency: list[float],
    evidence_count: int,
) -> float:
    """Calculate confidence score based on evidence quality.

    Args:
        competitor_count: Number of comparable competitors
        price_consistency: List of competitor prices
        evidence_count: Number of evidence sources

    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence from competitor count
    # More competitors = higher confidence
    competitor_score = min(competitor_count / 5.0, 1.0)  # Max at 5 competitors

    # Consistency score (lower variance = higher confidence)
    if len(price_consistency) > 1:
        mean_price = sum(price_consistency) / len(price_consistency)
        variance = sum((p - mean_price) ** 2 for p in price_consistency) / len(price_consistency)
        # Normalize variance (assuming prices are typically $10-$1000/month)
        normalized_variance = min(variance / 10000.0, 1.0)
        consistency_score = 1.0 - normalized_variance
    else:
        consistency_score = 0.5

    # Evidence count score
    evidence_score = min(evidence_count / 10.0, 1.0)  # Max at 10 sources

    # Weighted average
    confidence = 0.5 * competitor_score + 0.3 * consistency_score + 0.2 * evidence_score

    return min(max(confidence, 0.0), 1.0)  # Clamp to [0, 1]
