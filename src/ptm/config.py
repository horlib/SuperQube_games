# -*- coding: utf-8 -*-
"""Configuration management for Pricing Truth Machine."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_config() -> None:
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)


def get_tavily_api_key() -> str:
    """Get Tavily API key from environment.

    Raises:
        ValueError: If TAVILY_API_KEY is not set.

    Returns:
        Tavily API key.
    """
    load_config()
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise ValueError(
            "TAVILY_API_KEY is required but not set. "
            "Please set it in your .env file or environment variables."
        )
    return key


def get_openai_api_key() -> str | None:
    """Get OpenAI API key from environment.

    Returns:
        OpenAI API key if set, None otherwise.
    """
    load_config()
    return os.getenv("OPENAI_API_KEY")


def get_openai_model() -> str:
    """Get OpenAI model name from environment.

    Returns:
        OpenAI model name, defaults to 'gpt-4' if not set.
    """
    load_config()
    return os.getenv("OPENAI_MODEL", "gpt-4")


def is_openai_available() -> bool:
    """Check if OpenAI is configured and available.

    Returns:
        True if OpenAI API key is set, False otherwise.
    """
    return get_openai_api_key() is not None
