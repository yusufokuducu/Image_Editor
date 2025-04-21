"""
Layer Panel Module
Provides UI for managing image layers.
"""

import logging
import tkinter as tk
from typing import Dict, List, Optional, Any

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from core.layer_manager import Layer
from core.image_handler import ImageHandler

logger = logging.getLogger("PhotoForge.LayerPanel")

class LayerItem(ctk.CTkFrame):
    """
    Widget representing a single layer in the layer panel.
    """
    
    def __init__(self, parent, layer_id: str, layer_name: str, 
                visible: bool = True, opacity: float = 1.0, 
                thumbnail=None, selected: bool = False,
                on_select=None, on_visibility_change=None, 
                on_opacity_change=None, **kwargs):
        """
        Initialize a layer item.
        
        Args:
            parent: Parent widget
            layer_id: Unique ID for the layer
            layer_name: Display name for the layer
            visible: Whether the layer is visible
            opacity: Layer opacity (0.0 to 1.0)
            thumbnail: Optional thumbnail image
            selected: Whether the layer is selected
            on_select: Callback for selection
            on_visibility_change: Callback for visibility changes
            on_opacity_change: Callback for opacity changes
            **kwargs: Additional arguments for CTkFrame
        """
        fg_color = kwargs.pop('fg_color', ("#EEEEEE", "#333333"))
        super().__init__(parent, fg_color=fg_color, **kwargs)
        
        self.layer_id = layer_id
        self.layer_name = layer_name
        self.visible = visible
        self.opacity = opacity
        self.selected = selected
        self.thumbnail_image = None  # PIL Image
        self.thumbnail_photo = None  # Tkinter PhotoImage
        
        # Callbacks
        self.on_select = on_select
        self.on_visibility_change = on_visibility_change
        self.on_opacity_change = on_opacity_change
        
        # State colors
        self.selected_color = ("#C0E0FF", "#405060")
        self.normal_color = ("#EEEEEE", "#333333")
        
        # Create UI elements
        self.create_widgets()
        
        # Set thumbnail if provided
        if thumbnail is not None:
            self.set_thumbnail(thumbnail)
        
        # Set selection state
        self.set_selected(selected)
        
        # Bind events
        self.bind("<Button-1>", self._on_click)
        self.thumbnail_label.bind("<Button-1>", self._on_click)
        self.name_label.bind("<Button-1>", self._on_click)
        self.name_label.bind("<Double-Button-1>", self._on_double_click)
    
    def create_widgets(self):
        """Create layer item widgets."""
        # Main layout - horizontal
        self.columnconfigure(1, weight=1)  # Let name label expand
        
        # Visibility toggle
        self.visible_var = tk.BooleanVar(value=self.visible)
        self.visibility_btn = ctk.CTkCheckBox(
            self, 
            text="",
            variable=self.visible_var,
            command=self._on_visibility_change,
            width=20,
            height=20,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3
        )
        self.visibility_btn.grid(row=0, column=0, padx=(5, 0), pady=5, sticky="w")
        
        # Thumbnail preview
        self.thumbnail_label = ctk.CTkLabel(
            self,
            text="",
            width=40,
            height=40
        )
        self.thumbnail_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Layer name
        self.name_label = ctk.CTkLabel(
            self,
            text=self.layer_name,
            anchor="w"
        )
        self.name_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Layer opacity
        opacity_frame = ctk.CTkFrame(self, fg_color="transparent")
        opacity_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="ew")
        
        opacity_label = ctk.CTkLabel(
            opacity_frame,
            text="Opacity:",
            font=("Helvetica", 10)
        )
        opacity_label.pack(side=tk.LEFT, padx=5)
        
        self.opacity_var = tk.IntVar(value=int(self.opacity * 100))
        opacity_slider = ctk.CTkSlider(
            opacity_frame,
            from_=0,
            to=100,
            variable=self.opacity_var,
            command=self._on_opacity_change,
            width=120
        )
        opacity_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.opacity_value_label = ctk.CTkLabel(
            opacity_frame,
            text=f"{int(self.opacity * 100)}%",
            font=("Helvetica", 10),
            width=35
        )
        self.opacity_value_label.pack(side=tk.RIGHT, padx=5)
    
    def set_thumbnail(self, image):
        """
        Set the layer thumbnail.
        
        Args:
            image: PIL Image or NumPy array
        """
        try:
            # Convert to PIL Image if needed
            if not isinstance(image, Image.Image):
                if isinstance(image, np.ndarray):
                    # Convert NumPy array to PIL Image
                    if len(image.shape) == 3 and image.shape[2] == 4:  # RGBA
                        pil_image = Image.fromarray(image, 'RGBA')
                    elif len(image.shape) == 3 and image.shape[2] == 3:  # RGB
                        pil_image = Image.fromarray(image, 'RGB')
                    else:
                        # Handle grayscale or other formats
                        pil_image = Image.fromarray(image.astype('uint8'))
                else:
                    raise ValueError("Unsupported image format")
            else:
                pil_image = image
            
            # Resize to thumbnail size
            thumbnail_size = (36, 36)
            # Create a copy to avoid modifying the original
            thumb = pil_image.copy()
            thumb.thumbnail(thumbnail_size, Image.LANCZOS)
            
            # Create a PhotoImage for Tkinter
            self.thumbnail_image = thumb
            self.thumbnail_photo = ImageTk.PhotoImage(thumb)
            
            # Update the label
            self.thumbnail_label.configure(image=self.thumbnail_photo)
            
        except Exception as e:
            logger.error(f"Error setting thumbnail: {str(e)}")
            # Set fallback thumbnail or clear existing one
            self.thumbnail_label.configure(image=None, text="No\nPreview")
    
    def set_selected(self, selected: bool):
        """
        Set the selection state of the layer item.
        
        Args:
            selected: Whether the layer is selected
        """
        self.selected = selected
        if selected:
            self.configure(fg_color=self.selected_color)
        else:
            self.configure(fg_color=self.normal_color)
    
    def set_name(self, name: str):
        """
        Set the layer name.
        
        Args:
            name: New layer name
        """
        self.layer_name = name
        self.name_label.configure(text=name)
    
    def set_visible(self, visible: bool):
        """
        Set the layer visibility.
        
        Args:
            visible: Whether the layer is visible
        """
        self.visible = visible
        self.visible_var.set(visible)
    
    def set_opacity(self, opacity: float):
        """
        Set the layer opacity.
        
        Args:
            opacity: Layer opacity (0.0 to 1.0)
        """
        self.opacity = max(0.0, min(1.0, opacity))
        self.opacity_var.set(int(self.opacity * 100))
        self.opacity_value_label.configure(text=f"{int(self.opacity * 100)}%")
    
    def _on_click(self, event):
        """Handle click event."""
        if self.on_select:
            self.on_select(self.layer_id)
    
    def _on_double_click(self, event):
        """Handle double-click event for renaming."""
        # TODO: Implement layer renaming
        pass
    
    def _on_visibility_change(self):
        """Handle visibility checkbox change."""
        self.visible = self.visible_var.get()
        if self.on_visibility_change:
            self.on_visibility_change(self.layer_id, self.visible)
    
    def _on_opacity_change(self, value=None):
        """Handle opacity slider change."""
        self.opacity = self.opacity_var.get() / 100.0
        self.opacity_value_label.configure(text=f"{int(self.opacity * 100)}%")
        if self.on_opacity_change:
            self.on_opacity_change(self.layer_id, self.opacity)


