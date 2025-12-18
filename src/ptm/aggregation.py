# -*- coding: utf-8 -*-
"""Competitor pricing aggregation."""

import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

from ptm.extraction import (
    extract_price_texts,
    extract_pricing_snippets,
    extract_product_attributes,
)
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
        
        # Extract product attributes for better competitor matching
        attributes = extract_product_attributes(domain_source_list)

        # Try to parse and normalize prices
        normalized_monthly_usd = None
        cadence = None
        gaps = []

        # Try to normalize first valid price
        # Use snippet context to help detect cadence
        for price_text in price_texts:
            # Find snippet containing this price text for context
            context = None
            for snippet in snippets:
                if price_text.lower() in snippet.lower():
                    context = snippet
                    break
            
            parsed = parse_price(price_text, context=context)
            if parsed:
                normalized = normalize_to_monthly_usd(
                    parsed, fx_rates=fx_rates, seat_count=seat_count
                )
                if normalized.gaps:
                    gaps.extend(normalized.gaps)
                else:
                    # Only set normalized price if it's positive (no gaps)
                    if normalized.monthly_usd > 0:
                        normalized_monthly_usd = normalized.monthly_usd
                        cadence = parsed.cadence  # Store cadence for reporting
                        break  # Use first successfully normalized price
                    else:
                        gaps.extend(normalized.gaps)

        # If no normalized price, collect all gaps
        if normalized_monthly_usd is None and not gaps:
            gaps.append("Could not normalize any price (missing cadence, FX rate, or seat count)")

        # Create competitor pricing record
        competitor_pricing = CompetitorPricing(
            domain=domain,
            extracted_price_texts=price_texts,
            evidence_snippets=snippets[:10],  # Limit to first 10 snippets
            normalized_monthly_usd=normalized_monthly_usd,
            cadence=cadence if 'cadence' in locals() else None,
            gaps=gaps,
            category=attributes.get("category"),
            target_customer=attributes.get("target_customer"),
            key_features=attributes.get("key_features", []),
            product_description=attributes.get("product_description"),
            problem_statement=attributes.get("problem_statement"),
            decision_context=attributes.get("decision_context"),
            payment_model=attributes.get("payment_model"),
        )

        competitor_pricing_list.append(competitor_pricing)

    return competitor_pricing_list


