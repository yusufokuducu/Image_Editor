"""
Color Palette Module
Provides a UI widget for color selection and management.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import colorchooser
from typing import Tuple, List, Callable, Optional


class ColorPalette(ctk.CTkFrame):
    """Widget for selecting and managing colors."""
    
    def __init__(self, parent, main_window=None):
        """
        Initialize the color palette.
        
        Args:
            parent: Parent widget
            main_window: Reference to the main window object (optional)
        """
        super().__init__(parent)
        
        self.main_window = main_window
        
        # Current foreground and background colors
        self.foreground_color = (0, 0, 0, 255)  # RGBA
        self.background_color = (255, 255, 255, 255)  # RGBA
        
        # Recent colors
        self.recent_colors = [
            (0, 0, 0, 255),
            (255, 255, 255, 255),
            (255, 0, 0, 255),
            (0, 255, 0, 255),
            (0, 0, 255, 255),
            (255, 255, 0, 255),
            (0, 255, 255, 255),
            (255, 0, 255, 255),
        ]
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface elements."""
        # Main title
        title = ctk.CTkLabel(self, text="Color", font=("Inter", 14, "bold"))
        title.pack(pady=(10, 5))
        
        # Current color swatches
        self.current_colors_frame = ctk.CTkFrame(self)
        self.current_colors_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Foreground color
        self.fg_label = ctk.CTkLabel(self.current_colors_frame, text="Foreground:")
        self.fg_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.fg_color_btn = ctk.CTkButton(
            self.current_colors_frame, 
            text="", 
            width=30, 
            height=30,
            fg_color=self._rgba_to_hex(self.foreground_color),
            hover_color=self._rgba_to_hex(self.foreground_color),
            command=self._pick_foreground_color
        )
        self.fg_color_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Background color
        self.bg_label = ctk.CTkLabel(self.current_colors_frame, text="Background:")
        self.bg_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.bg_color_btn = ctk.CTkButton(
            self.current_colors_frame, 
            text="", 
            width=30, 
            height=30,
            fg_color=self._rgba_to_hex(self.background_color),
            hover_color=self._rgba_to_hex(self.background_color),
            command=self._pick_background_color
        )
        self.bg_color_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Swap colors button
        self.swap_btn = ctk.CTkButton(
            self.current_colors_frame,
            text="⇅",
            width=30,
            height=30,
            command=self._swap_colors
        )
        self.swap_btn.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
        
        # Recent colors
        self.recent_label = ctk.CTkLabel(self, text="Recent Colors:", font=("Inter", 12))
        self.recent_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Recent colors grid
        self.recent_colors_frame = ctk.CTkFrame(self)
        self.recent_colors_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create color swatches for recent colors
        self.recent_color_buttons = []
        cols = 4
        for i, color in enumerate(self.recent_colors):
            row = i // cols
            col = i % cols
            
            color_btn = ctk.CTkButton(
                self.recent_colors_frame,
                text="",
                width=25,
                height=25,
                fg_color=self._rgba_to_hex(color),
                hover_color=self._rgba_to_hex(color),
                command=lambda c=color: self._set_foreground_color(c)
            )
            color_btn.grid(row=row, column=col, padx=2, pady=2)
            self.recent_color_buttons.append(color_btn)
    
    def _rgba_to_hex(self, rgba: Tuple[int, int, int, int]) -> str:
        """
        Convert RGBA color to hex string.
        
        Args:
            rgba: RGBA color tuple (values 0-255)
            
        Returns:
            Hex color string (#RRGGBB)
        """
        r, g, b, _ = rgba  # Ignore alpha for now
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _hex_to_rgba(self, hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        """
        Convert hex color to RGBA tuple.
        
        Args:
            hex_color: Hex color string (#RRGGBB)
            alpha: Alpha value (0-255)
            
        Returns:
            RGBA color tuple
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)
    
    def _pick_foreground_color(self):
        """Open color picker for foreground color."""
        color = colorchooser.askcolor(
            title="Select Foreground Color",
            initialcolor=self._rgba_to_hex(self.foreground_color)
        )
        
        if color[1]:  # If not canceled
            # Convert from RGB to RGBA, preserving alpha
            rgb = color[0]
            r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
            _, _, _, a = self.foreground_color
            self.set_foreground_color((r, g, b, a))
    
    def _pick_background_color(self):
        """Open color picker for background color."""
        color = colorchooser.askcolor(
            title="Select Background Color",
            initialcolor=self._rgba_to_hex(self.background_color)
        )
        
        if color[1]:  # If not canceled
            # Convert from RGB to RGBA, preserving alpha
            rgb = color[0]
            r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
            _, _, _, a = self.background_color
            self.set_background_color((r, g, b, a))
    
    def _swap_colors(self):
        """Swap foreground and background colors."""
        fg = self.foreground_color
        bg = self.background_color
        
        self.set_foreground_color(bg)
        self.set_background_color(fg)
    
    def _set_foreground_color(self, color: Tuple[int, int, int, int]):
        """Set foreground color and update recent colors."""
        self.set_foreground_color(color)
        self._add_to_recent_colors(color)
    
    def set_foreground_color(self, color: Tuple[int, int, int, int]):
        """
        Set the foreground color.
        
        Args:
            color: RGBA color tuple
        """
        self.foreground_color = color
        self.fg_color_btn.configure(
            fg_color=self._rgba_to_hex(color),
            hover_color=self._rgba_to_hex(color)
        )
        
        # Update app state if main window is available
        if self.main_window and hasattr(self.main_window, 'app_state'):
            self.main_window.app_state.foreground_color = color
    
    def set_background_color(self, color: Tuple[int, int, int, int]):
        """
        Set the background color.
        
        Args:
            color: RGBA color tuple
        """
        self.background_color = color
        self.bg_color_btn.configure(
            fg_color=self._rgba_to_hex(color),
            hover_color=self._rgba_to_hex(color)
        )
        
        # Update app state if main window is available
        if self.main_window and hasattr(self.main_window, 'app_state'):
            self.main_window.app_state.background_color = color
    
    def _add_to_recent_colors(self, color: Tuple[int, int, int, int]):
        """
        Add a color to the recent colors list.
        
        Args:
            color: RGBA color tuple
        """
        # Remove if already in list
        if color in self.recent_colors:
            self.recent_colors.remove(color)
        
        # Add to beginning
        self.recent_colors.insert(0, color)
        
        # Limit to 8 colors
        if len(self.recent_colors) > 8:
            self.recent_colors = self.recent_colors[:8]
        
        # Update buttons
        self._update_recent_color_buttons()
    
    def _update_recent_color_buttons(self):
        """Update the recent color buttons to reflect the current list."""
        for i, color in enumerate(self.recent_colors):
            if i < len(self.recent_color_buttons):
                btn = self.recent_color_buttons[i]
                btn.configure(
                    fg_color=self._rgba_to_hex(color),
                    hover_color=self._rgba_to_hex(color),
                    command=lambda c=color: self._set_foreground_color(c)
                ) 