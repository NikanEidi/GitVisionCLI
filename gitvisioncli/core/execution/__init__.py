"""
Execution Layer

Modular execution system with specialized executors for different action types.
Uses factory pattern for executor creation.
"""

from gitvisioncli.core.execution.base_executor import BaseExecutor, ExecutionResult
from gitvisioncli.core.execution.executor_factory import ExecutorFactory
from gitvisioncli.core.execution.file_executor import FileExecutor
from gitvisioncli.core.execution.git_executor import GitExecutor
from gitvisioncli.core.execution.github_executor import GitHubExecutor
from gitvisioncli.core.execution.shell_executor import ShellExecutor

__all__ = [
    "BaseExecutor",
    "ExecutionResult",
    "ExecutorFactory",
    "FileExecutor",
    "GitExecutor",
    "GitHubExecutor",
    "ShellExecutor",
]