def get_comparable_competitors(
    competitor_pricing_list: list[CompetitorPricing],
    current_price_usd: float | None = None,
    price_similarity_factor: float = 5.0,  # Stricter default: 0.2x to 5x instead of 0.1x to 10x
    product_category: str | None = None,
    product_target_customer: str | None = None,
    product_key_features: list[str] | None = None,
    product_name: str | None = None,
    product_problem_statement: str | None = None,
    product_decision_context: str | None = None,
    product_payment_model: str | None = None,
    min_similarity_threshold: float = 0.4,  # Require at least 40% similarity (stricter)
) -> list[CompetitorPricing]:
    """Get competitors that belong to the same competitive group.
    
    Products belong to the same competitive group when they:
    1. Solve the same specific problem (problem_statement)
    2. Have the same decision context (decision_context)
    3. Have comparable price (price similarity)
    4. Have unifiable payment form (payment_model)
    
    Filters competitors to ensure they are truly comparable based on these criteria.

    Args:
        competitor_pricing_list: List of CompetitorPricing objects
        current_price_usd: Optional current product price in USD for filtering
        price_similarity_factor: Maximum price difference factor (default 5.0 means 
                                 0.2x to 5x current price). Lower values = stricter filtering.
        product_category: Optional product category for matching
        product_target_customer: Optional target customer segment for matching
        product_key_features: Optional list of key features for matching
        product_name: Optional product name for keyword matching
        product_problem_statement: Optional problem statement that product solves
        product_decision_context: Optional decision context (who decides, when, why)
        product_payment_model: Optional payment model (subscription, one-time, etc.)
        min_similarity_threshold: Minimum similarity score required (default 0.4 = 40%)

    Returns:
        List of competitors with normalized_monthly_usd set that solve the same problem,
        in the same decision context, with comparable price and payment model
    """
    # First filter: only competitors with normalized prices
    competitors_with_prices = [
        cp for cp in competitor_pricing_list 
        if cp.normalized_monthly_usd is not None
    ]
    
    # If no current price provided, return all with normalized prices
    if current_price_usd is None or current_price_usd <= 0:
        return competitors_with_prices
    
    # Second filter: price similarity
    # If current price is very small (< $1), it might be usage-based pricing
    # In that case, be more lenient with price filtering
    if current_price_usd < 1.0:
        # For usage-based pricing, use wider range (0.1x to 20x)
        price_similarity_factor_usage = price_similarity_factor * 4.0
        min_price = current_price_usd / price_similarity_factor_usage
        max_price = current_price_usd * price_similarity_factor_usage
    else:
        min_price = current_price_usd / price_similarity_factor
        max_price = current_price_usd * price_similarity_factor
    
    price_filtered = [
        cp for cp in competitors_with_prices
        if min_price <= cp.normalized_monthly_usd <= max_price
    ]
    
    # Third filter: competitive group matching
    # Products belong to the same competitive group when they:
    # 1. Solve the same specific problem (problem_statement) - weight: 0.4
    # 2. Have the same decision context (decision_context) - weight: 0.3
    # 3. Have comparable price (already filtered) - weight: 0.2
    # 4. Have unifiable payment form (payment_model) - weight: 0.1
    
    # Adjust threshold if competitive group attributes are not available
    has_competitive_group_attrs = bool(product_problem_statement or product_decision_context or product_payment_model)
    # If competitive group attributes are not available, use lower threshold (0.15 instead of 0.4)
    # This allows legacy matching to work when new attributes aren't extracted
    effective_threshold = min_similarity_threshold if has_competitive_group_attrs else 0.15
    
    comparable = []
    for cp in price_filtered:
        # Calculate competitive group similarity
        group_score = _calculate_competitive_group_similarity(
            competitor=cp,
            product_problem_statement=product_problem_statement,
            product_decision_context=product_decision_context,
            product_payment_model=product_payment_model,
        )
        
        # Calculate legacy attribute similarity (for backward compatibility)
        legacy_score = _calculate_attribute_similarity(
            competitor=cp,
            product_category=product_category,
            product_target_customer=product_target_customer,
            product_key_features=product_key_features,
        )
        
        # Calculate name/keyword similarity bonus
        name_bonus = 0.0
        if product_name:
            name_bonus = _calculate_name_similarity(cp.domain, product_name)
        
        # Combine scores: prioritize competitive group matching
        if has_competitive_group_attrs:
            # Use competitive group matching as primary
            # If group_score is 0 (no matches), fall back more to legacy
            if group_score > 0:
                total_score = group_score + (legacy_score * 0.2) + (name_bonus * 0.1)
            else:
                # No competitive group matches, rely more on legacy
                total_score = (legacy_score * 0.7) + (name_bonus * 0.3)
        else:
            # Fallback to legacy matching if new attributes not available
            total_score = legacy_score + name_bonus
        
        # Filter out non-product domains
        if _is_non_product_domain(cp.domain):
            if total_score < 0.5 and name_bonus < 0.3:
                continue
        
        # Include competitor if total score meets threshold
        if total_score >= effective_threshold:
            comparable.append(cp)
        elif not has_competitive_group_attrs:
            # Fallback: if no competitive group attributes, use legacy logic
            has_attributes = cp.category or cp.target_customer or cp.key_features
            if not has_attributes:
                price_ratio = cp.normalized_monthly_usd / current_price_usd if current_price_usd else 1.0
                if 0.5 <= price_ratio <= 2.0 or name_bonus >= 0.3:
                    comparable.append(cp)
    
    return comparable


