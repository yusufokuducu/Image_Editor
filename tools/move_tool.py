"""
Move Tool Module
Provides the move tool for moving layers or selections.
"""

import logging
import tkinter as tk
from typing import Optional, Tuple

import numpy as np

from tools.base_tool import BaseTool

logger = logging.getLogger("Image_Editor.Tools.Move")

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
        super().__init__(app_state, "move")
        
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
        
        # Canvas reference
        self.canvas = None
        
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
    
    def activate(self, canvas=None):
        """
        Activate the move tool.
        
        Args:
            canvas: The canvas to activate the tool on
        """
        self.active = True
        self.canvas = canvas or self.app_state.get_active_canvas()
        
        if self.canvas:
            self.canvas.config(cursor=self.get_cursor())
            
            # Set up event bindings
            self.canvas.bind("<Button-1>", self.on_mouse_down)
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<Motion>", self.on_mouse_move)
        
        logger.debug("Move tool activated")
    
    def deactivate(self):
        """Deactivate the move tool."""
        self.active = False
        
        # Clean up any temporary overlays
        self._clear_preview()
        
        # Remove event bindings
        if self.canvas:
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<Motion>")
            self.canvas = None
        
        logger.debug("Move tool deactivated")
    
    def on_mouse_down(self, event):
        """
        Start moving on mouse down.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas:
            return
            
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
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
    
    def on_mouse_up(self, event):
        """
        Finish moving on mouse up.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas or not self.dragging:
            return
            
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
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
    
    def on_mouse_drag(self, event):
        """
        Move while dragging the mouse.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas or not self.dragging:
            return
            
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
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
    
    def on_mouse_move(self, event):
        """
        Update cursor on mouse move.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas or self.dragging:
            return
            
        # Always use the move cursor when active
        self.canvas.config(cursor=self.get_cursor())
    
    def _canvas_to_image_coords(self, canvas_x, canvas_y):
        """Convert canvas coordinates to image coordinates."""
        scale = self.app_state.view_scale
        offset_x, offset_y = self.app_state.view_offset
        
        img_x = int((canvas_x - offset_x) / scale)
        img_y = int((canvas_y - offset_y) / scale)
        
        return img_x, img_y
    
    def _image_to_canvas_coords(self, img_x, img_y):
        """Convert image coordinates to canvas coordinates."""
        scale = self.app_state.view_scale
        offset_x, offset_y = self.app_state.view_offset
        
        canvas_x = int(img_x * scale + offset_x)
        canvas_y = int(img_y * scale + offset_y)
        
        return canvas_x, canvas_y
    
    def _create_preview(self, image_data: np.ndarray):
        """
        Create a visual preview of the layer being moved.
        
        Args:
            image_data: The image data for the layer
        """
        if not self.canvas or image_data is None:
            return
            
        # Clean up any existing preview
        self._clear_preview()
        
        # Create PIL Image from numpy array
        from PIL import Image, ImageTk
        if image_data.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(image_data)
        else:  # RGB
            pil_image = Image.fromarray(image_data)
            
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(pil_image)
        
        # Keep a reference to prevent garbage collection
        self._preview_image_ref = photo
        
        # Get the current position of the layer (in canvas coordinates)
        offset_x, offset_y = self.app_state.view_offset
        scale = self.app_state.view_scale
        
        # Create the preview image on the canvas
        self.preview_image_id = self.canvas.create_image(
            offset_x, offset_y,
            image=photo,
            anchor=tk.NW,
            tags="move_preview"
        )
        
        # Move the preview to the top of the canvas display list
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
            
        # Convert image coordinate delta to canvas coordinate delta
        scale = self.app_state.view_scale
        canvas_dx = dx * scale
        canvas_dy = dy * scale
        
        # Move the preview
        self.canvas.move(self.preview_image_id, canvas_dx, canvas_dy)
    
    def _clear_preview(self):
        """Clear the move preview."""
        if self.canvas and self.preview_image_id:
            self.canvas.delete(self.preview_image_id)
            self.preview_image_id = None
            self._preview_image_ref = None
    
    def _apply_layer_move(self, dx: int, dy: int):
        """
        Apply the movement to the layer.
        
        Args:
            dx: X movement in image coordinates
            dy: Y movement in image coordinates
        """
        if not self.active_layer:
            return
            
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager:
            return
            
        # Update the layer position
        if hasattr(self.active_layer, 'position'):
            # Get current position
            x, y = self.active_layer.position
            
            # Update position
            self.active_layer.position = (x + dx, y + dy)
            
            # Create history state
            self.app_state.add_history_state(
                "Move Layer",
                {
                    "layer_index": layer_manager.active_layer_index,
                    "previous_position": (x, y),
                    "new_position": self.active_layer.position
                }
            )
            
        # Update the canvas display
        if self.canvas.main_window:
            self.canvas.main_window.refresh_view()
            
        logger.debug(f"Applied layer move: dx={dx}, dy={dy}")
    
    def _move_selection(self, dx: int, dy: int):
        """
        Move the current selection.
        
        Args:
            dx: X movement in image coordinates
            dy: Y movement in image coordinates
        """
        if not self.app_state.has_selection:
            return
            
        selection_bounds = self.app_state.selection_bounds
        if not selection_bounds:
            return
            
        # Unpack the current bounds
        sel_x, sel_y, sel_width, sel_height = selection_bounds
        
        # Update the bounds
        new_bounds = (sel_x + dx, sel_y + dy, sel_width, sel_height)
        self.app_state.selection_bounds = new_bounds
        
        # Update any selection visuals
        # This would typically be handled by the selection_manager or similar component
        
        # Refresh the view
        if self.canvas.main_window:
            self.canvas.main_window.refresh_view()
            
        logger.debug(f"Moved selection: dx={dx}, dy={dy}") 