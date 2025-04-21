#!/usr/bin/env python3
"""
PhotoForge Pro - Advanced Image Editor
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
        logging.FileHandler("photoforge.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("PhotoForge")

# Add project directory to path to make imports work properly
project_root = Path(__file__).parent.parent
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
from photoforge_pro.ui.main_window import MainWindow
from photoforge_pro.core.app_state import AppState

def setup_appearance():
    """Configure the appearance settings for the application."""
    ctk.set_appearance_mode("System")  # Options: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "dark-blue", "green"

def main():
    """Main application entry point."""
    logger.info("Starting PhotoForge Pro application")
    
    # Configure appearance
    setup_appearance()
    
    # Create app state
    app_state = AppState()
    
    # Create main application window
    root = ctk.CTk()
    app = MainWindow(root, app_state)
    
    # Run the application
    root.mainloop()
    
    logger.info("PhotoForge Pro application closed")

if __name__ == "__main__":
    main() 