def _calculate_competitive_group_similarity(
    competitor: CompetitorPricing,
    product_problem_statement: str | None = None,
    product_decision_context: str | None = None,
    product_payment_model: str | None = None,
) -> float:
    """Calculate similarity score based on competitive group criteria.
    
    Products belong to the same competitive group when they:
    1. Solve the same specific problem (problem_statement) - weight: 0.4
    2. Have the same decision context (decision_context) - weight: 0.3
    3. Have unifiable payment form (payment_model) - weight: 0.1
    (Price similarity is already filtered separately)
    
    Args:
        competitor: CompetitorPricing object to compare
        product_problem_statement: Problem statement that product solves
        product_decision_context: Decision context (who decides, when, why)
        product_payment_model: Payment model (subscription, one-time, etc.)
        
    Returns:
        Similarity score (0.0 = no match, 1.0 = perfect match)
    """
    score = 0.0
    total_weight = 0.0
    
    # Problem statement match (weight: 0.4) - MOST IMPORTANT
    if product_problem_statement:
        total_weight += 0.4
        if competitor.problem_statement:
            problem_similarity = _calculate_text_similarity(
                product_problem_statement.lower(),
                competitor.problem_statement.lower()
            )
            score += 0.4 * problem_similarity
        else:
            # If competitor has no problem statement, check if description/keywords match
            if competitor.product_description:
                desc_similarity = _calculate_text_similarity(
                    product_problem_statement.lower(),
                    competitor.product_description.lower()
                )
                score += 0.4 * desc_similarity * 0.7  # Lower weight for description match
    
    # Decision context match (weight: 0.3)
    if product_decision_context:
        total_weight += 0.3
        if competitor.decision_context:
            context_similarity = _calculate_text_similarity(
                product_decision_context.lower(),
                competitor.decision_context.lower()
            )
            score += 0.3 * context_similarity
        else:
            # Fallback to target_customer if decision_context not available
            if competitor.target_customer:
                customer_match = _calculate_text_similarity(
                    product_decision_context.lower(),
                    competitor.target_customer.lower()
                )
                score += 0.3 * customer_match * 0.6  # Lower weight for fallback
    
    # Payment model match (weight: 0.1)
    if product_payment_model:
        total_weight += 0.1
        if competitor.payment_model:
            if product_payment_model.lower() == competitor.payment_model.lower():
                score += 0.1
            # Check for compatible models
            elif _are_payment_models_compatible(product_payment_model, competitor.payment_model):
                score += 0.05
    
    # Normalize score if weights don't sum to 1.0
    if total_weight > 0:
        return score / total_weight
    
    return 0.0


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using multiple methods.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Exact match
    if text1 == text2:
        return 1.0
    
    # Substring match
    if text1 in text2 or text2 in text1:
        shorter = min(len(text1), len(text2))
        longer = max(len(text1), len(text2))
        return shorter / longer
    
    # Word overlap
    words1 = set(text1.split())
    words2 = set(text2.split())
    if words1 and words2:
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        jaccard = overlap / union if union > 0 else 0.0
        
        # SequenceMatcher for fuzzy similarity
        from difflib import SequenceMatcher
        sequence_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Combine both methods
        return (jaccard * 0.6) + (sequence_similarity * 0.4)
    
    return 0.0


def _are_payment_models_compatible(model1: str, model2: str) -> bool:
    """Check if two payment models are compatible/unifiable.
    
    Args:
        model1: First payment model
        model2: Second payment model
        
    Returns:
        True if models are compatible
    """
    model1_lower = model1.lower()
    model2_lower = model2.lower()
    
    # Compatible groups
    compatible_groups = [
        {"subscription", "tiered", "freemium"},  # All recurring models
        {"one-time", "lifetime"},  # One-time payments
        {"per-seat", "per-user"},  # Per-user pricing
    ]
    
    for group in compatible_groups:
        if model1_lower in group and model2_lower in group:
            return True
    
    return False


