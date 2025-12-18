"""Tests for Tavily client."""

from unittest.mock import Mock, patch

import httpx
import pytest
from ptm.tavily_client import TavilyAuthError, TavilyClient, TavilyClientError


def test_tavily_client_init_with_key() -> None:
    """Test TavilyClient initialization with explicit API key."""
    client = TavilyClient(api_key="test_key")
    assert client.api_key == "test_key"


@patch("ptm.tavily_client.get_tavily_api_key")
def test_tavily_client_init_without_key(mock_get_key: Mock) -> None:
    """Test TavilyClient initialization without explicit API key."""
    mock_get_key.return_value = "config_key"
    client = TavilyClient()
    assert client.api_key == "config_key"


@patch("httpx.Client")
def test_tavily_search_success(mock_client_class: Mock) -> None:
    """Test successful Tavily search."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "url": "https://example.com/pricing",
                "title": "Pricing Page",
                "content": "Price: $99/month",
                "score": 0.95,
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

    client = TavilyClient(api_key="test_key")
    sources = client.search("test query")

    assert len(sources) == 1
    assert str(sources[0].url) == "https://example.com/pricing"
    assert sources[0].title == "Pricing Page"
    assert sources[0].content == "Price: $99/month"


@patch("httpx.Client")
def test_tavily_search_auth_error(mock_client_class: Mock) -> None:
    """Test Tavily search with authentication error."""
    # Mock response with 401
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    # Mock client
    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.post.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=Mock(), response=mock_response
    )
    mock_client_class.return_value = mock_client

    client = TavilyClient(api_key="test_key")

    with pytest.raises(TavilyAuthError, match="authentication failed"):
        client.search("test query")


@patch("httpx.Client")
def test_tavily_search_deduplication(mock_client_class: Mock) -> None:
    """Test that Tavily search deduplicates results by URL."""
    # Mock response with duplicate URLs
    mock_response = Mock()
    mock_response.json.return_value = {
        "results": [
            {
                "url": "https://example.com/pricing",
                "title": "Pricing Page 1",
                "content": "Price: $99/month",
            },
            {
                "url": "https://example.com/pricing?ref=test",
                "title": "Pricing Page 2",
                "content": "Price: $99/month",
            },
        ]
    }
    mock_response.raise_for_status = Mock()

    # Mock client
    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    client = TavilyClient(api_key="test_key")
    sources = client.search("test query")

    # Should deduplicate to 1 result
    assert len(sources) == 1


@patch("httpx.Client")
def test_tavily_search_timeout(mock_client_class: Mock) -> None:
    """Test Tavily search with timeout error."""
    # Mock client that raises timeout
    mock_client = Mock()
    mock_client.__enter__ = Mock(return_value=mock_client)
    mock_client.__exit__ = Mock(return_value=False)
    mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
    mock_client_class.return_value = mock_client

    client = TavilyClient(api_key="test_key")

    # Should retry and eventually raise TavilyClientError
    with pytest.raises(TavilyClientError, match="timed out"):
        client.search("test query")
