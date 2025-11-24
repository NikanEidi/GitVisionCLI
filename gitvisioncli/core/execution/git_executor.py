"""
Git Operation Executor

Specialized executor for all Git operations.
"""

from typing import Dict, Any, Optional

from gitvisioncli.core.execution.base_executor import BaseExecutor, ExecutionResult
from gitvisioncli.core.supervisor import ActionType


class GitExecutor(BaseExecutor):
    """Executor for Git operations."""
    
    # Git operation action types
    GIT_ACTIONS = {
        ActionType.GIT_INIT,
        ActionType.GIT_ADD,
        ActionType.GIT_COMMIT,
        ActionType.GIT_PUSH,
        ActionType.GIT_PULL,
        ActionType.GIT_BRANCH,
        ActionType.GIT_CHECKOUT,
        ActionType.GIT_MERGE,
        ActionType.GIT_REMOTE,
        ActionType.RUN_GIT_COMMAND,
    }
    
    def can_execute(self, action_type: str) -> bool:
        """Check if this executor can handle the action."""
        try:
            action_enum = ActionType(action_type)
            return action_enum in self.GIT_ACTIONS
        except ValueError:
            return False
    
    async def execute(
        self,
        action_type: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute Git operation."""
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
                message=f"Git execution failed: {str(e)}",
                error=str(e)
            )

