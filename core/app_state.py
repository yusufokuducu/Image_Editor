"""
Application State Management Module
Manages the state and data of the application, including:
- Current image data
- Project information
- Application settings
- Current tool and operation states
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("PhotoForge.AppState")

class AppState:
    """
    Class to manage the application's global state.
    Acts as a centralized data store for the application.
    """
    
    def __init__(self):
        """Initialize the application state with default values."""
        # Application information
        self.app_name = "Image_Editor"
        self.app_version = "0.1.0"
        
        # Project state
        self.project_file_path: Optional[str] = None
        self.project_saved: bool = True
        self.project_name: str = "Untitled"
        
        # Current image state
        self.current_image = None  # Will hold the primary image data
        self.image_dimensions: Tuple[int, int] = (0, 0)  # (width, height)
        self.zoom_level: float = 1.0
        
        # Layers management
        self.layers: List[Dict[str, Any]] = []
        self.active_layer_index: int = -1
        
        # History management for undo/redo
        self.history: List[Dict[str, Any]] = []
        self.history_position: int = -1
        self.max_history_size: int = 100  # Maximum number of history states to keep
        
        # Tool state
        self.current_tool: str = "move_tool"  # Default tool
        self.tool_settings: Dict[str, Dict[str, Any]] = self._init_default_tool_settings()
        
        # Selection state
        self.has_selection: bool = False
        self.selection_bounds: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
        
        # Application settings
        self.settings = self._load_settings()
        
        logger.info("AppState initialized")
    
    def _init_default_tool_settings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default settings for all tools."""
        return {
            "brush_tool": {
                "size": 10,
                "hardness": 0.8,
                "opacity": 1.0,
                "flow": 1.0,
                "spacing": 0.1,
                "color": (0, 0, 0)  # RGB
            },
            "eraser_tool": {
                "size": 10,
                "hardness": 0.8,
                "opacity": 1.0,
                "flow": 1.0,
                "spacing": 0.1
            },
            "selection_tool": {
                "mode": "rectangle",  # rectangle, ellipse, lasso, magic_wand
                "feather": 0,  # Feathering radius in pixels
                "anti_alias": True,
            },
            "text_tool": {
                "font": "Arial",
                "size": 12,
                "color": (0, 0, 0),  # RGB
                "alignment": "left",  # left, center, right
                "bold": False,
                "italic": False
            },
            "crop_tool": {
                "aspect_ratio": None,  # None for free form, or ratio like 16/9, 4/3, 1/1
                "rule_of_thirds": True  # Show rule of thirds grid
            },
            "move_tool": {
                "auto_select_layer": True
            }
        }

    def _load_settings(self) -> Dict[str, Any]:
        """Load application settings from config file or use defaults."""
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        default_settings = {
            "appearance": {
                "theme": "dark",
                "accent_color": "blue",
                "interface_scaling": 1.0
            },
            "performance": {
                "preview_quality": "medium",  # low, medium, high
                "undo_levels": 100,
                "use_gpu_acceleration": False,
                "background_processing": True
            },
            "file_handling": {
                "autosave_enabled": True,
                "autosave_interval_minutes": 10,
                "recent_files": [],
                "default_save_format": "png",
                "export_quality_jpeg": 95
            },
            "workspace": {
                "show_rulers": True,
                "show_grid": False,
                "grid_size": 32,
                "snap_to_grid": False,
                "panels_layout": "default"
            },
            "shortcuts": {
                # Default keyboard shortcuts would go here
            }
        }
        
        # Try to load settings from file
        try:
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    loaded_settings = json.load(f)
                logger.info("Settings loaded from file")
                
                # Merge with defaults to ensure all settings exist
                self._deep_update(default_settings, loaded_settings)
                return default_settings
            else:
                logger.info("Settings file not found, using defaults")
                self._save_settings(default_settings)  # Save defaults for future
                return default_settings
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return default_settings
    
    def _save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save application settings to config file."""
        settings_path = Path(__file__).parent.parent / "config" / "settings.json"
        try:
            # Ensure directory exists
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info("Settings saved to file")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def save_settings(self) -> bool:
        """Public method to save current settings."""
        return self._save_settings(self.settings)
    
    def _deep_update(self, target: Dict, source: Dict) -> None:
        """
        Recursively update a nested dictionary with values from another dictionary.
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def create_new_image(self, width: int, height: int, background_color=(255, 255, 255)) -> None:
        """Create a new image with specified dimensions and background color."""
        self.project_name = "Untitled"
        self.project_file_path = None
        self.project_saved = False
        self.image_dimensions = (width, height)
        
        # Reset layers
        self.layers = [{
            "name": "Background",
            "visible": True,
            "opacity": 1.0,
            "blending_mode": "normal",
            "locked": False
        }]
        self.active_layer_index = 0
        
        # Reset history
        self.history = []
        self.history_position = -1
        
        # Reset selection
        self.has_selection = False
        self.selection_bounds = None
        
        logger.info(f"Created new {width}x{height} image")
    
    def add_history_state(self, state_name: str, state_data: Dict[str, Any]) -> None:
        """Add a new state to the history stack for undo/redo functionality."""
        # If we're not at the end of the history, truncate the future states
        if self.history_position < len(self.history) - 1:
            self.history = self.history[:self.history_position + 1]
        
        # Add the new state
        self.history.append({
            "name": state_name,
            "data": state_data,
            "timestamp": import_datetime().now().isoformat()
        })
        self.history_position = len(self.history) - 1
        
        # Keep history size within limits
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
            self.history_position = len(self.history) - 1
        
        # Mark project as unsaved
        self.project_saved = False
        
        logger.debug(f"Added history state: {state_name}")
    
    def can_undo(self) -> bool:
        """Check if undo operation is available."""
        return self.history_position > 0
    
    def can_redo(self) -> bool:
        """Check if redo operation is available."""
        return self.history_position < len(self.history) - 1
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """Move back one step in history and return the previous state."""
        if not self.can_undo():
            return None
        
        self.history_position -= 1
        state = self.history[self.history_position]
        self.project_saved = False
        logger.debug(f"Undo to state: {state['name']}")
        return state
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """Move forward one step in history and return the next state."""
        if not self.can_redo():
            return None
        
        self.history_position += 1
        state = self.history[self.history_position]
        self.project_saved = False
        logger.debug(f"Redo to state: {state['name']}")
        return state

# Helper function to avoid circular import
def import_datetime():
    import datetime
    return datetime 