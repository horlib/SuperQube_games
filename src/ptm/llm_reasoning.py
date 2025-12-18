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

    # Models that support response_format json_object
    models_with_json_support = [
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4-1106-preview",
        "gpt-4-0125-preview",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo-1106",
    ]
    
    # Build payload - conditionally include response_format
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
                    "explicitly state the uncertainty. "
                    "You MUST respond with valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,  # Lower temperature for more deterministic output
    }
    
    # Only add response_format if model supports it
    if any(model.startswith(supported) for supported in models_with_json_support):
        payload["response_format"] = {"type": "json_object"}

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            # Better error handling - show response details
            if not response.is_success:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except Exception:
                    pass
                raise LLMReasoningError(
                    f"OpenAI API error {response.status_code}: {error_detail}"
                )
            
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
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        if e.response is not None:
            try:
                error_json = e.response.json()
                error_detail = error_json.get("error", {}).get("message", str(e))
            except Exception:
                error_detail = e.response.text
        raise LLMReasoningError(
            f"OpenAI API HTTP error {e.response.status_code if e.response else 'unknown'}: {error_detail}"
        ) from e
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

    # Build evidence section safely
    evidence_lines = [f"- {snippet[:200]}..." for snippet in snippets[:10]] if snippets else ["- No evidence snippets available"]
    evidence_text = "\n".join(evidence_lines)
    
    # Build gaps section safely
    gaps_lines = [f"- {gap}" for gap in verdict.gaps[:5]] if verdict.gaps else ["- No gaps identified"]
    gaps_text = "\n".join(gaps_lines)
    
    # Build reasons section safely
    reasons_lines = [f"- {reason}" for reason in verdict.key_reasons] if verdict.key_reasons else ["- No reasons provided"]
    reasons_text = "\n".join(reasons_lines)
    
    # Format confidence safely
    confidence_str = f"{float(verdict.confidence):.2f}"
    
    prompt = f"""Analyze the pricing verdict for {product.name} ({product.url}).

Current Price: {product.current_price}
Verdict Status: {verdict.status.value}
Confidence: {confidence_str}

Competitor Pricing Evidence:
{evidence_text}

Gaps in Data:
{gaps_text}

Current Reasoning:
{reasons_text}

Provide additional insights based ONLY on the evidence above. Do NOT estimate or invent any data.
Return ONLY valid JSON with this exact structure:
{{
  "additional_insights": ["insight 1", "insight 2", ...]
}}
Each insight should be a string referencing specific evidence. Do not include any text outside the JSON.
"""

    return prompt
