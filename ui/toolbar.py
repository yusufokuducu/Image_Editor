"""
Toolbar Module
Provides the main toolbar with editing tools.
"""

import os
import logging
import tkinter as tk
from typing import Dict, List, Any, Optional, Callable

import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter.ttk as ttk

from image_editor.tools.move_tool import MoveTool
from image_editor.tools.crop_tool import CropTool

logger = logging.getLogger("Image_Editor.Toolbar")

class ToolButton(ctk.CTkButton):
    """Custom button for tools in the toolbar."""
    
    def __init__(self, parent, name: str, icon_path: Optional[str] = None, 
                command: Optional[Callable] = None, tooltip: Optional[str] = None,
                **kwargs):
        """
        Initialize a tool button.
        
        Args:
            parent: Parent widget
            name: Tool name
            icon_path: Path to the icon image
            command: Callback function when the button is clicked
            tooltip: Tooltip text
            **kwargs: Additional arguments for CTkButton
        """
        self.name = name
        self.tooltip = tooltip
        self.icon_image = None
        
        # Configure default button appearance
        width = kwargs.pop('width', 50)
        height = kwargs.pop('height', 50)
        corner_radius = kwargs.pop('corner_radius', 10)
        fg_color = kwargs.pop('fg_color', ("gray80", "gray28"))
        hover_color = kwargs.pop('hover_color', ("gray70", "gray38"))
        border_width = kwargs.pop('border_width', 0)
        
        # Load icon if provided
        if icon_path and os.path.exists(icon_path):
            try:
                pil_image = Image.open(icon_path)
                icon_size = kwargs.pop('icon_size', 24)
                pil_image = pil_image.resize((icon_size, icon_size))
                self.icon_image = ImageTk.PhotoImage(pil_image)
                image = self.icon_image
            except Exception as e:
                logger.error(f"Failed to load icon {icon_path}: {str(e)}")
                image = None
        else:
            image = None
        
        # Create the button
        super().__init__(
            parent,
            text="" if image else name,
            image=image,
            width=width,
            height=height,
            corner_radius=corner_radius,
            fg_color=fg_color,
            hover_color=hover_color,
            border_width=border_width,
            command=command,
            **kwargs
        )
        
        # Bind hover events for tooltip
        if tooltip:
            self.tooltip_window = None
            self.bind("<Enter>", self._show_tooltip)
            self.bind("<Leave>", self._hide_tooltip)
    
    def _show_tooltip(self, event):
        """Show tooltip when mouse hovers over the button."""
        if self.tooltip:
            x, y, _, _ = self.bbox("insert")
            x += self.winfo_rootx() + 25
            y += self.winfo_rooty() + 25
            
            # Create a toplevel window
            self.tooltip_window = tk.Toplevel(self)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            
            # Create modern tooltip label with dark theme
            label = tk.Label(
                self.tooltip_window, 
                text=self.tooltip, 
                background="#2d2d2d", 
                foreground="#ffffff",
                relief="flat", 
                borderwidth=0,
                font=("Inter", 11),
                padx=8,
                pady=5
            )
            label.pack()
    
    def _hide_tooltip(self, event):
        """Hide tooltip when mouse leaves the button."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class Toolbar(ctk.CTkFrame):
    """Toolbar containing editing tools."""
    
    def __init__(self, parent, main_window):
        """
        Initialize the toolbar.
        
        Args:
            parent: Parent widget
            main_window: Reference to the main window
        """
        super().__init__(parent, corner_radius=12)
        
        self.main_window = main_window
        self.app_state = main_window.app_state
        
        # Store tool buttons
        self.tool_buttons: Dict[str, ToolButton] = {}
        self.active_tool: Optional[str] = None
        
        # Create tools
        self._initialize_tools()
        
        # Create modern toolbar UI
        self._create_toolbar_buttons()
        
        logger.info("Toolbar initialized")
    
    def _initialize_tools(self):
        """Initialize all tools."""
        # Create tool instances
        self.tools = {
            "move": MoveTool(self.app_state),
            "crop": CropTool(self.app_state),
            # Add other tools here
        }
        
        # Set the initially active tool
        self.active_tool = "move"
        self.app_state.current_tool = "move"
    
    def _create_toolbar_buttons(self):
        """Create buttons for the toolbar."""
        # Create main container with padding
        self.tools_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tools_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        # Section label
        self.tools_label = ctk.CTkLabel(
            self.tools_container, 
            text="TOOLS", 
            font=("Inter", 12, "bold"),
            text_color=("gray50", "gray70")
        )
        self.tools_label.pack(pady=(0, 10))

        # Create buttons for each tool
        # Move tool
        self.tool_buttons["move"] = ToolButton(
            self.tools_container,
            name="Move",
            tooltip="Move Tool (V)",
            text="⥮",
            font=("Arial", 18),
            command=lambda: self.set_active_tool("move")
        )
        self.tool_buttons["move"].pack(pady=5, fill=tk.X)
        
        # Selection tool
        self.tool_buttons["select"] = ToolButton(
            self.tools_container,
            name="Select",
            tooltip="Selection Tool (M)",
            text="◫",
            font=("Arial", 18),
            command=lambda: self.set_active_tool("select")
        )
        self.tool_buttons["select"].pack(pady=5, fill=tk.X)
        
        # Crop tool
        self.tool_buttons["crop"] = ToolButton(
            self.tools_container,
            name="Crop",
            tooltip="Crop Tool (C)",
            text="⟗",
            font=("Arial", 18),
            command=lambda: self.set_active_tool("crop")
        )
        self.tool_buttons["crop"].pack(pady=5, fill=tk.X)
        
        # Brush tool
        self.tool_buttons["brush"] = ToolButton(
            self.tools_container,
            name="Brush",
            tooltip="Brush Tool (B)",
            text="⦿",
            font=("Arial", 18),
            command=lambda: self.set_active_tool("brush")
        )
        self.tool_buttons["brush"].pack(pady=5, fill=tk.X)
        
        # Eraser tool
        self.tool_buttons["eraser"] = ToolButton(
            self.tools_container,
            name="Eraser",
            tooltip="Eraser Tool (E)",
            text="⌫",
            font=("Arial", 18),
            command=lambda: self.set_active_tool("eraser")
        )
        self.tool_buttons["eraser"].pack(pady=5, fill=tk.X)
        
        # Text tool
        self.tool_buttons["text"] = ToolButton(
            self.tools_container,
            name="Text",
            tooltip="Text Tool (T)",
            text="T",
            font=("Arial", 18),
            command=lambda: self.set_active_tool("text")
        )
        self.tool_buttons["text"].pack(pady=5, fill=tk.X)
        
        # Set initial active tool
        self.set_active_tool("move")
    
    def set_active_tool(self, tool_name: str):
        """
        Select a tool and update the UI.
        
        Args:
            tool_name: Name of the tool to select
        """
        # Skip if already selected
        if self.active_tool == tool_name:
            return
        
        # Deactivate current tool button
        if self.active_tool and self.active_tool in self.tool_buttons:
            self.tool_buttons[self.active_tool].configure(
                fg_color=("gray80", "gray28")
            )
        
        # Activate new tool button
        if tool_name in self.tool_buttons:
            self.tool_buttons[tool_name].configure(
                fg_color=("#3a7ebf", "#1f538d")
            )
        
        # Update active tool
        self.active_tool = tool_name
        self.app_state.current_tool = tool_name
        
        # Log selection
        logger.info(f"Selected tool: {tool_name}")
        
        # Notify main window to update active tool
        # TODO: Implement callback
    
    def get_active_tool(self) -> Optional[str]:
        """Get the currently active tool name."""
        return self.active_tool 