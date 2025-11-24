"""
Git Operation Handlers

Comprehensive handlers for all Git operations.
"""

import re
from typing import Optional, List, Dict, Any
from gitvisioncli.core.handlers.base import BaseHandler, HandlerResult, HandlerPriority


class GitHandlerCategory:
    """Category manager for all Git operation handlers."""
    
    def __init__(self):
        """Initialize the Git handler category."""
        self.handlers = [
            GitInitHandler(),
            GitAddHandler(),
            GitCommitHandler(),
            GitPushHandler(),
            GitPullHandler(),
            GitBranchHandler(),
            GitCheckoutHandler(),
            GitMergeHandler(),
            GitRemoteHandler(),
            GitStatusHandler(),
            GitLogHandler(),
        ]
    
    def get_handlers(self) -> List[BaseHandler]:
        """Get all Git handlers."""
        return self.handlers


class GitInitHandler(BaseHandler):
    """Handler for git init operations."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'\b(?:git\s+)?(?:init|initialize\s+git|set\s+up\s+git)\b', re.IGNORECASE),
            re.compile(r'\binit\s+git\b', re.IGNORECASE),
            re.compile(r'\binitialize\s+git\b', re.IGNORECASE),
            re.compile(r'\bset\s+up\s+git\b', re.IGNORECASE),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        text_lower = text.lower()
        if (re.search(r'\b(?:git\s+)?init\b', text_lower) or 
            re.search(r'\binit\s+git\b', text_lower) or
            re.search(r'\binitialize\s+git\b', text_lower) or
            re.search(r'\bset\s+up\s+git\b', text_lower) or
            re.search(r'\bgit\s+initialize\b', text_lower)):
            return 0.95
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        text_lower = text.lower()
        # Match both "git init" and "init git" and variations
        if (re.search(r'\b(?:git\s+)?init\b', text_lower) or 
            re.search(r'\binit\s+git\b', text_lower) or
            re.search(r'\binitialize\s+git\b', text_lower) or
            re.search(r'\bset\s+up\s+git\b', text_lower) or
            re.search(r'\bgit\s+initialize\b', text_lower)):
            return HandlerResult(
                success=True,
                action_type="GitInit",
                params={},
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse git init")
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        return HandlerResult(
            success=True,
            action_type="GitInit",
            params={},
            confidence=0.95
        )


class GitAddHandler(BaseHandler):
    """Handler for git add operations."""
    
    def __init__(self):
        """Initialize with high priority to match before file handlers."""
        super().__init__(priority=HandlerPriority.HIGH)
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Match "git add ." or "git add <path>" or "git add all"
            # Note: Use (?:\.|all|[^\s]+) to match . or all or any non-space sequence
            re.compile(r'\bgit\s+(?:add|stage)\s+(?P<path>\.|all|[^\s]+)', re.IGNORECASE),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        text_lower = text.lower().strip()
        # First check if it's clearly a file operation (has file operation keywords)
        # This check must come FIRST to avoid false matches
        file_op_keywords = ['at bottom', 'at top', 'at line', 'after line', 'before line', 'to bottom', 'to top', 'to end', 'at end', 'at the bottom', 'at the top', 'at start', 'at beginning', 'at tail', 'on line', 'in line']
        if any(kw in text_lower for kw in file_op_keywords):
            return 0.0  # It's a file operation, not git add
        
        # Only match if "git" is explicitly present
        if re.search(r'\bgit\s+(?:add|stage)\b', text_lower):
            return 0.9
        
        # Also match standalone "add" at start of line (but only if clearly git, not file operation)
        # Pattern: "add ." or "add all" or "add <file>" (but not "add X at bottom")
        if re.match(r'^add\s+(?:\.|all|[^\s]+)', text_lower):
            # It's likely a git add command
            return 0.85  # Higher confidence for standalone git add
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        text_lower = text.lower().strip()
        # Try "git add" first
        match = re.search(r'\bgit\s+(?:add|stage)\s+(?P<path>\.|all|[^\s]+)', text_lower)
        if not match:
            # Try standalone "add" command (but only if it doesn't look like a file operation)
            # Check if it's clearly a git add (starts with "add" and has ".", "all", or a file path)
            if re.match(r'^add\s+(?:\.|all|[^\s]+)', text_lower):
                # Make sure it's not a file operation like "add X at bottom"
                if not any(kw in text_lower for kw in ['at bottom', 'at top', 'at line', 'after line', 'before line', 'with']):
                    # Match "add ." or "add all" or "add <file>"
                    match = re.search(r'^add\s+(?P<path>\.|all|[^\s]+)', text_lower)
        if match:
            path = match.group("path")
            return HandlerResult(
                success=True,
                action_type="GitAdd",
                params={"path": path},
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse git add")


class GitCommitHandler(BaseHandler):
    """Handler for git commit operations."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Match "git commit -m 'message'" or "git commit 'message'" or "git commit \"message\""
            re.compile(r'\b(?:git\s+)?commit\s+(?:-m\s+)?["\'](?P<msg>[^"\']+)["\']', re.IGNORECASE),
            # Match "git commit message" (no quotes)
            re.compile(r'\b(?:git\s+)?commit\s+(?:-m\s+)?(?P<msg>[^\s]+)', re.IGNORECASE),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?commit\b', text, re.IGNORECASE):
            return 0.9
        # Also match standalone "commit" at start
        if re.search(r'^commit\s+', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Try quoted message first
        match = re.search(r'\b(?:git\s+)?commit\s+(?:-m\s+)?["\'](?P<msg>[^"\']+)["\']', text, re.IGNORECASE)
        if match:
            message = match.group("msg")
            return HandlerResult(
                success=True,
                action_type="GitCommit",
                params={"message": message},
                confidence=0.95
            )
        
        # Try unquoted message
        match = re.search(r'\b(?:git\s+)?commit\s+(?:-m\s+)?(?P<msg>[^\s]+)', text, re.IGNORECASE)
        if not match:
            # Try standalone "commit" command
            match = re.search(r'^commit\s+(?:-m\s+)?["\']?(?P<msg>[^"\']+)["\']?', text, re.IGNORECASE)
        if match:
            message = match.group("msg")
            return HandlerResult(
                success=True,
                action_type="GitCommit",
                params={"message": message},
                confidence=0.95
            )
        
        return HandlerResult(success=False, error="Could not parse git commit")


class GitPushHandler(BaseHandler):
    """Handler for git push operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?push\b', text, re.IGNORECASE):
            return 0.9
        # Also match standalone "push" at start
        if re.search(r'^push\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Support "git push -u origin main"
            re.compile(r'\b(?:git\s+)?push\s+(?:-u\s+)?(?P<remote>\w+)\s+(?P<branch>\w+)\b', re.IGNORECASE),
            # Support "git push"
            re.compile(r'\b(?:git\s+)?push\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Try to parse "git push -u origin main" or "git push origin main"
        match = re.search(r'\b(?:git\s+)?push\s+(?:-u\s+)?(?P<remote>\w+)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try standalone "push origin main"
            match = re.search(r'^push\s+(?:-u\s+)?(?P<remote>\w+)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try "push to origin"
            match = re.search(r'\bpush\s+to\s+(?P<remote>\w+)\b', text, re.IGNORECASE)
        if match:
            branch = match.groupdict().get("branch")
            return HandlerResult(
                success=True,
                action_type="GitPush",
                params={
                    "remote": match.group("remote"),
                    "branch": branch
                },
                confidence=0.95
            )
        
        # Default push (no remote/branch specified)
        return HandlerResult(
            success=True,
            action_type="GitPush",
            params={},
            confidence=0.95
        )


class GitPullHandler(BaseHandler):
    """Handler for git pull operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?pull\b', text, re.IGNORECASE):
            return 0.9
        # Also match standalone "pull" at start
        if re.search(r'^pull\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Support "git pull origin main"
            re.compile(r'\b(?:git\s+)?pull\s+(?P<remote>\w+)\s+(?P<branch>\w+)\b', re.IGNORECASE),
            # Support "git pull"
            re.compile(r'\b(?:git\s+)?pull\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Try to parse "git pull origin main"
        match = re.search(r'\b(?:git\s+)?pull\s+(?P<remote>\w+)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try standalone "pull origin main"
            match = re.search(r'^pull\s+(?P<remote>\w+)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try "pull from origin"
            match = re.search(r'\bpull\s+from\s+(?P<remote>\w+)\b', text, re.IGNORECASE)
        if match:
            branch = match.groupdict().get("branch")
            return HandlerResult(
                success=True,
                action_type="GitPull",
                params={
                    "remote": match.group("remote"),
                    "branch": branch
                },
                confidence=0.95
            )
        
        # Default pull (no remote/branch specified)
        return HandlerResult(
            success=True,
            action_type="GitPull",
            params={},
            confidence=0.95
        )


class GitBranchHandler(BaseHandler):
    """Handler for git branch operations."""
    
    def __init__(self):
        """Initialize with high priority to match before CreateFileHandler."""
        super().__init__(priority=HandlerPriority.HIGH)
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        text_lower = text.lower()
        # Higher priority to avoid conflicts with CreateFileHandler
        # Check for "create branch" first (before CreateFileHandler matches "create")
        if re.search(r'^create\s+branch\s+(\w+)\b', text_lower):
            return 0.95
        if re.search(r'\b(?:git\s+)?(?:branch|create\s+branch)\s+(\w+)\b', text_lower):
            return 0.95
        # Also match standalone "branch" command
        if re.search(r'^branch\s+(\w+)\b', text_lower):
            return 0.95
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'\b(?:git\s+)?(?:branch|create\s+branch)\s+(?P<name>\w+)\b', re.IGNORECASE),
            re.compile(r'^branch\s+(?P<name>\w+)\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        text_lower = text.lower()
        match = re.search(r'\b(?:git\s+)?(?:branch|create\s+branch)\s+(?P<name>\w+)\b', text_lower)
        if not match:
            # Try standalone "branch" command
            match = re.search(r'^branch\s+(?P<name>\w+)\b', text_lower)
        if not match:
            # Try "create branch X"
            match = re.search(r'^create\s+branch\s+(?P<name>\w+)\b', text_lower)
        if match:
            return HandlerResult(
                success=True,
                action_type="GitBranch",
                params={"name": match.group("name")},
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse git branch")


class GitCheckoutHandler(BaseHandler):
    """Handler for git checkout operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?(?:checkout|switch|go\s+to)\b', text, re.IGNORECASE):
            return 0.9
        # Also match standalone commands
        if re.search(r'^(?:checkout|switch|go\s+to)\s+\w+', text, re.IGNORECASE):
            return 0.9
        if re.search(r'\bswitch\s+to\s+\w+', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            # Support "git checkout -b feature" (create and switch)
            re.compile(r'\b(?:git\s+)?checkout\s+-b\s+(?P<branch>\w+)\b', re.IGNORECASE),
            # Support "git checkout feature" (switch only)
            re.compile(r'\b(?:git\s+)?(?:checkout|switch|go\s+to)\s+(?P<branch>\w+)\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Check for "git checkout -b feature" first (create new branch)
        match = re.search(r'\b(?:git\s+)?checkout\s+-b\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if match:
            return HandlerResult(
                success=True,
                action_type="GitCheckout",
                params={
                    "branch": match.group("branch"),
                    "create_new": True
                },
                confidence=0.95
            )
        
        # Check for regular checkout/switch/go to
        match = re.search(r'\b(?:git\s+)?(?:checkout|switch|go\s+to)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try standalone "checkout" or "switch" commands
            match = re.search(r'^(?:checkout|switch|go\s+to)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try "switch to" format
            match = re.search(r'\bswitch\s+to\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if match:
            return HandlerResult(
                success=True,
                action_type="GitCheckout",
                params={"branch": match.group("branch")},
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse git checkout")


class GitMergeHandler(BaseHandler):
    """Handler for git merge operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?merge\b', text, re.IGNORECASE):
            return 0.9
        # Also match standalone "merge" and "combine"
        if re.search(r'^(?:merge|combine)\s+\w+', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'\b(?:git\s+)?merge\s+(?P<branch>\w+)\b', re.IGNORECASE),
            re.compile(r'^(?:merge|combine)\s+(?P<branch>\w+)\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(r'\b(?:git\s+)?merge\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try standalone "merge" or "combine"
            match = re.search(r'^(?:merge|combine)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
        if match:
            return HandlerResult(
                success=True,
                action_type="GitMerge",
                params={"branch": match.group("branch")},
                confidence=0.95
            )
        return HandlerResult(success=False, error="Could not parse git merge")


class GitRemoteHandler(BaseHandler):
    """Handler for git remote operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        # Higher priority - check for "remote" keyword specifically
        if re.search(r'\b(?:git\s+)?remote\b', text, re.IGNORECASE):
            return 0.95  # Higher confidence than GitAdd
        # Also match "remove remote" format
        if re.search(r'\bremove\s+remote\b', text, re.IGNORECASE):
            return 0.95
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'\b(?:git\s+)?remote\s+add\s+(?P<name>\w+)\s+(?P<url>[^\s]+)\b', re.IGNORECASE),
            re.compile(r'\b(?:git\s+)?remote\s+remove\s+(?P<name>\w+)\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Add remote
        match = re.search(r'\b(?:git\s+)?remote\s+add\s+(?P<name>\w+)\s+(?P<url>[^\s]+)\b', text, re.IGNORECASE)
        if not match:
            # Try without "git" prefix
            match = re.search(r'^remote\s+add\s+(?P<name>\w+)\s+(?P<url>[^\s]+)\b', text, re.IGNORECASE)
        if match:
            return HandlerResult(
                success=True,
                action_type="GitRemote",
                params={
                    "operation": "add",
                    "name": match.group("name"),
                    "url": match.group("url")
                },
                confidence=0.95
            )
        
        # Remove remote
        match = re.search(r'\b(?:git\s+)?remote\s+remove\s+(?P<name>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try "remove remote" format (without "git")
            match = re.search(r'\bremove\s+remote\s+(?P<name>\w+)\b', text, re.IGNORECASE)
        if not match:
            # Try "remote remove" format
            match = re.search(r'^remote\s+remove\s+(?P<name>\w+)\b', text, re.IGNORECASE)
        if match:
            return HandlerResult(
                success=True,
                action_type="GitRemote",
                params={
                    "operation": "remove",
                    "name": match.group("name")
                },
                confidence=0.95
            )
        
        return HandlerResult(success=False, error="Could not parse git remote")


class GitStatusHandler(BaseHandler):
    """Handler for git status operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\bgit\s+status\b', text, re.IGNORECASE):
            return 0.95
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\bgit\s+status\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        return HandlerResult(
            success=True,
            action_type="GitStatus",
            params={},
            confidence=0.95
        )


class GitLogHandler(BaseHandler):
    """Handler for git log operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\bgit\s+log\b', text, re.IGNORECASE):
            return 0.95
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\bgit\s+log\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        return HandlerResult(
            success=True,
            action_type="GitLog",
            params={},
            confidence=0.95
        )

