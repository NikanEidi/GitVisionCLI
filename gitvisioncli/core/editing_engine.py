"""
Unified Editing Engine for GitVisionCLI.

This module centralizes all text-based file editing logic so that:
  - Line- and block-based operations have consistent 1-based semantics.
  - Parameter aliases (line/line_number, start/start_line, etc.) are normalized.
  - Range validation is strict (no negative or out-of-bounds indices).
  - Newline normalization is handled once (CRLF/CR → LF).
  - Pattern-based edits (exact, regex, fuzzy) behave consistently.
  - JSON/YAML key updates are applied in a predictable way.

It is intentionally content-centric: it operates on strings and returns
new strings, leaving filesystem I/O, sandbox enforcement, and transactional
rollback to higher-level components such as ActionSupervisor or SafePatchEngine.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


logger = logging.getLogger(__name__)


class EditingError(Exception):
    """Base error for editing failures (invalid ranges, missing patterns, etc.)."""


@dataclass
class EditOperationResult:
    """Structured result for a single in-memory edit operation."""

    content: str
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)


class EditingEngine:
    """
    Pure in-memory editing engine.

    All methods take a ``content`` string and return a new content string,
    never mutating in place. Callers are responsible for reading/writing
    files and coordinating transactions / backups.
    """

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        # base_dir is currently informational; path sandboxing is enforced
        # by higher layers (SecurityPolicy, TerminalEngine, etc.).
        self.base_dir = Path(base_dir).resolve() if base_dir else None

    # ------------------------------------------------------------------
    # Core helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_newlines(text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def _split_lines(text: str) -> List[str]:
        return EditingEngine._normalize_newlines(text).split("\n")

    @staticmethod
    def _join_lines(lines: List[str]) -> str:
        # Always join with '\n'; callers can adapt when writing to disk.
        return "\n".join(lines)

    # ---- line / range normalization -----------------------------------
    @staticmethod
    def _normalize_line_number(
        raw: Any,
        *,
        max_allowed: Optional[int] = None,
        allow_end_plus_one: bool = False,
        field_name: str = "line_number",
    ) -> int:
        """
        Convert a user-supplied line index into a 1-based integer.

        - Rejects non-integers and values < 1.
        - If max_allowed is given, rejects values > max_allowed (or
          max_allowed + 1 when allow_end_plus_one=True).
        """
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise EditingError(f"Invalid {field_name}: {raw!r} is not an integer")

        if value < 1:
            raise EditingError(f"{field_name} must be >= 1 (got {value})")

        if max_allowed is not None:
            limit = max_allowed + (1 if allow_end_plus_one else 0)
            if value > limit:
                raise EditingError(
                    f"{field_name} {value} is out of range (max {limit})"
                )

        return value

    @staticmethod
    def _normalize_line_range(
        raw_start: Any,
        raw_end: Any,
        *,
        max_lines: int,
        start_field: str = "start_line",
        end_field: str = "end_line",
    ) -> Tuple[int, int]:
        """
        Normalize an inclusive [start, end] 1-based range.

        Ensures:
          - 1 <= start <= end
          - end <= max_lines
        """
        # First normalize to positive integers without applying an
        # upper bound, then handle file-length semantics explicitly so
        # error messages are consistent ("beyond file length").
        start = EditingEngine._normalize_line_number(
            raw_start,
            max_allowed=None,
            allow_end_plus_one=False,
            field_name=start_field,
        )
        end = EditingEngine._normalize_line_number(
            raw_end,
            max_allowed=None,
            allow_end_plus_one=False,
            field_name=end_field,
        )

        if end < start:
            raise EditingError(
                f"{end_field} ({end}) must be >= {start_field} ({start})"
            )

        if start > max_lines:
            raise EditingError(
                f"{start_field} ({start}) is beyond file length ({max_lines})"
            )
        if end > max_lines:
            raise EditingError(
                f"{end_field} ({end}) is beyond file length ({max_lines})"
            )

        return start, end

    # ------------------------------------------------------------------
    # Line-based operations
    # ------------------------------------------------------------------
    def insert_before_line(
        self,
        content: str,
        *,
        line_number: Optional[Any] = None,
        line: Optional[Any] = None,
        text: str = "",
    ) -> EditOperationResult:
        """
        Insert a single line *before* the given 1-based line index.

        Aliases:
          - line_number, line
        """
        lines = self._split_lines(content)
        max_lines = max(1, len(lines) or 1)

        raw_line = line_number if line_number is not None else line
        if raw_line is None:
            raw_line = 1

        ln = self._normalize_line_number(
            raw_line,
            max_allowed=max_lines,
            allow_end_plus_one=True,
            field_name="line_number",
        )

        # Convert 1-based to 0-based index.
        idx = ln - 1
        if idx > len(lines):
            idx = len(lines)

        lines.insert(idx, text)
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Inserted line before {ln}",
            details={"line_number": ln},
        )

    def insert_after_line(
        self,
        content: str,
        *,
        line_number: Optional[Any] = None,
        line: Optional[Any] = None,
        text: str = "",
    ) -> EditOperationResult:
        """
        Insert a single line *after* the given 1-based line index.

        Aliases:
          - line_number, line
        """
        lines = self._split_lines(content)
        max_lines = len(lines) or 0

        raw_line = line_number if line_number is not None else line
        if raw_line is None:
            raw_line = max_lines  # default append to end if not provided

        ln = self._normalize_line_number(
            raw_line,
            max_allowed=max_lines,
            allow_end_plus_one=False,
            field_name="line_number",
        )

        idx = ln  # after line N → index N (0-based)
        if idx > len(lines):
            idx = len(lines)

        lines.insert(idx, text)
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Inserted line after {ln}",
            details={"line_number": ln},
        )

    def replace_line(
        self,
        content: str,
        *,
        line_number: Optional[Any] = None,
        line: Optional[Any] = None,
        text: str = "",
    ) -> EditOperationResult:
        """
        Replace the contents of a specific 1-based line.
        """
        lines = self._split_lines(content)
        max_lines = len(lines) or 0
        if max_lines == 0:
            raise EditingError("Cannot replace line in empty file")

        raw_line = line_number if line_number is not None else line
        if raw_line is None:
            raw_line = 1

        ln = self._normalize_line_number(
            raw_line,
            max_allowed=max_lines,
            allow_end_plus_one=False,
            field_name="line_number",
        )

        idx = ln - 1
        lines[idx] = text
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Replaced line {ln}",
            details={"line_number": ln},
        )

    def delete_line_range(
        self,
        content: str,
        *,
        start_line: Optional[Any] = None,
        end_line: Optional[Any] = None,
        start: Optional[Any] = None,
        end: Optional[Any] = None,
    ) -> EditOperationResult:
        """
        Delete an inclusive 1-based line range [start, end].

        Aliases:
          - start_line, start
          - end_line, end
        """
        lines = self._split_lines(content)
        max_lines = len(lines) or 0
        if max_lines == 0:
            raise EditingError("Cannot delete lines from empty file")

        raw_start = start_line if start_line is not None else start
        raw_end = end_line if end_line is not None else end

        if raw_start is None:
            raw_start = 1
        if raw_end is None:
            raw_end = raw_start

        s, e = self._normalize_line_range(
            raw_start,
            raw_end,
            max_lines=max_lines,
        )

        start_idx = s - 1
        end_idx = e  # exclusive

        del lines[start_idx:end_idx]
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Deleted lines {s}-{e}",
            details={"start_line": s, "end_line": e},
        )

    def append_line(self, content: str, *, text: str = "") -> EditOperationResult:
        """Append a single line at the bottom of the file."""
        lines = self._split_lines(content)
        lines.append(text)
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary="Appended line at bottom",
        )

    def prepend_line(self, content: str, *, text: str = "") -> EditOperationResult:
        """Prepend a single line at the top of the file."""
        lines = self._split_lines(content)
        lines.insert(0, text)
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary="Prepended line at top",
        )

    def insert_at_top(self, content: str, *, block: str) -> EditOperationResult:
        """Insert a multi-line block at the beginning of the file."""
        existing = self._normalize_newlines(content)
        prefix = self._normalize_newlines(block)
        joined = prefix + ("\n" + existing if existing else "")
        return EditOperationResult(
            content=joined,
            summary="Inserted block at top of file",
        )

    def insert_at_bottom(self, content: str, *, block: str) -> EditOperationResult:
        """Insert a multi-line block at the end of the file."""
        existing = self._normalize_newlines(content)
        suffix = self._normalize_newlines(block)
        if not existing:
            joined = suffix
        else:
            joined = existing + ("\n" if not existing.endswith("\n") else "") + suffix
        return EditOperationResult(
            content=joined,
            summary="Inserted block at bottom of file",
        )

    # ------------------------------------------------------------------
    # Block-based operations
    # ------------------------------------------------------------------
    def insert_block_at_line(
        self,
        content: str,
        *,
        line_number: Optional[Any] = None,
        line: Optional[Any] = None,
        block: str,
    ) -> EditOperationResult:
        """
        Insert a multi-line block starting at a specific 1-based line.
        Existing lines are pushed down.
        """
        lines = self._split_lines(content)
        max_lines = len(lines)

        raw_line = line_number if line_number is not None else line
        if raw_line is None:
            raw_line = max_lines + 1  # default append

        ln = self._normalize_line_number(
            raw_line,
            max_allowed=max_lines + 1,
            allow_end_plus_one=True,
            field_name="line_number",
        )

        idx = ln - 1
        idx = max(0, min(idx, len(lines)))

        block_norm = self._normalize_newlines(block)
        new_lines = block_norm.split("\n") if block_norm else [""]

        lines[idx:idx] = new_lines
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Inserted block at line {ln}",
            details={"line_number": ln, "line_count": len(new_lines)},
        )

    def replace_block(
        self,
        content: str,
        *,
        start_line: Any,
        end_line: Any,
        block: str,
    ) -> EditOperationResult:
        """
        Replace the inclusive range [start_line, end_line] with a new block.
        """
        lines = self._split_lines(content)
        max_lines = len(lines)
        if max_lines == 0:
            raise EditingError("Cannot replace block in empty file")

        s, e = self._normalize_line_range(
            start_line,
            end_line,
            max_lines=max_lines,
        )

        block_norm = self._normalize_newlines(block)
        new_lines = block_norm.split("\n") if block_norm else [""]

        start_idx = s - 1
        end_idx = e  # exclusive
        lines[start_idx:end_idx] = new_lines
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Replaced lines {s}-{e} with block",
            details={"start_line": s, "end_line": e, "line_count": len(new_lines)},
        )

    def remove_block(
        self,
        content: str,
        *,
        start_line: Any,
        end_line: Any,
    ) -> EditOperationResult:
        """Alias for delete_line_range using explicit names."""
        return self.delete_line_range(
            content,
            start_line=start_line,
            end_line=end_line,
        )

    # ------------------------------------------------------------------
    # Smart / semantic operations
    # ------------------------------------------------------------------
    def replace_by_exact_match(
        self,
        content: str,
        *,
        old: str,
        new: str,
        count: Optional[int] = None,
    ) -> EditOperationResult:
        """
        Replace occurrences of ``old`` with ``new``.

        - If count is None, replaces all occurrences.
        - If count is 1, replaces the first occurrence only.
        """
        if not old:
            raise EditingError("old value for ReplaceByExactMatch cannot be empty")

        occurrences = content.count(old)
        if occurrences == 0:
            raise EditingError("Exact match string not found in content")

        if count is None:
            new_content = content.replace(old, new)
        else:
            new_content = content.replace(old, new, count)

        return EditOperationResult(
            content=new_content,
            summary="Replaced exact matches",
            details={"old": old, "new": new, "replacements": occurrences},
        )

    def replace_by_pattern(
        self,
        content: str,
        *,
        pattern: str,
        replacement: str,
        flags: int = 0,
    ) -> EditOperationResult:
        """
        Regex-based replacement.

        Raises EditingError if the pattern does not match the content.
        """
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise EditingError(f"Invalid regex pattern: {e}") from e

        if not regex.search(content):
            raise EditingError("Pattern not found in content")

        new_content, count = regex.subn(replacement, content)
        return EditOperationResult(
            content=new_content,
            summary="Replaced by pattern",
            details={"pattern": pattern, "replacements": count},
        )

    def delete_by_pattern(
        self,
        content: str,
        *,
        pattern: str,
        flags: int = 0,
    ) -> EditOperationResult:
        """
        Delete all text matching a regex pattern.
        """
        return self.replace_by_pattern(
            content,
            pattern=pattern,
            replacement="",
            flags=flags,
        )

    def replace_by_fuzzy_match(
        self,
        content: str,
        *,
        target: str,
        replacement: str,
        threshold: float = 0.6,
    ) -> EditOperationResult:
        """
        Fuzzy line-level replacement.

        - Finds the single line whose content is most similar to ``target``.
        - If similarity < threshold, raises EditingError.
        - Replaces the entire line with ``replacement``.
        """
        if not target:
            raise EditingError("target for ReplaceByFuzzyMatch cannot be empty")

        lines = self._split_lines(content)
        if not lines:
            raise EditingError("Cannot perform fuzzy match on empty file")

        best_idx = -1
        best_score = 0.0
        for idx, line in enumerate(lines):
            score = SequenceMatcher(None, line, target).ratio()
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx == -1 or best_score < threshold:
            raise EditingError(
                f"No sufficiently similar line found (best score {best_score:.2f} < {threshold})"
            )

        lines[best_idx] = replacement
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary="Replaced line by fuzzy match",
            details={"line_number": best_idx + 1, "similarity": best_score},
        )

    def insert_after_import_section(
        self,
        content: str,
        *,
        block: str,
    ) -> EditOperationResult:
        """
        Insert a block after an import section near the top of the file.

        Heuristic:
        - Skip initial shebang and encoding comments.
        - Collect contiguous 'import' / 'from' lines.
        - Insert block after the last such line; if none, insert at top.
        """
        lines = self._split_lines(content)
        insert_idx = 0
        i = 0
        # Skip shebang / encoding
        while i < len(lines) and (
            lines[i].startswith("#!") or "coding" in lines[i].lower()
        ):
            i += 1

        # Collect import block
        last_import_idx = -1
        while i < len(lines) and lines[i].strip().startswith(("import ", "from ")):
            last_import_idx = i
            i += 1

        if last_import_idx >= 0:
            insert_idx = last_import_idx + 1
        else:
            insert_idx = 0

        block_norm = self._normalize_newlines(block)
        new_lines = block_norm.split("\n") if block_norm else [""]

        lines[insert_idx:insert_idx] = new_lines
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary="Inserted block after import section",
            details={"insert_index": insert_idx, "line_count": len(new_lines)},
        )

    # ------------------------------------------------------------------
    # Semantic structure-aware operations (functions, classes, imports)
    # ------------------------------------------------------------------

    def insert_into_function(
        self,
        content: str,
        *,
        function_name: str,
        block: str,
        position: str = "bottom",
    ) -> EditOperationResult:
        """
        Insert a block inside a function body.

        - Supports Python 'def name(...)' patterns.
        - For now, JavaScript-style functions are only supported when
          they use a simple 'function name(...) {' form.
        - Raises EditingError on ambiguous or missing matches.
        """
        text = self._normalize_newlines(content)
        lines = text.split("\n")

        if not function_name:
            raise EditingError("Function name is required for InsertIntoFunction")

        py_def = re.compile(rf"^\s*def\s+{re.escape(function_name)}\s*\(")
        js_def = re.compile(
            rf"^\s*(async\s+)?function\s+{re.escape(function_name)}\s*\(", re.IGNORECASE
        )

        matches = [i for i, ln in enumerate(lines) if py_def.search(ln) or js_def.search(ln)]
        if not matches:
            raise EditingError(f"Function '{function_name}' not found")
        if len(matches) > 1:
            raise EditingError(f"Multiple functions named '{function_name}' found; please disambiguate")

        def_idx = matches[0]
        def_line = lines[def_idx]
        leading = def_line[: len(def_line) - len(def_line.lstrip())]

        is_python = py_def.search(def_line) is not None

        block_norm = self._normalize_newlines(block)
        raw_block_lines = block_norm.split("\n") if block_norm else [""]

        if is_python:
            # Determine indentation for body.
            body_indent = None
            j = def_idx + 1
            while j < len(lines):
                ln = lines[j]
                if not ln.strip():
                    j += 1
                    continue
                indent = ln[: len(ln) - len(ln.lstrip())]
                if len(indent) <= len(leading):
                    break
                body_indent = indent
                break

            if body_indent is None:
                indent_unit = " " * 4
                body_indent = leading + indent_unit
            else:
                indent_unit = body_indent[len(leading) :] or " " * 4

            # Determine insertion index.
            if position.lower() == "top":
                # Insert at the start of the function body, after any
                # docstring triple-quoted block if present.
                insert_idx = def_idx + 1

                # Skip docstring if it starts immediately after def.
                if insert_idx < len(lines):
                    first_body = lines[insert_idx].lstrip()
                    if first_body.startswith(('"""', "'''")):
                        quote = first_body[:3]
                        insert_idx += 1
                        while insert_idx < len(lines):
                            if quote in lines[insert_idx]:
                                insert_idx += 1
                                break
                            insert_idx += 1
            else:
                # Insert at the bottom of the function body, before the
                # first line whose indent is <= def indent (dedent).
                last_body = def_idx
                for j in range(def_idx + 1, len(lines)):
                    ln = lines[j]
                    if not ln.strip():
                        last_body = j
                        continue
                    indent = ln[: len(ln) - len(ln.lstrip())]
                    if len(indent) <= len(leading):
                        break
                    last_body = j
                insert_idx = last_body + 1

            new_lines = [
                (body_indent + blk if blk.strip() else body_indent.rstrip())
                for blk in raw_block_lines
            ]
            lines[insert_idx:insert_idx] = new_lines
            new_content = self._join_lines(lines)
            return EditOperationResult(
                content=new_content,
                summary=f"Inserted block into function '{function_name}'",
                details={"function": function_name, "position": position.lower()},
            )

        # Simple JS function with braces.
        brace_depth = 0
        body_start = None
        body_end = None
        # Find first '{' that opens the function body.
        for j in range(def_idx, len(lines)):
            ln = lines[j]
            for ch in ln:
                if ch == "{":
                    brace_depth += 1
                    if brace_depth == 1 and body_start is None:
                        body_start = j
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0 and body_start is not None:
                        body_end = j
                        break
            if body_end is not None:
                break

        if body_start is None or body_end is None:
            raise EditingError(f"Could not determine body for function '{function_name}'")

        # Insert after opening brace or before closing brace.
        if position.lower() == "top":
            insert_idx = body_start + 1
        else:
            insert_idx = body_end

        # Preserve indentation level of the first body line, if any.
        if body_start + 1 < len(lines):
            sample = lines[body_start + 1]
            body_indent = sample[: len(sample) - len(sample.lstrip())]
        else:
            body_indent = "    "

        new_lines = [
            (body_indent + blk if blk.strip() else body_indent.rstrip())
            for blk in raw_block_lines
        ]
        lines[insert_idx:insert_idx] = new_lines
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Inserted block into function '{function_name}'",
            details={"function": function_name, "position": position.lower()},
        )

    def insert_into_class(
        self,
        content: str,
        *,
        class_name: str,
        block: str,
        position: str = "bottom",
    ) -> EditOperationResult:
        """
        Insert a block inside a class body (Python or simple JS).
        """
        text = self._normalize_newlines(content)
        lines = text.split("\n")

        if not class_name:
            raise EditingError("Class name is required for InsertIntoClass")

        py_cls = re.compile(rf"^\s*class\s+{re.escape(class_name)}\b")
        js_cls = re.compile(rf"^\s*class\s+{re.escape(class_name)}\b", re.IGNORECASE)

        matches = [i for i, ln in enumerate(lines) if py_cls.search(ln) or js_cls.search(ln)]
        if not matches:
            raise EditingError(f"Class '{class_name}' not found")
        if len(matches) > 1:
            raise EditingError(f"Multiple classes named '{class_name}' found; please disambiguate")

        cls_idx = matches[0]
        cls_line = lines[cls_idx]
        leading = cls_line[: len(cls_line) - len(cls_line.lstrip())]

        is_python = py_cls.search(cls_line) is not None

        block_norm = self._normalize_newlines(block)
        raw_block_lines = block_norm.split("\n") if block_norm else [""]

        if is_python:
            # Determine indentation for body.
            body_indent = None
            j = cls_idx + 1
            while j < len(lines):
                ln = lines[j]
                if not ln.strip():
                    j += 1
                    continue
                indent = ln[: len(ln) - len(ln.lstrip())]
                if len(indent) <= len(leading):
                    break
                body_indent = indent
                break

            if body_indent is None:
                indent_unit = " " * 4
                body_indent = leading + indent_unit
            else:
                indent_unit = body_indent[len(leading) :] or " " * 4

            if position.lower() == "top":
                insert_idx = cls_idx + 1
            else:
                last_body = cls_idx
                for j in range(cls_idx + 1, len(lines)):
                    ln = lines[j]
                    if not ln.strip():
                        last_body = j
                        continue
                    indent = ln[: len(ln) - len(ln.lstrip())]
                    if len(indent) <= len(leading):
                        break
                    last_body = j
                insert_idx = last_body + 1

            new_lines = [
                (body_indent + blk if blk.strip() else body_indent.rstrip())
                for blk in raw_block_lines
            ]
            lines[insert_idx:insert_idx] = new_lines
            new_content = self._join_lines(lines)
            return EditOperationResult(
                content=new_content,
                summary=f"Inserted block into class '{class_name}'",
                details={"class": class_name, "position": position.lower()},
            )

        # JS-style class with braces.
        brace_depth = 0
        body_start = None
        body_end = None
        for j in range(cls_idx, len(lines)):
            ln = lines[j]
            for ch in ln:
                if ch == "{":
                    brace_depth += 1
                    if brace_depth == 1 and body_start is None:
                        body_start = j
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0 and body_start is not None:
                        body_end = j
                        break
            if body_end is not None:
                break

        if body_start is None or body_end is None:
            raise EditingError(f"Could not determine body for class '{class_name}'")

        if position.lower() == "top":
            insert_idx = body_start + 1
        else:
            insert_idx = body_end

        if body_start + 1 < len(lines):
            sample = lines[body_start + 1]
            body_indent = sample[: len(sample) - len(sample.lstrip())]
        else:
            body_indent = "    "

        new_lines = [
            (body_indent + blk if blk.strip() else body_indent.rstrip())
            for blk in raw_block_lines
        ]
        lines[insert_idx:insert_idx] = new_lines
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Inserted block into class '{class_name}'",
            details={"class": class_name, "position": position.lower()},
        )

    def add_decorator(
        self,
        content: str,
        *,
        target_name: str,
        decorator: str,
    ) -> EditOperationResult:
        """
        Add a decorator (Python/JS-style) above a function or class.

        - Ensures we don't duplicate existing decorators.
        - Preserves any existing decorator stack order.
        """
        text = self._normalize_newlines(content)
        lines = text.split("\n")

        if not target_name:
            raise EditingError("Target name is required for AddDecorator")
        if not decorator:
            raise EditingError("Decorator name is required for AddDecorator")

        deco_str = decorator.strip()
        if not deco_str.startswith("@"):
            deco_str = "@" + deco_str

        # Find target definition.
        def_re = re.compile(
            rf"^\s*(def\s+{re.escape(target_name)}\s*\(|class\s+{re.escape(target_name)}\b|function\s+{re.escape(target_name)}\s*\()"
        )

        target_idx = None
        for i, ln in enumerate(lines):
            if def_re.search(ln):
                target_idx = i
                break

        if target_idx is None:
            raise EditingError(f"Target '{target_name}' not found for decorator")

        # Walk upwards collecting existing decorators.
        insert_idx = target_idx
        i = target_idx - 1
        while i >= 0:
            stripped = lines[i].lstrip()
            if stripped.startswith("@"):
                if stripped.split()[0] == deco_str:
                    # Decorator already present; no-op.
                    raise EditingError(f"Decorator {deco_str} already present on '{target_name}'")
                insert_idx = i
                i -= 1
                continue
            break

        indent = lines[target_idx][: len(lines[target_idx]) - len(lines[target_idx].lstrip())]
        deco_line = indent + deco_str
        lines.insert(insert_idx, deco_line)
        new_content = self._join_lines(lines)
        return EditOperationResult(
            content=new_content,
            summary=f"Added decorator {deco_str} to '{target_name}'",
            details={"target": target_name, "decorator": deco_str},
        )

    def auto_import(
        self,
        content: str,
        *,
        symbol: str,
        import_path: Optional[str] = None,
    ) -> EditOperationResult:
        """
        Ensure that a symbol is imported once.

        - For Python, prefers 'from import_path import symbol' when
          import_path is provided and not equal to symbol.
        - Otherwise falls back to 'import symbol'.
        - For other languages, uses a conservative 'import symbol' line.
        """
        if not symbol:
            raise EditingError("Symbol name is required for AutoImport")

        text = self._normalize_newlines(content)
        lines = text.split("\n")

        # Check if already imported.
        sym = symbol.strip()
        imp_path = (import_path or "").strip() or sym

        py_import_re = re.compile(
            rf"^\s*(from\s+{re.escape(imp_path)}\s+import\s+.*\b{re.escape(sym)}\b|import\s+.*\b{re.escape(sym)}\b)"
        )
        for ln in lines:
            if py_import_re.search(ln):
                raise EditingError(f"Import for '{sym}' already exists")

        # Compose import line (Python-first heuristic).
        if "." in imp_path and imp_path != sym:
            import_line = f"from {imp_path} import {sym}"
        else:
            import_line = f"import {sym}"

        result = self.insert_after_import_section(
            content,
            block=import_line,
        )
        return EditOperationResult(
            content=result.content,
            summary=f"Auto-imported '{sym}' from '{imp_path}'",
            details={"symbol": sym, "import_path": imp_path},
        )

    # ------------------------------------------------------------------
    # JSON / YAML key updates
    # ------------------------------------------------------------------
    def update_json_key(
        self,
        content: str,
        *,
        key_path: Union[str, List[str]],
        value: Any,
    ) -> EditOperationResult:
        """
        Update a nested JSON key.

        key_path may be:
          - a dotted string: "a.b.c"
          - a list of path segments: ["a", "b", "c"]
        """
        try:
            data = json.loads(content or "{}")
        except json.JSONDecodeError as e:
            raise EditingError(f"File content is not valid JSON: {e}") from e

        if isinstance(key_path, str):
            parts = [p for p in key_path.split(".") if p]
        else:
            parts = list(key_path)

        if not parts:
            raise EditingError("key_path must not be empty")

        cursor: Any = data
        for seg in parts[:-1]:
            if not isinstance(cursor, dict):
                raise EditingError(
                    f"Cannot traverse into '{seg}': parent is not an object"
                )
            if seg not in cursor or not isinstance(cursor[seg], dict):
                cursor[seg] = {}
            cursor = cursor[seg]

        if not isinstance(cursor, dict):
            raise EditingError(
                f"Cannot set final key '{parts[-1]}': parent is not an object"
            )

        cursor[parts[-1]] = value
        new_content = json.dumps(data, indent=2, sort_keys=False)
        return EditOperationResult(
            content=new_content,
            summary="Updated JSON key",
            details={"key_path": parts},
        )

    def update_yaml_key(
        self,
        content: str,
        *,
        key_path: Union[str, List[str]],
        value: Any,
    ) -> EditOperationResult:
        """
        Update a nested YAML key (best-effort).

        - Uses PyYAML if available; otherwise raises EditingError.
        - key_path rules mirror update_json_key.
        """
        try:
            import yaml  # type: ignore[import]
        except Exception as e:  # pragma: no cover - optional dependency
            raise EditingError(
                "PyYAML is required for UpdateYAMLKey but is not installed"
            ) from e

        try:
            data = yaml.safe_load(content) or {}
        except Exception as e:
            raise EditingError(f"File content is not valid YAML: {e}") from e

        if isinstance(key_path, str):
            parts = [p for p in key_path.split(".") if p]
        else:
            parts = list(key_path)

        if not parts:
            raise EditingError("key_path must not be empty")

        cursor: Any = data
        for seg in parts[:-1]:
            if not isinstance(cursor, dict):
                raise EditingError(
                    f"Cannot traverse into '{seg}': parent is not a mapping"
                )
            if seg not in cursor or not isinstance(cursor[seg], dict):
                cursor[seg] = {}
            cursor = cursor[seg]

        if not isinstance(cursor, dict):
            raise EditingError(
                f"Cannot set final key '{parts[-1]}': parent is not a mapping"
            )

        cursor[parts[-1]] = value
        new_content = yaml.safe_dump(data, sort_keys=False)
        return EditOperationResult(
            content=new_content,
            summary="Updated YAML key",
            details={"key_path": parts},
        )
