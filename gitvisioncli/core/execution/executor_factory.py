"""
Executor Factory

Factory pattern for creating executor instances.
Supports dynamic executor registration.
"""

import logging
from typing import Dict, Type, Optional, List
from pathlib import Path

from gitvisioncli.core.execution.base_executor import BaseExecutor
from gitvisioncli.core.execution.file_executor import FileExecutor
from gitvisioncli.core.execution.git_executor import GitExecutor
from gitvisioncli.core.execution.github_executor import GitHubExecutor
from gitvisioncli.core.execution.shell_executor import ShellExecutor

logger = logging.getLogger(__name__)


class ExecutorFactory:
    """
    Factory for creating executor instances.
    
    Supports:
    - Dynamic executor registration
    - Automatic executor selection
    - Multiple executors for different action types
    """
    
    _executors: List[Type[BaseExecutor]] = [
        FileExecutor,
        GitExecutor,
        GitHubExecutor,
        ShellExecutor,
    ]
    
    @classmethod
    def register_executor(cls, executor_class: Type[BaseExecutor]) -> None:
        """
        Register a new executor class.
        
        Args:
            executor_class: Executor class implementing BaseExecutor
        """
        if executor_class not in cls._executors:
            cls._executors.append(executor_class)
            logger.info(f"Registered executor: {executor_class.__name__}")
    
    @classmethod
    def create_executors(
        cls,
        base_dir: Path,
        supervisor=None
    ) -> Dict[str, BaseExecutor]:
        """
        Create all executor instances.
        
        Args:
            base_dir: Base directory for operations
            supervisor: Optional ActionSupervisor instance
        
        Returns:
            Dictionary mapping executor names to instances
        """
        executors = {}
        for executor_class in cls._executors:
            executor = executor_class(base_dir, supervisor)
            executors[executor_class.__name__] = executor
        return executors
    
    @classmethod
    def get_executor_for_action(
        cls,
        action_type: str,
        base_dir: Path,
        supervisor=None
    ) -> Optional[BaseExecutor]:
        """
        Get the appropriate executor for an action type.
        
        Args:
            action_type: Action type string
            base_dir: Base directory for operations
            supervisor: Optional ActionSupervisor instance
        
        Returns:
            Executor instance that can handle the action, or None
        """
        for executor_class in cls._executors:
            executor = executor_class(base_dir, supervisor)
            if executor.can_execute(action_type):
                return executor
        return None
    
    @classmethod
    def get_available_executors(cls) -> List[str]:
        """
        Get list of available executor class names.
        
        Returns:
            List of executor class names
        """
        return [e.__name__ for e in cls._executors]

