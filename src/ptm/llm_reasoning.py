"""Optional LLM reasoning mode (OpenAI) - enhances interpretation without violating real-data policy."""

import json

from ptm.config import get_openai_api_key, get_openai_model, is_openai_available
from ptm.schemas import EvidenceBundle, PricingVerdict


class LLMReasoningError(Exception):
    """Exception raised during LLM reasoning."""


def enhance_verdict_with_llm(
    verdict: PricingVerdict,
    evidence_bundle: EvidenceBundle,
) -> PricingVerdict:
    """Enhance verdict with LLM reasoning (optional).

    LLM sees ONLY:
    - Product facts
    - Extracted evidence snippets
    - Explicit gaps

    Prompt forbids estimation or invention.
    Output must be structured JSON.

    Args:
        verdict: Base verdict from evidence-only logic
        evidence_bundle: Evidence bundle with all data

    Returns:
        Enhanced PricingVerdict (or original if LLM unavailable/fails)

    Raises:
        LLMReasoningError: If LLM processing fails
    """
    if not is_openai_available():
        # Return original verdict if OpenAI not available
        return verdict

    try:
        enhanced_reasons = _call_openai_for_reasoning(
            verdict=verdict,
            evidence_bundle=evidence_bundle,
        )

        # Merge enhanced reasons with original
        combined_reasons = verdict.key_reasons + enhanced_reasons

        # Create enhanced verdict
        enhanced_verdict = PricingVerdict(
            status=verdict.status,
            confidence=verdict.confidence,
            key_reasons=combined_reasons,
            gaps=verdict.gaps,
            citations=verdict.citations,
            competitor_count=verdict.competitor_count,
            evidence_bundle=verdict.evidence_bundle,
        )

        return enhanced_verdict
    except Exception as e:
        # If LLM fails, return original verdict
        raise LLMReasoningError(f"LLM reasoning failed: {e}") from e


def _call_openai_for_reasoning(
    verdict: PricingVerdict,
    evidence_bundle: EvidenceBundle,
) -> list[str]:
    """Call OpenAI API for enhanced reasoning.

    Args:
        verdict: Current verdict
        evidence_bundle: Evidence bundle

    Returns:
        List of additional reasoning insights
    """
    import httpx

    api_key = get_openai_api_key()
    model = get_openai_model()

    # Build prompt with strict constraints
    prompt = _build_reasoning_prompt(verdict, evidence_bundle)

    # Call OpenAI API
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a pricing analysis assistant. You MUST ONLY use "
                    "the provided evidence. You MUST NOT estimate, guess, or "
                    "invent any prices, benchmarks, or data. Every conclusion "
                    "must reference specific evidence. If data is missing, "
                    "explicitly state the uncertainty."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,  # Lower temperature for more deterministic output
        "response_format": {"type": "json_object"},
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Extract reasoning from response
            content = data["choices"][0]["message"]["content"]
            reasoning_data = json.loads(content)

            # Extract additional insights
            insights = reasoning_data.get("additional_insights", [])
            if isinstance(insights, list):
                return insights
            return []
    except Exception as e:
        raise LLMReasoningError(f"OpenAI API call failed: {e}") from e


def _build_reasoning_prompt(
    verdict: PricingVerdict,
    evidence_bundle: EvidenceBundle,
) -> str:
    """Build prompt for LLM reasoning.

    Args:
        verdict: Current verdict
        evidence_bundle: Evidence bundle

    Returns:
        Prompt string
    """
    product = evidence_bundle.product_input

    # Collect evidence snippets (limit to avoid token limits)
    snippets = []
    for cp in evidence_bundle.competitor_pricing[:5]:  # Limit to 5 competitors
        snippets.extend(cp.evidence_snippets[:3])  # 3 snippets per competitor

    prompt = f"""Analyze the pricing verdict for {product.name} ({product.url}).

Current Price: {product.current_price}
Verdict Status: {verdict.status.value}
Confidence: {verdict.confidence:.2f}

Competitor Pricing Evidence:
{chr(10).join(f"- {snippet[:200]}..." for snippet in snippets[:10])}

Gaps in Data:
{chr(10).join(f"- {gap}" for gap in verdict.gaps[:5])}

Current Reasoning:
{chr(10).join(f"- {reason}" for reason in verdict.key_reasons)}

Provide additional insights based ONLY on the evidence above. Do NOT estimate or invent any data.
Return JSON with "additional_insights" array of strings, each referencing specific evidence.
"""

    return prompt
