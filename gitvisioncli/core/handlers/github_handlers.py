"""
GitHub Operation Handlers

Comprehensive handlers for all GitHub operations.
"""

import re
from typing import Optional, List, Dict, Any
from gitvisioncli.core.handlers.base import BaseHandler, HandlerResult, HandlerPriority


class GitHubHandlerCategory:
    """Category manager for all GitHub operation handlers."""
    
    def __init__(self):
        """Initialize the GitHub handler category."""
        self.handlers = [
            GitHubCreateRepoHandler(),
            GitHubCreateIssueHandler(),
            GitHubCreatePRHandler(),
        ]
    
    def get_handlers(self) -> List[BaseHandler]:
        """Get all GitHub handlers."""
        return self.handlers


class GitHubCreateRepoHandler(BaseHandler):
    """Handler for creating GitHub repositories."""
    
    def __init__(self):
        """Initialize with high priority to match before CreateFileHandler."""
        super().__init__(priority=HandlerPriority.HIGH)
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(
                r'\b(?:create|make)\s+(?:github\s+)?(?:repo|repository)\s+(?P<name>[^\s]+)\s+(?P<private>private|public)\b',
                re.IGNORECASE
            ),
            re.compile(
                r'\b(?:create|make)\s+(?:github\s+)?(?:repo|repository)\s+(?P<name>[^\s]+)\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        text_lower = text.lower()
        # Higher priority - check for "github repo" or "github repository" specifically
        if re.search(r'\b(?:create|make)\s+(?:github\s+)?(?:repo|repository)\b', text_lower):
            return 0.95  # Higher than CreateFileHandler
        # Also match "create repo" and "make repo" (without github keyword) - but only if followed by a name
        if re.search(r'^(?:create|make)\s+repo\s+[\w-]+', text_lower):
            return 0.95
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        text_lower = text.lower()
        match = re.search(
            r'\b(?:create|make)\s+(?:github\s+)?(?:repo|repository)\s+(?P<name>[^\s]+)(?:\s+(?P<private>private|public))?\b',
            text_lower
        )
        if not match:
            # Try "create repo" or "make repo" (without github keyword)
            match = re.search(
                r'^(?:create|make)\s+repo\s+(?P<name>[\w-]+)(?:\s+(?P<private>private|public))?\b',
                text_lower
        )
        if match:
            name = match.group("name")
            private_flag = match.group("private")
            is_private = private_flag == "private" if private_flag else False
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": is_private
                },
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse create github repo")


class GitHubCreateIssueHandler(BaseHandler):
    """Handler for creating GitHub issues."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Match "create github issue 'title'" or "create github issue \"title\""
            re.compile(
                r'\b(?:create|open|file)\s+(?:github\s+)?issue\s+["\'](?P<title>[^"\']+)["\']',
                re.IGNORECASE
            ),
            # Match "create github issue title" (unquoted)
            re.compile(
                r'\b(?:create|open|file)\s+(?:github\s+)?issue\s+(?P<title>[^\s]+)',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        # Higher priority to avoid conflicts with other handlers
        if re.search(r'\b(?:create|open|file)\s+(?:github\s+)?issue\b', text, re.IGNORECASE):
            return 0.95
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Try quoted title first
        match = re.search(
            r'\b(?:create|open|file)\s+(?:github\s+)?issue\s+["\'](?P<title>[^"\']+)["\']',
            text,
            re.IGNORECASE
        )
        if not match:
            # Try unquoted title
            match = re.search(
                r'\b(?:create|open|file)\s+(?:github\s+)?issue\s+(?P<title>[^\s]+)',
            text,
            re.IGNORECASE
        )
        if match:
            body = self.extract_content(text, full_message, ["with body", "with description"])
            return HandlerResult(
                success=True,
                action_type="GitHubCreateIssue",
                params={
                    "title": match.group("title"),
                    "body": body or ""
                },
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse create github issue")


class GitHubCreatePRHandler(BaseHandler):
    """Handler for creating GitHub pull requests."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Match "create github pr 'title'" or "create github pull request 'title'"
            re.compile(
                r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+["\'](?P<title>[^"\']+)["\']',
                re.IGNORECASE
            ),
            # Match "create github pr title" (unquoted)
            re.compile(
                r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+(?P<title>[^\s]+)',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        # Higher priority to avoid conflicts with other handlers (especially GitPullHandler)
        # Check for "github" keyword to distinguish from git pull
        if re.search(r'\b(?:create|open|file|submit)\s+github\s+(?:pr|pull\s+request)\b', text, re.IGNORECASE):
            return 0.95
        # Also match "create github pr" (shorter form)
        if re.search(r'\b(?:create|open|file|submit)\s+github\s+pr\b', text, re.IGNORECASE):
            return 0.95
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Try quoted title first
        match = re.search(
            r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+["\'](?P<title>[^"\']+)["\']',
            text,
            re.IGNORECASE
        )
        if not match:
            # Try unquoted title
            match = re.search(
                r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+(?P<title>[^\s]+)',
            text,
            re.IGNORECASE
        )
        if match:
            body = self.extract_content(text, full_message, ["with body", "with description"])
            return HandlerResult(
                success=True,
                action_type="GitHubCreatePR",
                params={
                    "title": match.group("title"),
                    "body": body or ""
                },
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse create github pr")


# Placeholder handlers for other categories
class FolderHandlerCategory:
    """Category manager for folder operation handlers."""
    
    def __init__(self):
        self.handlers = []
    
    def get_handlers(self):
        return self.handlers


class SearchHandlerCategory:
    """Category manager for search operation handlers."""
    
    def __init__(self):
        self.handlers = []
    
    def get_handlers(self):
        return self.handlers


class ShellHandlerCategory:
    """Category manager for shell operation handlers."""
    
    def __init__(self):
        self.handlers = []
    
    def get_handlers(self):
        return self.handlers

