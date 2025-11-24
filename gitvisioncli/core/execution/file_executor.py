"""
File Operation Executor

Specialized executor for all file operations.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from gitvisioncli.core.execution.base_executor import BaseExecutor, ExecutionResult
from gitvisioncli.core.supervisor import ActionType


class FileExecutor(BaseExecutor):
    """Executor for file operations."""
    
    # File operation action types
    FILE_ACTIONS = {
        ActionType.CREATE_FILE,
        ActionType.READ_FILE,
        ActionType.DELETE_FILE,
        ActionType.MOVE_FILE,
        ActionType.COPY_FILE,
        ActionType.RENAME_FILE,
        ActionType.EDIT_FILE,
    }
    
    # Line editing action types
    LINE_ACTIONS = {
        ActionType.INSERT_BEFORE_LINE,
        ActionType.INSERT_AFTER_LINE,
        ActionType.DELETE_LINE_RANGE,
        ActionType.REPLACE_BLOCK,
        ActionType.INSERT_AT_TOP,
        ActionType.INSERT_AT_BOTTOM,
    }
    
    def can_execute(self, action_type: str) -> bool:
        """Check if this executor can handle the action."""
        try:
            action_enum = ActionType(action_type)
            return action_enum in self.FILE_ACTIONS or action_enum in self.LINE_ACTIONS
        except ValueError:
            return False
    
    async def execute(
        self,
        action_type: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute file operation."""
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
                message=f"Execution failed: {str(e)}",
                error=str(e)
            )

