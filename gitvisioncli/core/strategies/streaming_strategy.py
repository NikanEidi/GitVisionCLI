"""
Streaming Strategy

Strategy pattern for different streaming behaviors in ChatEngine.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class StreamingStrategy(ABC):
    """
    Abstract base class for streaming strategies.
    
    Different strategies handle:
    - Token-by-token streaming
    - Tool call handling
    - Error recovery
    - Provider-specific behavior
    """
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from AI provider.
        
        Args:
            messages: Conversation messages
            tools: Optional tools/function definitions
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Text chunks from the AI response
        """
        pass
    
    @abstractmethod
    async def stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response with tool call support.
        
        Args:
            messages: Conversation messages
            tools: Tool/function definitions
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Dict with 'type' ('text' or 'tool_call') and 'data'
        """
        pass
    
    def can_handle_tools(self) -> bool:
        """
        Check if this strategy supports tool calls.
        
        Returns:
            True if tool calls are supported
        """
        return False


class DefaultStreamingStrategy(StreamingStrategy):
    """
    Default streaming strategy using AIClient.
    """
    
    def __init__(self, ai_client):
        """
        Initialize default streaming strategy.
        
        Args:
            ai_client: AIClient instance
        """
        self.ai_client = ai_client
    
    async def stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response using AIClient."""
        async for chunk in self.ai_client.stream(messages, tools=tools, **kwargs):
            yield chunk
    
    async def stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream with tool call support."""
        async for chunk in self.ai_client.stream_with_tools(messages, tools, **kwargs):
            yield chunk
    
    def can_handle_tools(self) -> bool:
        """Default strategy supports tools if AIClient does."""
        return hasattr(self.ai_client, 'stream_with_tools')


class StreamingStrategyFactory:
    """
    Factory for creating streaming strategies.
    """
    
    @staticmethod
    def create_strategy(
        provider: str,
        ai_client,
        **kwargs
    ) -> StreamingStrategy:
        """
        Create appropriate streaming strategy for provider.
        
        Args:
            provider: Provider name (openai, claude, gemini, ollama)
            ai_client: AIClient instance
            **kwargs: Additional configuration
        
        Returns:
            StreamingStrategy instance
        """
        provider_lower = provider.lower()
        
        if provider_lower in ("openai", "claude", "gemini", "ollama"):
            return DefaultStreamingStrategy(ai_client)
        
        # Default fallback
        logger.warning(f"Unknown provider {provider}, using default strategy")
        return DefaultStreamingStrategy(ai_client)

