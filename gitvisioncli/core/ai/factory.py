"""
AI Provider Factory

Factory pattern for creating AI provider instances.
Supports dynamic provider registration and creation.
"""

import logging
from typing import Dict, Type, Optional
import shutil

from gitvisioncli.core.ai.base import (
    BaseAIProvider,
    AIProviderConfig,
    ProviderType,
)
from gitvisioncli.core.ai.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class AIProviderFactory:
    """
    Factory for creating AI provider instances.
    
    Supports:
    - Dynamic provider registration
    - Automatic provider detection
    - Configuration-based provider creation
    """
    
    _providers: Dict[ProviderType, Type[BaseAIProvider]] = {
        ProviderType.OPENAI: OpenAIProvider,
    }
    
    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        provider_class: Type[BaseAIProvider]
    ) -> None:
        """
        Register a new provider type.
        
        Args:
            provider_type: Provider type enum
            provider_class: Provider class implementing BaseAIProvider
        """
        cls._providers[provider_type] = provider_class
        logger.info(f"Registered provider: {provider_type.value}")
    
    @classmethod
    def create(
        cls,
        provider_type: ProviderType,
        config: AIProviderConfig
    ) -> BaseAIProvider:
        """
        Create a provider instance.
        
        Args:
            provider_type: Provider type to create
            config: Provider configuration
        
        Returns:
            Provider instance
        
        Raises:
            ValueError: If provider type is not registered
        """
        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Provider type {provider_type.value} not registered")
        
        return provider_class(config)
    
    @classmethod
    def create_from_config(
        cls,
        providers_config: Dict[str, Any],
        active_provider: Optional[str] = None
    ) -> Optional[BaseAIProvider]:
        """
        Create provider from configuration dictionary.
        
        Args:
            providers_config: Dictionary with provider configurations
            active_provider: Preferred provider name
        
        Returns:
            Provider instance or None if no valid config found
        """
        # Determine which provider to use
        if active_provider:
            provider_name = active_provider.lower()
        else:
            # Auto-detect based on available configs
            if providers_config.get("openai", {}).get("api_key"):
                provider_name = "openai"
            elif providers_config.get("gemini", {}).get("api_key"):
                provider_name = "gemini"
            elif providers_config.get("claude", {}).get("api_key"):
                provider_name = "claude"
            elif shutil.which("ollama") or providers_config.get("ollama", {}).get("base_url"):
                provider_name = "ollama"
            else:
                return None
        
        # Create config based on provider
        if provider_name == "openai":
            openai_config = providers_config.get("openai", {})
            config = AIProviderConfig(
                provider_type=ProviderType.OPENAI,
                api_key=openai_config.get("api_key"),
                default_model=openai_config.get("model", "gpt-4o-mini"),
                temperature=openai_config.get("temperature", 0.7),
                max_tokens=openai_config.get("max_tokens", 4096),
            )
            return cls.create(ProviderType.OPENAI, config)
        
        # TODO: Add other providers (Gemini, Claude, Ollama)
        logger.warning(f"Provider {provider_name} not yet implemented in factory")
        return None
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get list of available provider types.
        
        Returns:
            List of provider type names
        """
        return [pt.value for pt in cls._providers.keys()]

