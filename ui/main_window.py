"""
Main Window Module
Contains the main application window and UI layout for Image_Editor.
"""

import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any, List, Callable

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from core.app_state import AppState
from core.image_handler import ImageHandler
from core.layer_manager import LayerManager, Layer
from ui.panels.layer_panel import LayerPanel
from ui.panels.tool_options_panel import ToolOptionsPanel
from ui.panels.effects_panel import EffectsPanel
from ui.canvas import EditCanvas
from ui.toolbar import Toolbar
from ui.dialogs.new_file_dialog import NewFileDialog
from ui.welcome_screen import WelcomeScreen
from ui.menu_bar import MenuBar
from ui.color_palette import ColorPalette

logger = logging.getLogger("Image_Editor.MainWindow")

class MainWindow:
    """Main application window class for Image_Editor."""
    
    def __init__(self, root: ctk.CTk, app_state: AppState):
        """
        Initialize the main window.
        
        Args:
            root: The root Tk instance
            app_state: The application state object
        """
        self.root = root
        self.app_state = app_state
        self.image_handler = ImageHandler()
        self.layer_manager = None  # Will be initialized when opening or creating an image
        
        # Callback to be called when canvas is ready
        self.on_canvas_ready = None
        
        # Configure the main window
        self.setup_window()
        
        # Create UI components
        self.create_ui()
        
        # Set up event bindings
        self.setup_bindings()
        
        logger.info("Main window initialized")
    
    def setup_window(self):
        """Configure the main application window properties."""
        # Set window title
        self.root.title(f"{self.app_state.app_name} - {self.app_state.app_version}")
        
        # Set initial window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Enable window resizing
        self.root.resizable(True, True)
        
        # Set minimum window size
        self.root.minsize(900, 700)
        
        # Set the window icon
        # TODO: Add application icon
    
    def create_ui(self):
        """Create the user interface components."""
        # Create menubar
        self.menu = MenuBar(self.root, self)
        
        # Create main layout frames with improved styling
        self.main_frame = ctk.CTkFrame(self.root, fg_color=("gray90", "gray17"))
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Left panel for tools with modern styling
        self.left_panel = ctk.CTkFrame(self.main_frame, width=70, corner_radius=10)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        
        # Create toolbar
        self.toolbar = Toolbar(self.left_panel, self)
        self.toolbar.pack(fill=tk.BOTH, expand=True)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Create canvas area with improved styling
        self.canvas_frame = ctk.CTkFrame(self.content_frame, corner_radius=5)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Create edit canvas with modern scroll bars
        self.h_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal")
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical")
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create the canvas
        self.canvas = EditCanvas(
            self.canvas_frame, 
            app_state=self.app_state,
            width=800, 
            height=600,
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Connect the canvas to this window
        self.canvas.set_main_window(self)
        
        # Connect scrollbars to canvas
        self.h_scrollbar.configure(command=self.canvas.xview)
        self.v_scrollbar.configure(command=self.canvas.yview)
        
        # Status bar with modern styling
        self.status_bar = ctk.CTkFrame(self.content_frame, height=30, corner_radius=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        
        self.status_label = ctk.CTkLabel(
            self.status_bar, 
            text="Ready", 
            font=("Inter", 12)
        )
        self.status_label.pack(side=tk.LEFT, padx=12)
        
        self.position_label = ctk.CTkLabel(
            self.status_bar, 
            text="", 
            font=("Inter", 12)
        )
        self.position_label.pack(side=tk.RIGHT, padx=12)
        
        self.zoom_label = ctk.CTkLabel(
            self.status_bar, 
            text="Zoom: 100%", 
            font=("Inter", 12)
        )
        self.zoom_label.pack(side=tk.RIGHT, padx=12)
        
        # Right panel for layers, history, etc.
        self.right_panel = ctk.CTkFrame(self.main_frame, width=280, corner_radius=10)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=8)
        
        # Right panel tabs with modern styling
        self.right_panel_tabs = ctk.CTkTabview(self.right_panel, corner_radius=8)
        self.right_panel_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Add tabs
        self.layers_tab = self.right_panel_tabs.add("Layers")
        self.history_tab = self.right_panel_tabs.add("History")
        self.tool_options_tab = self.right_panel_tabs.add("Tool")
        self.effects_tab = self.right_panel_tabs.add("Effects")
        
        # Layers panel
        self.layer_panel = LayerPanel(self.layers_tab, self)
        self.layer_panel.pack(fill=tk.BOTH, expand=True)
        
        # Tool options panel
        self.tool_options_panel = ToolOptionsPanel(self.tool_options_tab, self)
        self.tool_options_panel.pack(fill=tk.BOTH, expand=True)
        
        # Effects panel
        self.effects_panel = EffectsPanel(self.effects_tab, self)
        self.effects_panel.pack(fill=tk.BOTH, expand=True)
        
        # Show welcome screen
        self.show_welcome_screen()
        
        # If there's a canvas_ready callback, execute it now
        if self.on_canvas_ready and callable(self.on_canvas_ready):
            self.on_canvas_ready(self.canvas)
    
    def setup_bindings(self):
        """Set up event bindings for the application."""
        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-Shift-Z>", lambda e: self.redo())
    
    def show_welcome_screen(self):
        """Display the welcome screen with options to open or create a file."""
        # Create the welcome screen frame
        self.welcome_frame = WelcomeScreen(
            self.canvas_frame, 
            new_file_callback=self.new_file,
            open_file_callback=self.open_file
        )
        self.welcome_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    def new_file(self):
        """Show the new file dialog."""
        NewFileDialog(self.root, self)
    
    def create_new_document(self, width: int, height: int, background_color=(255, 255, 255, 255)):
        """
        Create a new document with specified dimensions and background color.
        
        Args:
            width: Width in pixels
            height: Height in pixels
            background_color: RGBA background color tuple
        """
        try:
            # Ensure background_color has 4 components (RGBA)
            if len(background_color) == 3:
                background_color = (*background_color, 255)  # Add alpha channel
            
            # Create blank image
            new_image = self.image_handler.create_blank_image(width, height, background_color)
            
            # Initialize layer manager
            self.layer_manager = LayerManager(width, height)
            
            # Add background layer
            self.layer_manager.add_layer(Layer("Background", new_image, locked=False))
            
            # Update app state
            self.app_state.current_image = new_image
            self.app_state.image_dimensions = (width, height)
            self.app_state.project_file_path = None
            self.app_state.project_name = "Untitled"
            
            # Close welcome screen if visible
            if hasattr(self, 'welcome_frame') and self.welcome_frame:
                self.welcome_frame.destroy()
                self.welcome_frame = None
            
            # Set image on canvas
            composite = self.layer_manager.render_composite()
            self.canvas.set_image(composite)
            
            # Update UI
            self.update_ui_for_new_document()
            
            logger.info(f"Created new document: {width}x{height}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating new document: {str(e)}")
            messagebox.showerror("Error", f"Failed to create new document: {str(e)}")
            return False
    
    def open_file(self, file_path=None):
        """
        Open an image file.
        
        Args:
            file_path: Optional path to the file to open. If None, a file dialog will be shown.
        """
        if file_path is None:
            # Show file dialog
            file_path = filedialog.askopenfilename(
                title="Open Image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("BMP files", "*.bmp"),
                    ("TIFF files", "*.tiff"),
                    ("GIF files", "*.gif"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:  # User canceled
                return False
        
        try:
            # Load the image
            loaded_image, error_msg = self.image_handler.load_image(file_path)
            
            if loaded_image is None:
                messagebox.showerror("Error", f"Failed to open '{os.path.basename(file_path)}': {error_msg}")
                return False
            
            # Initialize layer manager with image dimensions
            height, width = loaded_image.shape[:2]
            self.layer_manager = LayerManager(width, height)
            
            # Add background layer
            from core.layer_manager import Layer  # Ensure Layer is imported
            self.layer_manager.add_layer(Layer("Background", loaded_image, locked=False))
            
            # Update app state
            self.app_state.current_image = loaded_image
            self.app_state.image_dimensions = (width, height)
            self.app_state.project_file_path = file_path
            self.app_state.project_name = os.path.basename(file_path)
            
            # Close welcome screen if visible
            if hasattr(self, 'welcome_frame') and self.welcome_frame:
                self.welcome_frame.destroy()
                self.welcome_frame = None
            
            # Set image on canvas
            composite = self.layer_manager.render_composite()
            self.canvas.set_image(composite)
            
            # Update UI
            self.update_ui_for_new_document()
            
            # Add to recent files
            self.add_to_recent_files(file_path)
            
            logger.info(f"Opened file: {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {str(e)}")
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            return False
    
    def save_file(self):
        """Save the current document."""
        if self.app_state.project_file_path:
            # Save to existing file
            return self._save_to_path(self.app_state.project_file_path)
        else:
            # No file path yet, use save as
            return self.save_file_as()
    
    def save_file_as(self):
        """Save the current document with a new file name."""
        # Show save dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("BMP files", "*.bmp"),
                ("TIFF files", "*.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:  # User canceled
            return False
        
        return self._save_to_path(file_path)
    
    def _save_to_path(self, file_path):
        """
        Save the current document to the specified path.
        
        Args:
            file_path: Path to save the file to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.layer_manager:
                # Render composite image
                composite = self.layer_manager.render_composite()
                
                # Save the image
                error_msg = self.image_handler.save_image(composite, file_path)
                
                if error_msg is None:
                    # Update app state
                    self.app_state.project_file_path = file_path
                    self.app_state.project_name = os.path.basename(file_path)
                    self.app_state.project_saved = True
                    
                    # Update UI
                    self.update_window_title()
                    
                    # Add to recent files
                    self.add_to_recent_files(file_path)
                    
                    logger.info(f"Saved file: {file_path}")
                    return True
                else:
                    messagebox.showerror("Error", f"Failed to save to '{os.path.basename(file_path)}': {error_msg}")
                    return False
            else:
                messagebox.showwarning("Warning", "No image to save")
                return False
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {str(e)}")
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            return False
    
    def update_ui_for_new_document(self):
        """Update the UI after loading or creating a new document."""
        # Update window title
        self.update_window_title()
        
        # Update layers panel
        if self.layer_panel:
            try:
                self.layer_panel.refresh()
            except Exception as e:
                logger.error(f"Error refreshing layer panel: {str(e)}")
        
        # Fit image to view
        self.canvas.zoom_to_fit()
        
        # Update status
        self.set_status("Document ready")
        
        # Make sure first tab (Layers) is selected
        self.right_panel_tabs.set("Layers")
    
    def update_window_title(self):
        """Update the window title based on the current document."""
        title = f"{self.app_state.app_name} - {self.app_state.project_name}"
        if not self.app_state.project_saved:
            title += " *"
        self.root.title(title)
    
    def add_to_recent_files(self, file_path):
        """
        Add a file to the recent files list.
        
        Args:
            file_path: Path to add to recent files
        """
        # Get recent files from settings
        recent_files = self.app_state.settings["file_handling"].get("recent_files", [])
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning of list
        recent_files.insert(0, file_path)
        
        # Limit list size
        max_recent = 10
        if len(recent_files) > max_recent:
            recent_files = recent_files[:max_recent]
        
        # Update settings
        self.app_state.settings["file_handling"]["recent_files"] = recent_files
        
        # Save settings
        self.app_state.save_settings()
    
    def undo(self):
        """Undo the last action."""
        if self.app_state.can_undo():
            state = self.app_state.undo()
            if state:
                # TODO: Implement undo handling
                logger.info(f"Undo: {state['name']}")
                self.set_status(f"Undo: {state['name']}")
                
                # Update window title to show unsaved state
                self.update_window_title()
    
    def redo(self):
        """Redo the last undone action."""
        if self.app_state.can_redo():
            state = self.app_state.redo()
            if state:
                # TODO: Implement redo handling
                logger.info(f"Redo: {state['name']}")
                self.set_status(f"Redo: {state['name']}")
                
                # Update window title to show unsaved state
                self.update_window_title()
    
    def set_status(self, message):
        """Set the status bar message."""
        self.status_label.configure(text=message)
    
    def update_cursor_position(self, x, y):
        """Update the cursor position display in the status bar."""
        self.position_label.configure(text=f"X: {x}, Y: {y}")
    
    def set_zoom_level(self, zoom_level):
        """Update the zoom level display in the status bar."""
        zoom_percent = int(zoom_level * 100)
        self.zoom_label.configure(text=f"Zoom: {zoom_percent}%")
    
    def refresh_view(self):
        """Refresh the view to reflect changes in layers or image data."""
        if self.layer_manager:
            # Render composite
            composite = self.layer_manager.render_composite()
            
            # Update canvas
            self.canvas.set_image(composite)
            
            # Update layer panel
            if self.layer_panel:
                self.layer_panel.refresh()
    
    def on_close(self):
        """Handle window close event."""
        # Check for unsaved changes
        if not self.app_state.project_saved and self.app_state.current_image is not None:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Do you want to save changes before closing?",
                icon=messagebox.WARNING
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes, save
                saved = self.save_file()
                if not saved:  # Save failed or canceled
                    return
        
        # Close the application
        self.root.destroy() 