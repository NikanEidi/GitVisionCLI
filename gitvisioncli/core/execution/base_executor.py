"""
Base Executor Interface

Abstract base class for all action executors.
Implements strategy pattern for different execution types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

from gitvisioncli.core.supervisor import ActionResult, ActionStatus


@dataclass
class ExecutionResult:
    """Standardized execution result."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_action_result(self) -> ActionResult:
        """Convert to ActionResult."""
        return ActionResult(
            status=ActionStatus.SUCCESS if self.success else ActionStatus.FAILURE,
            message=self.message,
            data=self.data,
            error=self.error,
        )


class BaseExecutor(ABC):
    """
    Abstract base class for all action executors.
    
    Each executor is responsible for executing a specific category of actions:
    - FileExecutor: File operations
    - GitExecutor: Git operations
    - GitHubExecutor: GitHub operations
    - ShellExecutor: Shell commands
    
    This provides clear separation of concerns and makes the system
    more maintainable and testable.
    """
    
    def __init__(self, base_dir: Path, supervisor=None):
        """
        Initialize the executor.
        
        Args:
            base_dir: Base directory for operations
            supervisor: Optional ActionSupervisor instance
        """
        self.base_dir = Path(base_dir).resolve()
        self.supervisor = supervisor
    
    @abstractmethod
    def can_execute(self, action_type: str) -> bool:
        """
        Check if this executor can handle the given action type.
        
        Args:
            action_type: Action type string
        
        Returns:
            True if this executor can handle the action
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        action_type: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute an action.
        
        Args:
            action_type: Type of action to execute
            params: Action parameters
            context: Optional execution context
        
        Returns:
            ExecutionResult with execution outcome
        """
        pass
    
    def validate_params(self, params: Dict[str, Any], required: list[str]) -> bool:
        """
        Validate that required parameters are present.
        
        Args:
            params: Parameters to validate
            required: List of required parameter names
        
        Returns:
            True if all required parameters are present
        """
        return all(key in params for key in required)

