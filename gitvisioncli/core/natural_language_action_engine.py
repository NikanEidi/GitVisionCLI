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

# Import file handlers
from gitvisioncli.core.file_handlers import (
    InsertHandler,
    ReplaceHandler,
    DeleteHandler,
    AppendHandler,
)


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
    
    def __init__(self, use_modular_handlers: bool = True):
        """
        Initialize the natural language action engine.
        
        Args:
            use_modular_handlers: If True, use the new modular handler system
                                 (default: True for better extensibility)
        """
        # Precompile regex patterns for performance
        self._init_patterns()
        
        # Initialize file operation handlers (legacy)
        self.file_handlers = [
            DeleteHandler(),    # Check delete first (most specific)
            ReplaceHandler(),   # Then replace
            InsertHandler(),    # Then insert
            AppendHandler(),    # Finally append (least specific)
        ]
        
        # Initialize modular command router (new system)
        self.use_modular_handlers = use_modular_handlers
        if use_modular_handlers:
            try:
                from gitvisioncli.core.command_router import CommandRouter
                self.command_router = CommandRouter()
            except ImportError:
                # Fallback if modular system not available
                self.use_modular_handlers = False
                self.command_router = None
        else:
            self.command_router = None
    
    def _init_patterns(self):
        """Initialize all regex patterns for action detection."""
        
        # File operations - line-based
        # Support "remove", "delete", "rm", "dl", "erase", "drop", "clear"
        self._remove_line_re = re.compile(
            r"\b(remove|delete|rm|dl|erase|drop|clear)\s+line\s*(?P<line>\d+)\b", re.IGNORECASE
        )
        # Also match broken grammar: "rm 10", "delete line1", "remove ln5"
        self._remove_line_broken_re = re.compile(
            r"\b(?:rm|dl)\s+(?P<line>\d+)(?:\s|$)", re.IGNORECASE
        )
        # Support "remove lines", "delete lines", "remove line range"
        self._remove_lines_re = re.compile(
            r"\b(remove|delete|rm|dl|erase|drop|clear)\s+lines?\s+(?P<start>\d+)\s*-\s*(?P<end>\d+)\b", re.IGNORECASE
        )
        self._remove_lines_to_re = re.compile(
            r"\b(remove|delete|rm|dl|erase|drop|clear)\s+lines?\s+(?P<start>\d+)\s+to\s+(?P<end>\d+)\b", re.IGNORECASE
        )
        # Replace line - support "replace", "update", "change", "edit", "modify", "set"
        self._replace_line_re = re.compile(
            r"\b(replace|update|change|edit|modify|set)\s+line\s*(?P<line>\d+)\s+(?:with|to|by)\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        # Replace lines - support "replace", "update", "change", "edit", "modify"
        self._replace_lines_re = re.compile(
            r"\b(replace|update|change|edit|modify|set)\s+lines?\s+(?P<start>\d+)\s*-\s*(?P<end>\d+)\s+(?:with|to|by)\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE | re.DOTALL
        )
        # Insert at line - support "insert", "add", "write", "put", "place"
        self._insert_at_line_re = re.compile(
            r"\b(insert|add|write|put|place)\s+(?:at|on|in)\s+line\s*(?P<line>\d+)\s*:?\s*(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE | re.DOTALL
        )
        # Add line patterns - support "add", "insert", "write", "put"
        self._add_line_re = re.compile(
            r"\b(add|insert|write|put)\s+(?P<text>.+?)\s+in\s+line\s*(?P<line>\d+)\b", re.IGNORECASE
        )
        self._add_line_with_re = re.compile(
            r"\b(add|insert|write|put)\s+line\s*(?P<line>\d+)\s+with\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        self._edit_line_re = re.compile(
            r"\b(edit|change|update)\s+line\s*(?P<line>\d+)\s+with\s+(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE
        )
        # Insert before/after line patterns - support "insert", "add", "write", "put", "place"
        self._insert_before_line_re = re.compile(
            r"\b(insert|add|write|put|place)\s+(?:before|above|prior\s+to)\s+line\s*(?P<line>\d+)\s*:?\s*(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE | re.DOTALL
        )
        self._insert_after_line_re = re.compile(
            r"\b(insert|add|write|put|place)\s+(?:after|below|following)\s+line\s*(?P<line>\d+)\s*:?\s*(?P<text>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE | re.DOTALL
        )
        # Append - support "add", "append", "insert", "write", "put" at bottom/end
        self._append_re = re.compile(
            r"\b(add|append|insert|write|put)\s+(?:comment|text|code|line)?\s*(?:at|to)?\s*(?:the\s+)?(?:bottom|end|tail)\b", re.IGNORECASE
        )
        
        # File operations - file-level
        # Support quoted paths for files with spaces: "read 'my file.txt'" or 'read "my file.txt"'
        self._read_file_re = re.compile(
            r"\b(?:read|show|display|cat|view|see|print|list)\s+(?:file\s+)?(?P<path>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        self._delete_file_re = re.compile(
            r"\b(?:delete|remove|rm|erase|trash)\s+(?:file\s+)?(?P<path>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        # Create file - require explicit "file" keyword to avoid matching folder operations
        # Also support "new file", "make file", "generate file", "write file"
        # Support quoted paths: "create file 'my file.txt'" or 'create file "my file.txt"'
        self._create_file_re = re.compile(
            r"\b(?:create|make|new|generate|write|add)\s+file\s+(?P<path>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        # Also support "create <path>" without "file" but only if no folder keywords follow
        # Also support "make <path>", "new <path>", "generate <path>"
        # Support quoted paths
        self._create_file_simple_re = re.compile(
            r"\b(?:create|make|new|generate|write|add)\s+(?P<path>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        # Rename file - support "rename", "mv", "move", "change name", "rechristen"
        # Support quoted paths: "rename 'old file.txt' to 'new file.txt'"
        self._rename_file_re = re.compile(
            r"\b(?:rename|mv|move|change\s+name|rechristen)\s+(?:file\s+)?(?P<old>(?:['\"][^'\"]+['\"]|[^\s]+))\s+(?:to|as|into)\s+(?P<new>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        # Move file - support "move", "mv", "transfer", "relocate"
        # Support quoted paths
        self._move_file_re = re.compile(
            r"\b(?:move|mv|transfer|relocate)\s+(?:file\s+)?(?P<path>(?:['\"][^'\"]+['\"]|[^\s]+))\s+to\s+(?P<target>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        # Copy file - support "copy", "cp", "duplicate", "clone", "backup"
        # Support quoted paths
        self._copy_file_re = re.compile(
            r"\b(?:copy|cp|duplicate|clone|backup)\s+(?:file\s+)?(?P<path>(?:['\"][^'\"]+['\"]|[^\s]+))\s+(?:to|as|into)\s+(?P<new>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        self._open_file_re = re.compile(
            r"\b(?:open|edit|nano|code|view|show|load)\s+(?:file\s+)?(?P<path>[^\s]+)\b", re.IGNORECASE
        )
        
        # Search operations - support "search", "find", "grep", "locate", "look for"
        # Support quoted search patterns: "search for 'hello world'"
        self._search_files_re = re.compile(
            r"\b(?:search|find|grep|locate|look\s+for)\s+(?:for|files?|text)?\s*(?P<pattern>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
        )
        # Find files by name - support quoted names for files with spaces
        self._find_files_re = re.compile(
            r"\b(?:find|locate|search\s+for)\s+(?:files?\s+)?(?:named|called|with\s+name)\s+(?P<name>(?:['\"][^'\"]+['\"]|[^\s]+))\b", re.IGNORECASE
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
        
        # Git operations - comprehensive natural language support
        # Git init - support "initialize git", "init git", "git init", "set up git"
        # CRITICAL FIX: Exclude "create git repo" when followed by project name or privacy setting
        # to prevent false positives with GitHub repo creation commands
        self._git_init_re = re.compile(
            r"\b(?:git\s+init|initialize\s+git|init\s+git|set\s+up\s+git|start\s+git\s+repository|create\s+git\s+repo(?!\s+[^\s]+\s+(?:private|public)))\b", 
            re.IGNORECASE
        )
        # CRITICAL FIX: Require explicit "git" prefix for status/log to avoid false positives
        # from common English words like "What's the status?" or "check the log file"
        self._git_status_re = re.compile(r"\bgit\s+status\b", re.IGNORECASE)
        self._git_log_re = re.compile(r"\bgit\s+log\b", re.IGNORECASE)
        # Git add - support "add files", "stage files", "add all", "stage all", "add everything"
        # Also support "stash", "add .", "stage .", "add all files", "stage everything"
        # CRITICAL FIX: Put [^\s]+ before keyword patterns to prevent files like "all_files.txt"
        # from matching just "all" instead of the full filename
        self._git_add_re = re.compile(
            r"\b(?:git\s+)?(?:add|stage|stash)\s+(?P<path>[^\s]+|\.|all|everything|files?|changes?|staged?)\b", 
            re.IGNORECASE
        )
        # Git commit - support "commit changes", "commit with message", "save changes", "commit all"
        # Also support "commit -m", "save with message", "save changes with"
        self._git_commit_re = re.compile(
            r"\b(?:git\s+)?(?:commit|save\s+changes|save)\s+(?:all\s+)?(?:with\s+)?(?:message\s+)?['\"](?P<msg>[^'\"]+)['\"]", 
            re.IGNORECASE
        )
        self._git_commit_simple_re = re.compile(
            r"\b(?:git\s+)?(?:commit|save\s+changes|save)\s+(?:-m\s+)?['\"](?P<msg>[^'\"]+)['\"]", 
            re.IGNORECASE
        )
        # Git commit without message - support "commit changes", "commit all", "save"
        self._git_commit_no_msg_re = re.compile(
            r"\b(?:git\s+)?(?:commit|save)\s+(?:all\s+)?(?:changes?|files?)?\b(?!\s+['\"])", 
            re.IGNORECASE
        )
        # Git branch - support "create branch", "new branch", "make branch", "branch"
        self._git_branch_re = re.compile(
            r"\b(?:git\s+)?(?:create\s+)?(?:new\s+)?(?:make\s+)?branch\s+(?P<name>[^\s]+)\b", re.IGNORECASE
        )
        # Git checkout - support "checkout", "switch to", "switch", "go to branch"
        self._git_checkout_re = re.compile(
            r"\b(?:git\s+)?(?:switch\s+(?:to\s+)?|checkout\s+|change\s+to\s+branch\s+)(?:branch\s+)?(?P<branch>[^\s]+)\b", re.IGNORECASE
        )
        # Git checkout with -b flag (create and switch)
        self._git_checkout_b_re = re.compile(
            r"\b(?:git\s+)?checkout\s+-b\s+(?P<branch>[^\s]+)\b", re.IGNORECASE
        )
        # Git merge - support "merge branch", "merge into", "combine branches"
        self._git_merge_re = re.compile(
            r"\b(?:git\s+)?(?:merge|combine)\s+(?:branch\s+)?(?:into\s+)?(?P<branch>[^\s]+)\b", re.IGNORECASE
        )
        # Git push - support "push", "push all files", "push to github", "push everything", "upload to github"
        # Also handle "push -u origin main", "push origin main", "upload", "sync to github"
        self._git_push_re = re.compile(
            r"\b(?:git\s+)?(?:push|upload|sync\s+to)\s*(?:all\s+)?(?:files?\s+and\s+folders?|everything|changes?)?\s*(?:to\s+(?:github|origin|remote))?\s*(?:-u\s+)?(?:origin\s+)?(?P<branch>[^\s]*)\b", 
            re.IGNORECASE
        )
        # Git pull - support "pull changes", "sync from github", "get latest"
        # CRITICAL FIX: "get latest" requires explicit Git context to avoid false positives
        # from common English phrases like "get latest posts" or "get latest data"
        # "get latest" must have either: "git" prefix OR "from github/origin/remote" after it
        # Note: Python regex doesn't allow same named group in alternatives, so we use branch and branch2
        # and handle both in the code
        self._git_pull_re = re.compile(
            r"\b(?:git\s+)?(?:pull|sync)\s*(?:from\s+(?:github|origin|remote))?\s*(?:origin\s+)?(?P<branch>[^\s]*)\b|\b(?:git\s+get\s+latest|get\s+latest\s+from\s+(?:github|origin|remote))\s*(?:origin\s+)?(?P<branch2>[^\s]*)\b", 
            re.IGNORECASE
        )
        # Git remote operations - comprehensive support
        # Remote add - support "add remote", "set remote", "configure remote"
        self._git_remote_add_re = re.compile(
            r"\b(?:git\s+)?(?:remote\s+)?(?:add|set|configure)\s+(?:remote\s+)?(?P<name>[^\s]+)\s+(?:to\s+)?(?P<url>[^\s]+)\b", re.IGNORECASE
        )
        # Also support: "git remote add origin <url>"
        self._git_remote_add_explicit_re = re.compile(
            r"\b(?:git\s+)?remote\s+add\s+(?P<name>[^\s]+)\s+(?P<url>[^\s]+)\b", re.IGNORECASE
        )
        # Remote remove/rm - support "remove remote", "delete remote", "rm remote"
        self._git_remote_remove_re = re.compile(
            r"\b(?:git\s+)?(?:remote\s+)?(?:remove|rm|delete)\s+(?:remote\s+)?(?P<name>[^\s]+)\b", re.IGNORECASE
        )
        # Remote list/show all - support "list remotes", "show remotes", "list all remotes"
        self._git_remote_list_re = re.compile(
            r"\b(?:git\s+)?(?:remote\s+)?(?:list|show\s+all|show\s+remotes|list\s+remotes|list\s+all\s+remotes|-v)\b", re.IGNORECASE
        )
        # Remote rename - support "rename remote", "change remote name"
        self._git_remote_rename_re = re.compile(
            r"\b(?:git\s+)?(?:remote\s+)?(?:rename|change\s+name)\s+(?:remote\s+)?(?P<old>[^\s]+)\s+(?:to\s+)?(?P<new>[^\s]+)\b", re.IGNORECASE
        )
        # Remote set-url - support "update remote url", "change remote url"
        self._git_remote_set_url_re = re.compile(
            r"\b(?:git\s+)?(?:remote\s+)?(?:set-url|update\s+url|change\s+url)\s+(?:remote\s+)?(?P<name>[^\s]+)\s+(?:to\s+)?(?P<url>[^\s]+)\b", re.IGNORECASE
        )
        # Remote show (specific remote) - support "show remote", "remote info"
        self._git_remote_show_re = re.compile(
            r"\b(?:git\s+)?(?:remote\s+)?(?:show|info)\s+(?:remote\s+)?(?P<name>[^\s]+)\b", re.IGNORECASE
        )
        # Legacy: git remote add (backward compatibility)
        self._git_remote_re = self._git_remote_add_explicit_re
        self._git_graph_re = re.compile(
            r"\b(?:git\s+)?(?:show\s+)?(?:graph|log\s+--graph)\b", re.IGNORECASE
        )
        # Also match "git graph" as two words
        self._git_graph_words_re = re.compile(
            r"\bgit\s+graph\b", re.IGNORECASE
        )
        
        # GitHub operations - comprehensive natural language support
        # Support: "create private repository call it demo", "create github repo named demo private", 
        # "make a private repo called demo", "create repo demo private"
        # CRITICAL FIX: Also support "create git repo <name> <private>" to distinguish from local git init
        self._github_repo_re = re.compile(
            r"\b(?:create|make|set\s+up)\s+(?:a\s+)?(?:github\s+|git\s+)?(?:repo|repository)\s+(?:named\s+|called\s+|call\s+it\s+)?(?P<name>[^\s]+)\s+(?P<private>private|public)\b", 
            re.IGNORECASE
        )
        # Also support: "create private repository demo", "create demo repository private"
        self._github_repo_alt_re = re.compile(
            r"\b(?:create|make)\s+(?:a\s+)?(?P<private>private|public)\s+(?:github\s+|git\s+)?(?:repo|repository)\s+(?:named\s+|called\s+|call\s+it\s+)?(?P<name>[^\s]+)\b", 
            re.IGNORECASE
        )
        # Support: "create github repo <name>" (without privacy setting, defaults to public)
        self._github_repo_simple_re = re.compile(
            r"\b(?:create|make|set\s+up)\s+(?:a\s+)?(?:github\s+)(?:repo|repository)\s+(?:named\s+|called\s+|call\s+it\s+)?(?P<name>[^\s]+)\b(?!\s+(?:private|public))", 
            re.IGNORECASE
        )
        # CRITICAL FIX: Support "create git repo <name>" (without privacy) as GitHub repo
        # This distinguishes from "create git repo" (no name) which is local git init
        self._github_repo_git_name_re = re.compile(
            r"\bcreate\s+git\s+repo\s+(?P<name>[^\s]+)\b(?!\s+(?:private|public))", 
            re.IGNORECASE
        )
        # GitHub issue with body - support quoted titles and bodies
        # Also support "with description" instead of "with body"
        self._github_issue_re = re.compile(
            r"\b(?:create\s+)?(?:github\s+)?issue\s+['\"](?P<title>[^'\"]+)['\"]\s+(?:with\s+)?(?:body|description)\s+['\"](?P<body>[^'\"]+)['\"]", re.IGNORECASE
        )
        # GitHub issue - support "create issue", "new issue", "make issue", "open issue"
        # Also support "file issue", "report issue", "add issue"
        self._github_issue_simple_re = re.compile(
            r"\b(?:create|new|make|open|add|file|report)\s+(?:github\s+)?issue\s+['\"](?P<title>[^'\"]+)['\"]", re.IGNORECASE
        )
        # GitHub PR - support "create pr", "new pr", "make pr", "open pr", "create pull request"
        # Also support "file pr", "submit pr", "add pr"
        self._github_pr_re = re.compile(
            r"\b(?:create|new|make|open|add|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+['\"](?P<title>[^'\"]+)['\"]", re.IGNORECASE
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
        # Use DOTALL flag to match newlines, and capture everything after "with" until end
        self._with_content_re = re.compile(
            r"\bwith\s+(?P<content>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE | re.DOTALL
        )
        self._colon_content_re = re.compile(
            r":\s*(?P<content>.+?)(?:\s+in\s+|\s*$)", re.IGNORECASE | re.DOTALL
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
        """Extract content from instruction text. Handles both single-line and multi-line content."""
        # For multi-line input, extract everything after "with" (including newlines)
        if "\n" in text:
            # Split on "with" and take everything after it
            # This handles: "create app.py with\ncontent here\nmore content"
            with_match = re.search(r"\bwith\s+(.+)", text, re.IGNORECASE | re.DOTALL)
            if with_match:
                content = with_match.group(1).strip()
                # Remove any trailing "in <file>" patterns that might be at the end
                content = re.sub(r"\s+in\s+[\w./]+\s*$", "", content, flags=re.IGNORECASE)
                return content.strip()
            
            # Also try colon pattern for multi-line
            colon_match = re.search(r":\s+(.+)", text, re.IGNORECASE | re.DOTALL)
            if colon_match:
                content = colon_match.group(1).strip()
                content = re.sub(r"\s+in\s+[\w./]+\s*$", "", content, flags=re.IGNORECASE)
                return content.strip()
        
        # For single-line input, use the original patterns
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
        # Use modular handlers for powerful, flexible parsing
        # ============================================================
        if active_file:
            # Try modular command router first (if enabled)
            if self.use_modular_handlers and self.command_router:
                result = self.command_router.route(user_message, active_file)
                if result:
                    return result
            
            # Try all file handlers and pick the best match
            best_handler = None
            best_confidence = 0.0
            best_result = None
            
            for handler in self.file_handlers:
                can_handle_confidence = handler.can_handle(text, active_file.path)
                # Only try parsing if handler can handle it (confidence > 0)
                if can_handle_confidence > 0:
                    result = handler.parse(text, active_file.path, user_message)
                    # Compare parse confidence against best parse confidence
                    if result.success and result.confidence > best_confidence:
                        best_handler = handler
                        best_confidence = result.confidence
                        best_result = result
            
            # If we found a good match, use it
            if best_result and best_confidence >= 0.7:
                return ActionJSON(
                    type=best_result.action_type,
                    params=best_result.params
                )
            
            # Fallback to legacy regex patterns for backward compatibility
            # (Keep existing patterns as fallback)
            # Delete single line (also handle broken grammar: "rm 10", "delete line1", "remove ln5", "delete 5", "remove 5")
            match = self._remove_line_re.search(text) or self._remove_line_broken_re.search(text) or self._broken_line_re.search(text)
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
            
            # Replace line range (check before single line replace)
            match = self._replace_lines_re.search(text)
            if match:
                start = int(match.group("start"))
                end = int(match.group("end"))
                content = match.group("text").strip()
                # Only strip outer quotes if content doesn't contain newlines
                if "\n" not in content:
                    content = content.strip('"\'')
                # Preserve multi-line content as-is
                return ActionJSON(
                    type="ReplaceBlock",
                    params={
                        "path": active_file.path,
                        "start_line": start,
                        "end_line": end,
                        "text": content,
                    }
                )
            
            # Replace single line
            match = self._replace_line_re.search(text)
            if match:
                line_num = int(match.group("line"))
                content = match.group("text").strip()
                # Only strip outer quotes if content doesn't contain newlines
                if "\n" not in content:
                    content = content.strip('"\'')
                # Preserve multi-line content as-is
                return ActionJSON(
                    type="ReplaceBlock",
                    params={
                        "path": active_file.path,
                        "start_line": line_num,
                        "end_line": line_num,
                        "text": content,
                    }
                )
            
            # Insert before line (check before "at line" to avoid conflicts)
            match = self._insert_before_line_re.search(text)
            if match:
                line_num = int(match.group("line"))
                content = match.group("text").strip()
                # Only strip outer quotes if content doesn't contain newlines
                if "\n" not in content:
                    content = content.strip('"\'')
                # Preserve multi-line content as-is
                return ActionJSON(
                    type="InsertBeforeLine",
                    params={
                        "path": active_file.path,
                        "line_number": line_num,
                        "text": content,
                    }
                )
            
            # Insert after line (check before "at line" to avoid conflicts)
            match = self._insert_after_line_re.search(text)
            if match:
                line_num = int(match.group("line"))
                content = match.group("text").strip()
                # Only strip outer quotes if content doesn't contain newlines
                if "\n" not in content:
                    content = content.strip('"\'')
                # Preserve multi-line content as-is
                return ActionJSON(
                    type="InsertAfterLine",
                    params={
                        "path": active_file.path,
                        "line_number": line_num,
                        "text": content,
                    }
                )
            
            # Insert at line (handle "insert at line N", "add line N with X", and "add X in line N")
            # Also handle multi-line content from :ml mode
            match = self._insert_at_line_re.search(text) or self._add_line_re.search(text) or self._add_line_with_re.search(text)
            if match:
                line_num = int(match.group("line"))
                content = match.group("text").strip()
                # Only strip outer quotes if content doesn't contain newlines
                if "\n" not in content:
                    content = content.strip('"\'')
                # Preserve multi-line content as-is
                return ActionJSON(
                    type="InsertAfterLine",
                    params={
                        "path": active_file.path,
                        "line_number": line_num,
                        "text": content,
                    }
                )
            
            # Append to file - handle "add X at bottom" or "add X at the bottom"
            if self._append_re.search(text):
                # Extract content after "add/append/insert" and before "at bottom/end"
                # Pattern: "add print('end') at bottom" or "add X at the bottom"
                content_match = re.search(
                    r"\b(add|append|insert)\s+(.+?)\s+(?:at|to)\s+(?:the\s+)?(?:bottom|end)\b",
                    text,
                    re.IGNORECASE | re.DOTALL
                )
                if content_match:
                    content = content_match.group(2).strip()
                    # Only strip outer quotes if content doesn't contain newlines
                    # Preserve quotes that are part of the content (e.g., print("hello"))
                    if "\n" not in content:
                        # Strip only if content starts and ends with matching quotes
                        if (content.startswith('"') and content.endswith('"')) or \
                           (content.startswith("'") and content.endswith("'")):
                            # Check if it's a simple quoted string (no internal quotes)
                            if content.count('"') == 2 or content.count("'") == 2:
                                content = content.strip('"\'')
                    return ActionJSON(
                        type="InsertAtBottom",
                        params={
                            "path": active_file.path,
                            "text": content,
                        }
                    )
                # Fallback to extract_content for other patterns
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
            # Strip quotes if present (for paths with spaces)
            path = path.strip('"\'')
            return ActionJSON(
                type="ReadFile",
                params={"path": path}
            )
        
        # Delete file
        match = self._delete_file_re.search(text)
        if match:
            path = match.group("path")
            # Strip quotes if present (for paths with spaces)
            path = path.strip('"\'')
            return ActionJSON(
                type="DeleteFile",
                params={"path": path}
            )
        
        # Create file (require explicit "file" keyword or check it's not a folder)
        match = self._create_file_re.search(text)
        if match:
            path = match.group("path")
            # Strip quotes if present (for paths with spaces)
            path = path.strip('"\'')
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
                # Strip quotes if present (for paths with spaces)
                path = path.strip('"\'')
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
            # Strip quotes if present (for paths with spaces)
            old_path = old_path.strip('"\'')
            new_path = new_path.strip('"\'')
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
            # Strip quotes if present (for paths with spaces)
            path = path.strip('"\'')
            target = target.strip('"\'')
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
            # Strip quotes if present (for paths with spaces)
            path = path.strip('"\'')
            new_path = new_path.strip('"\'')
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
            # Strip quotes if present (for paths with spaces)
            path = path.strip('"\'')
            return ActionJSON(
                type="OpenFile",
                params={"path": path}
            )
        
        # Search files
        match = self._search_files_re.search(text)
        if match:
            pattern = match.group("pattern")
            # Strip quotes if present
            pattern = pattern.strip('"\'')
            return ActionJSON(
                type="RunShellCommand",
                params={"command": f"grep -r '{pattern}' ."}
            )
        
        # Find files by name
        match = self._find_files_re.search(text)
        if match:
            name = match.group("name")
            # Strip quotes if present
            name = name.strip('"\'')
            return ActionJSON(
                type="RunShellCommand",
                params={"command": f"find . -name '{name}'"}
            )
        
        # ============================================================
        # GIT OPERATIONS
        # ============================================================
        
        # Git init
        # CRITICAL FIX: Check for GitHub repo creation first to prevent false positives
        # "create git repo my-project private" should be GitHub, not git init
        github_repo_check = (self._github_repo_re.search(text) or 
                             self._github_repo_alt_re.search(text) or 
                             self._github_repo_simple_re.search(text) or
                             self._github_repo_git_name_re.search(text))
        if not github_repo_check and self._git_init_re.search(text):
            return ActionJSON(type="GitInit", params={})
        
        # Git status (routed to RunGitCommand for display)
        # Also support "check status", "show status", "git state"
        if self._git_status_re.search(text) or re.search(r"\b(?:check|show|view)\s+git\s+status\b", text, re.IGNORECASE):
            return ActionJSON(type="RunGitCommand", params={"command": "status"})
        
        # Git log (routed to RunGitCommand for display)
        # Also support "show history", "view commits", "show log"
        if self._git_log_re.search(text) or re.search(r"\b(?:show|view|see)\s+(?:git\s+)?(?:history|commits|log)\b", text, re.IGNORECASE):
            return ActionJSON(type="RunGitCommand", params={"command": "log"})
        
        # Git add
        match = self._git_add_re.search(text)
        if match:
            path = match.group("path")
            # Normalize "all", "everything", "files", "changes" to "." for staging all
            if path.lower() in (".", "all", "everything", "files", "file", "changes", "change"):
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
        
        # Git commit without message - use default message
        if self._git_commit_no_msg_re.search(text):
            return ActionJSON(
                type="GitCommit",
                params={"message": "Update files"}
            )
        
        # Git branch
        match = self._git_branch_re.search(text)
        if match:
            name = match.group("name")
            return ActionJSON(
                type="GitBranch",
                params={"name": name}
            )
        
        # Git checkout with -b flag (create and switch) - check this first
        match = self._git_checkout_b_re.search(text)
        if match:
            branch = match.group("branch")
            return ActionJSON(
                type="GitCheckout",
                params={"branch": branch, "create_new": True}
            )
        
        # Git checkout - also handle "go to <branch>" for branch switching
        match = self._git_checkout_re.search(text)
        if match:
            branch = match.group("branch")
            return ActionJSON(
                type="GitCheckout",
                params={"branch": branch}
            )
        
        # Handle "go to <branch>" for git branch switching (check before directory change)
        # This pattern should be checked before the general "go to" directory change
        go_to_match = re.search(r"\bgo\s+to\s+(?P<branch>[^\s]+)\b", text, re.IGNORECASE)
        if go_to_match:
            # Check if this looks like a branch name (alphanumeric, hyphens, underscores)
            # and if we're likely in a git context (user said "go to feature", "go to main", etc.)
            branch_name = go_to_match.group("branch")
            # Common branch name patterns
            if re.match(r"^[a-zA-Z0-9_-]+$", branch_name) and branch_name not in ["..", ".", "/"]:
                # Check if it's not a clear directory path (no slashes, not "src", "home", etc.)
                # This is a heuristic - if it looks like a branch name, treat it as git checkout
                if branch_name.lower() not in ["src", "home", "tmp", "var", "usr", "etc", "bin"]:
                    return ActionJSON(
                        type="GitCheckout",
                        params={"branch": branch_name}
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
            # CRITICAL FIX: Handle both capture group names (branch and branch2)
            # since Python regex doesn't allow same named group in alternatives
            branch = match.group("branch") if "branch" in match.groupdict() and match.group("branch") else None
            branch2 = match.group("branch2") if "branch2" in match.groupdict() and match.group("branch2") else None
            branch = branch or branch2 or ""
            params = {}
            if branch:
                params["branch"] = branch
            return ActionJSON(
                type="GitPull",
                params=params
            )
        
        # Git remote operations - check in order of specificity
        # Remote remove/rm (check before add to avoid false matches)
        match = self._git_remote_remove_re.search(text)
        if match:
            name = match.group("name")
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "remove",
                    "name": name
                }
            )
        
        # Remote rename
        match = self._git_remote_rename_re.search(text)
        if match:
            old_name = match.group("old")
            new_name = match.group("new")
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "rename",
                    "old_name": old_name,
                    "new_name": new_name
                }
            )
        
        # Remote set-url
        match = self._git_remote_set_url_re.search(text)
        if match:
            name = match.group("name")
            url = match.group("url")
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "set-url",
                    "name": name,
                    "url": url
                }
            )
        
        # Remote list/show all (check BEFORE show to avoid false matches)
        # This must come before show to prevent "show remotes" from matching as show operation
        match = self._git_remote_list_re.search(text)
        if match:
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "list"
                }
            )
        
        # Remote show (specific remote) - check AFTER list to avoid false positives
        # Pattern is more restrictive to exclude "remotes" and "all" as remote names
        match = self._git_remote_show_re.search(text)
        if match:
            name = match.group("name")
            # Exclude common list keywords that might be captured as remote names
            if name.lower() in ("remotes", "all"):
                # This was likely meant to be a list operation, but we already checked that
                # Return an error action instead of silently skipping
                return ActionJSON(
                    type="GitRemote",
                    params={
                        "operation": "show",
                        "name": name,
                        "error": f"'{name}' is not a valid remote name. Use 'list' to see all remotes."
                    }
                )
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "show",
                    "name": name
                }
            )
        
        # Remote add (default operation) - try explicit pattern first
        match = self._git_remote_add_explicit_re.search(text)
        if match:
            name = match.group("name")
            url = match.group("url")
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "add",
                    "name": name,
                    "url": url
                }
            )
        
        # Try general add pattern
        match = self._git_remote_add_re.search(text)
        if match:
            name = match.group("name")
            url = match.group("url")
            return ActionJSON(
                type="GitRemote",
                params={
                    "operation": "add",
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
        
        # Create GitHub repo - try all patterns
        # CRITICAL FIX: Check GitHub patterns first to prevent false positives with git init
        match = (self._github_repo_re.search(text) or 
                 self._github_repo_alt_re.search(text) or 
                 self._github_repo_simple_re.search(text) or
                 self._github_repo_git_name_re.search(text))
        if match:
            name = match.group("name")
            # Privacy setting may not be present in simple/git_name patterns
            private_str = match.group("private") if "private" in match.groupdict() else None
            is_private = private_str and private_str.lower() == "private" if private_str else False
            return ActionJSON(
                type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": is_private,
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

