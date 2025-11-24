"""
Shell Operation Executor

Specialized executor for shell commands.
"""

from typing import Dict, Any, Optional

from gitvisioncli.core.execution.base_executor import BaseExecutor, ExecutionResult
from gitvisioncli.core.supervisor import ActionType


class ShellExecutor(BaseExecutor):
    """Executor for shell operations."""
    
    # Shell operation action types
    SHELL_ACTIONS = {
        ActionType.RUN_SHELL_COMMAND,
        ActionType.RUN_TESTS,
        ActionType.BUILD_PROJECT,
    }
    
    def can_execute(self, action_type: str) -> bool:
        """Check if this executor can handle the action."""
        try:
            action_enum = ActionType(action_type)
            return action_enum in self.SHELL_ACTIONS
        except ValueError:
            return False
    
    async def execute(
        self,
        action_type: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute shell operation."""
        if not self.supervisor:
            return ExecutionResult(
                success=False,
                message="Supervisor not available",
                error="Supervisor not initialized"
            )
        
        try:
            action_enum = ActionType(action_type)
            handler = self.supervisor.handlers.get(action_enum)
            
            if not handler:
                return ExecutionResult(
                    success=False,
                    message=f"No handler for {action_type}",
                    error=f"Action type {action_type} not supported"
                )
            
            # Create action context
            from gitvisioncli.core.supervisor import ActionContext, TransactionManager
            action_context = ActionContext(
                base_dir=self.base_dir,
                current_dir=self.base_dir,
            )
            transaction = TransactionManager()
            
            # Execute handler
            result = handler(params, action_context, transaction)
            
            return ExecutionResult(
                success=result.status.value == "success",
                message=result.message,
                data=result.data,
                error=result.error,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Shell execution failed: {str(e)}",
                error=str(e)
            )