class LayerPanel(ctk.CTkFrame):
    """
    Panel for displaying and managing layers.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize the layer panel.
        
        Args:
            parent: Parent widget
            main_window: Reference to the main window
        """
        super().__init__(parent)
        
        self.main_window = main_window
        self.app_state = main_window.app_state
        
        # Store layer widgets
        self.layer_widgets: Dict[str, LayerItem] = {}
        
        # Create UI elements
        self.create_widgets()
        
        logger.info("Layer panel initialized")
    
    def create_widgets(self):
        """Create layer panel widgets."""
        # Layer list frame
        self.layers_frame = ctk.CTkScrollableFrame(self)
        self.layers_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Layer action buttons
        add_btn = ctk.CTkButton(
            btn_frame, 
            text="+",
            width=30,
            height=30,
            command=self.add_layer
        )
        add_btn.pack(side=tk.LEFT, padx=2)
        
        duplicate_btn = ctk.CTkButton(
            btn_frame,
            text="D",
            width=30,
            height=30,
            command=self.duplicate_layer
        )
        duplicate_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="-",
            width=30,
            height=30,
            command=self.delete_layer
        )
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        # Blend mode selection
        blend_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        blend_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        blend_label = ctk.CTkLabel(blend_frame, text="Blend:")
        blend_label.pack(side=tk.LEFT, padx=5)
        
        blend_modes = ["Normal", "Multiply", "Screen", "Overlay", "Darken", "Lighten"]
        self.blend_var = tk.StringVar(value=blend_modes[0])
        
        blend_dropdown = ctk.CTkOptionMenu(
            blend_frame,
            values=blend_modes,
            variable=self.blend_var,
            command=self.set_blend_mode,
            width=120
        )
        blend_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Initial state - display message when no layers
        self.no_layers_label = ctk.CTkLabel(
            self.layers_frame,
            text="No image open.\nCreate a new image or open an existing one.",
            font=("Helvetica", 12),
            justify=tk.CENTER
        )
        self.no_layers_label.pack(pady=20)
    
    def update_layers(self):
        """Update the layer list based on the current document."""
        # Clear existing layer widgets
        for widget in self.layer_widgets.values():
            widget.destroy()
        self.layer_widgets.clear()
        
        # Remove no layers message if present
        if hasattr(self, 'no_layers_label') and self.no_layers_label.winfo_exists():
            self.no_layers_label.destroy()
        
        # Check if we have a layer manager
        layer_manager = self.main_window.layer_manager
        if not layer_manager or not layer_manager.layers:
            # Show no layers message
            self.no_layers_label = ctk.CTkLabel(
                self.layers_frame,
                text="No layers available.",
                font=("Helvetica", 12),
                justify=tk.CENTER
            )
            self.no_layers_label.pack(pady=20)
            return
        
        # Add layers in reverse order (top to bottom)
        for i, layer in enumerate(reversed(layer_manager.layers)):
            # Create layer widget
            layer_widget = LayerItem(
                self.layers_frame,
                layer_id=layer.id,
                layer_name=layer.name,
                visible=layer.visible,
                opacity=layer.opacity,
                selected=(i == len(layer_manager.layers) - 1 - layer_manager.active_layer_index),
                on_select=self.on_layer_selected,
                on_visibility_change=self.on_layer_visibility_changed,
                on_opacity_change=self.on_layer_opacity_changed
            )
            
            # Set thumbnail if image is available
            if layer.image_data is not None:
                layer_widget.set_thumbnail(layer.image_data)
            
            # Add to the frame
            layer_widget.pack(fill=tk.X, padx=5, pady=2)
            
            # Store in dictionary
            self.layer_widgets[layer.id] = layer_widget
    
    def add_layer(self):
        """Add a new layer."""
        layer_manager = self.main_window.layer_manager
        if not layer_manager:
            self.main_window.set_status("No document open")
            return
        
        # Create a new transparent layer
        from photoforge_pro.core.layer_manager import Layer
        
        # Get image dimensions
        width, height = self.app_state.image_dimensions
        
        # Create transparent image
        from photoforge_pro.core.image_handler import ImageHandler
        transparent_image = ImageHandler.create_blank_image(
            width, height, (0, 0, 0), True
        )
        
        # Create layer with transparent image
        new_layer = Layer(
            name=f"Layer {len(layer_manager.layers)}",
            image_data=transparent_image,
            visible=True,
            opacity=1.0,
            blend_mode="normal"
        )
        
        # Add to layer manager
        layer_manager.add_layer(new_layer)
        
        # Update UI
        self.update_layers()
        
        # Update canvas
        self.main_window.canvas.set_image(layer_manager.render_composite())
        
        # Set status message
        self.main_window.set_status(f"Added new layer: {new_layer.name}")
        
        logger.info(f"Added new layer: {new_layer.name}")
    
    def duplicate_layer(self):
        """Duplicate the selected layer."""
        layer_manager = self.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            self.main_window.set_status("No layer selected")
            return
        
        # Duplicate the active layer
        index = layer_manager.duplicate_layer(layer_manager.active_layer_index)
        
        if index >= 0:
            # Update UI
            self.update_layers()
            
            # Update canvas
            self.main_window.canvas.set_image(layer_manager.render_composite())
            
            # Set status message
            layer_name = layer_manager.layers[index].name
            self.main_window.set_status(f"Duplicated layer: {layer_name}")
            
            logger.info(f"Duplicated layer: {layer_name}")
    
    def delete_layer(self):
        """Delete the selected layer."""
        layer_manager = self.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            self.main_window.set_status("No layer selected")
            return
        
        # Get the layer name
        layer_name = layer_manager.layers[layer_manager.active_layer_index].name
        
        # Don't delete the last layer
        if len(layer_manager.layers) <= 1:
            self.main_window.set_status("Cannot delete the only layer")
            return
        
        # Delete the active layer
        if layer_manager.delete_layer(layer_manager.active_layer_index):
            # Update UI
            self.update_layers()
            
            # Update canvas
            self.main_window.canvas.set_image(layer_manager.render_composite())
            
            # Set status message
            self.main_window.set_status(f"Deleted layer: {layer_name}")
            
            logger.info(f"Deleted layer: {layer_name}")
    
    def on_layer_selected(self, layer_id):
        """
        Handle layer selection.
        
        Args:
            layer_id: ID of the selected layer
        """
        layer_manager = self.main_window.layer_manager
        if not layer_manager:
            return
        
        # Find the layer index by ID
        for i, layer in enumerate(layer_manager.layers):
            if layer.id == layer_id:
                # Set as active layer
                layer_manager.set_active_layer(i)
                
                # Update UI
                self.update_layers()
                
                # Set status message
                self.main_window.set_status(f"Selected layer: {layer.name}")
                
                logger.info(f"Selected layer: {layer.name}")
                return
    
    def on_layer_visibility_changed(self, layer_id, visible):
        """
        Handle layer visibility change.
        
        Args:
            layer_id: ID of the layer
            visible: New visibility state
        """
        layer_manager = self.main_window.layer_manager
        if not layer_manager:
            return
        
        # Find the layer by ID
        for layer in layer_manager.layers:
            if layer.id == layer_id:
                # Update layer visibility
                layer.visible = visible
                
                # Update canvas
                self.main_window.canvas.set_image(layer_manager.render_composite())
                
                # Set status message
                status = "visible" if visible else "hidden"
                self.main_window.set_status(f"Layer '{layer.name}' is now {status}")
                
                logger.info(f"Layer '{layer.name}' visibility changed to {visible}")
                return
    
    def on_layer_opacity_changed(self, layer_id, opacity):
        """
        Handle layer opacity change.
        
        Args:
            layer_id: ID of the layer
            opacity: New opacity value (0.0 to 1.0)
        """
        layer_manager = self.main_window.layer_manager
        if not layer_manager:
            return
        
        # Find the layer by ID
        for layer in layer_manager.layers:
            if layer.id == layer_id:
                # Update layer opacity
                layer.opacity = opacity
                
                # Update canvas
                self.main_window.canvas.set_image(layer_manager.render_composite())
                
                # Set status message
                self.main_window.set_status(f"Layer '{layer.name}' opacity: {int(opacity * 100)}%")
                
                logger.info(f"Layer '{layer.name}' opacity changed to {opacity:.2f}")
                return
    
    def set_blend_mode(self, blend_mode):
        """
        Set the blend mode for the active layer.
        
        Args:
            blend_mode: Blend mode name
        """
        layer_manager = self.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            self.main_window.set_status("No layer selected")
            return
        
        # Convert UI blend mode name to internal name
        blend_mode_map = {
            "Normal": "normal",
            "Multiply": "multiply",
            "Screen": "screen",
            "Overlay": "overlay",
            "Darken": "darken",
            "Lighten": "lighten"
        }
        
        internal_mode = blend_mode_map.get(blend_mode, "normal")
        
        # Get the active layer
        layer = layer_manager.layers[layer_manager.active_layer_index]
        
        # Update blend mode
        layer.blend_mode = internal_mode
        
        # Update canvas
        self.main_window.canvas.set_image(layer_manager.render_composite())
        
        # Set status message
        self.main_window.set_status(f"Layer '{layer.name}' blend mode: {blend_mode}")
        
        logger.info(f"Layer '{layer.name}' blend mode changed to {blend_mode}") 