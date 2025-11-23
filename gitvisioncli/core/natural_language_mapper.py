"""
Natural language → structured edit mapping for GitVision.

This module interprets high-level user instructions about code and files
and converts them into deterministic execute_action-compatible edit
intents. It is provider-agnostic and operates purely on text plus a
lightweight file/line context snapshot provided by the caller.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EditIntent:
    """Structured edit intent compatible with the execute_action schema."""

    type: str
    params: Dict[str, Any]


@dataclass
class MappingResult:
    """
    Result of natural-language mapping.

    - intents: zero or more concrete EditIntent objects.
    - clarification: if not None, the mapper could not safely resolve
      the instruction and asks for a single short clarification.
    - error: if not None, the mapper failed hard and no edit should run.
    """

    intents: List[EditIntent]
    clarification: Optional[str] = None
    error: Optional[str] = None


@dataclass
class FileContext:
    """
    Minimal view of the active file for mapping decisions.

    - path: absolute or workspace-relative path
    - content: raw text
    """

    path: str
    content: str


@dataclass
class LiveEditIntent:
    """
    Line-based edit intent for AI Live Editor Mode.
    
    Unlike EditIntent which includes file paths and is meant for disk operations,
    LiveEditIntent is purely line-based and operates on in-memory buffers.
    
    Supported types:
    - "insert_after": Insert new_text after start_line
    - "replace_range": Replace lines [start_line, end_line] with new_text
    - "delete_range": Delete lines [start_line, end_line]
    - "append": Append new_text to end of file
    """
    
    type: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    new_text: str = ""


class NaturalLanguageEditMapper:
    """
    Deterministic mapper from free-text edit descriptions to structured
    edit intents. All ambiguity handling happens here; destructive edits
    are only emitted when the target is clear.
    """

    def __init__(self) -> None:
        # Precompiled regexes for performance and determinism.
        self._line_after_re = re.compile(
            r"\b(after|below)\s+line\s+(?P<line>\d+)\b", re.IGNORECASE
        )
        self._line_before_re = re.compile(
            r"\b(before|above)\s+line\s+(?P<line>\d+)\b", re.IGNORECASE
        )
        self._at_line_re = re.compile(
            r"\b(at|on)\s+line\s+(?P<line>\d+)\b", re.IGNORECASE
        )
        self._range_re = re.compile(
            r"\blines?\s+(?P<start>\d+)\s*-\s*(?P<end>\d+)\b", re.IGNORECASE
        )
        self._json_key_re = re.compile(
            r"\b(json|yaml)\s+key\s+(?P<old>[A-Za-z0-9_.-]+)\s+.*\b(with|to)\s+(?P<new>[A-Za-z0-9_.-]+)\b",
            re.IGNORECASE,
        )
        self._delete_function_re = re.compile(
            r"\bdelete\s+the\s+function\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
            re.IGNORECASE,
        )
        # CRITICAL: Patterns for "remove/delete line X" commands
        self._delete_line_re = re.compile(
            r"\b(remove|delete)\s+line\s*(?P<line>\d+)\b",
            re.IGNORECASE,
        )
        self._delete_lines_re = re.compile(
            r"\b(remove|delete)\s+lines?\s+(?P<start>\d+)\s*-\s*(?P<end>\d+)\b",
            re.IGNORECASE,
        )
        # CRITICAL: Patterns for "add/insert line X" commands  
        self._add_line_re = re.compile(
            r"\b(add|insert|write)\s+line\s*(?P<line>\d+)\b",
            re.IGNORECASE,
        )
        self._replace_line_re = re.compile(
            r"\b(replace|update|change|edit)\s+line\s*(?P<line>\d+)\b",
            re.IGNORECASE,
        )
        self._bottom_re = re.compile(
            r"\b(at|to|at\s+the)\s+bottom\b", re.IGNORECASE
        )
        self._top_re = re.compile(r"\b(at|to|at\s+the)\s+top\b", re.IGNORECASE)
        self._between_markers_re = re.compile(
            r"\bbetween\s+markers?\s+(?P<start>.+?)\s+and\s+(?P<end>.+)$",
            re.IGNORECASE,
        )
        self._into_function_re = re.compile(
            r"\b(?:inside|in|into)\s+the\s+function\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
            re.IGNORECASE,
        )
        self._into_class_re = re.compile(
            r"\b(?:inside|in|into)\s+the\s+class\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b",
            re.IGNORECASE,
        )
        self._decorator_re = re.compile(
            r"\badd\s+(?:a\s+)?decorator\s+(?P<decorator>@?[A-Za-z_][A-Za-z0-9_\.]*)\s+to\s+(?:the\s+)?(function|class)\s+(?P<target>[A-Za-z_][A-Za-z0-9_]*)",
            re.IGNORECASE,
        )
        self._auto_import_re = re.compile(
            r"\bimport\s+(?P<name>[A-Za-z_][A-Za-z0-9_\.]*)\s+(?:if\s+missing|if\s+not\s+present)?",
            re.IGNORECASE,
        )
        
        # Vague instruction patterns for smart defaults
        self._vague_add_re = re.compile(
            r"\b(add|write|put|insert|place)\s+(this|the\s+following|this\s+code)\b",
            re.IGNORECASE,
        )
        self._vague_update_re = re.compile(
            r"\b(update|change|modify|edit)\s+(this|the)\s+(function|class|method|file)\b",
            re.IGNORECASE,
        )
        self._here_re = re.compile(
            r"\b(here|in\s+this\s+file|right\s+here|in\s+the\s+file)\b",
            re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def map_instruction(
        self,
        instruction: str,
        *,
        active_file: Optional[FileContext] = None,
        attached_block: Optional[str] = None,
    ) -> MappingResult:
        """
        Map a single natural-language instruction and optional attached
        code block into one or more EditIntent objects.

        active_file.content is required for line/marker-based edits.
        attached_block is the literal code/text the user wants to insert
        or replace with (e.g., from a fenced block following the command).
        """
        text = (instruction or "").strip()
        if not text:
            return MappingResult(intents=[], error="Empty instruction.")

        # 1) JSON/YAML key modifications
        jk = self._json_key_re.search(text)
        if jk and active_file:
            return self._handle_json_key_edit(text, active_file, jk)

        rng = self._range_re.search(text)
        if rng and active_file:
            return self._handle_line_range_edit(text, active_file, rng, attached_block)

        # 3) Single-line based insert/replace/delete
        text = instruction.strip()

        # 1) DELETE LINE COMMANDS - HIGHEST PRIORITY!
        if active_file:
            # Single line deletion: "remove line 1" or "delete line 5"
            m_del = self._delete_line_re.search(text)
            if m_del:
                line_num = int(m_del.group("line"))
                return MappingResult(
                    intents=[
                        EditIntent(
                            type="DeleteLineRange",
                            params={
                                "path": active_file.path,
                                "start_line": line_num,
                                "end_line": line_num,
                            },
                        )
                    ]
                )
            
            # Multiple line deletion: "remove lines 1-3" or "delete lines 5-10"
            m_dels = self._delete_lines_re.search(text)
            if m_dels:
                start = int(m_dels.group("start"))
                end = int(m_dels.group("end"))
                return MappingResult(
                    intents=[
                        EditIntent(
                            type="DeleteLineRange",
                            params={
                                "path": active_file.path,
                                "start_line": start,
                                "end_line": end,
                            },
                        )
                    ]
                )

        # 2) ADD/INSERT/REPLACE LINE COMMANDS - HIGH PRIORITY!
        if active_file:
            # Add line: "add line 1" or "insert line 5"
            m_add = self._add_line_re.search(text)
            if m_add:
                line_num = int(m_add.group("line"))
                # Extract the content after the command
                # "add line 1 with concept of truth" -> extract "with concept of truth"
                content_match = re.search(r"line\s*\d+\s+(with\s+)?(.+)$", text, re.IGNORECASE)
                if content_match:
                    content = content_match.group(2).strip()
                    return MappingResult(
                        intents=[
                            EditIntent(
                                type="InsertBeforeLine",
                                params={
                                    "path": active_file.path,
                                    "line_number": line_num,
                                    "text": content,
                                },
                            )
                        ]
                    )
            
            # Replace line: "replace line 1" or "update line 5"
            m_replace = self._replace_line_re.search(text)
            if m_replace:
                line_num = int(m_replace.group("line"))
                # Extract the content after the command
                content_match = re.search(r"line\s*\d+\s+(with\s+)?(.+)$", text, re.IGNORECASE)
                if content_match:
                    content = content_match.group(2).strip()
                    return MappingResult(
                        intents=[
                            EditIntent(
                                type="ReplaceLine",
                                params={
                                    "path": active_file.path,
                                    "line_number": line_num,
                                    "text": content,
                                },
                            )
                        ]
                    )

        # 3) Line-specific anchors (after, before, at)
        m_after = self._line_after_re.search(text)
        if m_after and active_file:
            return self._handle_after_line(
                text, active_file, int(m_after.group("line")), attached_block
            )

        m_before = self._line_before_re.search(text)
        if m_before and active_file:
            return self._handle_before_line(
                text, active_file, int(m_before.group("line")), attached_block
            )

        m_at = self._at_line_re.search(text)
        if m_at and active_file:
            return self._handle_at_line(
                text, active_file, int(m_at.group("line")), attached_block
            )

        # 3) Range operations
        m_range = self._range_re.search(text)
        if m_range and active_file:
            return self._handle_range(
                text,
                active_file,
                int(m_range.group("start")),
                int(m_range.group("end")),
                attached_block,
            )

        # 4) JSON/YAML key updates
        if active_file:
            m_json = self._json_key_re.search(text)
            if m_json:
                return self._handle_json_yaml_key_update(
                    text,
                    active_file,
                    m_json.group("old"),
                    m_json.group("new"),
                )

        # 5) Insert at top/bottom with explicit instructionp_re.search(text):
                return MappingResult(
                    intents=[
                        EditIntent(
                            type="InsertBlock",
                            params={
                                "path": active_file.path,
                                "line_number": None,
                                "text": attached_block,
                            },
                        )
                    ]
                )
            if self._top_re.search(text):
                return MappingResult(
                    intents=[
                        EditIntent(
                            type="InsertBlock",
                            params={
                                "path": active_file.path,
                                "line_number": 1,
                                "text": attached_block,
                            },
                        )
                    ]
                )

        # 5) Delete function
        if active_file:
            df = self._delete_function_re.search(text)
            if df:
                return self._handle_delete_function(active_file, df.group("name"))

        # 6) Remove between markers
        if active_file:
            bm = self._between_markers_re.search(text)
            if bm:
                return self._handle_remove_between_markers(
                    active_file, bm.group("start").strip(), bm.group("end").strip()
                )

        # 7) Semantic inserts into functions/classes, decorators, and imports
        if active_file:
            into_func = self._into_function_re.search(text)
            if into_func:
                return self._handle_insert_into_function(
                    text,
                    active_file,
                    into_func.group("name"),
                    attached_block,
                )

            into_cls = self._into_class_re.search(text)
            if into_cls:
                return self._handle_insert_into_class(
                    text,
                    active_file,
                    into_cls.group("name"),
                    attached_block,
                )

            deco = self._decorator_re.search(text)
            if deco:
                return self._handle_add_decorator(
                    active_file,
                    deco.group("target"),
                    deco.group("decorator"),
                )

            auto_imp = self._auto_import_re.search(text)
            if auto_imp:
                return self._handle_auto_import(active_file, auto_imp.group("name"))

        # 8) Vague "add/write/put" instructions with attached block
        if attached_block and active_file:
            if self._vague_add_re.search(text) or self._here_re.search(text):
                return self._handle_generic_add(text, active_file, attached_block)

        # 9) Vague "update/change" instructions
        if active_file and self._vague_update_re.search(text):
            return self._handle_generic_update(text, active_file, attached_block)

        # 10) Generic "insert this block" with no precise anchor
        if attached_block and not active_file:
            return MappingResult(
                intents=[],
                clarification="Which file and position should this block be inserted into?",
            )

        # If we reach here, we could not confidently map the instruction.
        return MappingResult(
            intents=[],
            clarification="Please specify the exact file and line numbers for this edit.",
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _handle_after_line(
        self,
        instruction: str,
        file_ctx: FileContext,
        line_number: int,
        block: Optional[str],
    ) -> MappingResult:
        if line_number < 1:
            return MappingResult(
                intents=[], error="Line numbers must be 1-based and positive."
            )
        if block is None:
            return MappingResult(
                intents=[],
                clarification="You said 'after line {0}'. What exact text should be inserted?".format(
                    line_number
                ),
            )
        return MappingResult(
            intents=[
                EditIntent(
                    type="InsertAfterLine",
                    params={
                        "path": file_ctx.path,
                        "line_number": line_number,
                        "text": block,
                    },
                )
            ]
        )

    def _handle_before_line(
        self,
        instruction: str,
        file_ctx: FileContext,
        line_number: int,
        block: Optional[str],
    ) -> MappingResult:
        if line_number < 1:
            return MappingResult(
                intents=[], error="Line numbers must be 1-based and positive."
            )
        if block is None:
            return MappingResult(
                intents=[],
                clarification="You said 'before line {0}'. What exact text should be inserted?".format(
                    line_number
                ),
            )
        return MappingResult(
            intents=[
                EditIntent(
                    type="InsertBeforeLine",
                    params={
                        "path": file_ctx.path,
                        "line_number": line_number,
                        "text": block,
                    },
                )
            ]
        )

    def _handle_at_line(
        self,
        instruction: str,
        file_ctx: FileContext,
        line_number: int,
        block: Optional[str],
    ) -> MappingResult:
        if line_number < 1:
            return MappingResult(
                intents=[], error="Line numbers must be 1-based and positive."
            )
        if block is None:
            return MappingResult(
                intents=[],
                clarification="You said 'at line {0}'. What text should replace that line?".format(
                    line_number
                ),
            )
        return MappingResult(
            intents=[
                EditIntent(
                    type="ReplaceBlock",
                    params={
                        "path": file_ctx.path,
                        "line_number": line_number,
                        "start_line": line_number,
                        "end_line": line_number,
                        "text": block,
                    },
                )
            ]
        )

    def _handle_line_range_edit(
        self,
        instruction: str,
        file_ctx: FileContext,
        match: re.Match,
        block: Optional[str],
    ) -> MappingResult:
        start = int(match.group("start"))
        end = int(match.group("end"))
        if start < 1 or end < start:
            return MappingResult(
                intents=[],
                error="Line ranges must be 1-based and end_line >= start_line.",
            )

        lower = instruction.lower()
        if "delete" in lower or "remove" in lower:
            return MappingResult(
                intents=[
                    EditIntent(
                        type="DeleteLineRange",
                        params={
                            "path": file_ctx.path,
                            "start_line": start,
                            "end_line": end,
                        },
                    )
                ]
            )

        if block is not None:
            return MappingResult(
                intents=[
                    EditIntent(
                        type="ReplaceBlock",
                        params={
                            "path": file_ctx.path,
                            "start_line": start,
                            "end_line": end,
                            "text": block,
                        },
                    )
                ]
            )

        return MappingResult(
            intents=[],
            clarification="You mentioned lines {0}-{1}. Do you want to delete them or replace them with something?".format(
                start, end
            ),
        )

    def _handle_json_key_edit(
        self,
        instruction: str,
        file_ctx: FileContext,
        match: re.Match,
    ) -> MappingResult:
        is_yaml = "yaml" in match.group(1).lower()
        old = match.group("old")
        new = match.group("new")

        if "replace" in instruction.lower():
            # Interpret as a rename: create new key with value from old, then delete old.
            # We cannot read JSON here, so we emit a high-level UpdateJSONKey on the new key.
            op_type = "UpdateYAMLKey" if is_yaml else "UpdateJSONKey"
            return MappingResult(
                intents=[
                    EditIntent(
                        type=op_type,
                        params={
                            "path": file_ctx.path,
                            "key_path": new,
                            "value": None,
                        },
                    )
                ]
            )

        return MappingResult(
            intents=[],
            clarification="For key '{0}' → '{1}', should I update its value, rename the key, or both?".format(
                old, new
            ),
        )

    def _handle_delete_function(
        self, file_ctx: FileContext, func_name: str
    ) -> MappingResult:
        """
        Conservative Python/JS-style function deletion based on simple
        line scanning. If the function boundaries cannot be located
        unambiguously, we will ask for a clarification instead of
        emitting a destructive edit.
        """
        lines = file_ctx.content.splitlines()
        start_idx = None
        end_idx = None

        pattern = re.compile(rf"^\s*def\s+{re.escape(func_name)}\b|^\s*function\s+{re.escape(func_name)}\b")
        for i, line in enumerate(lines):
            if pattern.search(line):
                start_idx = i
                break

        if start_idx is None:
            return MappingResult(
                intents=[],
                clarification=(
                    f"Could not find a function '{func_name}'. "
                    "Please specify the exact line range to delete."
                ),
            )

        # Naive boundary: delete until next top-level def/function or EOF.
        end_idx = len(lines) - 1
        for j in range(start_idx + 1, len(lines)):
            if re.match(r"^\s*def\s+\w+\b|^\s*function\s+\w+\b", lines[j]):
                end_idx = j - 1
                break

        start_line = start_idx + 1
        end_line = end_idx + 1

        return MappingResult(
            intents=[
                EditIntent(
                    type="DeleteLineRange",
                    params={
                        "path": file_ctx.path,
                        "start_line": start_line,
                        "end_line": end_line,
                    },
                )
            ]
        )

    def _handle_remove_between_markers(
        self,
        file_ctx: FileContext,
        start_marker: str,
        end_marker: str,
    ) -> MappingResult:
        """
        Remove everything between two marker strings, inclusive of the
        markers themselves. If either marker is missing or ambiguous,
        ask for clarification.
        """
        content = file_ctx.content
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            return MappingResult(
                intents=[],
                clarification=(
                    "I could not safely locate both markers. "
                    "Please provide explicit line numbers for the region to remove."
                ),
            )

        # Map byte indices back to line numbers by counting newlines.
        prefix = content[:start_idx]
        middle = content[start_idx : end_idx + len(end_marker)]
        start_line = prefix.count("\n") + 1
        end_line = start_line + middle.count("\n")

        return MappingResult(
            intents=[
                EditIntent(
                    type="DeleteLineRange",
                    params={
                        "path": file_ctx.path,
                        "start_line": start_line,
                        "end_line": end_line,
                    },
                )
            ]
        )

    def _handle_insert_into_function(
        self,
        instruction: str,
        file_ctx: FileContext,
        func_name: str,
        block: Optional[str],
    ) -> MappingResult:
        if not block:
            return MappingResult(
                intents=[],
                clarification=(
                    f"You asked to insert into function '{func_name}'. "
                    "Please provide the code block to insert."
                ),
            )

        position = "bottom"
        lower = instruction.lower()
        if "top of function" in lower or "at the top" in lower:
            position = "top"
        elif "bottom of function" in lower or "at the bottom" in lower:
            position = "bottom"

        return MappingResult(
            intents=[
                EditIntent(
                    type="InsertIntoFunction",
                    params={
                        "path": file_ctx.path,
                        "function_name": func_name,
                        "position": position,
                        "text": block,
                    },
                )
            ]
        )

    def _handle_insert_into_class(
        self,
        instruction: str,
        file_ctx: FileContext,
        class_name: str,
        block: Optional[str],
    ) -> MappingResult:
        if not block:
            return MappingResult(
                intents=[],
                clarification=(
                    f"You asked to insert into class '{class_name}'. "
                    "Please provide the code block to insert."
                ),
            )

        position = "bottom"
        lower = instruction.lower()
        if "top of class" in lower or "at the top" in lower:
            position = "top"
        elif "bottom of class" in lower or "at the bottom" in lower:
            position = "bottom"

        return MappingResult(
            intents=[
                EditIntent(
                    type="InsertIntoClass",
                    params={
                        "path": file_ctx.path,
                        "class_name": class_name,
                        "position": position,
                        "text": block,
                    },
                )
            ]
        )

    def _handle_add_decorator(
        self,
        file_ctx: FileContext,
        target_name: str,
        decorator: str,
    ) -> MappingResult:
        deco = decorator.strip()
        if not deco:
            return MappingResult(
                intents=[],
                clarification="Decorator name appears empty; please specify the decorator to add.",
            )
        return MappingResult(
            intents=[
                EditIntent(
                    type="AddDecorator",
                    params={
                        "path": file_ctx.path,
                        "target_name": target_name,
                        "decorator": deco,
                    },
                )
            ]
        )

    def _handle_auto_import(
        self,
        file_ctx: FileContext,
        name: str,
    ) -> MappingResult:
        symbol = name.strip()
        if not symbol:
            return MappingResult(
                intents=[],
                clarification="Import target is empty; please specify a symbol to import.",
            )

        # Safe default: use symbol as both symbol and import_path.
        return MappingResult(
            intents=[
                EditIntent(
                    type="AddImport",
                    params={
                        "path": file_ctx.path,
                        "symbol": symbol,
                        "import_path": symbol,
                    },
                )
            ]
        )

    def _handle_generic_add(
        self,
        instruction: str,
        file_ctx: FileContext,
        block: str,
    ) -> MappingResult:
        """
        Handle vague 'add this' / 'write X' / 'put this code' instructions.
        
        When the user says something like "add this to the file" or "write this here"
        with a code block but no specific location, we default to appending at the
        end of the file rather than asking for clarification.
        """
        if not block:
            return MappingResult(
                intents=[],
                clarification="What code should be added?",
            )

        # Default to appending at the bottom of the file
        return MappingResult(
            intents=[
                EditIntent(
                    type="AppendBlock",
                    params={
                        "path": file_ctx.path,
                        "text": block,
                    },
                )
            ]
        )

    def _handle_generic_update(
        self,
        instruction: str,
        file_ctx: FileContext,
        block: Optional[str],
    ) -> MappingResult:
        """
        Handle vague 'update this' / 'change the function' instructions.
        
        Without specific line numbers or function names, we ask for clarification
        rather than making destructive changes.
        """
        return MappingResult(
            intents=[],
            clarification=(
                "Please specify which part of the file to update "
                "(e.g., 'update lines 10-20' or 'update function foo')."
            ),
        )

    # ------------------------------------------------------------------
    # LIVE EDIT MAPPING (FOR AI LIVE EDITOR MODE)
    # ------------------------------------------------------------------

    def map_to_live_edits(
        self,
        instruction: str,
        file_content: str,
        attached_block: Optional[str] = None,
    ) -> List[LiveEditIntent]:
        """
        Map natural language instruction to live edit intents.
        
        This method reuses existing pattern matching from map_instruction() but
        returns line-based LiveEditIntent objects instead of file-based EditIntent.
        
        Used by AI Live Editor Mode for in-memory buffer manipulation.
        
        Args:
            instruction: Natural language edit instruction
            file_content: Current file content as string
            attached_block: Optional code block attached to instruction
        
        Returns:
            List of LiveEditIntent objects ready to apply to EditorPanel
        
        Examples:
            "delete lines 5-10" → [LiveEditIntent(type="delete_range", start_line=5, end_line=10)]
            "add this after line 20" → [LiveEditIntent(type="insert_after", start_line=20, new_text=block)]
            "replace lines 1-3" → [LiveEditIntent(type="replace_range", start_line=1, end_line=3, new_text=block)]
        """
        text = (instruction or "").strip()
        if not text:
            return []

        # Build FileContext for existing pattern matching
        file_ctx = FileContext(path="<live_edit>", content=file_content)

        # Use existing map_instruction to leverage all pattern matching
        result = self.map_instruction(text, active_file=file_ctx, attached_block=attached_block)

        # If mapping failed or needs clarification, return empty list
        if result.error or result.clarification or not result.intents:
            return []

        # Convert EditIntent objects to LiveEditIntent objects
        live_intents: List[LiveEditIntent] = []

        for intent in result.intents:
            intent_type = intent.type.lower()
            params = intent.params

            # Delete line range
            if intent_type == "deletelinerange":
                live_intents.append(
                    LiveEditIntent(
                        type="delete_range",
                        start_line=params.get("start_line"),
                        end_line=params.get("end_line"),
                    )
                )

            # Replace block (line range replacement)
            elif intent_type == "replaceblock":
                live_intents.append(
                    LiveEditIntent(
                        type="replace_range",
                        start_line=params.get("start_line"),
                        end_line=params.get("end_line"),
                        new_text=params.get("text", ""),
                    )
                )

            # Insert after line
            elif intent_type == "insertafterline":
                live_intents.append(
                    LiveEditIntent(
                        type="insert_after",
                        start_line=params.get("line_number"),
                        new_text=params.get("text", ""),
                    )
                )

            # Insert before line (convert to insert_after previous line)
            elif intent_type == "insertbeforeline":
                line_num = params.get("line_number", 1)
                live_intents.append(
                    LiveEditIntent(
                        type="insert_after",
                        start_line=max(0, line_num - 1),
                        new_text=params.get("text", ""),
                    )
                )

            # Append block (insert at end)
            elif intent_type == "appendblock":
                live_intents.append(
                    LiveEditIntent(
                        type="append",
                        new_text=params.get("text", ""),
                    )
                )

            # Insert at top (insert after line 0)
            elif intent_type == "insertattop":
                live_intents.append(
                    LiveEditIntent(
                        type="insert_after",
                        start_line=0,
                        new_text=params.get("text", ""),
                    )
                )

            # Insert at bottom (same as append)
            elif intent_type == "insertatbottom":
                live_intents.append(
                    LiveEditIntent(
                        type="append",
                        new_text=params.get("text", ""),
                    )
                )

            # Insert block at line
            elif intent_type == "insertblockatline":
                line_num = params.get("line_number", 1)
                live_intents.append(
                    LiveEditIntent(
                        type="insert_after",
                        start_line=max(0, line_num - 1),
                        new_text=params.get("text", ""),
                    )
                )

        return live_intents


