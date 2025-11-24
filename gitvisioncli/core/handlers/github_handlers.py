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
        if re.search(r'\b(?:create|make)\s+(?:github\s+)?(?:repo|repository)\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(
            r'\b(?:create|make)\s+(?:github\s+)?(?:repo|repository)\s+(?P<name>[^\s]+)(?:\s+(?P<private>private|public))?\b',
            text,
            re.IGNORECASE
        )
        if match:
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": match.group("name"),
                    "private": match.group("private") == "private" if match.group("private") else False
                },
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse create github repo")


class GitHubCreateIssueHandler(BaseHandler):
    """Handler for creating GitHub issues."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(
                r'\b(?:create|open|file)\s+(?:github\s+)?issue\s+["\'](?P<title>[^"\']+)["\']\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:create|open|file)\s+(?:github\s+)?issue\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(
            r'\b(?:create|open|file)\s+(?:github\s+)?issue\s+["\'](?P<title>[^"\']+)["\']\b',
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
            re.compile(
                r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+["\'](?P<title>[^"\']+)["\']\b',
                re.IGNORECASE
            ),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(
            r'\b(?:create|open|file|submit)\s+(?:github\s+)?(?:pr|pull\s+request)\s+["\'](?P<title>[^"\']+)["\']\b',
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

