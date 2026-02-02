"""Configuration settings for the energy agents application."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # MCP Database endpoint
    MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://192.168.68.126/agents-db-mcp")
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "anthropic"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model settings
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    # German market specific settings
    DEFAULT_COUNTRY = "Germany"
    CURRENCY = "EUR"
    DEFAULT_UNIT = "kWh"
