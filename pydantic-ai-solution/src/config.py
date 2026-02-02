"""Configuration settings for the German Energy Market agents."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration."""
    
    # Model settings - use 'test' for testing without API key
    model_name: str = os.getenv("MODEL_NAME", "openai:gpt-4o-mini")
    
    # API Keys (loaded from environment)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    
    # Application settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    language: str = os.getenv("LANGUAGE", "en")  # English by default
    
    def get_model(self) -> str:
        """Get the model to use, falling back to 'test' if no API key is available."""
        if self.model_name == "test":
            return "test"
        if self.openai_api_key or self.github_token:
            return self.model_name
        # No API key available, use test model
        return "test"


config = Config()
