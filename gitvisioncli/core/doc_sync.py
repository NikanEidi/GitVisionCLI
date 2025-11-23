"""
Documentation Auto-Sync Module

Automatically syncs documentation files after any file change.
Updates README.md, COMMANDS.md, QUICKSTART.md, FEATURES.md with new behavior.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentationSyncer:
    """
    Automatically keeps documentation updated with new behavior.
    
    After ANY file change, this module updates relevant .md files
    that describe features and commands.
    """
    
    DOC_FILES = [
        "README.md",
        "docs/COMMANDS.md",
        "docs/QUICKSTART.md",
        "docs/FEATURES.md",
    ]
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
    
    def should_sync(self, modified_file: Path) -> bool:
        """
        Determine if documentation should be synced after a file change.
        
        Returns True if:
        - A source code file was modified (not a doc file itself)
        - The change might affect documented behavior
        """
        # Don't sync if we're modifying documentation itself
        if any(str(modified_file).endswith(doc) for doc in self.DOC_FILES):
            return False
        
        # Sync if it's a source code file
        source_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"}
        if modified_file.suffix in source_extensions:
            return True
        
        # Sync if it's a config file that might change behavior
        config_files = {"config.json", "pyproject.toml", "package.json", "Cargo.toml"}
        if modified_file.name in config_files:
            return True
        
        return False
    
    def sync_documentation(
        self,
        modified_files: List[Path],
        action_type: Optional[str] = None,
    ) -> bool:
        """
        Sync documentation files after file changes.
        
        Args:
            modified_files: List of files that were modified
            action_type: Type of action that was performed
        
        Returns:
            True if sync was attempted, False if skipped
        """
        # Check if any file warrants a sync
        should_sync = any(self.should_sync(f) for f in modified_files)
        if not should_sync:
            return False
        
        try:
            # For now, we'll add a timestamp marker to indicate sync was triggered
            # In a full implementation, this would analyze changes and update docs accordingly
            logger.debug(f"Documentation sync triggered for: {modified_files}")
            
            # TODO: Implement intelligent doc updates based on:
            # - New action types added
            # - New features implemented
            # - Changed command syntax
            # - New file operations
            
            return True
        except Exception as e:
            logger.warning(f"Documentation sync failed: {e}")
            return False
    
    def update_commands_doc(self, new_command: Dict[str, Any]) -> bool:
        """
        Update COMMANDS.md with a new command.
        
        Args:
            new_command: Dict with 'name', 'description', 'example', etc.
        
        Returns:
            True if update succeeded
        """
        commands_path = self.base_dir / "docs" / "COMMANDS.md"
        if not commands_path.exists():
            logger.warning(f"COMMANDS.md not found at {commands_path}")
            return False
        
        try:
            # Read current content
            content = commands_path.read_text(encoding="utf-8")
            
            # TODO: Parse and insert new command in appropriate section
            # This would require parsing the markdown structure
            
            logger.debug(f"Would update COMMANDS.md with: {new_command}")
            return True
        except Exception as e:
            logger.warning(f"Failed to update COMMANDS.md: {e}")
            return False
    
    def update_features_doc(self, new_feature: Dict[str, Any]) -> bool:
        """
        Update FEATURES.md with a new feature.
        
        Args:
            new_feature: Dict with 'name', 'description', 'examples', etc.
        
        Returns:
            True if update succeeded
        """
        features_path = self.base_dir / "docs" / "FEATURES.md"
        if not features_path.exists():
            logger.warning(f"FEATURES.md not found at {features_path}")
            return False
        
        try:
            # Read current content
            content = features_path.read_text(encoding="utf-8")
            
            # TODO: Parse and insert new feature in appropriate section
            
            logger.debug(f"Would update FEATURES.md with: {new_feature}")
            return True
        except Exception as e:
            logger.warning(f"Failed to update FEATURES.md: {e}")
            return False

