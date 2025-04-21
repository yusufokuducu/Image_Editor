"""
Tool Options Panel Module
Provides UI for displaying and adjusting tool options.
"""

import logging
import tkinter as tk
from typing import Dict, Any, Optional

import customtkinter as ctk

logger = logging.getLogger("Image_Editor.ToolOptionsPanel")

class ToolOptionsPanel(ctk.CTkFrame):
    """
    Panel for displaying options for the active tool.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize the tool options panel.
        
        Args:
            parent: Parent widget
            main_window: Reference to the main window
        """
        super().__init__(parent)
        
        self.main_window = main_window
        self.app_state = main_window.app_state
        
        # Current tool
        self.current_tool = None
        
        # Tool option widgets
        self.option_widgets = {}
        
        # Create UI elements
        self.create_widgets()
        
        # Update for current tool
        self.update_for_tool(self.app_state.current_tool)
        
        logger.info("Tool options panel initialized")
    
    def create_widgets(self):
        """Create tool options panel widgets."""
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="Tool Options",
            font=("Helvetica", 14, "bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Options frame
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Default message
        self.default_label = ctk.CTkLabel(
            self.options_frame,
            text="Select a tool to see its options.",
            font=("Helvetica", 12),
            justify=tk.CENTER
        )
        self.default_label.pack(pady=20)
    
    def clear_options(self):
        """Clear all option widgets."""
        # Destroy all existing option widgets
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Clear widget references
        self.option_widgets = {}
    
    def update_for_tool(self, tool_name: str):
        """
        Update the panel for the specified tool.
        
        Args:
            tool_name: Name of the tool
        """
        if self.current_tool == tool_name:
            return
        
        self.current_tool = tool_name
        
        # Clear existing options
        self.clear_options()
        
        # Update title
        self.title_label.configure(text=f"{tool_name.replace('_', ' ').title()} Options")
        
        # Create options based on the tool
        if tool_name == "brush_tool":
            self.create_brush_options()
        elif tool_name == "eraser_tool":
            self.create_eraser_options()
        elif tool_name == "selection_tool":
            self.create_selection_options()
        elif tool_name == "text_tool":
            self.create_text_options()
        elif tool_name == "crop_tool":
            self.create_crop_options()
        elif tool_name == "move_tool":
            self.create_move_options()
        else:
            # Default message
            self.default_label = ctk.CTkLabel(
                self.options_frame,
                text=f"No options available for {tool_name.replace('_', ' ').title()}.",
                font=("Helvetica", 12),
                justify=tk.CENTER
            )
            self.default_label.pack(pady=20)
    
    def create_brush_options(self):
        """Create options for the brush tool."""
        # Get tool settings
        settings = self.app_state.tool_settings.get("brush_tool", {})
        
        # Size option
        self._create_slider_option(
            "Size", 
            min_val=1, 
            max_val=100, 
            default=settings.get("size", 10),
            callback=lambda val: self._update_tool_setting("brush_tool", "size", int(val))
        )
        
        # Hardness option
        self._create_slider_option(
            "Hardness", 
            min_val=0, 
            max_val=100, 
            default=int(settings.get("hardness", 0.8) * 100),
            callback=lambda val: self._update_tool_setting("brush_tool", "hardness", float(val) / 100.0)
        )
        
        # Opacity option
        self._create_slider_option(
            "Opacity", 
            min_val=0, 
            max_val=100, 
            default=int(settings.get("opacity", 1.0) * 100),
            callback=lambda val: self._update_tool_setting("brush_tool", "opacity", float(val) / 100.0)
        )
        
        # Flow option
        self._create_slider_option(
            "Flow", 
            min_val=0, 
            max_val=100, 
            default=int(settings.get("flow", 1.0) * 100),
            callback=lambda val: self._update_tool_setting("brush_tool", "flow", float(val) / 100.0)
        )
        
        # Color option
        color_frame = ctk.CTkFrame(self.options_frame)
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        color_label = ctk.CTkLabel(color_frame, text="Color:", width=80)
        color_label.pack(side=tk.LEFT, padx=5)
        
        color_preview = ctk.CTkButton(
            color_frame,
            text="",
            width=30,
            height=30,
            fg_color=self._rgb_to_hex(settings.get("color", (0, 0, 0))),
            command=self._pick_color
        )
        color_preview.pack(side=tk.LEFT, padx=5)
        
        # Store reference to color preview
        self.option_widgets["color_preview"] = color_preview
    
    def create_eraser_options(self):
        """Create options for the eraser tool."""
        # Get tool settings
        settings = self.app_state.tool_settings.get("eraser_tool", {})
        
        # Size option
        self._create_slider_option(
            "Size", 
            min_val=1, 
            max_val=100, 
            default=settings.get("size", 10),
            callback=lambda val: self._update_tool_setting("eraser_tool", "size", int(val))
        )
        
        # Hardness option
        self._create_slider_option(
            "Hardness", 
            min_val=0, 
            max_val=100, 
            default=int(settings.get("hardness", 0.8) * 100),
            callback=lambda val: self._update_tool_setting("eraser_tool", "hardness", float(val) / 100.0)
        )
        
        # Opacity option
        self._create_slider_option(
            "Opacity", 
            min_val=0, 
            max_val=100, 
            default=int(settings.get("opacity", 1.0) * 100),
            callback=lambda val: self._update_tool_setting("eraser_tool", "opacity", float(val) / 100.0)
        )
    
    def create_selection_options(self):
        """Create options for the selection tool."""
        # Get tool settings
        settings = self.app_state.tool_settings.get("selection_tool", {})
        
        # Mode option
        mode_frame = ctk.CTkFrame(self.options_frame)
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        mode_label = ctk.CTkLabel(mode_frame, text="Mode:", width=80)
        mode_label.pack(side=tk.LEFT, padx=5)
        
        modes = ["Rectangle", "Ellipse", "Lasso", "Magic Wand"]
        mode_var = tk.StringVar(value=settings.get("mode", "rectangle").title())
        
        mode_dropdown = ctk.CTkOptionMenu(
            mode_frame,
            values=modes,
            variable=mode_var,
            command=lambda val: self._update_tool_setting(
                "selection_tool", 
                "mode", 
                val.lower()
            )
        )
        mode_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Feather option
        self._create_slider_option(
            "Feather", 
            min_val=0, 
            max_val=100, 
            default=settings.get("feather", 0),
            callback=lambda val: self._update_tool_setting("selection_tool", "feather", int(val))
        )
        
        # Anti-alias option
        anti_alias_frame = ctk.CTkFrame(self.options_frame)
        anti_alias_frame.pack(fill=tk.X, padx=10, pady=5)
        
        anti_alias_var = tk.BooleanVar(value=settings.get("anti_alias", True))
        anti_alias_cb = ctk.CTkCheckBox(
            anti_alias_frame, 
            text="Anti-aliasing",
            variable=anti_alias_var,
            command=lambda: self._update_tool_setting(
                "selection_tool", 
                "anti_alias", 
                anti_alias_var.get()
            )
        )
        anti_alias_cb.pack(padx=5)
    
    def create_text_options(self):
        """Create options for the text tool."""
        # Get tool settings
        settings = self.app_state.tool_settings.get("text_tool", {})
        
        # Font option
        font_frame = ctk.CTkFrame(self.options_frame)
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        font_label = ctk.CTkLabel(font_frame, text="Font:", width=80)
        font_label.pack(side=tk.LEFT, padx=5)
        
        fonts = ["Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana"]
        font_var = tk.StringVar(value=settings.get("font", "Arial"))
        
        font_dropdown = ctk.CTkOptionMenu(
            font_frame,
            values=fonts,
            variable=font_var,
            command=lambda val: self._update_tool_setting("text_tool", "font", val)
        )
        font_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Size option
        self._create_slider_option(
            "Size", 
            min_val=8, 
            max_val=72, 
            default=settings.get("size", 12),
            callback=lambda val: self._update_tool_setting("text_tool", "size", int(val))
        )
        
        # Color option
        color_frame = ctk.CTkFrame(self.options_frame)
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        color_label = ctk.CTkLabel(color_frame, text="Color:", width=80)
        color_label.pack(side=tk.LEFT, padx=5)
        
        color_preview = ctk.CTkButton(
            color_frame,
            text="",
            width=30,
            height=30,
            fg_color=self._rgb_to_hex(settings.get("color", (0, 0, 0))),
            command=self._pick_text_color
        )
        color_preview.pack(side=tk.LEFT, padx=5)
        
        # Store reference to color preview
        self.option_widgets["text_color_preview"] = color_preview
        
        # Style options
        style_frame = ctk.CTkFrame(self.options_frame)
        style_frame.pack(fill=tk.X, padx=10, pady=5)
        
        bold_var = tk.BooleanVar(value=settings.get("bold", False))
        bold_cb = ctk.CTkCheckBox(
            style_frame, 
            text="Bold",
            variable=bold_var,
            command=lambda: self._update_tool_setting("text_tool", "bold", bold_var.get())
        )
        bold_cb.pack(side=tk.LEFT, padx=5)
        
        italic_var = tk.BooleanVar(value=settings.get("italic", False))
        italic_cb = ctk.CTkCheckBox(
            style_frame, 
            text="Italic",
            variable=italic_var,
            command=lambda: self._update_tool_setting("text_tool", "italic", italic_var.get())
        )
        italic_cb.pack(side=tk.LEFT, padx=5)
    
    def create_crop_options(self):
        """Create options for the crop tool."""
        # Get tool settings
        settings = self.app_state.tool_settings.get("crop_tool", {})
        
        # Aspect ratio option
        aspect_frame = ctk.CTkFrame(self.options_frame)
        aspect_frame.pack(fill=tk.X, padx=10, pady=5)
        
        aspect_label = ctk.CTkLabel(aspect_frame, text="Aspect Ratio:", width=100)
        aspect_label.pack(side=tk.LEFT, padx=5)
        
        aspects = ["Free", "1:1", "4:3", "16:9", "2:1"]
        aspect_var = tk.StringVar(value="Free")
        
        aspect_dropdown = ctk.CTkOptionMenu(
            aspect_frame,
            values=aspects,
            variable=aspect_var,
            command=self._set_aspect_ratio
        )
        aspect_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Rule of thirds option
        thirds_frame = ctk.CTkFrame(self.options_frame)
        thirds_frame.pack(fill=tk.X, padx=10, pady=5)
        
        thirds_var = tk.BooleanVar(value=settings.get("rule_of_thirds", True))
        thirds_cb = ctk.CTkCheckBox(
            thirds_frame, 
            text="Show Rule of Thirds",
            variable=thirds_var,
            command=lambda: self._update_tool_setting(
                "crop_tool", 
                "rule_of_thirds", 
                thirds_var.get()
            )
        )
        thirds_cb.pack(padx=5)
    
    def create_move_options(self):
        """Create options for the move tool."""
        # Get tool settings
        settings = self.app_state.tool_settings.get("move_tool", {})
        
        # Auto-select layer option
        auto_select_frame = ctk.CTkFrame(self.options_frame)
        auto_select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        auto_select_var = tk.BooleanVar(value=settings.get("auto_select_layer", True))
        auto_select_cb = ctk.CTkCheckBox(
            auto_select_frame, 
            text="Auto-select Layer",
            variable=auto_select_var,
            command=lambda: self._update_tool_setting(
                "move_tool", 
                "auto_select_layer", 
                auto_select_var.get()
            )
        )
        auto_select_cb.pack(padx=5)
    
    def _create_slider_option(self, label: str, min_val: int, max_val: int, 
                            default: int, callback=None):
        """
        Create a slider option.
        
        Args:
            label: Option label
            min_val: Minimum value
            max_val: Maximum value
            default: Default value
            callback: Function to call when value changes
        """
        # Create frame
        frame = ctk.CTkFrame(self.options_frame)
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add label
        option_label = ctk.CTkLabel(frame, text=f"{label}:", width=80)
        option_label.pack(side=tk.LEFT, padx=5)
        
        # Add slider
        slider_var = tk.IntVar(value=default)
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            variable=slider_var,
            command=callback,
            width=120
        )
        slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Add value label
        value_label = ctk.CTkLabel(frame, text=str(default), width=35)
        value_label.pack(side=tk.RIGHT, padx=5)
        
        # Update value label when slider changes
        def update_value(*args):
            value_label.configure(text=str(slider_var.get()))
            if callback:
                callback(slider_var.get())
        
        slider_var.trace_add("write", update_value)
        
        # Store widget references
        key = label.lower().replace(" ", "_")
        self.option_widgets[f"{key}_slider"] = slider
        self.option_widgets[f"{key}_value"] = value_label
    
    def _update_tool_setting(self, tool: str, setting: str, value: Any):
        """
        Update a tool setting.
        
        Args:
            tool: Tool name
            setting: Setting name
            value: New value
        """
        if tool in self.app_state.tool_settings:
            self.app_state.tool_settings[tool][setting] = value
            logger.debug(f"Updated {tool}.{setting} = {value}")
    
    def _set_aspect_ratio(self, aspect: str):
        """
        Set the crop aspect ratio.
        
        Args:
            aspect: Aspect ratio string
        """
        ratio = None
        
        if aspect == "1:1":
            ratio = 1.0
        elif aspect == "4:3":
            ratio = 4.0 / 3.0
        elif aspect == "16:9":
            ratio = 16.0 / 9.0
        elif aspect == "2:1":
            ratio = 2.0
        
        self._update_tool_setting("crop_tool", "aspect_ratio", ratio)
        logger.debug(f"Set crop aspect ratio to {aspect} ({ratio})")
    
    def _pick_color(self):
        """Open a color picker for the brush color."""
        # TODO: Implement proper color picker
        # For now, just cycle through some colors
        settings = self.app_state.tool_settings.get("brush_tool", {})
        current_color = settings.get("color", (0, 0, 0))
        
        colors = [
            (0, 0, 0),      # Black
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255) # White
        ]
        
        # Find current color index
        try:
            index = colors.index(current_color)
            next_index = (index + 1) % len(colors)
        except ValueError:
            next_index = 0
        
        # Set new color
        new_color = colors[next_index]
        self._update_tool_setting("brush_tool", "color", new_color)
        
        # Update color preview
        if "color_preview" in self.option_widgets:
            self.option_widgets["color_preview"].configure(
                fg_color=self._rgb_to_hex(new_color)
            )
    
    def _pick_text_color(self):
        """Open a color picker for the text color."""
        # TODO: Implement proper color picker
        # For now, just cycle through some colors
        settings = self.app_state.tool_settings.get("text_tool", {})
        current_color = settings.get("color", (0, 0, 0))
        
        colors = [
            (0, 0, 0),      # Black
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255) # White
        ]
        
        # Find current color index
        try:
            index = colors.index(current_color)
            next_index = (index + 1) % len(colors)
        except ValueError:
            next_index = 0
        
        # Set new color
        new_color = colors[next_index]
        self._update_tool_setting("text_tool", "color", new_color)
        
        # Update color preview
        if "text_color_preview" in self.option_widgets:
            self.option_widgets["text_color_preview"].configure(
                fg_color=self._rgb_to_hex(new_color)
            )
    
    def _rgb_to_hex(self, rgb):
        """
        Convert RGB tuple to hex color string.
        
        Args:
            rgb: (R, G, B) tuple
            
        Returns:
            Hex color string
        """
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}" 