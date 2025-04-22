"""
Welcome Screen Module
Provides the initial welcome screen shown when the application starts.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional


class WelcomeScreen(ctk.CTkFrame):
    """Welcome screen widget displayed when the application starts."""
    
    def __init__(self, parent, new_file_callback: Callable, open_file_callback: Callable):
        """
        Initialize the welcome screen.
        
        Args:
            parent: Parent widget
            new_file_callback: Callback for creating a new file
            open_file_callback: Callback for opening an existing file
        """
        super().__init__(parent, corner_radius=15, fg_color=("gray85", "gray20"))
        
        # Store callbacks
        self.new_file_callback = new_file_callback
        self.open_file_callback = open_file_callback
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface elements."""
        # Add logo or icon (placeholder)
        logo_frame = ctk.CTkFrame(self, width=100, height=100, corner_radius=15, fg_color="transparent")
        logo_frame.pack(pady=(30, 10))
        
        logo_placeholder = ctk.CTkLabel(
            logo_frame,
            text="Image Editor",
            font=("Inter", 24, "bold"),
            text_color=("gray10", "gray90")
        )
        logo_placeholder.pack(expand=True)
        
        # Welcome message
        welcome_msg = ctk.CTkLabel(
            self,
            text="Welcome to Image Editor",
            font=("Inter", 20, "bold")
        )
        welcome_msg.pack(pady=(0, 10))
        
        description = ctk.CTkLabel(
            self,
            text="Create a new image or open an existing one to get started.",
            font=("Inter", 14)
        )
        description.pack(pady=(0, 20))
        
        # Action buttons with modern styling
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.pack(pady=10, padx=40)
        
        new_file_btn = ctk.CTkButton(
            buttons_frame,
            text="New Image",
            font=("Inter", 14),
            width=150,
            height=40,
            corner_radius=8,
            command=self.new_file_callback
        )
        new_file_btn.pack(pady=(0, 10))
        
        open_file_btn = ctk.CTkButton(
            buttons_frame,
            text="Open Image",
            font=("Inter", 14),
            width=150,
            height=40,
            corner_radius=8,
            command=self.open_file_callback
        )
        open_file_btn.pack(pady=(0, 30)) 