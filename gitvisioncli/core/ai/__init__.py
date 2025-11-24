"""
AI Provider Abstraction Layer

Provides a unified interface for all AI providers (OpenAI, Anthropic, Google, Ollama).
Uses strategy pattern for provider switching.
"""

from gitvisioncli.core.ai.base import BaseAIProvider, AIProviderConfig, AIResponse
from gitvisioncli.core.ai.openai_provider import OpenAIProvider
from gitvisioncli.core.ai.factory import AIProviderFactory

__all__ = [
    "BaseAIProvider",
    "AIProviderConfig",
    "AIResponse",
    "OpenAIProvider",
    "AIProviderFactory",
]

