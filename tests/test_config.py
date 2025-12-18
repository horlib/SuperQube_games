"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from ptm.config import (
    get_openai_api_key,
    get_openai_model,
    get_tavily_api_key,
    is_openai_available,
)


def test_get_tavily_api_key_missing() -> None:
    """Test that missing Tavily API key raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="TAVILY_API_KEY is required"):
            get_tavily_api_key()


def test_get_tavily_api_key_present() -> None:
    """Test that present Tavily API key is returned."""
    with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}):
        assert get_tavily_api_key() == "test_key"


def test_get_openai_api_key_missing() -> None:
    """Test that missing OpenAI API key returns None."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_openai_api_key() is None


def test_get_openai_api_key_present() -> None:
    """Test that present OpenAI API key is returned."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        assert get_openai_api_key() == "test_key"


def test_get_openai_model_default() -> None:
    """Test that default OpenAI model is returned when not set."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_openai_model() == "gpt-4"


def test_get_openai_model_custom() -> None:
    """Test that custom OpenAI model is returned when set."""
    with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-3.5-turbo"}):
        assert get_openai_model() == "gpt-3.5-turbo"


def test_is_openai_available_false() -> None:
    """Test that is_openai_available returns False when key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        assert is_openai_available() is False


def test_is_openai_available_true() -> None:
    """Test that is_openai_available returns True when key is present."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
        assert is_openai_available() is True