def _calculate_attribute_similarity(
    competitor: CompetitorPricing,
    product_category: str | None = None,
    product_target_customer: str | None = None,
    product_key_features: list[str] | None = None,
) -> float:
    """Calculate similarity score based on product attributes.
    
    Returns a score between 0.0 and 1.0 based on how well competitor
    attributes match the product attributes.
    
    Args:
        competitor: CompetitorPricing object to compare
        product_category: Product category to match
        product_target_customer: Target customer segment to match
        product_key_features: List of key features to match
        
    Returns:
        Similarity score (0.0 = no match, 1.0 = perfect match)
    """
    score = 0.0
    matches = 0
    total_checks = 0
    
    # Category match (weight: 0.4)
    if product_category:
        total_checks += 1
        if competitor.category:
            # Case-insensitive comparison
            if product_category.lower() == competitor.category.lower():
                score += 0.4
                matches += 1
            # Partial match (substring)
            elif product_category.lower() in competitor.category.lower() or \
                 competitor.category.lower() in product_category.lower():
                score += 0.2
                matches += 1
    
    # Target customer match (weight: 0.3)
    if product_target_customer:
        total_checks += 1
        if competitor.target_customer:
            if product_target_customer.lower() == competitor.target_customer.lower():
                score += 0.3
                matches += 1
            # Partial match
            elif product_target_customer.lower() in competitor.target_customer.lower() or \
                 competitor.target_customer.lower() in product_target_customer.lower():
                score += 0.15
                matches += 1
    
    # Features match (weight: 0.3)
    if product_key_features:
        total_checks += 1
        if competitor.key_features:
            # Use fuzzy matching for features
            product_features_lower = [f.lower().strip() for f in product_key_features]
            competitor_features_lower = [f.lower().strip() for f in competitor.key_features]
            
            # Calculate fuzzy similarity for each feature pair
            best_matches = []
            for pf in product_features_lower:
                best_ratio = 0.0
                for cf in competitor_features_lower:
                    # Exact match
                    if pf == cf:
                        best_ratio = 1.0
                        break
                    # Substring match
                    elif pf in cf or cf in pf:
                        best_ratio = max(best_ratio, 0.7)
                    # Fuzzy similarity
                    else:
                        ratio = SequenceMatcher(None, pf, cf).ratio()
                        if ratio > 0.6:  # Threshold for fuzzy match
                            best_ratio = max(best_ratio, ratio)
                best_matches.append(best_ratio)
            
            # Calculate average match ratio
            if best_matches:
                avg_match_ratio = sum(best_matches) / len(best_matches)
                # Also consider overlap of exact matches
                exact_matches = sum(1 for r in best_matches if r >= 0.9)
                overlap_bonus = exact_matches / max(len(product_features_lower), len(competitor_features_lower))
                
                # Combine fuzzy match and exact overlap
                final_ratio = (avg_match_ratio * 0.7) + (overlap_bonus * 0.3)
                score += 0.3 * final_ratio
                matches += 1
    
    # If no attributes to check, return neutral score
    if total_checks == 0:
        return 0.5
    
    return score


def _calculate_name_similarity(competitor_domain: str, product_name: str) -> float:
    """Calculate similarity score based on product name and competitor domain.
    
    Extracts keywords from product name and checks if they appear in domain.
    This helps identify direct competitors (e.g., "ChatGPT" vs "chatgpt.com").
    
    Args:
        competitor_domain: Competitor domain name
        product_name: Product name to match
        
    Returns:
        Similarity bonus score (0.0 to 0.5)
    """
    if not product_name or not competitor_domain:
        return 0.0
    
    product_lower = product_name.lower()
    domain_lower = competitor_domain.lower()
    
    # Remove common TLDs and www
    domain_clean = domain_lower.replace("www.", "").split(".")[0]
    
    # Extract key words from product name (remove common words)
    common_words = {"the", "a", "an", "and", "or", "but", "for", "with", "plus", "pro", "free"}
    product_words = [w for w in product_lower.split() if w not in common_words and len(w) > 2]
    
    if not product_words:
        return 0.0
    
    # Check if any product word appears in domain
    matches = sum(1 for word in product_words if word in domain_clean)
    
    if matches == 0:
        return 0.0
    
    # Calculate bonus based on match ratio
    match_ratio = matches / len(product_words)
    
    # Also check if domain contains significant portion of product name
    if len(product_lower) > 5:
        # Check if domain contains substantial substring of product name
        for i in range(len(product_lower) - 4):
            substring = product_lower[i:i+5]
            if substring in domain_clean:
                match_ratio = max(match_ratio, 0.5)
    
    return min(match_ratio * 0.5, 0.5)  # Max bonus of 0.5


def _is_non_product_domain(domain: str) -> bool:
    """Check if domain is likely a non-product site (forum, blog, news, etc.).
    
    Args:
        domain: Domain name to check
        
    Returns:
        True if domain appears to be non-product (forum, blog, news site)
    """
    if not domain:
        return False
    
    domain_lower = domain.lower()
    
    # Known non-product domains/patterns
    non_product_patterns = [
        "reddit.com",
        "forum",
        "blog",
        "news",
        "medium.com",
        "quora.com",
        "stackoverflow.com",
        "github.com",
        "youtube.com",
        "facebook.com",
        "twitter.com",
        "linkedin.com",
        "pinterest.com",
        "tumblr.com",
        "wikipedia.org",
        "wikihow.com",
        ".edu",
        ".gov",
        "help.",
        "support.",
        "docs.",
        "documentation",
    ]
    
    # Check if domain matches any non-product pattern
    for pattern in non_product_patterns:
        if pattern in domain_lower:
            return True
    
    # Check if domain looks like a subdomain of a non-product site
    parts = domain_lower.split(".")
    if len(parts) >= 2:
        # Check second-level domain
        if parts[-2] in ["reddit", "medium", "quora", "stackoverflow", "github"]:
            return True
    
    return False
