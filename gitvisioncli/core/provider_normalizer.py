"""
Provider normalization layer for GitVision.

This module enforces a stable, provider-independent format for:
  - JSON tool-call payloads
  - Code fences
  - Plan and error message structure

ChatEngine should route assistant text and tool metadata through this
layer so that behavior is deterministic across OpenAI, Claude, Gemini,
Llama, and local models.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedToolCall:
    """Canonical representation of a single tool call."""

    name: str
    arguments: Dict[str, Any]


class ProviderNormalizer:
    """
    Stateless normalizer to clean provider-specific quirks in tool
    calls and fenced JSON so that downstream logic sees a single,
    predictable schema.
    """

    def normalize_fences(self, text: str) -> str:
        """
        Ensure ```json fences are well-formed and that there are no
        stray backticks that would break the CLI parser. This does
        NOT attempt to parse or reflow arbitrary markdown; it only
        cleans trivial provider quirks (extra language labels, etc.).
        """
        if not text:
            return ""

        # Collapse ```jsonc or ```JSON into ```json
        text = re.sub(r"```jsonc", "```json", text, flags=re.IGNORECASE)
        text = re.sub(r"```JSON", "```json", text)

        return text

    def extract_json_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract JSON payloads from ```json / ```tool / ```action fenced blocks.

        Supports:
        - Single JSON objects: ```json {"action": {...}} ```
        - Arrays of objects:  ```json [ {"action": ...}, {...} ] ```

        Returns a flat list of dicts. Invalid JSON blocks are ignored to
        avoid accidental execution of malformed payloads.
        """
        if not text:
            return []

        blocks: List[Dict[str, Any]] = []

        pattern = re.compile(
            r"```(?:json|tool|action)?\s*(.*?)\s*```",
            re.DOTALL | re.IGNORECASE,
        )

        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if isinstance(data, dict):
                blocks.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        blocks.append(item)

        return blocks

    def normalize_tool_calls_from_openai_delta(
        self, raw_calls: List[Dict[str, Any]]
    ) -> List[NormalizedToolCall]:
        """
        Convert the streaming OpenAI tool_call fragments into a stable,
        provider-agnostic representation.
        """
        normalized: List[NormalizedToolCall] = []
        for tc in raw_calls:
            name = (tc.get("function") or {}).get("name") or ""
            args_raw = (tc.get("function") or {}).get("arguments") or "{}"
            try:
                args = json.loads(args_raw)
            except json.JSONDecodeError:
                # Ignore invalid tool calls; downstream logic must not execute them.
                continue
            normalized.append(NormalizedToolCall(name=name, arguments=args))
        return normalized

    def normalize_error_message(self, text: str) -> str:
        """
        Provide a concise, provider-neutral error message string.
        Strips provider-specific prefixes and verbose stack traces.
        """
        if not text:
            return ""

        # Strip typical "Error:" prefixes and line breaks.
        cleaned = re.sub(r"^\s*(Error|ERROR|Exception)[:\-]\s*", "", text).strip()
        cleaned = cleaned.replace("\r", " ").replace("\n", " ")
        return cleaned

    def extract_code_from_assistant_text(self, text: str) -> Optional[str]:
        """
        Extract code content from assistant text, looking for fenced code blocks.
        
        Returns the first substantial code block found, or None if no code is present.
        This is used to recover content when a model splits its response between
        natural text (containing code) and a tool call (with missing content).
        """
        if not text:
            return None

        # Look for fenced code blocks (```language ... ```)
        pattern = re.compile(
            r"```(?:[a-zA-Z0-9]+)?\s*(.*?)\s*```",
            re.DOTALL | re.IGNORECASE,
        )

        for m in pattern.finditer(text):
            code = m.group(1).strip()
            # Only return substantial code (more than just whitespace/comments)
            if code and len(code) > 5:
                return code

        return None

    def combine_text_and_tool_call(
        self, assistant_text: str, tool_call: NormalizedToolCall
    ) -> NormalizedToolCall:
        """
        Combine assistant text with a tool call to fill in missing content.
        
        When a model emits code in its text response but calls a tool with
        missing 'content' parameter, this method extracts the code and
        merges it into the tool call arguments.
        
        Returns an updated NormalizedToolCall with complete arguments.
        """
        if not assistant_text or not tool_call:
            return tool_call

        # Only process execute_action tool calls
        if tool_call.name != "execute_action":
            return tool_call

        args = tool_call.arguments or {}
        action = args.get("action", {})
        if not isinstance(action, dict):
            return tool_call

        action_type = (action.get("type") or "").lower()
        params = action.get("params") or {}

        # Check if this is an edit action with missing content
        needs_content = action_type in {
            "editfile",
            "createfile",
            "rewriteentirefile",
        }

        if not needs_content:
            return tool_call

        # If content is already present and non-empty, don't override
        if params.get("content"):
            return tool_call

        # Extract code from assistant text
        extracted_code = self.extract_code_from_assistant_text(assistant_text)
        if not extracted_code:
            return tool_call

        # Merge the extracted code into the tool call
        updated_params = dict(params)
        updated_params["content"] = extracted_code

        updated_action = dict(action)
        updated_action["params"] = updated_params

        updated_args = dict(args)
        updated_args["action"] = updated_action

        return NormalizedToolCall(name=tool_call.name, arguments=updated_args)

    def normalize_edit_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize edit actions to prevent incomplete content fields.
        
        This ensures that EditFile, CreateFile, and similar actions always have
        their required content/text parameters populated. If content is missing
        or None, this method will flag it for downstream handling.
        
        Returns a normalized action dict with a '_incomplete' flag if content is missing.
        """
        if not isinstance(action, dict):
            return action

        normalized = dict(action)
        action_type = (normalized.get("type") or "").strip().lower()
        params = normalized.get("params") or {}

        if not isinstance(params, dict):
            return normalized

        # Actions that require 'content' field
        content_required = {
            "editfile",
            "createfile",
            "rewriteentirefile",
        }

        # Actions that require 'text' field
        text_required = {
            "appendtext",
            "prependtext",
            "insertbeforeline",
            "insertafterline",
            "insertattop",
            "insertatbottom",
            "insertblockatline",
            "replaceblock",
        }

        # Check for missing content
        if action_type in content_required:
            content = params.get("content")
            if content is None or (isinstance(content, str) and not content.strip()):
                normalized["_incomplete"] = True
                normalized["_missing_field"] = "content"

        elif action_type in text_required:
            text = params.get("text")
            if text is None or (isinstance(text, str) and not text.strip()):
                normalized["_incomplete"] = True
                normalized["_missing_field"] = "text"

        return normalized
