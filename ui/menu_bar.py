"""
Menu Bar Module
Provides the main application menu bar implementation.
"""

import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk


class MenuBar:
    """Class representing the application menu bar."""
    
    def __init__(self, parent, main_window):
        """
        Initialize the menu bar.
        
        Args:
            parent: Parent widget (usually the main window)
            main_window: Reference to the main window object
        """
        self.parent = parent
        self.main_window = main_window
        
        # Create the menu bar
        self.menu_bar = tk.Menu(parent)
        self.parent.configure(menu=self.menu_bar)
        
        # Create the file menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        self.file_menu.add_command(label="New...", command=self.main_window.new_file, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open...", command=self.main_window.open_file, accelerator="Ctrl+O")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save", command=self.main_window.save_file, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save As...", command=self.main_window.save_file_as, accelerator="Ctrl+Shift+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.main_window.on_close)
        
        # Create the edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        
        self.edit_menu.add_command(label="Undo", command=self.main_window.undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.main_window.redo, accelerator="Ctrl+Y")
        
        # Create the view menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        
        self.view_menu.add_command(label="Zoom In", command=lambda: self.main_window.canvas.zoom_in())
        self.view_menu.add_command(label="Zoom Out", command=lambda: self.main_window.canvas.zoom_out())
        self.view_menu.add_command(label="Fit to Screen", command=lambda: self.main_window.canvas.zoom_to_fit())
        self.view_menu.add_command(label="Actual Size (100%)", command=lambda: self.main_window.canvas.zoom_actual())
        
        # Create the image menu
        self.image_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Image", menu=self.image_menu)
        
        # Placeholder for image menu commands
        self.image_menu.add_command(label="Image Size...", command=self._not_implemented)
        self.image_menu.add_command(label="Canvas Size...", command=self._not_implemented)
        
        # Create the layer menu
        self.layer_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Layer", menu=self.layer_menu)
        
        # Placeholder for layer menu commands
        self.layer_menu.add_command(label="New Layer", command=self._not_implemented)
        self.layer_menu.add_command(label="Duplicate Layer", command=self._not_implemented)
        self.layer_menu.add_command(label="Delete Layer", command=self._not_implemented)
        
        # Create the help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.help_menu.add_command(label="About", command=self._show_about)
    
    def _not_implemented(self):
        """Placeholder for not implemented functionality."""
        tk.messagebox.showinfo("Not Implemented", "This feature is not yet implemented.")
    
    def _show_about(self):
        """Show the about dialog."""
        about_text = f"{self.main_window.app_state.app_name} v{self.main_window.app_state.app_version}\n\n" \
                    f"A powerful image editor with layer support\n\n" \
                    f"© 2023 Your Name"
                    
        tk.messagebox.showinfo("About", about_text) 