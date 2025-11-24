"""
Handler Manager

Manages handler execution, routing, and result selection.
"""

from typing import Dict, Any, Optional, List
from gitvisioncli.core.handlers.base import BaseHandler, HandlerResult, HandlerPriority
from gitvisioncli.core.handlers.registry import HandlerRegistry


class HandlerManager:
    """
    Manages handler execution and routing.
    
    This class coordinates between multiple handlers, selecting the best
    match for a given instruction and executing it.
    """
    
    def __init__(self, registry: Optional[HandlerRegistry] = None):
        """
        Initialize the handler manager.
        
        Args:
            registry: Optional handler registry (creates new one if not provided)
        """
        self.registry = registry or HandlerRegistry()
        self.min_confidence = 0.7  # Minimum confidence to accept a handler result
    
    def find_best_handler(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> Optional[HandlerResult]:
        """
        Find the best handler for the given instruction.
        
        Args:
            text: The instruction text
            context: Optional context (e.g., active_file, workspace state)
            category: Optional category to limit search to
        
        Returns:
            Best HandlerResult or None if no suitable handler found
        """
        handlers = self.registry.get_handlers(category)
        
        best_result: Optional[HandlerResult] = None
        best_confidence = 0.0
        
        for handler in handlers:
            # Check if handler can handle this instruction
            confidence = handler.can_handle(text, context)
            
            if confidence > best_confidence:
                # Try to parse with this handler
                # Pass full text as full_message for multiline content extraction
                result = handler.parse(text, context, text)
                
                if result and result.success and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
        
        # Only return if confidence is above threshold
        if best_result and best_confidence >= self.min_confidence:
            return best_result
        
        return None
    
    def try_all_handlers(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> List[HandlerResult]:
        """
        Try all handlers and return all successful results.
        
        Useful for debugging or when multiple interpretations are possible.
        
        Args:
            text: The instruction text
            context: Optional context
            category: Optional category to limit search to
        
        Returns:
            List of all successful HandlerResults, sorted by confidence
        """
        handlers = self.registry.get_handlers(category)
        results = []
        
        for handler in handlers:
            confidence = handler.can_handle(text, context)
            if confidence > 0:
                result = handler.parse(text, context, text)
                if result and result.success:
                    results.append(result)
        
        # Sort by confidence (highest first)
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results
    
    def register_handler(
        self,
        handler: BaseHandler,
        category: str,
        name: Optional[str] = None
    ) -> None:
        """
        Register a handler.
        
        Args:
            handler: Handler instance
            category: Category name
            name: Optional handler name
        """
        self.registry.register(handler, category, name)
    
    def set_min_confidence(self, min_confidence: float) -> None:
        """
        Set minimum confidence threshold.
        
        Args:
            min_confidence: Minimum confidence (0.0 to 1.0)
        """
        self.min_confidence = max(0.0, min(1.0, min_confidence))

