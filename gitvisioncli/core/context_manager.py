# gitvisioncli/core/context_manager.py
"""
Manages the conversation state, including history, system prompts,
and dynamic workspace context.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Internal message model
# ----------------------------------------------------------------------

@dataclass
class Message:
    """
    Internal representation of a chat message.
    Mirrors the OpenAI API message format.
    """
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

# ----------------------------------------------------------------------
# Context Manager
# ----------------------------------------------------------------------

@dataclass
class ContextManager:
    """
    Tracks the full conversation state, including history,
    system prompt, and dynamic workspace context.
    """
    messages: List[Message] = field(default_factory=list)
    system_prompt: Optional[str] = None
    workspace_summary: Optional[str] = None  # <-- STABILIZED: Explicit field
    summary_history: Optional[str] = None

    # Added for AI Editor synchronization
    active_file_path: Optional[str] = None
    active_file_content: Optional[str] = None

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        Append a new message (user, assistant) to the conversation.
        """
        self.messages.append(Message(role=role, content=content, **kwargs))
        logger.debug(f"Added message: role={role}, content_len={len(content)}")

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        """
        Append a new 'tool' message to the conversation.
        This is the result of a tool call.
        """
        self.add_message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id
        )
        logger.debug(f"Added tool result for {tool_call_id}")

    def update_workspace_context(self, summary: str) -> None:
        """
        Updates the persistent workspace context (e.g., file tree, open file).
        This is injected into the system prompt.
        """
        self.workspace_summary = summary
    
    def set_active_file(self, path: Optional[str], content: Optional[str]) -> None:
        """
        Sets the currently active file path and its content.
        Used to synchronize the AI's context with the editor panel.
        """
        self.active_file_path = path
        self.active_file_content = content

    def get_openai_messages(self) -> List[Dict[str, Any]]:
        """
        Convert internal Message objects into OpenAI-style dicts
        for sending to the API.
        """
        msgs: List[Dict[str, Any]] = []

        # --- 1. Build the System Prompt ---
        # Combine the static system prompt with the dynamic workspace context,
        # active file view, and any summarized history.
        system_content = self.system_prompt or ""

        if self.workspace_summary:
            system_content += (
                "\n\n--- DYNAMIC WORKSPACE CONTEXT ---\n"
                f"{self.workspace_summary}"
                "\n--- END WORKSPACE CONTEXT ---"
            )

        if self.active_file_path and self.active_file_content:
            system_content += (
                f"\n\n# ACTIVE FILE\n"
                f"path: {self.active_file_path}\n"
                f"content:\n{self.active_file_content}\n"
            )

        if self.summary_history:
            system_content += (
                "\n\n--- SUMMARY OF PREVIOUS CONVERSATION ---\n"
                f"{self.summary_history}\n"
                "--- END SUMMARY ---"
            )

        if system_content:
            msgs.append({"role": "system", "content": system_content})

        # --- 2. Add all other messages (user, assistant, tool) ---
        for msg in self.messages:
            m: Dict[str, Any] = {"role": msg.role, "content": msg.content}
            # Add optional fields only if they exist
            if msg.name:
                m["name"] = msg.name
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            msgs.append(m)

        return msgs

    def estimate_token_usage(self) -> int:
        """
        Lightweight, provider-neutral token usage estimator.

        Uses a simple heuristic based on character count:
            approx_tokens ≈ total_chars / 3.5

        This intentionally ignores provider-specific tokenization
        details and is only used for approximate context budgeting.
        """
        messages = self.get_openai_messages()
        if not messages:
            return 0

        total_chars = 0
        for m in messages:
            try:
                content = m.get("content") or ""
            except AttributeError:
                # Defensive: tolerate non-dict entries, though we do not expect them.
                content = ""
            total_chars += len(str(content))

        # Integer rounding is fine for an approximate budget.
        return int(total_chars / 3.5) if total_chars > 0 else 0

    def clear(self) -> None:
        """
        Reset only the conversation history and any accumulated summary.
        Keeps the system prompt and workspace summary intact.
        """
        self.clear_messages()
        self.summary_history = None

    def clear_messages(self) -> None:
        """
        Clear all non-system messages.
        System prompt, workspace summary, and active file context are preserved.
        """
        self.messages.clear()
        logger.info("Conversation message history cleared (clear_messages).")

    def prune_messages(self, n: int) -> None:
        """
        Keep only the last N user turns (user + assistant + tool messages).
        If n <= 0, behaves like clear_messages().
        """
        if n <= 0:
            self.clear_messages()
            return

        if not self.messages:
            return

        user_indices = [i for i, m in enumerate(self.messages) if m.role == "user"]
        if len(user_indices) <= n:
            return

        # Index of the first user message we want to keep
        keep_from = user_indices[-n]
        self.messages = self.messages[keep_from:]
        logger.info(f"Pruned conversation history to last {n} user turns.")

    def get_message_count(self) -> int:
        """
        Check conversation message count
        """
        return len(self.messages)
