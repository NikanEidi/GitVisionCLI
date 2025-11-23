"""
GitVision Natural Language Action Engine

Converts every user message into a single structured ACTION JSON.
Zero questions, zero clarifications, zero explanations (unless no context exists).

This engine is designed to work with ALL model types (GPT-4o, Gemini, Claude, LLaMA, etc.)
and provides deterministic, simple action mapping.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ActionJSON:
    """Structured action JSON output."""
    type: str
    params: Dict[str, Any]


@dataclass
class ActiveFileContext:
    """Context about the currently active/editing file."""
    path: str
    content: Optional[str] = None


class NaturalLanguageActionEngine:
    """
    Deterministic natural language → action JSON converter.
    
    ALWAYS infers intent, ALWAYS picks the most likely action,
    NEVER asks questions (unless no context exists at all).
    """
    
    def __init__(self):
        # Precompile regex patterns for performance
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize all regex patterns for action detection."""
        
        # File operations - line-based
        self._remove_line_re = re.compile(
            r"\b(remove|delete|rm|dl)\s+line\s*(?P<line>\d+)\b", re.IGNORECASE
        )
        # Also match broken grammar: "rm 10", "delete line1", "remove ln5"
        self._remove_line_broken_re = re.compile(
            r"\b(?:rm|dl)\s+(?P<line>\d+)(?:\s|$)", re.IGNORECASE
        )
        self._remove_lines_re = re.compile(
            r"\b(remove|delete|rm|dl)\s+lines?\s+(?P<start>\d+)\s*-\s*(?P<end>\d+)\b", re.IGNORECASE
        )
        self._remove_lines_to_re = re.compile(
            r"\b(remove|delete|rm|dl)\s+lines?\s+(?P<start>\d+)\s+to\s+(?P<end>\d+)\b", re.IGNORECASE
        )
        self._replace_line_re = re.compile(
            r"\b(replace|update|change|edit)\s+line\s*(?P<line>\d+)\s+(?:with|to)\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        self._insert_at_line_re = re.compile(
            r"\b(insert|add|write)\s+(?:at|on)\s+line\s*(?P<line>\d+)\s*:?\s*(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        self._add_line_re = re.compile(
            r"\b(add|insert)\s+line\s*(?P<line>\d+)\s+with\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        self._edit_line_re = re.compile(
            r"\b(edit|change|update)\s+line\s*(?P<line>\d+)\s+with\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        self._append_re = re.compile(
            r"\b(add|append|insert)\s+(?:comment|text|code|line)?\s*(?:at|to)?\s*(?:the\s+)?(?:bottom|end)\b", re.IGNORECASE
        )
        
        # File operations - file-level
        self._read_file_re = re.compile(
            r"\b(?:read|show|display|cat|view)\s+(?:file\s+)?(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        self._delete_file_re = re.compile(
            r"\b(?:delete|remove|rm)\s+(?:file\s+)?(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        # Create file - require explicit "file" keyword to avoid matching folder operations
        self._create_file_re = re.compile(
            r"\b(?:create|make|new)\s+file\s+(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        # Also support "create <path>" without "file" but only if no folder keywords follow
        self._create_file_simple_re = re.compile(
            r"\b(?:create|make|new)\s+(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        self._rename_file_re = re.compile(
            r"\b(?:rename|mv|move)\s+(?:file\s+)?(?P<old>[^\s]+)\s+(?:to|as)\s+(?P<new>[^\s]+)\b", re.IGNORECASE
        )
        self._move_file_re = re.compile(
            r"\b(?:move|mv)\s+(?:file\s+)?(?P<path>[^\s]+)\s+to\s+(?P<target>[^\s]+)\b", re.IGNORECASE
        )
        self._copy_file_re = re.compile(
            r"\b(?:copy|cp)\s+(?:file\s+)?(?P<path>[^\s]+)\s+(?:to|as)\s+(?P<new>[^\s]+)\b", re.IGNORECASE
        )
        self._open_file_re = re.compile(
            r"\b(?:open|edit|nano|code|view)\s+(?:file\s+)?(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        
        # Search operations
        self._search_files_re = re.compile(
            r"\b(?:search|find|grep|locate)\s+(?:for|files?|text)?\s*(?P<pattern>[^\s]+)\b", re.IGNORECASE
        )
        self._find_files_re = re.compile(
            r"\b(?:find|locate|search\s+for)\s+(?:files?\s+)?(?:named|called|with\s+name)\s+(?P<name>[^\s]+)\b", re.IGNORECASE
        )
        
        # Folder operations
        self._create_folder_re = re.compile(
            r"\b(?:create|make|new|mkdir)\s+(?:folder|directory|dir)\s+(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        self._delete_folder_re = re.compile(
            r"\b(?:delete|remove|rm|rmdir)\s+(?:folder|directory|dir)\s+(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        self._move_folder_re = re.compile(
            r"\b(?:move|mv)\s+(?:folder|directory|dir)\s+(?P<path>[^\s]+)\s+to\s+(?P<target>[^\s]+)\b", re.IGNORECASE
        )
        self._copy_folder_re = re.compile(
            r"\b(?:copy|cp)\s+(?:folder|directory|dir)\s+(?P<path>[^\s]+)\s+(?:to|as)\s+(?P<new>[^\s]+)\b", re.IGNORECASE
        )
        self._rename_folder_re = re.compile(
            r"\b(?:rename|mv)\s+(?:folder|directory|dir)\s+(?P<old>[^\s]+)\s+(?:to|as)\s+(?P<new>[^\s]+)\b", re.IGNORECASE
        )
        
        # Git operations
        self._git_init_re = re.compile(r"\bgit\s+init\b", re.IGNORECASE)
        # CRITICAL FIX: Require explicit "git" prefix for status/log to avoid false positives
        # from common English words like "What's the status?" or "check the log file"
        self._git_status_re = re.compile(r"\bgit\s+status\b", re.IGNORECASE)
        self._git_log_re = re.compile(r"\bgit\s+log\b", re.IGNORECASE)
        self._git_add_re = re.compile(
            r"\b(?:git\s+)?add\s+(?P<path>\.|all|[^\s]+)\b", re.IGNORECASE
        )
        self._git_commit_re = re.compile(
            r"\b(?:git\s+)?commit\s+(?:all\s+)?(?:with\s+)?message\s+['\"](?P<msg>[^'\"]+)['\"]", re.IGNORECASE
        )
        self._git_commit_simple_re = re.compile(
            r"\b(?:git\s+)?commit\s+(?:-m\s+)?['\"](?P<msg>[^'\"]+)['\"]", re.IGNORECASE
        )
        self._git_branch_re = re.compile(
            r"\b(?:git\s+)?(?:create\s+)?(?:new\s+)?branch\s+(?P<name>[^\s]+)\b", re.IGNORECASE
        )
        self._git_checkout_re = re.compile(
            r"\b(?:git\s+)?(?:switch\s+to\s+|checkout\s+)(?:branch\s+)?(?P<branch>[^\s]+)\b", re.IGNORECASE
        )
        self._git_merge_re = re.compile(
            r"\b(?:git\s+)?merge\s+(?:branch\s+)?(?P<branch>[^\s]+)\b", re.IGNORECASE
        )
        self._git_push_re = re.compile(
            r"\b(?:git\s+)?push\s+(?:-u\s+)?(?:origin\s+)?(?P<branch>[^\s]*)\b", re.IGNORECASE
        )
        self._git_pull_re = re.compile(
            r"\b(?:git\s+)?pull\s+(?:origin\s+)?(?P<branch>[^\s]*)\b", re.IGNORECASE
        )
        self._git_remote_re = re.compile(
            r"\b(?:git\s+)?remote\s+add\s+(?P<name>[^\s]+)\s+(?P<url>[^\s]+)\b", re.IGNORECASE
        )
        self._git_graph_re = re.compile(
            r"\b(?:git\s+)?(?:show\s+)?(?:graph|log\s+--graph)\b", re.IGNORECASE
        )
        # Also match "git graph" as two words
        self._git_graph_words_re = re.compile(
            r"\bgit\s+graph\b", re.IGNORECASE
        )
        
        # GitHub operations
        self._github_repo_re = re.compile(
            r"\b(?:create\s+)?(?:github\s+)?(?:repo|repository)\s+(?:named\s+)?(?P<name>[^\s]+)\s+(?P<private>private|public)?\b", re.IGNORECASE
        )
        self._github_issue_re = re.compile(
            r"\b(?:create\s+)?(?:github\s+)?issue\s+['\"](?P<title>[^'\"]+)['\"]\s+(?:with\s+)?body\s+['\"](?P<body>[^'\"]+)['\"]", re.IGNORECASE
        )
        self._github_issue_simple_re = re.compile(
            r"\b(?:create\s+)?(?:github\s+)?issue\s+['\"](?P<title>[^'\"]+)['\"]", re.IGNORECASE
        )
        self._github_pr_re = re.compile(
            r"\b(?:create\s+)?(?:github\s+)?(?:pr|pull\s+request)\s+['\"](?P<title>[^'\"]+)['\"]", re.IGNORECASE
        )
        
        # Change directory operations
        self._cd_re = re.compile(
            r"\b(?:cd|change\s+directory|go\s+to|go\s+into|enter|navigate\s+to)\s+(?:the\s+)?(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        self._cd_contextual_re = re.compile(
            r"\b(?:create|make)\s+(?P<name>[^\s/]+)\s+(?:folder|directory)\s+and\s+(?:go\s+to|cd|enter)\s+(?:it|there|the\s+(?:folder|directory))\b", re.IGNORECASE
        )
        self._cd_up_re = re.compile(
            r"\b(?:cd|go)\s+\.\.\b", re.IGNORECASE
        )
        
        # List directory operations (natural language)
        self._list_dir_re = re.compile(
            r"\b(?:list|show|display|ls)\s+(?:files|contents|directory|folder|dir)\s+(?:in|of|at)?\s*(?P<path>[^\s]*)\b", re.IGNORECASE
        )
        
        # Debugging/testing commands
        self._debug_re = re.compile(
            r"\b(?:debug|test|run|execute)\s+(?:file|script|program|code)\s+(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        self._run_script_re = re.compile(
            r"\b(?:run|execute|launch)\s+(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        
        # Broken grammar patterns (fix automatically)
        self._broken_line_re = re.compile(
            r"\b(?:remove|delete|rm|dl)\s*(?:line|ln)?\s*(?P<line>\d+)\b", re.IGNORECASE
        )
        self._broken_lines_re = re.compile(
            r"\b(?:remove|delete|rm|dl)\s*(?:line|ln)?\s*(?P<start>\d+)\s*[-~]\s*(?P<end>\d+)\b", re.IGNORECASE
        )
        
        # Content extraction patterns
        self._with_content_re = re.compile(
            r"\bwith\s+(?P<content>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        self._colon_content_re = re.compile(
            r":\s*(?P<content>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
    
    def normalize_grammar(self, text: str) -> str:
        """
        Fix broken grammar automatically.
        Examples:
        - "remove line1" → "remove line 1"
        - "delete ln5" → "delete line 5"
        - "rm 2" → "remove line 2" (if context suggests line operation)
        - "replace line5" → "replace line 5"
        - "edit line3" → "edit line 3"
        - "add at line10" → "add at line 10"
        """
        # Fix "line1", "line5", etc. → "line 1", "line 5"
        text = re.sub(r"\bline(\d+)\b", r"line \1", text, flags=re.IGNORECASE)
        
        # Fix "ln5", "ln10", etc. → "line 5", "line 10"
        text = re.sub(r"\bln(\d+)\b", r"line \1", text, flags=re.IGNORECASE)
        
        # Fix "rm 2", "dl 10" → "remove line 2", "delete line 10"
        # Only if it's a standalone number after rm/dl
        rm_match = re.search(r"\b(?:rm|dl)\s+(\d+)(?:\s|$)", text, re.IGNORECASE)
        if rm_match:
            num = rm_match.group(1)
            # Check if context suggests line operation (active file exists or "line" mentioned nearby)
            if "line" in text.lower()[:20] or "line" in text.lower()[-20:]:
                text = re.sub(r"\b(?:rm|dl)\s+" + num + r"(?:\s|$)", f"remove line {num} ", text, flags=re.IGNORECASE)
        
        # Fix "replace line5" → "replace line 5"
        text = re.sub(r"\breplace\s+line(\d+)\b", r"replace line \1", text, flags=re.IGNORECASE)
        
        # Fix "delete line5", "remove line5" → "delete line 5", "remove line 5"
        text = re.sub(r"\b(delete|remove)\s+line(\d+)\b", r"\1 line \2", text, flags=re.IGNORECASE)
        
        # Fix "edit line3", "change line7" → "edit line 3", "change line 7"
        text = re.sub(r"\b(edit|change|update)\s+line(\d+)\b", r"\1 line \2", text, flags=re.IGNORECASE)
        
        # Fix "add at line10", "insert at line5" → "add at line 10", "insert at line 5"
        text = re.sub(r"\b(add|insert|write)\s+at\s+line(\d+)\b", r"\1 at line \2", text, flags=re.IGNORECASE)
        
        # Fix "line3-7", "line5~10" → "line 3-7", "line 5-10"
        text = re.sub(r"\bline(\d+)\s*[-~]\s*(\d+)\b", r"line \1-\2", text, flags=re.IGNORECASE)
        
        # Fix "lines3-7", "lines5~10" → "lines 3-7", "lines 5-10"
        text = re.sub(r"\blines(\d+)\s*[-~]\s*(\d+)\b", r"lines \1-\2", text, flags=re.IGNORECASE)
        
        return text
    
    def extract_content(self, text: str, instruction: str) -> Optional[str]:
        """Extract content from instruction text."""
        # Try "with X" pattern
        match = self._with_content_re.search(text)
        if match:
            return match.group("content").strip()
        
        # Try ": X" pattern
        match = self._colon_content_re.search(text)
        if match:
            return match.group("content").strip()
        
        # Try to extract after action verb
        # "add hello world" → "hello world"
        add_match = re.search(r"\b(add|insert|write|append)\s+(.+?)(?:\s+in\s+|\s*$)", text, re.IGNORECASE)
        if add_match:
            return add_match.group(2).strip()
        
        return None
    
    def convert_to_action(
        self,
        user_message: str,
        active_file: Optional[ActiveFileContext] = None,
    ) -> Optional[ActionJSON]:
        """
        Convert user message to a single structured action JSON.
        
        Returns None only if no context exists and action cannot be inferred.
        Otherwise, ALWAYS returns an action (picks the most likely one).
        """
        if not user_message or not user_message.strip():
            return None
        
        # Normalize grammar first
        text = self.normalize_grammar(user_message.strip())
        text_lower = text.lower()
        
        # ============================================================
        # FILE OPERATIONS - Line-based (highest priority if active_file)
        # ============================================================
        if active_file:
            # Delete single line (also handle broken grammar: "rm 10", "delete line1", "remove ln5")
            match = self._remove_line_re.search(text) or self._broken_line_re.search(text) or self._remove_line_broken_re.search(text)
            if match:
                line_num = int(match.group("line"))
                return ActionJSON(
                    type="DeleteLineRange",
                    params={
                        "path": active_file.path,
                        "start_line": line_num,
                        "end_line": line_num,
                    }
                )
            
            # Delete line range
            match = self._remove_lines_re.search(text) or self._remove_lines_to_re.search(text)
            if match:
                start = int(match.group("start"))
                end = int(match.group("end"))
                return ActionJSON(
                    type="DeleteLineRange",
                    params={
                        "path": active_file.path,
                        "start_line": start,
                        "end_line": end,
                    }
                )
            
            # Replace line
            match = self._replace_line_re.search(text)
            if match:
                line_num = int(match.group("line"))
                content = match.group("text").strip().strip('"\'')
                return ActionJSON(
                    type="ReplaceBlock",
                    params={
                        "path": active_file.path,
                        "start_line": line_num,
                        "end_line": line_num,
                        "text": content,
                    }
                )
            
            # Insert at line (handle both "insert at line N" and "add line N with X")
            match = self._insert_at_line_re.search(text) or self._add_line_re.search(text)
            if match:
                line_num = int(match.group("line"))
                content = match.group("text").strip().strip('"\'')
                return ActionJSON(
                    type="InsertAfterLine",
                    params={
                        "path": active_file.path,
                        "line_number": line_num,
                        "text": content,
                    }
                )
            
            # Append to file
            if self._append_re.search(text):
                content = self.extract_content(text, user_message)
                if content:
                    return ActionJSON(
                        type="InsertAtBottom",
                        params={
                            "path": active_file.path,
                            "text": content,
                        }
                    )
        
        # ============================================================
        # FOLDER OPERATIONS (CHECK BEFORE FILE OPERATIONS)
        # ============================================================
        
        # Create folder (must check before CreateFile to avoid false matches)
        match = self._create_folder_re.search(text)
        if match:
            path = match.group("path")
            return ActionJSON(
                type="CreateFolder",
                params={"path": path}
            )
        
        # Delete folder
        match = self._delete_folder_re.search(text)
        if match:
            path = match.group("path")
            return ActionJSON(
                type="DeleteFolder",
                params={"path": path}
            )
        
        # Move folder
        match = self._move_folder_re.search(text)
        if match:
            path = match.group("path")
            target = match.group("target")
            return ActionJSON(
                type="MoveFolder",
                params={
                    "path": path,
                    "target_folder": target,
                }
            )
        
        # Copy folder
        match = self._copy_folder_re.search(text)
        if match:
            path = match.group("path")
            new_path = match.group("new")
            return ActionJSON(
                type="CopyFolder",
                params={
                    "path": path,
                    "new_path": new_path,
                }
            )
        
        # Rename folder
        match = self._rename_folder_re.search(text)
        if match:
            old_path = match.group("old")
            new_path = match.group("new")
            return ActionJSON(
                type="RenameFile",  # RenameFile works for both files and folders
                params={
                    "old_path": old_path,
                    "new_path": new_path,
                }
            )
        
        # ============================================================
        # FILE OPERATIONS - File-level
        # ============================================================
        
        # Read file
        match = self._read_file_re.search(text)
        if match:
            path = match.group("path")
            return ActionJSON(
                type="ReadFile",
                params={"path": path}
            )
        
        # Delete file
        match = self._delete_file_re.search(text)
        if match:
            path = match.group("path")
            return ActionJSON(
                type="DeleteFile",
                params={"path": path}
            )
        
        # Create file (require explicit "file" keyword or check it's not a folder)
        match = self._create_file_re.search(text)
        if match:
            path = match.group("path")
            content = self.extract_content(text, user_message) or ""
            return ActionJSON(
                type="CreateFile",
                params={
                    "path": path,
                    "content": content,
                }
            )
        
        # Create file (simple form - only if no folder keywords present)
        match = self._create_file_simple_re.search(text)
        if match:
            # Check if this is actually a folder command
            if not re.search(r"\bfolder\b|\bdirectory\b|\bdir\b", text, re.IGNORECASE):
                path = match.group("path")
                content = self.extract_content(text, user_message) or ""
                return ActionJSON(
                    type="CreateFile",
                    params={
                        "path": path,
                        "content": content,
                    }
                )
        
        # Rename file
        match = self._rename_file_re.search(text)
        if match:
            old_path = match.group("old")
            new_path = match.group("new")
            return ActionJSON(
                type="RenameFile",
                params={
                    "old_path": old_path,
                    "new_path": new_path,
                }
            )
        
        # Move file
        match = self._move_file_re.search(text)
        if match:
            path = match.group("path")
            target = match.group("target")
            return ActionJSON(
                type="MoveFile",
                params={
                    "path": path,
                    "target_folder": target,
                }
            )
        
        # Copy file
        match = self._copy_file_re.search(text)
        if match:
            path = match.group("path")
            new_path = match.group("new")
            return ActionJSON(
                type="CopyFile",
                params={
                    "path": path,
                    "new_path": new_path,
                }
            )
        
        # Open file
        match = self._open_file_re.search(text)
        if match:
            path = match.group("path")
            return ActionJSON(
                type="OpenFile",
                params={"path": path}
            )
        
        # Search files
        match = self._search_files_re.search(text)
        if match:
            pattern = match.group("pattern")
            return ActionJSON(
                type="RunShellCommand",
                params={"command": f"grep -r '{pattern}' ."}
            )
        
        # Find files by name
        match = self._find_files_re.search(text)
        if match:
            name = match.group("name")
            return ActionJSON(
                type="RunShellCommand",
                params={"command": f"find . -name '{name}'"}
            )
        
        # ============================================================
        # GIT OPERATIONS
        # ============================================================
        
        # Git init
        if self._git_init_re.search(text):
            return ActionJSON(type="GitInit", params={})
        
        # Git status (routed to RunGitCommand for display)
        if self._git_status_re.search(text):
            return ActionJSON(type="RunGitCommand", params={"command": "status"})
        
        # Git log (routed to RunGitCommand for display)
        if self._git_log_re.search(text):
            return ActionJSON(type="RunGitCommand", params={"command": "log"})
        
        # Git add
        match = self._git_add_re.search(text)
        if match:
            path = match.group("path")
            if path in (".", "all"):
                path = "."
            return ActionJSON(
                type="GitAdd",
                params={"path": path}
            )
        
        # Git commit
        match = self._git_commit_re.search(text) or self._git_commit_simple_re.search(text)
        if match:
            message = match.group("msg")
            return ActionJSON(
                type="GitCommit",
                params={"message": message}
            )
        
        # Git branch
        match = self._git_branch_re.search(text)
        if match:
            name = match.group("name")
            return ActionJSON(
                type="GitBranch",
                params={"name": name}
            )
        
        # Git checkout
        match = self._git_checkout_re.search(text)
        if match:
            branch = match.group("branch")
            return ActionJSON(
                type="GitCheckout",
                params={"branch": branch}
            )
        
        # Git merge
        match = self._git_merge_re.search(text)
        if match:
            branch = match.group("branch")
            return ActionJSON(
                type="GitMerge",
                params={"branch": branch}
            )
        
        # Git push
        match = self._git_push_re.search(text)
        if match:
            branch = match.group("branch")
            params = {}
            if branch:
                params["branch"] = branch
            return ActionJSON(
                type="GitPush",
                params=params
            )
        
        # Git pull
        match = self._git_pull_re.search(text)
        if match:
            branch = match.group("branch")
            params = {}
            if branch:
                params["branch"] = branch
            return ActionJSON(
                type="GitPull",
                params=params
            )
        
        # Git remote add
        match = self._git_remote_re.search(text)
        if match:
            name = match.group("name")
            url = match.group("url")
            return ActionJSON(
                type="GitRemote",
                params={
                    "name": name,
                    "url": url
                }
            )
        
        # Git graph (UI command - handled by CLI/UI layer)
        # Note: This is a UI panel command, not a supervisor action
        if self._git_graph_re.search(text) or self._git_graph_words_re.search(text):
            # Return a special marker that the CLI can handle
            # The CLI will route this to :git-graph command
            return ActionJSON(type="ShowGitGraph", params={})
        
        # ============================================================
        # CHANGE DIRECTORY OPERATIONS
        # ============================================================
        
        # Handle "create X folder and go to it" - extract folder name for cd
        match = self._cd_contextual_re.search(text)
        if match:
            folder_name = match.group("name")
            # Return a compound action marker - executor will handle both
            return ActionJSON(
                type="CreateFolderAndCD",
                params={"path": folder_name}
            )
        
        # Change directory
        match = self._cd_re.search(text)
        if match:
            path = match.group("path")
            # Handle "it", "there" as contextual references
            if path.lower() in ("it", "there"):
                # Try to extract from context (e.g., "create demo folder and go to it")
                folder_match = re.search(r"(?:create|make)\s+(?P<name>[^\s/]+)\s+(?:folder|directory)", text, re.IGNORECASE)
                if folder_match:
                    path = folder_match.group("name")
            return ActionJSON(
                type="ChangeDirectory",
                params={"path": path}
            )
        
        # Change directory up (cd ..)
        if self._cd_up_re.search(text):
            return ActionJSON(
                type="ChangeDirectory",
                params={"path": ".."}
            )
        
        # List directory (natural language)
        match = self._list_dir_re.search(text)
        if match:
            path = match.group("path") or "."
            return ActionJSON(
                type="RunShellCommand",
                params={"command": f"ls {path}"}
            )
        
        # Debug/run script
        match = self._debug_re.search(text) or self._run_script_re.search(text)
        if match:
            path = match.group("path")
            # Determine script type and run appropriately
            if path.endswith((".py", ".py3")):
                return ActionJSON(
                    type="RunShellCommand",
                    params={"command": f"python3 {path}"}
                )
            elif path.endswith((".js", ".mjs")):
                return ActionJSON(
                    type="RunShellCommand",
                    params={"command": f"node {path}"}
                )
            elif path.endswith((".sh", ".bash")):
                return ActionJSON(
                    type="RunShellCommand",
                    params={"command": f"bash {path}"}
                )
            else:
                # Generic execution
                return ActionJSON(
                    type="RunShellCommand",
                    params={"command": path}
                )
        
        # ============================================================
        # GITHUB OPERATIONS
        # ============================================================
        
        # Create GitHub repo
        match = self._github_repo_re.search(text)
        if match:
            name = match.group("name")
            private = match.group("private") and match.group("private").lower() == "private"
            return ActionJSON(
                type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": private,
                }
            )
        
        # Create GitHub issue
        match = self._github_issue_re.search(text) or self._github_issue_simple_re.search(text)
        if match:
            title = match.group("title")
            body = match.group("body") if "body" in match.groupdict() else ""
            return ActionJSON(
                type="GitHubCreateIssue",
                params={
                    "title": title,
                    "body": body,
                }
            )
        
        # Create GitHub PR
        match = self._github_pr_re.search(text)
        if match:
            title = match.group("title")
            # Extract head/base if present
            head_match = re.search(r"\bhead\s+([^\s]+)", text, re.IGNORECASE)
            base_match = re.search(r"\bbase\s+([^\s]+)", text, re.IGNORECASE)
            params = {"title": title}
            if head_match:
                params["head"] = head_match.group(1)
            if base_match:
                params["base"] = base_match.group(1)
            return ActionJSON(
                type="GitHubCreatePR",
                params=params
            )
        
        # ============================================================
        # FALLBACK: If active_file exists, try to infer file operation
        # ============================================================
        if active_file:
            # If user says something vague about the active file, default to append
            vague_patterns = [
                r"\b(add|insert|write|append)\s+(.+?)(?:\s+in\s+|\s*$)",
                r"\b(update|change|modify)\s+(?:this|the\s+file)",
            ]
            for pattern in vague_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    content = self.extract_content(text, user_message)
                    if content:
                        return ActionJSON(
                            type="InsertAtBottom",
                            params={
                                "path": active_file.path,
                                "text": content,
                            }
                        )
        
        # If we can't infer anything, return None (caller should handle)
        return None
    
    def to_json_string(self, action: ActionJSON) -> str:
        """Convert action to JSON string format."""
        return json.dumps({
            "type": action.type,
            "params": action.params
        }, indent=2)
    
    def to_dict(self, action: ActionJSON) -> Dict[str, Any]:
        """Convert action to dictionary format."""
        return {
            "type": action.type,
            "params": action.params
        }

