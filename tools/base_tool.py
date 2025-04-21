"""
Base Tool Module
Provides the abstract base class for all editing tools.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any

logger = logging.getLogger("Image_Editor.BaseTool")

class BaseTool(ABC):
    """Base class for all tools in Image_Editor."""
    
    def __init__(self, app_state, name):
        """
        Initialize the base tool.
        
        Args:
            app_state: The application state
            name: Name of the tool
        """
        self.app_state = app_state
        self.name = name
        self.active = False
        self.canvas = None
        self.settings = {}
        
        # Initialize tool-specific settings
        self.init_settings()
        
        logger.debug(f"Created tool: {name}")
    
    def init_settings(self):
        """Initialize tool-specific settings. Override in subclasses."""
        pass
    
    @abstractmethod
    def activate(self):
        """Activate the tool."""
        pass
    
    @abstractmethod
    def deactivate(self):
        """Deactivate the tool."""
        pass
    
    def get_cursor(self) -> Optional[str]:
        """
        Get the cursor to use when this tool is active.
        
        Returns:
            Cursor name or None for default cursor
        """
        return None
    
    def update_settings(self, settings: dict):
        """
        Update tool settings.
        
        Args:
            settings: Dictionary of settings to update
        """
        self.settings.update(settings)
    
    @abstractmethod
    def on_mouse_down(self, x: int, y: int, event):
        """
        Handle mouse button press.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        pass
    
    @abstractmethod
    def on_mouse_up(self, x: int, y: int, event):
        """
        Handle mouse button release.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        pass
    
    @abstractmethod
    def on_mouse_drag(self, x: int, y: int, event):
        """
        Handle mouse drag.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        pass
    
    @abstractmethod
    def on_mouse_move(self, x: int, y: int, event):
        """
        Handle mouse movement without dragging.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        pass 