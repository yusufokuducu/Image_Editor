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

from photoforge_pro.tools.move_tool import MoveTool
from photoforge_pro.tools.crop_tool import CropTool

logger = logging.getLogger("PhotoForge.Toolbar")

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
        width = kwargs.pop('width', 40)
        height = kwargs.pop('height', 40)
        corner_radius = kwargs.pop('corner_radius', 6)
        
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
            
            # Create tooltip label
            label = tk.Label(
                self.tooltip_window, text=self.tooltip, 
                background="#ffffe0", relief="solid", borderwidth=1,
                font=("TkDefaultFont", 10)
            )
            label.pack(ipadx=3, ipady=1)
    
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
        super().__init__(parent)
        
        self.main_window = main_window
        self.app_state = main_window.app_state
        
        # Store tool buttons
        self.tool_buttons: Dict[str, ToolButton] = {}
        self.active_tool: Optional[str] = None
        
        # Create tools
        self._initialize_tools()
        
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
        self.active_tool = self.tools["move"]
    
    def _create_toolbar_buttons(self):
        """Create buttons for the toolbar."""
        # Create tool buttons frame
        self.tool_buttons_frame = ttk.Frame(self)
        self.tool_buttons_frame.pack(side=tk.TOP, fill=tk.X)

        # Create buttons for each tool
        self.tool_buttons = {}
        
        # Move tool
        self.tool_buttons["move"] = ttk.Button(
            self.tool_buttons_frame,
            text="Move",
            command=lambda: self.set_active_tool("move")
        )
        self.tool_buttons["move"].pack(side=tk.LEFT, padx=2, pady=2)
        
        # Crop tool
        self.tool_buttons["crop"] = ttk.Button(
            self.tool_buttons_frame,
            text="Crop",
            command=lambda: self.set_active_tool("crop")
        )
        self.tool_buttons["crop"].pack(side=tk.LEFT, padx=2, pady=2)
        
        # Add more tool buttons here
    
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
                fg_color=("gray75", "gray25")
            )
        
        # Activate new tool button
        if tool_name in self.tool_buttons:
            self.tool_buttons[tool_name].configure(
                fg_color=("gray85", "gray35")
            )
        
        # Update active tool
        self.active_tool = tool_name
        self.app_state.current_tool = tool_name
        
        # Log selection
        logger.info(f"Selected tool: {tool_name}")
        
        # Notify main window to update active tool
        try:
            if hasattr(self.main_window, 'set_status'):
                self.main_window.set_status(f"Tool: {tool_name}")
        except AttributeError:
            # Status label might not be initialized yet
            pass
    
    def get_active_tool(self) -> Optional[str]:
        """Get the name of the active tool."""
        return self.active_tool 