"""Tests for optional LLM reasoning mode."""

from unittest.mock import Mock, patch

import httpx
import pytest
from ptm.llm_reasoning import LLMReasoningError, enhance_verdict_with_llm
from ptm.schemas import (
    EvidenceBundle,
    PricingVerdict,
    ProductInput,
    VerdictStatus,
)


def test_enhance_verdict_with_llm_unavailable() -> None:
    """Test that verdict is returned unchanged when OpenAI unavailable."""
    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    verdict = PricingVerdict(
        status=VerdictStatus.FAIR,
        confidence=0.8,
        competitor_count=2,
        evidence_bundle=bundle,
    )

    with patch("ptm.llm_reasoning.is_openai_available", return_value=False):
        enhanced = enhance_verdict_with_llm(verdict, bundle)
        assert enhanced == verdict


@patch("ptm.llm_reasoning.get_openai_api_key")
@patch("ptm.llm_reasoning.get_openai_model")
@patch("ptm.llm_reasoning.is_openai_available")
@patch("httpx.Client")
def test_enhance_verdict_with_llm_success(
    mock_client_class: Mock,
    mock_is_available: Mock,
    mock_get_model: Mock,
    mock_get_key: Mock,
) -> None:
    """Test successful LLM enhancement."""
    mock_is_available.return_value = True
    mock_get_key.return_value = "test_key"
    mock_get_model.return_value = "gpt-4"

    # Mock OpenAI API response
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"additional_insights": ["Competitor pricing is consistent", "Market appears competitive"]}'
                }
            }
        ]
    }
    mock_response.raise_for_status = Mock()

    # Mock client
    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    verdict = PricingVerdict(
        status=VerdictStatus.FAIR,
        confidence=0.8,
        key_reasons=["Original reason"],
        competitor_count=2,
        evidence_bundle=bundle,
    )

    enhanced = enhance_verdict_with_llm(verdict, bundle)

    assert len(enhanced.key_reasons) > len(verdict.key_reasons)
    assert enhanced.status == verdict.status


@patch("ptm.llm_reasoning.get_openai_api_key")
@patch("ptm.llm_reasoning.get_openai_model")
@patch("ptm.llm_reasoning.is_openai_available")
@patch("httpx.Client")
def test_enhance_verdict_with_llm_api_error(
    mock_client_class: Mock,
    mock_is_available: Mock,
    mock_get_model: Mock,
    mock_get_key: Mock,
) -> None:
    """Test LLM enhancement with API error."""
    mock_is_available.return_value = True
    mock_get_key.return_value = "test_key"
    mock_get_model.return_value = "gpt-4"

    # Mock client that raises error
    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.post.side_effect = httpx.HTTPStatusError("Error", request=Mock(), response=Mock())
    mock_client_class.return_value = mock_client

    product = ProductInput(
        name="Test Product",
        url="https://example.com",
        current_price="$99/month",
    )
    bundle = EvidenceBundle(product_input=product)
    verdict = PricingVerdict(
        status=VerdictStatus.FAIR,
        confidence=0.8,
        competitor_count=2,
        evidence_bundle=bundle,
    )

    with pytest.raises(LLMReasoningError):
        enhance_verdict_with_llm(verdict, bundle)
