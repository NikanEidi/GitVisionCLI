"""
Action Router - Integrates Natural Language Action Engine with ChatEngine

This module provides a bridge between the deterministic Natural Language Action Engine
and the ChatEngine, allowing direct action conversion without AI when possible.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from gitvisioncli.core.natural_language_action_engine import (
    NaturalLanguageActionEngine,
    ActiveFileContext,
    ActionJSON,
)
from gitvisioncli.core.doc_sync import DocumentationSyncer

logger = logging.getLogger(__name__)


class ActionRouter:
    """
    Routes user input to either:
    1. Direct action conversion (via NaturalLanguageActionEngine) - fast, deterministic
    2. AI processing (via ChatEngine) - for complex/ambiguous requests
    """
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.action_engine = NaturalLanguageActionEngine()
        self.doc_syncer = DocumentationSyncer(self.base_dir)
    
    def try_direct_action(
        self,
        user_message: str,
        active_file: Optional[ActiveFileContext] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Try to convert user message directly to an action without AI.
        
        Returns:
            Action dict if conversion succeeded, None if should use AI
        """
        if not user_message or not user_message.strip():
            return None
        
        try:
            action = self.action_engine.convert_to_action(
                user_message,
                active_file=active_file,
            )
            
            if action:
                # Check if action is already a dict (from command_router) or ActionJSON
                if isinstance(action, dict):
                    logger.debug(f"Direct action conversion: {action}")
                    return action
                elif hasattr(action, 'type') and hasattr(action, 'params'):
                    # It's an ActionJSON object
                action_dict = self.action_engine.to_dict(action)
                logger.debug(f"Direct action conversion: {action_dict}")
                return action_dict
                else:
                    logger.warning(f"Unexpected action type: {type(action)}")
                    return None
            
            return None
        except Exception as e:
            logger.warning(f"Direct action conversion failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def sync_after_action(
        self,
        action_type: str,
        modified_files: list[Path],
    ) -> bool:
        """
        Sync documentation after an action is executed.
        
        Args:
            action_type: Type of action that was executed
            modified_files: List of files that were modified
        
        Returns:
            True if sync was attempted
        """
        return self.doc_syncer.sync_documentation(
            modified_files,
            action_type=action_type,
        )
    
    def get_active_file_context(
        self,
        active_file_path: Optional[str] = None,
        active_file_content: Optional[str] = None,
    ) -> Optional[ActiveFileContext]:
        """
        Create ActiveFileContext from provided information.
        
        Args:
            active_file_path: Path to the active file
            active_file_content: Content of the active file (optional)
        
        Returns:
            ActiveFileContext if path is provided, None otherwise
        """
        if not active_file_path:
            return None
        
        return ActiveFileContext(
            path=active_file_path,
            content=active_file_content,
        )

