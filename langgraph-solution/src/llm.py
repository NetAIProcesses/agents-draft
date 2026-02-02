"""LLM initialization and configuration."""

import os
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.config import Config


def get_llm(
    provider: Literal["openai", "anthropic"] = None,
    model: str = None,
    temperature: float = 0.0,
):
    """
    Get the configured LLM instance.
    
    Args:
        provider: The LLM provider ("openai" or "anthropic").
        model: The model name to use.
        temperature: The temperature for generation (default: 0.0 for consistency).
    
    Returns:
        Configured LLM instance.
    """
    provider = provider or Config.LLM_PROVIDER
    
    if provider == "openai":
        model = model or Config.OPENAI_MODEL
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=Config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "anthropic":
        model = model or Config.ANTHROPIC_MODEL
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=Config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY"),
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_default_llm():
    """Get the default LLM based on configuration."""
    return get_llm()
