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
        if re.search(r'\b(?:create|make|set\s+up|initialize)\s+(?:a\s+)?(?:github\s+)?(?:repo|repository)\b', text_lower):
            return 0.95  # Higher than CreateFileHandler
        # Also match "create repo" and "make repo" (without github keyword) - but only if followed by a name
        if re.search(r'^(?:create|make|initialize)\s+repo\s+[\w-]+', text_lower):
            return 0.95
        # Match "initialize <name> private repository in my github" or similar patterns
        if re.search(r'\b(?:initialize|init|set\s+up)\s+[\w-]+\s+(?:private|public)\s+(?:github\s+)?(?:repo|repository)\s+in\s+(?:my\s+)?github\b', text_lower):
            return 0.95
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        text_lower = text.lower()
        
        # Pattern 0: "initialize demo private repository in my github" - special case for complex natural language
        match = re.search(
            r'\b(?:initialize|init|set\s+up)\s+(?P<name0>[\w-]+)\s+(?P<private0>private|public)\s+(?:github\s+)?(?:repo|repository)\s+in\s+(?:my\s+)?github\b',
            text_lower
        )
        if match:
            name = match.group("name0")
            is_private = match.group("private0") == "private"
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": is_private
                },
                confidence=0.95
            )
        
        # Pattern 1: "create private github repository call it demo" or "create github repo named demo private"
        # Supports: private/public before or after, "call it", "named", "called"
        match = re.search(
            r'\b(?:create|make|set\s+up|initialize)\s+(?:a\s+)?(?P<private1>private|public)\s+(?:github\s+)?(?:repo|repository)\s+(?:named\s+|called\s+|call\s+it\s+)?(?P<name1>[^\s]+)\b',
            text_lower
        )
        if match:
            name = match.group("name1")
            is_private = match.group("private1") == "private"
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": is_private
                },
                confidence=0.95
            )
        
        # Pattern 2: "create github repository call it demo private" or "create github repo demo private"
            match = re.search(
            r'\b(?:create|make|set\s+up)\s+(?:a\s+)?(?:github\s+)?(?:repo|repository)\s+(?:named\s+|called\s+|call\s+it\s+)?(?P<name2>[^\s]+)\s+(?P<private2>private|public)\b',
                text_lower
        )
        if match:
            name = match.group("name2")
            is_private = match.group("private2") == "private"
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": is_private
                },
                confidence=0.95
            )
        
        # Pattern 3: "create github repo demo" (no privacy specified, defaults to private)
        match = re.search(
            r'\b(?:create|make|set\s+up)\s+(?:a\s+)?(?:github\s+)?(?:repo|repository)\s+(?:named\s+|called\s+|call\s+it\s+)?(?P<name3>[^\s]+)\b(?!\s+(?:private|public))',
            text_lower
        )
        if match:
            name = match.group("name3")
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": True  # Default to private
                },
                confidence=0.95
            )
        
        # Pattern 4: "create repo demo" (without github keyword, but has name)
        match = re.search(
            r'^(?:create|make)\s+repo\s+(?P<name4>[\w-]+)(?:\s+(?P<private4>private|public))?\b',
            text_lower
        )
        if match:
            name = match.group("name4")
            private_flag = match.group("private4")
            is_private = private_flag == "private" if private_flag else True  # Default to private
            return HandlerResult(
                success=True,
                action_type="GitHubCreateRepo",
                params={
                    "name": name,
                    "private": is_private
                },
                confidence=0.90  # Slightly lower confidence without "github" keyword
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

