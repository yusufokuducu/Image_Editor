"""
Move Tool Module
Provides the move tool for moving layers or selections.
"""

import logging
import tkinter as tk
from typing import Optional, Tuple

import numpy as np

from photoforge_pro.tools.base_tool import BaseTool

logger = logging.getLogger("PhotoForge.Tools.Move")

class MoveTool(BaseTool):
    """
    Move tool for positioning layers or selections.
    """
    
    def __init__(self, app_state):
        """
        Initialize the move tool.
        
        Args:
            app_state: Application state object
        """
        super().__init__(app_state)
        
        # State for dragging
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.last_x = 0
        self.last_y = 0
        
        # Layer being moved
        self.active_layer = None
        self.layer_offset = (0, 0)  # Initial offset of the layer
        
        # Selection being moved
        self.moving_selection = False
        
        # Preview
        self.preview_image_id = None
        self._preview_image_ref = None  # Keep reference to prevent garbage collection
        
        logger.debug("MoveTool initialized")
    
    def init_settings(self):
        """Initialize move tool settings."""
        # Get default settings from app state
        self.settings = self.app_state.tool_settings.get("move_tool", {}).copy()
        
        # Set defaults if not in app state
        if not self.settings:
            self.settings = {
                "auto_select_layer": True
            }
    
    def get_cursor(self) -> str:
        """
        Get the cursor to use when this tool is active.
        
        Returns:
            Cursor name
        """
        return "fleur"  # Four-way arrow cursor
    
    def activate(self, canvas):
        """
        Activate the move tool.
        
        Args:
            canvas: The canvas to activate the tool on
        """
        super().activate(canvas)
    
    def deactivate(self):
        """Deactivate the move tool."""
        # Clean up any temporary overlays
        self._clear_preview()
        
        super().deactivate()
    
    def on_mouse_down(self, x: int, y: int, event):
        """
        Start moving on mouse down.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        # Reset state
        self.dragging = False
        self.active_layer = None
        self.moving_selection = False
        
        # Check if we have an active selection
        if self.app_state.has_selection:
            selection_bounds = self.app_state.selection_bounds
            if selection_bounds:
                sel_x, sel_y, sel_width, sel_height = selection_bounds
                
                # Check if the click is inside the selection
                if (sel_x <= x < sel_x + sel_width and
                    sel_y <= y < sel_y + sel_height):
                    # Start moving the selection
                    self.dragging = True
                    self.moving_selection = True
                    self.start_x = x
                    self.start_y = y
                    self.last_x = x
                    self.last_y = y
                    return
        
        # No selection being moved, try to move a layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager:
            return
        
        # Get the active layer
        active_layer_idx = layer_manager.active_layer_index
        if active_layer_idx < 0:
            return
        
        layer = layer_manager.get_active_layer()
        if layer is None or layer.locked:
            return
        
        # Start moving the layer
        self.dragging = True
        self.active_layer = layer
        self.start_x = x
        self.start_y = y
        self.last_x = x
        self.last_y = y
        
        # Create a preview of the layer being moved
        self._create_preview(layer.image_data)
    
    def on_mouse_up(self, x: int, y: int, event):
        """
        Finish moving on mouse up.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        if not self.dragging:
            return
        
        # Apply the final movement
        if self.moving_selection:
            self._move_selection(x - self.last_x, y - self.last_y)
        elif self.active_layer:
            # Calculate total movement
            total_dx = x - self.start_x
            total_dy = y - self.start_y
            
            # Apply the move to the layer
            self._apply_layer_move(total_dx, total_dy)
        
        # Clean up
        self._clear_preview()
        
        # Reset state
        self.dragging = False
        self.active_layer = None
        self.moving_selection = False
    
    def on_mouse_drag(self, x: int, y: int, event):
        """
        Move while dragging the mouse.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        if not self.dragging:
            return
        
        # Calculate movement delta
        dx = x - self.last_x
        dy = y - self.last_y
        
        if self.moving_selection:
            # Move the selection
            self._move_selection(dx, dy)
        elif self.active_layer:
            # Move the preview
            self._move_preview(dx, dy)
        
        # Update last position
        self.last_x = x
        self.last_y = y
    
    def on_mouse_move(self, x: int, y: int, event):
        """
        Update cursor based on what's under it.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        # We could change the cursor based on what's underneath
        # For example, if hovering over a selection or active layer
        pass
    
    def _create_preview(self, image_data: np.ndarray):
        """
        Create a preview image for dragging.
        
        Args:
            image_data: Image data for the preview
        """
        if not self.canvas:
            return
        
        # Convert numpy array to PIL Image
        from PIL import Image
        if image_data.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(image_data, 'RGBA')
        else:  # RGB
            pil_image = Image.fromarray(image_data, 'RGB')
        
        # Apply semi-transparency to indicate it's being moved
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(1.2)  # Slightly brighter
        
        # Convert to Tkinter PhotoImage
        from PIL import ImageTk
        tk_image = ImageTk.PhotoImage(pil_image)
        
        # Store reference to prevent garbage collection
        self._preview_image_ref = tk_image
        
        # Create image on canvas
        canvas_x, canvas_y = self.canvas.image_to_screen_coords(0, 0)
        
        self.preview_image_id = self.canvas.create_image(
            canvas_x, canvas_y,
            image=tk_image,
            anchor=tk.NW,
            tags="move_preview"
        )
        
        # Bring preview to front
        self.canvas.tag_raise(self.preview_image_id)
    
    def _move_preview(self, dx: int, dy: int):
        """
        Move the preview image on the canvas.
        
        Args:
            dx: X movement in image coordinates
            dy: Y movement in image coordinates
        """
        if not self.canvas or not self.preview_image_id:
            return
        
        # Convert to screen coordinates
        screen_dx = dx * self.canvas.zoom
        screen_dy = dy * self.canvas.zoom
        
        # Move the preview
        self.canvas.move(self.preview_image_id, screen_dx, screen_dy)
    
    def _clear_preview(self):
        """Remove the preview image from the canvas."""
        if self.canvas and self.preview_image_id:
            self.canvas.delete(self.preview_image_id)
            self.preview_image_id = None
            self._preview_image_ref = None
    
    def _apply_layer_move(self, dx: int, dy: int):
        """
        Apply the move to the layer.
        
        Args:
            dx: Total X movement
            dy: Total Y movement
        """
        if not self.active_layer:
            return
        
        # For now, we'll just update the layer's offset attribute
        # In a more complete implementation, this would modify the layer's position
        # and possibly apply the transformation to the image data
        
        # TODO: Implement layer position/transformation in the Layer class
        
        # Update the canvas
        layer_manager = self.canvas.main_window.layer_manager
        if layer_manager:
            # Re-render the composite with the moved layer
            composite = layer_manager.render_composite()
            self.canvas.set_image(composite)
            
            # Log the movement
            logger.debug(f"Moved layer by dx={dx}, dy={dy}")
    
    def _move_selection(self, dx: int, dy: int):
        """
        Move the current selection.
        
        Args:
            dx: X movement
            dy: Y movement
        """
        if not self.app_state.has_selection or not self.app_state.selection_bounds:
            return
        
        # Get the current selection bounds
        sel_x, sel_y, sel_width, sel_height = self.app_state.selection_bounds
        
        # Update the bounds
        sel_x += dx
        sel_y += dy
        
        # Enforce bounds within image dimensions
        if self.app_state.image_dimensions:
            img_width, img_height = self.app_state.image_dimensions
            sel_x = max(0, min(sel_x, img_width - sel_width))
            sel_y = max(0, min(sel_y, img_height - sel_height))
        
        # Update the selection in app state
        self.app_state.selection_bounds = (sel_x, sel_y, sel_width, sel_height)
        
        # Update the selection display on the canvas
        if self.canvas:
            # For now, we'll just assume the canvas will update the selection display
            # In a real implementation, you would call a method on the canvas to update
            # the selection visualization
            self.canvas.update_selection_display()
            
        # Log the selection movement
        logger.debug(f"Moved selection to x={sel_x}, y={sel_y}") 