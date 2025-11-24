"""
Provider Strategy

Strategy pattern for different AI provider behaviors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProviderStrategy(ABC):
    """
    Abstract base class for provider strategies.
    
    Handles provider-specific:
    - Configuration
    - Model normalization
    - API key management
    - Error handling
    """
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass
    
    @abstractmethod
    def normalize_model(self, model: str) -> str:
        """
        Normalize model name for this provider.
        
        Args:
            model: Model name
        
        Returns:
            Normalized model name
        """
        pass
    
    @abstractmethod
    def get_api_key(self) -> Optional[str]:
        """Get API key for this provider."""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration."""
        pass


class OpenAIStrategy(ProviderStrategy):
    """Strategy for OpenAI provider."""
    
    def __init__(self, api_key: Optional[str], config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
    
    def get_provider_name(self) -> str:
        return "openai"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def normalize_model(self, model: str) -> str:
        # OpenAI models are already normalized
        return model
    
    def get_api_key(self) -> Optional[str]:
        return self.api_key
    
    def get_config(self) -> Dict[str, Any]:
        return self.config


class ClaudeStrategy(ProviderStrategy):
    """Strategy for Claude/Anthropic provider."""
    
    def __init__(self, api_key: Optional[str], config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
    
    def get_provider_name(self) -> str:
        return "claude"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def normalize_model(self, model: str) -> str:
        # Normalize Claude model names
        model_lower = model.lower()
        if "claude" in model_lower:
            return model
        # Add claude prefix if missing
        return f"claude-{model}"
    
    def get_api_key(self) -> Optional[str]:
        return self.api_key
    
    def get_config(self) -> Dict[str, Any]:
        return self.config


class GeminiStrategy(ProviderStrategy):
    """Strategy for Gemini/Google provider."""
    
    def __init__(self, api_key: Optional[str], config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
    
    def get_provider_name(self) -> str:
        return "gemini"
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def normalize_model(self, model: str) -> str:
        # Normalize Gemini model names
        model_lower = model.lower()
        if "gemini" in model_lower:
            return model
        # Add gemini prefix if missing
        return f"gemini-{model}"
    
    def get_api_key(self) -> Optional[str]:
        return self.api_key
    
    def get_config(self) -> Dict[str, Any]:
        return self.config


class OllamaStrategy(ProviderStrategy):
    """Strategy for Ollama (local) provider."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.base_url = self.config.get("base_url", "http://localhost:11434")
    
    def get_provider_name(self) -> str:
        return "ollama"
    
    def is_configured(self) -> bool:
        # Ollama doesn't need API key, just needs to be available
        return True
    
    def normalize_model(self, model: str) -> str:
        # Ollama models are already normalized
        return model
    
    def get_api_key(self) -> Optional[str]:
        return None  # Ollama doesn't use API keys
    
    def get_config(self) -> Dict[str, Any]:
        return self.config


class ProviderStrategyFactory:
    """
    Factory for creating provider strategies.
    """
    
    @staticmethod
    def create_strategy(
        provider: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ProviderStrategy:
        """
        Create appropriate provider strategy.
        
        Args:
            provider: Provider name
            api_key: Optional API key
            config: Optional configuration
        
        Returns:
            ProviderStrategy instance
        """
        provider_lower = provider.lower()
        
        if provider_lower == "openai":
            return OpenAIStrategy(api_key, config)
        elif provider_lower == "claude":
            return ClaudeStrategy(api_key, config)
        elif provider_lower == "gemini":
            return GeminiStrategy(api_key, config)
        elif provider_lower == "ollama":
            return OllamaStrategy(config)
        else:
            logger.warning(f"Unknown provider {provider}, using OpenAI as default")
            return OpenAIStrategy(api_key, config)

