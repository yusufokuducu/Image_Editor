"""
Main Window Module
Contains the main application window and UI layout for Image_Editor.
"""

import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any, List

import customtkinter as ctk
from PIL import Image, ImageTk

from image_editor.core.app_state import AppState
from image_editor.core.image_handler import ImageHandler
from image_editor.core.layer_manager import LayerManager, Layer
from image_editor.ui.panels.layer_panel import LayerPanel
from image_editor.ui.panels.tool_options_panel import ToolOptionsPanel
from image_editor.ui.canvas import EditCanvas
from image_editor.ui.toolbar import Toolbar
from image_editor.ui.menubar import create_menubar
from image_editor.ui.dialogs.new_file_dialog import NewFileDialog

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
        self.menu = create_menubar(self.root, self)
        
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
        
        self.canvas = EditCanvas(
            self.canvas_frame, 
            app_state=self.app_state,
            width=800, 
            height=600,
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
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
        
        # Layers panel
        self.layer_panel = LayerPanel(self.layers_tab, self)
        self.layer_panel.pack(fill=tk.BOTH, expand=True)
        
        # Tool options panel
        self.tool_options_panel = ToolOptionsPanel(self.tool_options_tab, self)
        self.tool_options_panel.pack(fill=tk.BOTH, expand=True)
        
        # Show welcome screen
        self.show_welcome_screen()
    
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
        # Create a frame for the welcome screen with modern styling
        self.welcome_frame = ctk.CTkFrame(self.canvas_frame, corner_radius=15, fg_color=("gray85", "gray20"))
        self.welcome_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Add logo or icon (placeholder)
        # TODO: Add actual logo
        logo_frame = ctk.CTkFrame(self.welcome_frame, width=100, height=100, corner_radius=15, fg_color="transparent")
        logo_frame.pack(pady=(30, 10))
        
        logo_placeholder = ctk.CTkLabel(
            logo_frame,
            text="IE",
            font=("Inter", 48, "bold"),
            text_color=("#1f538d", "#2d7bbf")
        )
        logo_placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Welcome message with modern typography
        welcome_label = ctk.CTkLabel(
            self.welcome_frame, 
            text=f"Welcome to {self.app_state.app_name}",
            font=("Inter", 28, "bold")
        )
        welcome_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            self.welcome_frame,
            text="Professional Image Editing Made Simple",
            font=("Inter", 16)
        )
        subtitle_label.pack(pady=(0, 25))
        
        # Button container for better layout
        button_container = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        button_container.pack(pady=(0, 30), padx=50)
        
        # Buttons with modern styling
        new_file_button = ctk.CTkButton(
            button_container,
            text="Create New Image",
            font=("Inter", 14),
            height=38,
            corner_radius=8,
            command=self.new_file
        )
        new_file_button.pack(fill=tk.X, pady=8)
        
        open_file_button = ctk.CTkButton(
            button_container,
            text="Open Existing Image",
            font=("Inter", 14),
            height=38,
            corner_radius=8,
            command=self.open_file
        )
        open_file_button.pack(fill=tk.X, pady=8)
        
        # Recent files section with modern styling
        if self.app_state.settings["file_handling"]["recent_files"]:
            # Separator
            separator = ctk.CTkFrame(self.welcome_frame, height=1, fg_color=("gray70", "gray40"))
            separator.pack(fill=tk.X, padx=40, pady=20)
            
            recent_label = ctk.CTkLabel(
                self.welcome_frame,
                text="RECENT FILES",
                font=("Inter", 14, "bold"),
                text_color=("gray50", "gray70")
            )
            recent_label.pack(pady=(0, 10))
            
            # Container for recent files
            recent_container = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
            recent_container.pack(padx=40, pady=0, fill=tk.X)
            
            for file_path in self.app_state.settings["file_handling"]["recent_files"][:5]:
                file_button = ctk.CTkButton(
                    recent_container,
                    text=os.path.basename(file_path),
                    font=("Inter", 12),
                    height=32,
                    corner_radius=6,
                    fg_color=("gray80", "gray30"),
                    hover_color=("gray70", "gray40"),
                    anchor="w",
                    command=lambda p=file_path: self.open_file(p)
                )
                file_button.pack(fill=tk.X, pady=4)
    
    def new_file(self):
        """Open the new file dialog."""
        dialog = NewFileDialog(self.root, self)
        self.root.wait_window(dialog)
    
    def create_new_document(self, width: int, height: int, background_color=(255, 255, 255, 255)):
        """
        Create a new document with the specified properties.
        
        Args:
            width: Width of the new document in pixels
            height: Height of the new document in pixels
            background_color: Background color (RGBA)
        """
        # Create a new empty image
        blank_image = self.image_handler.create_blank_image(width, height, background_color[:3], True)
        
        # Initialize layer manager
        self.layer_manager = LayerManager(width, height)
        
        # Create background layer
        background_layer = Layer(
            name="Background",
            image_data=blank_image,
            visible=True,
            opacity=1.0,
            blend_mode="normal",
            locked=False
        )
        
        # Add the layer to the layer manager
        self.layer_manager.add_layer(background_layer)
        
        # Update application state
        self.app_state.create_new_image(width, height)
        self.app_state.current_image = blank_image
        
        # Update UI
        self.update_ui_for_new_document()
        
        logger.info(f"Created new document {width}x{height}")
    
    def open_file(self, file_path=None):
        """
        Open an image file.
        
        Args:
            file_path: Path to the image file or None to show file dialog
        """
        if file_path is None:
            # Show file dialog
            file_path = filedialog.askopenfilename(
                title="Open Image",
                filetypes=[
                    ("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.tif *.webp"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("PNG", "*.png"),
                    ("BMP", "*.bmp"),
                    ("GIF", "*.gif"),
                    ("TIFF", "*.tiff *.tif"),
                    ("WebP", "*.webp"),
                    ("All Files", "*.*")
                ]
            )
            
            if not file_path:
                return  # User cancelled
        
        # Load the image
        image_data, error = self.image_handler.load_image(file_path)
        
        if error is not None:
            messagebox.showerror("Error", f"Failed to open image: {error}")
            return
        
        # Set up the document
        height, width = image_data.shape[:2]
        
        # Initialize layer manager
        self.layer_manager = LayerManager(width, height)
        
        # Create background layer
        background_layer = Layer(
            name="Background",
            image_data=image_data,
            visible=True,
            opacity=1.0,
            blend_mode="normal",
            locked=False
        )
        
        # Add the layer to the layer manager
        self.layer_manager.add_layer(background_layer)
        
        # Update application state
        self.app_state.project_name = os.path.basename(file_path)
        self.app_state.project_file_path = file_path
        self.app_state.project_saved = True
        self.app_state.image_dimensions = (width, height)
        self.app_state.current_image = image_data
        
        # Add to recent files
        self.add_to_recent_files(file_path)
        
        # Update UI
        self.update_ui_for_new_document()
        
        logger.info(f"Opened image: {file_path}")
    
    def save_file(self):
        """Save the current document."""
        if not self.app_state.project_file_path:
            # If no file path is set, use save as
            self.save_file_as()
            return
        
        # Render composite image
        if self.layer_manager:
            composite = self.layer_manager.render_composite()
            
            # Save the image
            error = self.image_handler.save_image(
                composite,
                self.app_state.project_file_path,
                self.app_state.settings["file_handling"]["export_quality_jpeg"]
            )
            
            if error:
                messagebox.showerror("Error", f"Failed to save image: {error}")
                return
            
            # Update application state
            self.app_state.project_saved = True
            
            # Update UI
            self.update_window_title()
            self.status_label.configure(text=f"Saved to {self.app_state.project_file_path}")
            
            logger.info(f"Saved image to: {self.app_state.project_file_path}")
        else:
            messagebox.showerror("Error", "No document to save.")
    
    def save_file_as(self):
        """Save the current document with a new file name."""
        if not self.layer_manager:
            messagebox.showerror("Error", "No document to save.")
            return
        
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=[
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("BMP", "*.bmp"),
                ("TIFF", "*.tiff *.tif"),
                ("WebP", "*.webp"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return  # User cancelled
        
        # Render composite image
        composite = self.layer_manager.render_composite()
        
        # Save the image
        error = self.image_handler.save_image(
            composite,
            file_path,
            self.app_state.settings["file_handling"]["export_quality_jpeg"]
        )
        
        if error:
            messagebox.showerror("Error", f"Failed to save image: {error}")
            return
        
        # Update application state
        self.app_state.project_file_path = file_path
        self.app_state.project_name = os.path.basename(file_path)
        self.app_state.project_saved = True
        
        # Add to recent files
        self.add_to_recent_files(file_path)
        
        # Update UI
        self.update_window_title()
        self.status_label.configure(text=f"Saved to {file_path}")
        
        logger.info(f"Saved image as: {file_path}")
    
    def update_ui_for_new_document(self):
        """Update UI components when a new document is created or opened."""
        # Remove welcome screen if it exists
        if hasattr(self, 'welcome_frame') and self.welcome_frame.winfo_exists():
            self.welcome_frame.destroy()
        
        # Update window title
        self.update_window_title()
        
        # Update canvas
        self.canvas.set_image(self.app_state.current_image)
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))
        
        # Update layer panel
        self.layer_panel.update_layers()
        
        # Show message in status bar
        self.status_label.configure(text="Ready")
        
        # Update zoom label
        self.zoom_label.configure(text=f"Zoom: {int(self.app_state.zoom_level * 100)}%")
    
    def update_window_title(self):
        """Update the window title with the current document name and saved status."""
        saved_indicator = "" if self.app_state.project_saved else "*"
        self.root.title(f"{self.app_state.app_name} - {saved_indicator}{self.app_state.project_name}")
    
    def add_to_recent_files(self, file_path):
        """
        Add a file path to the recent files list.
        
        Args:
            file_path: Path to add to recent files
        """
        recent_files = self.app_state.settings["file_handling"]["recent_files"]
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to the start of the list
        recent_files.insert(0, file_path)
        
        # Limit list size
        self.app_state.settings["file_handling"]["recent_files"] = recent_files[:10]
        
        # Save settings
        self.app_state.save_settings()
    
    def undo(self):
        """Perform undo operation."""
        if self.app_state.can_undo():
            state = self.app_state.undo()
            if state:
                # TODO: Apply the state
                self.status_label.configure(text=f"Undo: {state['name']}")
                logger.info(f"Undo performed: {state['name']}")
        else:
            self.status_label.configure(text="Nothing to undo")
    
    def redo(self):
        """Perform redo operation."""
        if self.app_state.can_redo():
            state = self.app_state.redo()
            if state:
                # TODO: Apply the state
                self.status_label.configure(text=f"Redo: {state['name']}")
                logger.info(f"Redo performed: {state['name']}")
        else:
            self.status_label.configure(text="Nothing to redo")
    
    def set_status(self, message):
        """Update the status bar message."""
        self.status_label.configure(text=message)
    
    def update_cursor_position(self, x, y):
        """Update the cursor position display in the status bar."""
        if self.app_state.current_image is not None:
            self.position_label.configure(text=f"X: {x}, Y: {y}")
    
    def set_zoom_level(self, zoom_level):
        """
        Set the zoom level for the canvas.
        
        Args:
            zoom_level: New zoom level (as a float, e.g., 1.0 = 100%)
        """
        # Update application state
        self.app_state.zoom_level = zoom_level
        
        # Update zoom label
        self.zoom_label.configure(text=f"Zoom: {int(zoom_level * 100)}%")
        
        # Update canvas zoom
        self.canvas.set_zoom(zoom_level)
    
    def on_close(self):
        """Handle application close event."""
        # Check for unsaved changes
        if not self.app_state.project_saved and self.layer_manager is not None:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                icon="warning"
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_file()
        
        # Save application settings
        self.app_state.save_settings()
        
        # Close the application
        self.root.destroy() 