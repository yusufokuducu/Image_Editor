"""
New File Dialog Module
Dialog for creating a new image file.
"""

import logging
import tkinter as tk
from typing import Optional, Tuple, List, Dict, Any

import customtkinter as ctk

logger = logging.getLogger("PhotoForge.Dialogs.NewFile")

class NewFileDialog(ctk.CTkToplevel):
    """Dialog for creating a new image file."""
    
    def __init__(self, parent, main_window):
        """
        Initialize the new file dialog.
        
        Args:
            parent: Parent widget
            main_window: Reference to the main window
        """
        super().__init__(parent)
        
        self.main_window = main_window
        
        # Configure dialog
        self.title("New Image")
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Create dialog content
        self.create_widgets()
        
        logger.info("New file dialog opened")
    
    def create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Create New Image",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Preset section
        preset_frame = ctk.CTkFrame(main_frame)
        preset_frame.pack(fill=tk.X, padx=10, pady=10)
        
        preset_label = ctk.CTkLabel(preset_frame, text="Preset:")
        preset_label.pack(side=tk.LEFT, padx=10)
        
        # Define presets
        self.presets = [
            {"name": "Custom", "width": 800, "height": 600},
            {"name": "640x480", "width": 640, "height": 480},
            {"name": "800x600", "width": 800, "height": 600},
            {"name": "1024x768", "width": 1024, "height": 768},
            {"name": "1280x720 (HD)", "width": 1280, "height": 720},
            {"name": "1920x1080 (Full HD)", "width": 1920, "height": 1080},
            {"name": "2560x1440 (QHD)", "width": 2560, "height": 1440},
            {"name": "3840x2160 (4K UHD)", "width": 3840, "height": 2160},
            {"name": "Instagram Post", "width": 1080, "height": 1080},
            {"name": "Instagram Story", "width": 1080, "height": 1920},
            {"name": "Twitter Header", "width": 1500, "height": 500},
            {"name": "Facebook Cover", "width": 851, "height": 315}
        ]
        
        preset_names = [preset["name"] for preset in self.presets]
        
        self.preset_var = tk.StringVar(value=preset_names[0])
        preset_dropdown = ctk.CTkOptionMenu(
            preset_frame, 
            values=preset_names,
            variable=self.preset_var,
            command=self.on_preset_selected
        )
        preset_dropdown.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Dimensions section
        dimensions_frame = ctk.CTkFrame(main_frame)
        dimensions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        width_label = ctk.CTkLabel(dimensions_frame, text="Width:")
        width_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.width_var = tk.StringVar(value="800")
        width_entry = ctk.CTkEntry(
            dimensions_frame, 
            textvariable=self.width_var,
            width=100
        )
        width_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        width_unit_label = ctk.CTkLabel(dimensions_frame, text="pixels")
        width_unit_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        height_label = ctk.CTkLabel(dimensions_frame, text="Height:")
        height_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.height_var = tk.StringVar(value="600")
        height_entry = ctk.CTkEntry(
            dimensions_frame, 
            textvariable=self.height_var,
            width=100
        )
        height_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        height_unit_label = ctk.CTkLabel(dimensions_frame, text="pixels")
        height_unit_label.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Configure grid
        dimensions_frame.grid_columnconfigure(1, weight=1)
        
        # Resolution section
        resolution_frame = ctk.CTkFrame(main_frame)
        resolution_frame.pack(fill=tk.X, padx=10, pady=10)
        
        resolution_label = ctk.CTkLabel(resolution_frame, text="Resolution:")
        resolution_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        
        self.resolution_var = tk.StringVar(value="72")
        resolution_entry = ctk.CTkEntry(
            resolution_frame, 
            textvariable=self.resolution_var,
            width=100
        )
        resolution_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        resolution_unit_label = ctk.CTkLabel(resolution_frame, text="pixels/inch")
        resolution_unit_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Configure grid
        resolution_frame.grid_columnconfigure(1, weight=1)
        
        # Color mode section
        color_mode_frame = ctk.CTkFrame(main_frame)
        color_mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        color_mode_label = ctk.CTkLabel(color_mode_frame, text="Color Mode:")
        color_mode_label.pack(side=tk.LEFT, padx=10)
        
        self.color_mode_var = tk.StringVar(value="RGB")
        color_mode_dropdown = ctk.CTkOptionMenu(
            color_mode_frame, 
            values=["RGB", "RGBA", "Grayscale"],
            variable=self.color_mode_var
        )
        color_mode_dropdown.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Background color section
        bg_color_frame = ctk.CTkFrame(main_frame)
        bg_color_frame.pack(fill=tk.X, padx=10, pady=10)
        
        bg_color_label = ctk.CTkLabel(bg_color_frame, text="Background:")
        bg_color_label.pack(side=tk.LEFT, padx=10)
        
        self.bg_color_var = tk.StringVar(value="White")
        bg_color_dropdown = ctk.CTkOptionMenu(
            bg_color_frame, 
            values=["White", "Black", "Transparent", "Custom..."],
            variable=self.bg_color_var,
            command=self.on_bg_color_selected
        )
        bg_color_dropdown.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Color preview (placeholder for now)
        self.color_preview = ctk.CTkFrame(
            bg_color_frame, 
            width=30, 
            height=30,
            fg_color="white",
            corner_radius=15
        )
        self.color_preview.pack(side=tk.LEFT, padx=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        cancel_button = ctk.CTkButton(
            button_frame, 
            text="Cancel",
            command=self.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
        
        create_button = ctk.CTkButton(
            button_frame, 
            text="Create",
            command=self.on_create
        )
        create_button.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.X, expand=True)
    
    def on_preset_selected(self, preset_name):
        """
        Handle preset selection.
        
        Args:
            preset_name: Selected preset name
        """
        # Find the preset by name
        preset = next((p for p in self.presets if p["name"] == preset_name), None)
        
        if preset and preset["name"] != "Custom":
            # Update width and height
            self.width_var.set(str(preset["width"]))
            self.height_var.set(str(preset["height"]))
    
    def on_bg_color_selected(self, color_name):
        """
        Handle background color selection.
        
        Args:
            color_name: Selected color name
        """
        if color_name == "White":
            self.color_preview.configure(fg_color="white")
        elif color_name == "Black":
            self.color_preview.configure(fg_color="black")
        elif color_name == "Transparent":
            # Create checkered pattern for transparent preview
            self.color_preview.configure(fg_color="#DDDDDD")
        elif color_name == "Custom...":
            # Placeholder for color picker dialog
            self.color_preview.configure(fg_color="red")
    
    def on_create(self):
        """Handle create button click."""
        try:
            # Get dimensions
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            # Validate dimensions
            if width <= 0 or height <= 0:
                raise ValueError("Width and height must be positive values.")
            
            if width > 10000 or height > 10000:
                raise ValueError("Maximum image size is 10000x10000 pixels.")
            
            # Get background color
            bg_color_name = self.bg_color_var.get()
            if bg_color_name == "White":
                bg_color = (255, 255, 255, 255)
            elif bg_color_name == "Black":
                bg_color = (0, 0, 0, 255)
            elif bg_color_name == "Transparent":
                bg_color = (0, 0, 0, 0)
            else:  # Custom
                bg_color = (255, 0, 0, 255)  # Red for now
            
            # Create the new document
            self.main_window.create_new_document(width, height, bg_color)
            
            # Close the dialog
            self.destroy()
            
            logger.info(f"Created new image ({width}x{height})")
            
        except ValueError as e:
            # Show error message
            tk.messagebox.showerror("Invalid Input", str(e))
            logger.error(f"Invalid input in new file dialog: {str(e)}")
        except Exception as e:
            # Show error message
            tk.messagebox.showerror("Error", f"An error occurred: {str(e)}")
            logger.error(f"Error in new file dialog: {str(e)}") 