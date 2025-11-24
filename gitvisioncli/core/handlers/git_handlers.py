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
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?init\b', text, re.IGNORECASE):
            return 0.95
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        return HandlerResult(
            success=True,
            action_type="GitInit",
            params={},
            confidence=0.95
        )


class GitAddHandler(BaseHandler):
    """Handler for git add operations."""
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'\b(?:git\s+)?(?:add|stage)\s+(?P<path>[^\s]+|\.|all)\b', re.IGNORECASE),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?(?:add|stage)\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(r'\b(?:git\s+)?(?:add|stage)\s+(?P<path>[^\s]+|\.|all)\b', text, re.IGNORECASE)
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
            re.compile(r'\b(?:git\s+)?commit\s+(?:-m\s+)?["\'](?P<msg>[^"\']+)["\']\b', re.IGNORECASE),
        ]
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?commit\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(r'\b(?:git\s+)?commit\s+(?:-m\s+)?["\'](?P<msg>[^"\']+)["\']\b', text, re.IGNORECASE)
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
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\b(?:git\s+)?push\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
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
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\b(?:git\s+)?pull\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        return HandlerResult(
            success=True,
            action_type="GitPull",
            params={},
            confidence=0.95
        )


class GitBranchHandler(BaseHandler):
    """Handler for git branch operations."""
    
    def can_handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> float:
        if re.search(r'\b(?:git\s+)?(?:branch|create\s+branch)\s+(\w+)\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\b(?:git\s+)?(?:branch|create\s+branch)\s+(?P<name>\w+)\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(r'\b(?:git\s+)?(?:branch|create\s+branch)\s+(?P<name>\w+)\b', text, re.IGNORECASE)
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
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\b(?:git\s+)?(?:checkout|switch|go\s+to)\s+(?P<branch>\w+)\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(r'\b(?:git\s+)?(?:checkout|switch|go\s+to)\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
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
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [re.compile(r'\b(?:git\s+)?merge\s+(?P<branch>\w+)\b', re.IGNORECASE)]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        match = re.search(r'\b(?:git\s+)?merge\s+(?P<branch>\w+)\b', text, re.IGNORECASE)
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
        if re.search(r'\b(?:git\s+)?remote\b', text, re.IGNORECASE):
            return 0.9
        return 0.0
    
    def _init_patterns(self) -> List[re.Pattern]:
        return [
            re.compile(r'\b(?:git\s+)?remote\s+add\s+(?P<name>\w+)\s+(?P<url>[^\s]+)\b', re.IGNORECASE),
            re.compile(r'\b(?:git\s+)?remote\s+remove\s+(?P<name>\w+)\b', re.IGNORECASE),
        ]
    
    def parse(self, text: str, context: Optional[Dict[str, Any]] = None, full_message: Optional[str] = None) -> HandlerResult:
        # Add remote
        match = re.search(r'\b(?:git\s+)?remote\s+add\s+(?P<name>\w+)\s+(?P<url>[^\s]+)\b', text, re.IGNORECASE)
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

