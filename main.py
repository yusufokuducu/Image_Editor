#!/usr/bin/env python3
"""
Image_Editor - Advanced Image Editor
Main Application Entry Point
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("image_editor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("Image_Editor")

# Add project directory to path to make imports work properly
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import customtkinter as ctk
    from PIL import Image, ImageTk
    import numpy as np
    import cv2
except ImportError as e:
    logger.critical(f"Failed to import required libraries: {str(e)}")
    print(f"Error: Missing required dependency: {str(e)}")
    print("Please install required dependencies using: pip install -r requirements.txt")
    sys.exit(1)

# Import application components
from ui.main_window import MainWindow
from core.app_state import AppState
from tools.crop_tool import CropTool
from tools.move_tool import MoveTool
from tools.brush_tool import BrushTool
from tools.eraser_tool import EraserTool
from tools.effects_tool import EffectsTool

def setup_appearance():
    """Configure the appearance settings for the application."""
    ctk.set_appearance_mode("Dark")  # Options: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (default), "dark-blue", "green"

def setup_tools(app_state, canvas):
    """Initialize all tools and attach them to the app state."""
    logger.info("Initializing tools")
    
    # Create tool instances
    move_tool = MoveTool(app_state)
    crop_tool = CropTool(app_state)
    brush_tool = BrushTool(app_state)
    eraser_tool = EraserTool(app_state)
    effects_tool = EffectsTool(app_state)
    
    # Store tools in app_state
    app_state.tools = {
        "move": move_tool,
        "crop": crop_tool,
        "brush": brush_tool,
        "eraser": eraser_tool,
        "effects": effects_tool
    }
    
    # Set the active tool (default: move tool)
    app_state.set_active_tool("move", canvas)
    
    logger.info("Tools initialized")

def main():
    """Main application entry point."""
    logger.info("Starting Image_Editor application")
    
    # Configure appearance
    setup_appearance()
    
    # Create app state
    app_state = AppState()
    
    # Create main application window
    root = ctk.CTk()
    app = MainWindow(root, app_state)
    
    # Set up tools after the canvas is created
    if hasattr(app, 'canvas'):
        setup_tools(app_state, app.canvas)
    else:
        logger.warning("Canvas not yet available, tools will be initialized later")
        # Add a callback to initialize tools once the canvas is ready
        app.on_canvas_ready = lambda canvas: setup_tools(app_state, canvas)
    
    # Run the application
    root.mainloop()
    
    logger.info("Image_Editor application closed")

if __name__ == "__main__":
    main() 