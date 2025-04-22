"""
Effects Panel Module
Provides a UI panel for controlling the effects tool settings.
"""

import logging
import tkinter as tk
from typing import Dict, Any, Callable, Optional

import customtkinter as ctk
import numpy as np

logger = logging.getLogger("Image_Editor.EffectsPanel")

class EffectsPanel(ctk.CTkFrame):
    """Panel for adjusting image effects settings."""
    
    def __init__(self, parent, main_window):
        """Initialize the effects panel."""
        super().__init__(parent)
        
        self.main_window = main_window
        self.app_state = main_window.app_state
        
        # Effect sections
        self.sections = {}
        self.current_section = None
        
        # Create UI elements
        self.create_widgets()
        
        logger.debug("Effects panel initialized")
    
    def create_widgets(self):
        """Create the UI elements for the effects panel."""
        # Main container with padding
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Effect type selection
        self.effect_frame = ctk.CTkFrame(self.main_container)
        self.effect_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.effect_label = ctk.CTkLabel(self.effect_frame, text="Effect Type:", anchor="w")
        self.effect_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Effect type dropdown
        self.effect_types = [
            "Noise", "Grain", "Brightness & Contrast", 
            "Hue & Saturation", "Blur", "Sharpen", "Threshold"
        ]
        
        self.effect_var = ctk.StringVar(value=self.effect_types[0])
        self.effect_dropdown = ctk.CTkOptionMenu(
            self.effect_frame, 
            values=self.effect_types,
            variable=self.effect_var,
            command=self.on_effect_changed
        )
        self.effect_dropdown.pack(fill=tk.X, padx=5, pady=2)
        
        # Create scrollable frame for settings
        self.settings_container = ctk.CTkScrollableFrame(self.main_container)
        self.settings_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create sections for different effects
        self._create_noise_section()
        self._create_grain_section()
        self._create_brightness_contrast_section()
        self._create_hue_saturation_section()
        self._create_blur_section()
        self._create_sharpen_section()
        self._create_threshold_section()
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_container)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Preview button
        self.preview_button = ctk.CTkButton(
            self.button_frame, 
            text="Preview", 
            command=self.preview_effect
        )
        self.preview_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Apply button
        self.apply_button = ctk.CTkButton(
            self.button_frame, 
            text="Apply", 
            command=self.apply_effect
        )
        self.apply_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Reset button
        self.reset_button = ctk.CTkButton(
            self.button_frame, 
            text="Reset", 
            command=self.reset_settings
        )
        self.reset_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Show initial section
        self.show_section("Noise")
    
    def _create_noise_section(self):
        """Create the UI for noise effect settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Noise amount slider
        amount_label = ctk.CTkLabel(section, text="Amount:", anchor="w")
        amount_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.noise_amount_var = ctk.IntVar(value=25)
        amount_slider = ctk.CTkSlider(
            section, 
            from_=0, 
            to=100, 
            variable=self.noise_amount_var, 
            number_of_steps=100
        )
        amount_slider.pack(fill=tk.X, padx=5, pady=2)
        
        amount_value = ctk.CTkLabel(section, textvariable=self.noise_amount_var)
        amount_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Noise type selection
        type_label = ctk.CTkLabel(section, text="Type:", anchor="w")
        type_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.noise_type_var = ctk.StringVar(value="Gaussian")
        noise_types = ["Gaussian", "Salt & Pepper", "Speckle"]
        
        for noise_type in noise_types:
            radio = ctk.CTkRadioButton(
                section, 
                text=noise_type, 
                variable=self.noise_type_var, 
                value=noise_type
            )
            radio.pack(fill=tk.X, padx=5, pady=2)
        
        # Store the section
        self.sections["Noise"] = section
    
    def _create_grain_section(self):
        """Create the UI for grain effect settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Grain amount slider
        amount_label = ctk.CTkLabel(section, text="Amount:", anchor="w")
        amount_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.grain_amount_var = ctk.IntVar(value=25)
        amount_slider = ctk.CTkSlider(
            section, 
            from_=0, 
            to=100, 
            variable=self.grain_amount_var, 
            number_of_steps=100
        )
        amount_slider.pack(fill=tk.X, padx=5, pady=2)
        
        amount_value = ctk.CTkLabel(section, textvariable=self.grain_amount_var)
        amount_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Grain size slider
        size_label = ctk.CTkLabel(section, text="Size:", anchor="w")
        size_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.grain_size_var = ctk.DoubleVar(value=1.0)
        size_slider = ctk.CTkSlider(
            section, 
            from_=0.5, 
            to=3.0, 
            variable=self.grain_size_var, 
            number_of_steps=25
        )
        size_slider.pack(fill=tk.X, padx=5, pady=2)
        
        size_value = ctk.CTkLabel(section, textvariable=self.grain_size_var)
        size_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Color grain checkbox
        self.grain_color_var = ctk.BooleanVar(value=False)
        color_check = ctk.CTkCheckBox(
            section, 
            text="Color Grain", 
            variable=self.grain_color_var
        )
        color_check.pack(fill=tk.X, padx=5, pady=5)
        
        # Store the section
        self.sections["Grain"] = section
    
    def _create_brightness_contrast_section(self):
        """Create the UI for brightness and contrast settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Brightness slider
        brightness_label = ctk.CTkLabel(section, text="Brightness:", anchor="w")
        brightness_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.brightness_var = ctk.DoubleVar(value=1.0)
        brightness_slider = ctk.CTkSlider(
            section, 
            from_=0.0, 
            to=2.0, 
            variable=self.brightness_var, 
            number_of_steps=40
        )
        brightness_slider.pack(fill=tk.X, padx=5, pady=2)
        
        brightness_value = ctk.CTkLabel(section, textvariable=self.brightness_var)
        brightness_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Contrast slider
        contrast_label = ctk.CTkLabel(section, text="Contrast:", anchor="w")
        contrast_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.contrast_var = ctk.DoubleVar(value=1.0)
        contrast_slider = ctk.CTkSlider(
            section, 
            from_=0.0, 
            to=2.0, 
            variable=self.contrast_var, 
            number_of_steps=40
        )
        contrast_slider.pack(fill=tk.X, padx=5, pady=2)
        
        contrast_value = ctk.CTkLabel(section, textvariable=self.contrast_var)
        contrast_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Store the section
        self.sections["Brightness & Contrast"] = section
    
    def _create_hue_saturation_section(self):
        """Create the UI for hue and saturation settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Hue slider
        hue_label = ctk.CTkLabel(section, text="Hue:", anchor="w")
        hue_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.hue_var = ctk.DoubleVar(value=0.0)
        hue_slider = ctk.CTkSlider(
            section, 
            from_=0.0, 
            to=1.0, 
            variable=self.hue_var, 
            number_of_steps=100
        )
        hue_slider.pack(fill=tk.X, padx=5, pady=2)
        
        hue_value = ctk.CTkLabel(section, textvariable=self.hue_var)
        hue_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Saturation slider
        saturation_label = ctk.CTkLabel(section, text="Saturation:", anchor="w")
        saturation_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.saturation_var = ctk.DoubleVar(value=1.0)
        saturation_slider = ctk.CTkSlider(
            section, 
            from_=0.0, 
            to=2.0, 
            variable=self.saturation_var, 
            number_of_steps=40
        )
        saturation_slider.pack(fill=tk.X, padx=5, pady=2)
        
        saturation_value = ctk.CTkLabel(section, textvariable=self.saturation_var)
        saturation_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Store the section
        self.sections["Hue & Saturation"] = section
    
    def _create_blur_section(self):
        """Create the UI for blur settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Radius slider
        radius_label = ctk.CTkLabel(section, text="Radius:", anchor="w")
        radius_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.blur_radius_var = ctk.IntVar(value=5)
        radius_slider = ctk.CTkSlider(
            section, 
            from_=1, 
            to=20, 
            variable=self.blur_radius_var, 
            number_of_steps=19
        )
        radius_slider.pack(fill=tk.X, padx=5, pady=2)
        
        radius_value = ctk.CTkLabel(section, textvariable=self.blur_radius_var)
        radius_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Blur type selection
        type_label = ctk.CTkLabel(section, text="Type:", anchor="w")
        type_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.blur_type_var = ctk.StringVar(value="Gaussian")
        blur_types = ["Gaussian", "Box", "Median"]
        
        for blur_type in blur_types:
            radio = ctk.CTkRadioButton(
                section, 
                text=blur_type, 
                variable=self.blur_type_var, 
                value=blur_type
            )
            radio.pack(fill=tk.X, padx=5, pady=2)
        
        # Store the section
        self.sections["Blur"] = section
    
    def _create_sharpen_section(self):
        """Create the UI for sharpen settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Strength slider
        strength_label = ctk.CTkLabel(section, text="Strength:", anchor="w")
        strength_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.sharpen_strength_var = ctk.DoubleVar(value=1.0)
        strength_slider = ctk.CTkSlider(
            section, 
            from_=0.0, 
            to=3.0, 
            variable=self.sharpen_strength_var, 
            number_of_steps=30
        )
        strength_slider.pack(fill=tk.X, padx=5, pady=2)
        
        strength_value = ctk.CTkLabel(section, textvariable=self.sharpen_strength_var)
        strength_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Store the section
        self.sections["Sharpen"] = section
    
    def _create_threshold_section(self):
        """Create the UI for threshold settings."""
        section = ctk.CTkFrame(self.settings_container)
        
        # Threshold value slider
        value_label = ctk.CTkLabel(section, text="Threshold:", anchor="w")
        value_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.threshold_value_var = ctk.IntVar(value=127)
        value_slider = ctk.CTkSlider(
            section, 
            from_=0, 
            to=255, 
            variable=self.threshold_value_var, 
            number_of_steps=255
        )
        value_slider.pack(fill=tk.X, padx=5, pady=2)
        
        value_value = ctk.CTkLabel(section, textvariable=self.threshold_value_var)
        value_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Max value slider
        max_label = ctk.CTkLabel(section, text="Max Value:", anchor="w")
        max_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.threshold_max_var = ctk.IntVar(value=255)
        max_slider = ctk.CTkSlider(
            section, 
            from_=0, 
            to=255, 
            variable=self.threshold_max_var, 
            number_of_steps=255
        )
        max_slider.pack(fill=tk.X, padx=5, pady=2)
        
        max_value = ctk.CTkLabel(section, textvariable=self.threshold_max_var)
        max_value.pack(fill=tk.X, padx=5, pady=2)
        
        # Store the section
        self.sections["Threshold"] = section
    
    def show_section(self, section_name):
        """
        Show the selected section and hide others.
        
        Args:
            section_name: Name of the section to show
        """
        # Hide current section
        if self.current_section and self.current_section in self.sections:
            self.sections[self.current_section].pack_forget()
        
        # Show selected section
        if section_name in self.sections:
            self.sections[section_name].pack(fill=tk.BOTH, expand=True)
            self.current_section = section_name
    
    def on_effect_changed(self, selection):
        """
        Handle effect type change.
        
        Args:
            selection: Selected effect type
        """
        self.show_section(selection)
        
        # Update tool settings
        self.update_tool_settings()
    
    def update_tool_settings(self):
        """Update the effects tool settings based on UI values."""
        # Get the active tool
        active_tool = self.app_state.tools.get("effects")
        if not active_tool:
            return
        
        # Determine the effect type and mapping to tool's effect_type value
        effect_type = self.effect_var.get()
        tool_effect_type = ""
        
        if effect_type == "Noise":
            tool_effect_type = "noise"
            # Update noise settings
            active_tool.settings["noise"] = {
                "amount": self.noise_amount_var.get(),
                "type": self.noise_type_var.get().lower().replace(" & ", "_")
            }
            
        elif effect_type == "Grain":
            tool_effect_type = "grain"
            # Update grain settings
            active_tool.settings["grain"] = {
                "amount": self.grain_amount_var.get(),
                "size": self.grain_size_var.get(),
                "color": self.grain_color_var.get()
            }
            
        elif effect_type == "Brightness & Contrast":
            tool_effect_type = "brightness_contrast"
            # Update brightness & contrast settings
            active_tool.settings["brightness_contrast"] = {
                "brightness": self.brightness_var.get(),
                "contrast": self.contrast_var.get()
            }
            
        elif effect_type == "Hue & Saturation":
            tool_effect_type = "hue_saturation"
            # Update hue & saturation settings
            active_tool.settings["hue_saturation"] = {
                "hue": self.hue_var.get(),
                "saturation": self.saturation_var.get()
            }
            
        elif effect_type == "Blur":
            tool_effect_type = "blur"
            # Update blur settings
            active_tool.settings["blur"] = {
                "radius": self.blur_radius_var.get(),
                "type": self.blur_type_var.get().lower()
            }
            
        elif effect_type == "Sharpen":
            tool_effect_type = "sharpen"
            # Update sharpen settings
            active_tool.settings["sharpen"] = {
                "strength": self.sharpen_strength_var.get()
            }
            
        elif effect_type == "Threshold":
            tool_effect_type = "threshold"
            # Update threshold settings
            active_tool.settings["threshold"] = {
                "value": self.threshold_value_var.get(),
                "max_value": self.threshold_max_var.get()
            }
        
        # Set current effect type
        active_tool.settings["effect_type"] = tool_effect_type
    
    def preview_effect(self):
        """Preview the current effect."""
        # Update tool settings
        self.update_tool_settings()
        
        # Get the active tool
        active_tool = self.app_state.tools.get("effects")
        if active_tool and active_tool.active:
            active_tool.preview_effect()
    
    def apply_effect(self):
        """Apply the current effect."""
        # Update tool settings
        self.update_tool_settings()
        
        # Get the active tool
        active_tool = self.app_state.tools.get("effects")
        if active_tool and active_tool.active:
            active_tool.apply_effect()
    
    def reset_settings(self):
        """Reset all settings to default values."""
        # Reset based on current section
        if self.current_section == "Noise":
            self.noise_amount_var.set(25)
            self.noise_type_var.set("Gaussian")
            
        elif self.current_section == "Grain":
            self.grain_amount_var.set(25)
            self.grain_size_var.set(1.0)
            self.grain_color_var.set(False)
            
        elif self.current_section == "Brightness & Contrast":
            self.brightness_var.set(1.0)
            self.contrast_var.set(1.0)
            
        elif self.current_section == "Hue & Saturation":
            self.hue_var.set(0.0)
            self.saturation_var.set(1.0)
            
        elif self.current_section == "Blur":
            self.blur_radius_var.set(5)
            self.blur_type_var.set("Gaussian")
            
        elif self.current_section == "Sharpen":
            self.sharpen_strength_var.set(1.0)
            
        elif self.current_section == "Threshold":
            self.threshold_value_var.set(127)
            self.threshold_max_var.set(255)
        
        # Clear any preview
        active_tool = self.app_state.tools.get("effects")
        if active_tool and active_tool.active:
            active_tool.clear_preview() 