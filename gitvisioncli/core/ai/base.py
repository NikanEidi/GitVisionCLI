"""
Base AI Provider Interface

Abstract base class for all AI providers.
Implements strategy pattern for provider abstraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, List, Dict, Any, Optional
from enum import Enum


class ProviderType(Enum):
    """Supported AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


@dataclass
class AIProviderConfig:
    """Configuration for an AI provider."""
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    extra_params: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """Standardized AI response."""
    content: str
    model: str
    provider: ProviderType
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    All AI providers must implement this interface to ensure
    consistent behavior across different backends.
    """
    
    def __init__(self, config: AIProviderConfig):
        """
        Initialize the AI provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.provider_type = config.provider_type
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate provider configuration."""
        if not self.config.api_key and self.provider_type != ProviderType.OLLAMA:
            raise ValueError(f"API key required for {self.provider_type.value}")
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream responses from the AI provider.
        
        Args:
            messages: List of message dictionaries
            model: Model name (overrides default)
            temperature: Temperature setting (overrides default)
            max_tokens: Max tokens (overrides default)
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Content chunks as strings
        """
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AIResponse:
        """
        Get a complete (non-streaming) response.
        
        Args:
            messages: List of message dictionaries
            model: Model name (overrides default)
            temperature: Temperature setting (overrides default)
            max_tokens: Max tokens (overrides default)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            AIResponse with complete content
        """
        pass
    
    @abstractmethod
    async def stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream responses with tool/function calling support.
        
        Args:
            messages: List of message dictionaries
            tools: List of tool definitions
            model: Model name (overrides default)
            temperature: Temperature setting (overrides default)
            max_tokens: Max tokens (overrides default)
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Response chunks (content or tool calls)
        """
        pass
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of model names
        """
        return []
    
    def get_context_window(self, model: Optional[str] = None) -> int:
        """
        Get context window size for a model.
        
        Args:
            model: Model name (uses default if not provided)
        
        Returns:
            Context window size in tokens
        """
        model = model or self.config.default_model
        # Default context windows
        defaults = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 64000,
            "claude-3.5-sonnet": 200000,
            "gemini-1.5-pro": 1000000,
        }
        return defaults.get(model, 32768)

