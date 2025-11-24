"""
Application Controller

Central controller for GitVisionCLI application.
Refactored from cli.py to use application controller pattern.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from gitvisioncli.core.chat_engine import ChatEngine
from gitvisioncli.core.executor import AIActionExecutor
from gitvisioncli.workspace import RightPanel, FileSystemWatcher, PanelManager
from gitvisioncli.workspace.panel_manager import PanelMode
from gitvisioncli.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class ApplicationController:
    """
    Central application controller.
    
    Responsibilities:
    - Initialize application components
    - Manage application lifecycle
    - Coordinate between components
    - Handle application-level events
    """
    
    def __init__(
        self,
        base_dir: Path,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize application controller.
        
        Args:
            base_dir: Base directory for operations
            config: Optional configuration dictionary
        """
        self.base_dir = Path(base_dir).resolve()
        self.config = config or {}
        
        # Core components
        self.engine: Optional[ChatEngine] = None
        self.executor: Optional[AIActionExecutor] = None
        self.right_panel: Optional[RightPanel] = None
        self.fs_watcher: Optional[FileSystemWatcher] = None
        self.panel_manager: Optional[PanelManager] = None
        self.plugin_manager: Optional[PluginManager] = None
        
        # Application state
        self.initialized = False
        self.running = False
    
    def initialize(self) -> bool:
        """
        Initialize all application components.
        
        Returns:
            True if initialization successful
        """
        if self.initialized:
            logger.warning("Application already initialized")
            return True
        
        try:
            # Initialize chat engine
            self.engine = self._create_chat_engine()
            
            # Initialize executor
            self.executor = self._create_executor()
            
            # Initialize workspace
            self.right_panel, self.fs_watcher = self._init_workspace()
            
            # Initialize plugins
            self.plugin_manager = self._init_plugins()
            
            self.initialized = True
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}", exc_info=True)
            return False
    
    def _create_chat_engine(self) -> ChatEngine:
        """Create and configure chat engine."""
        from gitvisioncli.config.settings import load_config
        
        try:
            config = load_config()
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            config = {}
        
        # Create chat engine with config
        engine = ChatEngine(
            base_dir=str(self.base_dir),
            config=config
        )
        
        return engine
    
    def _create_executor(self) -> AIActionExecutor:
        """Create and configure executor."""
        if not self.engine:
            raise ValueError("Chat engine must be initialized before executor")
        
        executor = AIActionExecutor(
            base_dir=str(self.base_dir),
            security_policy=self.engine.executor.security_policy if hasattr(self.engine, 'executor') else None,
            github_config=self.config.get("github")
        )
        
        return executor
    
    def _init_workspace(self) -> Tuple[Optional[RightPanel], Optional[FileSystemWatcher]]:
        """Initialize workspace panels and file watcher."""
        if not self.engine or not self.executor:
            raise ValueError("Engine and executor must be initialized")
        
        try:
            # Initialize PanelManager
            panel_manager = PanelManager()
            try:
                panel_manager.supervisor = self.executor.supervisor  # type: ignore[attr-defined]
            except Exception:
                panel_manager.supervisor = None  # type: ignore[attr-defined]
            
            self.panel_manager = panel_manager
            
            # Initialize RightPanel
            right_panel = RightPanel(
                base_dir=self.base_dir,
                panel_manager=panel_manager
            )
            
            # Attach UI components
            if hasattr(panel_manager, "attach_ui"):
                panel_manager.attach_ui(
                    right_panel,
                    right_panel.editor_panel,
                    right_panel.tree_panel,
                )
            
            # Initialize FSWatcher
            fs_watcher = FileSystemWatcher(
                base_dir=str(self.base_dir),
                poll_interval=1.5
            )
            
            # Register callbacks
            if hasattr(panel_manager, "handle_fs_event"):
                fs_watcher.register_callback(panel_manager.handle_fs_event)
            
            def _refresh_if_tree(_change=None):
                try:
                    mode = panel_manager.get_mode()
                    if mode == PanelMode.TREE:
                        right_panel.refresh_tree_panel()
                except Exception as e:
                    logger.warning(f"Tree refresh guard failed: {e}")
                    right_panel.refresh_tree_panel()
            
            fs_watcher.register_callback(_refresh_if_tree)
            
            # Link executor to watcher
            if hasattr(self.engine, "set_fs_watcher"):
                self.engine.set_fs_watcher(fs_watcher)
            
            fs_watcher.start()
            
            return right_panel, fs_watcher
            
        except Exception as e:
            logger.error(f"Workspace initialization failed: {e}", exc_info=True)
            return None, None
    
    def _init_plugins(self) -> Optional[PluginManager]:
        """Initialize plugin system."""
        try:
            from gitvisioncli.plugins.plugin_manager import PluginManager
            from gitvisioncli.plugins.registry import PluginRegistry
            
            registry = PluginRegistry()
            manager = PluginManager(registry)
            
            # Initialize plugins with context
            context = {
                "engine": self.engine,
                "executor": self.executor,
                "base_dir": self.base_dir,
                "config": self.config,
            }
            
            manager.initialize_plugins(context)
            
            return manager
            
        except Exception as e:
            logger.warning(f"Plugin initialization failed: {e}")
            return None
    
    def start(self) -> None:
        """Start the application."""
        if not self.initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize application")
        
        self.running = True
        logger.info("Application started")
    
    def stop(self) -> None:
        """Stop the application and cleanup resources."""
        self.running = False
        
        # Stop file watcher
        if self.fs_watcher:
            try:
                self.fs_watcher.stop()
            except Exception as e:
                logger.warning(f"Error stopping file watcher: {e}")
        
        # Cleanup plugins
        if self.plugin_manager:
            try:
                self.plugin_manager.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up plugins: {e}")
        
        logger.info("Application stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get application status.
        
        Returns:
            Status dictionary
        """
        return {
            "initialized": self.initialized,
            "running": self.running,
            "base_dir": str(self.base_dir),
            "has_engine": self.engine is not None,
            "has_executor": self.executor is not None,
            "has_panels": self.right_panel is not None,
            "has_watcher": self.fs_watcher is not None,
        }

