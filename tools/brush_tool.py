"""
Brush Tool Module
Provides brush tool for painting on images.
"""

import logging
import math
import tkinter as tk
from typing import Tuple, List, Optional

import numpy as np
import cv2

from photoforge_pro.tools.base_tool import BaseTool

logger = logging.getLogger("PhotoForge.Tools.Brush")

class BrushTool(BaseTool):
    """
    Brush tool for painting on images.
    Supports various brushes with adjustable size, hardness, opacity, and color.
    """
    
    def __init__(self, app_state):
        """
        Initialize the brush tool.
        
        Args:
            app_state: Application state object
        """
        super().__init__(app_state)
        
        # Drawing state
        self.last_x = None
        self.last_y = None
        self.stroke_points = []
        self.temp_overlay_id = None
        self.temp_overlay = None
        
        # Brush preview
        self.brush_preview_id = None
        
        logger.debug("BrushTool initialized")
    
    def init_settings(self):
        """Initialize brush tool settings."""
        # Get default settings from app state
        self.settings = self.app_state.tool_settings.get("brush_tool", {}).copy()
        
        # Set defaults if not in app state
        if not self.settings:
            self.settings = {
                "size": 10,
                "hardness": 0.8,
                "opacity": 1.0,
                "flow": 1.0,
                "spacing": 0.1,
                "color": (0, 0, 0)  # RGB
            }
    
    def get_cursor(self) -> str:
        """
        Get the cursor to use when this tool is active.
        
        Returns:
            Cursor name
        """
        return "crosshair"
    
    def activate(self, canvas):
        """
        Activate the brush tool.
        
        Args:
            canvas: The canvas to activate the tool on
        """
        super().activate(canvas)
        
        # Create brush preview
        self._create_brush_preview()
    
    def deactivate(self):
        """Deactivate the brush tool."""
        # Remove brush preview
        self._remove_brush_preview()
        
        # Clean up any temporary overlays
        if self.temp_overlay_id and self.canvas:
            self.canvas.delete(self.temp_overlay_id)
            self.temp_overlay_id = None
        
        super().deactivate()
    
    def on_mouse_down(self, x: int, y: int, event):
        """
        Start drawing on mouse down.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        # Start a new stroke
        self.last_x = x
        self.last_y = y
        self.stroke_points = [(x, y)]
        
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            return
        
        # Create a temporary overlay for real-time preview
        layer = layer_manager.get_active_layer()
        if layer and layer.image_data is not None:
            # Create a copy of the layer image
            self.temp_overlay = layer.image_data.copy()
            
            # Draw the first point
            self._apply_brush_to_overlay(x, y, x, y)
            
            # Update the canvas display
            self._update_overlay_display()
        
        # Remove brush preview during drawing
        self._remove_brush_preview()
    
    def on_mouse_up(self, x: int, y: int, event):
        """
        Finish drawing on mouse up.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        # Apply final stroke
        if self.last_x is not None and self.last_y is not None:
            # Add final point if different
            if (x, y) != (self.last_x, self.last_y):
                self.stroke_points.append((x, y))
                self._apply_brush_to_layer(self.last_x, self.last_y, x, y)
            
            # Commit the changes
            self._commit_stroke()
        
        # Reset state
        self.last_x = None
        self.last_y = None
        self.stroke_points = []
        
        # Remove temporary overlay
        if self.temp_overlay_id and self.canvas:
            self.canvas.delete(self.temp_overlay_id)
            self.temp_overlay_id = None
        
        self.temp_overlay = None
        
        # Restore brush preview
        self._create_brush_preview()
    
    def on_mouse_drag(self, x: int, y: int, event):
        """
        Draw while dragging the mouse.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        if self.last_x is None or self.last_y is None:
            return
        
        # Add point to stroke
        self.stroke_points.append((x, y))
        
        # Draw line from last position to current position
        self._apply_brush_to_overlay(self.last_x, self.last_y, x, y)
        
        # Update the canvas display
        self._update_overlay_display()
        
        # Update last position
        self.last_x = x
        self.last_y = y
    
    def on_mouse_move(self, x: int, y: int, event):
        """
        Update brush preview when moving the mouse.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            event: Original event object
        """
        # Update brush preview position
        if self.brush_preview_id and self.canvas and not self.last_x:
            # Convert image coordinates to screen coordinates
            screen_x, screen_y = self.canvas.image_to_screen_coords(x, y)
            
            # Update preview position
            self.canvas.coords(self.brush_preview_id, screen_x, screen_y)
    
    def _create_brush_preview(self):
        """Create a preview of the brush cursor."""
        if not self.canvas:
            return
        
        # Remove existing preview
        self._remove_brush_preview()
        
        # Get brush size in screen coordinates
        size = int(self.settings["size"] * self.canvas.zoom)
        
        # Create brush preview circle
        self.brush_preview_id = self.canvas.create_oval(
            -size, -size, size, size,
            outline="black", width=1,
            tags="brush_preview"
        )
    
    def _remove_brush_preview(self):
        """Remove the brush preview."""
        if self.brush_preview_id and self.canvas:
            self.canvas.delete(self.brush_preview_id)
            self.brush_preview_id = None
    
    def _create_brush_stamp(self, size: int, hardness: float) -> np.ndarray:
        """
        Create a brush stamp with the given size and hardness.
        
        Args:
            size: Diameter of the brush in pixels
            hardness: Hardness of the brush (0.0 to 1.0)
        
        Returns:
            Numpy array with alpha channel values
        """
        # Ensure minimum size
        size = max(1, size)
        
        # Create a square image with a circle
        radius = size / 2
        center = radius
        
        # Create a square array
        y, x = np.ogrid[:size, :size]
        
        # Calculate distance from center
        dist = np.sqrt((x - center) ** 2 + (y - center) ** 2)
        
        # Create mask based on distance
        mask = np.zeros((size, size), dtype=np.float32)
        
        # Apply hardness
        # Hardness controls how quickly the alpha transitions from 1 to 0
        # Higher hardness = sharper edge
        if hardness >= 1.0:
            # Hard edge
            mask[dist <= radius] = 1.0
        else:
            # Soft edge with hardness control
            # Calculate transition zone based on hardness
            inner_radius = radius * hardness
            
            # Core area is fully opaque
            mask[dist <= inner_radius] = 1.0
            
            # Transition area has a gradient
            transition_mask = (radius - dist) / (radius - inner_radius)
            transition_area = (dist > inner_radius) & (dist <= radius)
            mask[transition_area] = np.clip(transition_mask[transition_area], 0, 1)
        
        return mask
    
    def _apply_brush_to_overlay(self, x1: int, y1: int, x2: int, y2: int):
        """
        Apply brush stroke to the temporary overlay.
        
        Args:
            x1: Starting X coordinate
            y1: Starting Y coordinate
            x2: Ending X coordinate
            y2: Ending Y coordinate
        """
        if self.temp_overlay is None:
            return
        
        # Get brush settings
        size = self.settings["size"]
        hardness = self.settings["hardness"]
        opacity = self.settings["opacity"]
        color = self.settings["color"]
        
        # Create brush stamp
        brush_stamp = self._create_brush_stamp(size, hardness)
        
        # Interpolate points along the line
        points = self._interpolate_points(x1, y1, x2, y2, size)
        
        # Apply brush to each point
        for x, y in points:
            self._stamp_brush(self.temp_overlay, x, y, brush_stamp, color, opacity)
    
    def _apply_brush_to_layer(self, x1: int, y1: int, x2: int, y2: int):
        """
        Apply brush stroke directly to the layer.
        
        Args:
            x1: Starting X coordinate
            y1: Starting Y coordinate
            x2: Ending X coordinate
            y2: Ending Y coordinate
        """
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            return
        
        layer = layer_manager.get_active_layer()
        if layer is None or layer.image_data is None:
            return
        
        # Get brush settings
        size = self.settings["size"]
        hardness = self.settings["hardness"]
        opacity = self.settings["opacity"]
        color = self.settings["color"]
        
        # Create brush stamp
        brush_stamp = self._create_brush_stamp(size, hardness)
        
        # Interpolate points along the line
        points = self._interpolate_points(x1, y1, x2, y2, size)
        
        # Apply brush to each point
        for x, y in points:
            self._stamp_brush(layer.image_data, x, y, brush_stamp, color, opacity)
    
    def _interpolate_points(self, x1: int, y1: int, x2: int, y2: int, 
                         min_spacing: int) -> List[Tuple[int, int]]:
        """
        Interpolate points along a line with at least the given spacing.
        
        Args:
            x1: Starting X coordinate
            y1: Starting Y coordinate
            x2: Ending X coordinate
            y2: Ending Y coordinate
            min_spacing: Minimum spacing between points
        
        Returns:
            List of (x, y) coordinate tuples
        """
        # Calculate distance between points
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If points are the same or very close, return just one point
        if distance < 1:
            return [(x1, y1)]
        
        # Calculate number of steps based on distance and spacing
        # Use at most min_spacing pixels between points
        spacing = min(min_spacing, distance / 2)
        num_steps = max(2, int(distance / spacing))
        
        # Interpolate points
        points = []
        for step in range(num_steps + 1):
            t = step / num_steps
            x = int(x1 + dx * t)
            y = int(y1 + dy * t)
            points.append((x, y))
        
        return points
    
    def _stamp_brush(self, image: np.ndarray, x: int, y: int, 
                    brush_stamp: np.ndarray, color: Tuple[int, int, int], 
                    opacity: float):
        """
        Apply a brush stamp to the image.
        
        Args:
            image: The image to modify
            x: Center X coordinate
            y: Center Y coordinate
            brush_stamp: Brush stamp alpha mask
            color: RGB color tuple
            opacity: Brush opacity (0.0 to 1.0)
        """
        # Get brush stamp dimensions
        h, w = brush_stamp.shape
        
        # Calculate brush boundaries
        half_w = w // 2
        half_h = h // 2
        left = x - half_w
        top = y - half_h
        
        # Get image dimensions
        img_h, img_w = image.shape[:2]
        
        # Calculate overlap with image
        img_left = max(0, left)
        img_top = max(0, top)
        img_right = min(img_w, left + w)
        img_bottom = min(img_h, top + h)
        
        # If no overlap, return
        if img_right <= img_left or img_bottom <= img_top:
            return
        
        # Calculate brush stamp region
        brush_left = img_left - left
        brush_top = img_top - top
        brush_right = brush_left + (img_right - img_left)
        brush_bottom = brush_top + (img_bottom - img_top)
        
        # Extract the overlapping regions
        brush_region = brush_stamp[brush_top:brush_bottom, brush_left:brush_right]
        img_region = image[img_top:img_bottom, img_left:img_right]
        
        # Apply the brush with opacity
        if image.shape[2] == 4:  # RGBA
            # Convert color to RGBA
            brush_color = np.array([color[0], color[1], color[2], 255], dtype=np.uint8)
            
            # Create a color array with the brush stamp shape
            color_array = np.zeros((brush_region.shape[0], brush_region.shape[1], 4), dtype=np.uint8)
            color_array[:, :] = brush_color
            
            # Apply stamp alpha to color alpha
            color_array[:, :, 3] = (brush_region * opacity * 255).astype(np.uint8)
            
            # Blend using alpha compositing
            alpha_s = color_array[:, :, 3] / 255.0
            alpha_d = img_region[:, :, 3] / 255.0
            
            # Calculate resulting alpha
            alpha_out = alpha_s + alpha_d * (1 - alpha_s)
            alpha_out_255 = (alpha_out * 255).astype(np.uint8)
            
            # Avoid division by zero
            np.clip(alpha_out, 1e-8, 1.0, out=alpha_out)
            
            # Calculate resulting color
            for c in range(3):
                img_region[:, :, c] = ((color_array[:, :, c] * alpha_s + 
                                      img_region[:, :, c] * alpha_d * (1 - alpha_s)) / 
                                     alpha_out).astype(np.uint8)
            
            # Update alpha channel
            img_region[:, :, 3] = alpha_out_255
        else:  # RGB
            # Create a color array with the brush stamp shape
            color_array = np.zeros((brush_region.shape[0], brush_region.shape[1], 3), dtype=np.uint8)
            color_array[:, :] = color
            
            # Calculate alpha for each pixel
            alpha = brush_region * opacity
            
            # Reshape alpha to match color_array shape for broadcasting
            alpha = alpha[:, :, np.newaxis]
            
            # Apply the blend
            img_region[:] = (color_array * alpha + img_region * (1 - alpha)).astype(np.uint8)
    
    def _update_overlay_display(self):
        """Update the overlay display on the canvas."""
        if self.temp_overlay is None or not self.canvas:
            return
        
        # Convert numpy array to PIL Image for display
        from PIL import Image
        if self.temp_overlay.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(self.temp_overlay, 'RGBA')
        else:  # RGB
            pil_image = Image.fromarray(self.temp_overlay, 'RGB')
        
        # Convert to Tkinter PhotoImage
        from PIL import ImageTk
        tk_image = ImageTk.PhotoImage(pil_image)
        
        # Store reference to prevent garbage collection
        self._tk_image_ref = tk_image
        
        # Update or create overlay image on canvas
        if self.temp_overlay_id:
            self.canvas.itemconfig(self.temp_overlay_id, image=tk_image)
        else:
            # Create a new image item
            self.temp_overlay_id = self.canvas.create_image(
                self.canvas.offset_x, self.canvas.offset_y,
                image=tk_image, anchor=tk.NW, tags="temp_overlay"
            )
    
    def _commit_stroke(self):
        """Commit the current stroke to the active layer."""
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            return
        
        layer = layer_manager.get_active_layer()
        if layer is None:
            return
        
        # Apply the changes to the layer
        if self.temp_overlay is not None:
            # Set the layer image data to the modified overlay
            layer.image_data = self.temp_overlay.copy()
            
            # Update the canvas display with the composite image
            self.canvas.set_image(layer_manager.render_composite())
            
            # Update the layer thumbnail
            if layer.id in self.canvas.main_window.layer_panel.layer_widgets:
                layer_widget = self.canvas.main_window.layer_panel.layer_widgets[layer.id]
                layer_widget.set_thumbnail(layer.image_data)
            
            # Add to undo history (TODO: implement proper history) 