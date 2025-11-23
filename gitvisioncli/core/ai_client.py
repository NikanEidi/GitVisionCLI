# gitvisioncli/core/ai_client.py
"""
GitVisionCLI AI Client
Wrapper for OpenAI-compatible API calls.
"""

# --- STABILIZATION FIX ---
# Import the AsyncOpenAI client
from openai import AsyncOpenAI
# --- END FIX ---

import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AIClient:
    """
    Central OpenAI client wrapper for GitVision.
    All direct SDK calls live here.
    """

    def __init__(self, api_key: str, default_model: str = "gpt-4o-mini"): # Updated default
        if not api_key:
            raise ValueError("OpenAI API key is required for AIClient")
        
        # --- STABILIZATION FIX ---
        # Use the AsyncOpenAI client
        self.client = AsyncOpenAI(api_key=api_key) 
        # --- END FIX ---
        self.default_model = default_model
        logger.info(f"AIClient initialized for model: {default_model}")

    # ------------------------------------------------------------------
    # Simple convenience methods
    # ------------------------------------------------------------------
    async def stream_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Convenience wrapper for simple streaming."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        async for chunk in self.stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            # Yield only the content string
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

    async def ask_full(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Convenience wrapper for a single, non-streaming completion."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        resp = await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # Core generic methods
    # ------------------------------------------------------------------
    async def stream(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """Core streaming method without tools."""
        # --- STABILIZATION FIX ---
        # `create` is now a coroutine and must be awaited
        stream = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        # --- END FIX ---
        async for chunk in stream:
            yield chunk
            await asyncio.sleep(0) # Yield control back to the event loop

    async def stream_with_tools(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """Core streaming method *with* tools enabled."""
        # --- STABILIZATION FIX ---
        # `create` is now a coroutine and must be awaited
        stream = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        # --- END FIX ---
        async for chunk in stream:
            yield chunk
            await asyncio.sleep(0)

    async def complete(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        """Core non-streaming method without tools."""
        # This method is async and must be awaited
        return await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def complete_with_tools(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ):
        """Core non-streaming method *with* tools enabled."""
        # This method is async and must be awaited
        return await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
