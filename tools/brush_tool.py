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

from tools.base_tool import BaseTool

logger = logging.getLogger("Image_Editor.Tools.Brush")

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
        super().__init__(app_state, "brush")
        
        # Drawing state
        self.last_x = None
        self.last_y = None
        self.stroke_points = []
        self.temp_overlay_id = None
        self.temp_overlay = None
        
        # Brush preview
        self.brush_preview_id = None
        
        # Canvas reference
        self.canvas = None
        
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
    
    def activate(self, canvas=None):
        """
        Activate the brush tool.
        
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
        
        # Create brush preview
        self._create_brush_preview()
        
        logger.debug("Brush tool activated")
    
    def deactivate(self):
        """Deactivate the brush tool."""
        self.active = False
        
        # Remove brush preview
        self._remove_brush_preview()
        
        # Clean up any temporary overlays
        if self.temp_overlay_id and self.canvas:
            self.canvas.delete(self.temp_overlay_id)
            self.temp_overlay_id = None
        
        # Remove event bindings
        if self.canvas:
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<Motion>")
            self.canvas = None
        
        logger.debug("Brush tool deactivated")
    
    def on_mouse_down(self, event):
        """
        Start drawing on mouse down.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas:
            return
            
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
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
    
    def on_mouse_up(self, event):
        """
        Finish drawing on mouse up.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas:
            return
            
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
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
    
    def on_mouse_drag(self, event):
        """
        Draw while dragging the mouse.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas:
            return
            
        if self.last_x is None or self.last_y is None:
            return
        
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
        # Add point to stroke
        self.stroke_points.append((x, y))
        
        # Draw line from last position to current position
        self._apply_brush_to_overlay(self.last_x, self.last_y, x, y)
        
        # Update the canvas display
        self._update_overlay_display()
        
        # Update last position
        self.last_x = x
        self.last_y = y
    
    def on_mouse_move(self, event):
        """
        Update brush preview when moving the mouse.
        
        Args:
            event: Original event object
        """
        if not self.active or not self.canvas:
            return
            
        # Get canvas coordinates
        canvas_x, canvas_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        
        # Convert to image coordinates
        x, y = self._canvas_to_image_coords(canvas_x, canvas_y)
        
        # Update brush preview position
        if self.brush_preview_id and not self.last_x:
            # Convert image coordinates to screen coordinates
            screen_x, screen_y = self._image_to_canvas_coords(x, y)
            
            # Update preview position
            brush_size = self.settings.get("size", 10)
            self.canvas.coords(
                self.brush_preview_id,
                screen_x - brush_size/2, screen_y - brush_size/2,
                screen_x + brush_size/2, screen_y + brush_size/2
            )
    
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

    def _create_brush_preview(self):
        """Create a visual preview of the brush."""
        if not self.canvas:
            return
            
        # Remove any existing preview
        self._remove_brush_preview()
        
        # Create a simple circle to represent the brush
        brush_size = self.settings.get("size", 10)
        
        self.brush_preview_id = self.canvas.create_oval(
            0, 0, brush_size, brush_size,
            outline="black", 
            width=1,
            dash=(2, 2),
            tags="brush_preview"
        )
    
    def _remove_brush_preview(self):
        """Remove the brush preview from the canvas."""
        if self.brush_preview_id and self.canvas:
            self.canvas.delete(self.brush_preview_id)
            self.brush_preview_id = None
    
    def _create_brush_stamp(self, size: int, hardness: float) -> np.ndarray:
        """
        Create a brush stamp as an alpha mask.
        
        Args:
            size: Diameter of the brush
            hardness: Edge hardness (0.0 to 1.0)
        
        Returns:
            Numpy array with shape (size, size) and values from 0 to 1
        """
        # Ensure size is odd
        if size % 2 == 0:
            size += 1
        
        # Create a grid of coordinates
        y, x = np.ogrid[-size//2:size//2+1, -size//2:size//2+1]
        
        # Compute distances from center
        distances = np.sqrt(x*x + y*y)
        
        # Normalize distances to range [0, 1]
        normalized_distances = distances / (size/2)
        
        # Apply hardness
        if hardness == 1.0:
            # Hard edge
            mask = (normalized_distances <= 1.0).astype(float)
        else:
            # Soft edge with hardness control
            # Adjust transition zone based on hardness
            inner_radius = hardness
            mask = np.clip(1.0 - (normalized_distances - inner_radius) / (1.0 - inner_radius), 0, 1)
            # Make inner circle solid
            mask[normalized_distances <= inner_radius] = 1.0
        
        return mask
    
    def _apply_brush_to_overlay(self, x1: int, y1: int, x2: int, y2: int):
        """
        Apply brush stroke to the temporary overlay.
        
        Args:
            x1, y1: Starting point in image coordinates
            x2, y2: Ending point in image coordinates
        """
        if self.temp_overlay is None:
            return
            
        # Get brush settings
        size = self.settings.get("size", 10)
        hardness = self.settings.get("hardness", 0.8)
        color = self.settings.get("color", (0, 0, 0))
        opacity = self.settings.get("opacity", 1.0)
        spacing = max(1, int(size * self.settings.get("spacing", 0.1)))
        
        # Create brush stamp
        brush_stamp = self._create_brush_stamp(size, hardness)
        
        # Get points along the line
        points = self._interpolate_points(x1, y1, x2, y2, spacing)
        
        # Apply brush stamps along the line
        for x, y in points:
            self._stamp_brush(self.temp_overlay, x, y, brush_stamp, color, opacity)
    
    def _apply_brush_to_layer(self, x1: int, y1: int, x2: int, y2: int):
        """
        Apply brush stroke directly to the active layer.
        
        Args:
            x1, y1: Starting point in image coordinates
            x2, y2: Ending point in image coordinates
        """
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            return
            
        layer = layer_manager.get_active_layer()
        if layer is None or layer.image_data is None:
            return
            
        # Get brush settings
        size = self.settings.get("size", 10)
        hardness = self.settings.get("hardness", 0.8)
        color = self.settings.get("color", (0, 0, 0))
        opacity = self.settings.get("opacity", 1.0)
        spacing = max(1, int(size * self.settings.get("spacing", 0.1)))
        
        # Create brush stamp
        brush_stamp = self._create_brush_stamp(size, hardness)
        
        # Get points along the line
        points = self._interpolate_points(x1, y1, x2, y2, spacing)
        
        # Get layer image as numpy array
        image = layer.image_data
        
        # Apply brush stamps along the line
        for x, y in points:
            self._stamp_brush(image, x, y, brush_stamp, color, opacity)
    
    def _interpolate_points(self, x1: int, y1: int, x2: int, y2: int, 
                         min_spacing: int) -> List[Tuple[int, int]]:
        """
        Generate a list of points along a line with minimum spacing.
        
        Args:
            x1, y1: Starting point
            x2, y2: Ending point
            min_spacing: Minimum spacing between points
            
        Returns:
            List of (x, y) coordinates
        """
        dx = x2 - x1
        dy = y2 - y1
        
        # Calculate distance between points
        distance = math.sqrt(dx*dx + dy*dy)
        
        # If points are too close, just return endpoints
        if distance < min_spacing:
            return [(x1, y1), (x2, y2)]
        
        # Calculate number of segments
        num_segments = max(1, int(distance / min_spacing))
        
        # Generate points
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            x = int(x1 + t * dx)
            y = int(y1 + t * dy)
            points.append((x, y))
            
        return points
    
    def _stamp_brush(self, image: np.ndarray, x: int, y: int, 
                    brush_stamp: np.ndarray, color: Tuple[int, int, int], 
                    opacity: float):
        """
        Apply a brush stamp to the image at the specified position.
        
        Args:
            image: Image to apply the stamp to
            x, y: Position to center the stamp at
            brush_stamp: Brush stamp alpha mask
            color: RGB color tuple
            opacity: Opacity of the brush stroke (0.0-1.0)
        """
        # Input validation and boundary checks
        if image is None or brush_stamp is None:
            return
            
        if x < 0 or y < 0 or x >= image.shape[1] or y >= image.shape[0]:
            return
        
        # Get the size of the brush stamp
        stamp_height, stamp_width = brush_stamp.shape[:2]
        
        # Calculate the top-left position for the stamp
        center_x = x
        center_y = y
        left = max(0, center_x - stamp_width // 2)
        top = max(0, center_y - stamp_height // 2)
        right = min(image.shape[1], center_x + (stamp_width - stamp_width // 2))
        bottom = min(image.shape[0], center_y + (stamp_height - stamp_height // 2))
        
        # Calculate corresponding region in the stamp
        stamp_left = max(0, (stamp_width // 2) - center_x)
        stamp_top = max(0, (stamp_height // 2) - center_y)
        stamp_right = stamp_width - max(0, (center_x + (stamp_width - stamp_width // 2)) - image.shape[1])
        stamp_bottom = stamp_height - max(0, (center_y + (stamp_height - stamp_height // 2)) - image.shape[0])
        
        # Ensure we have valid regions (at least 1 pixel)
        if left >= right or top >= bottom or stamp_left >= stamp_right or stamp_top >= stamp_bottom:
            return  # Nothing to do
        
        # Get the target regions
        img_region = image[top:bottom, left:right]
        stamp_region = brush_stamp[stamp_top:stamp_bottom, stamp_left:stamp_right]
        
        # Safety check: ensure regions have same dimensions
        if img_region.shape[:2] != stamp_region.shape[:2]:
            # Resize stamp region to match image region
            h, w = img_region.shape[:2]
            if h <= 0 or w <= 0:  # Additional safety check
                return
                
            # Create new stamp region with matching dimensions
            new_stamp = np.zeros((h, w), dtype=np.float32)
            # Copy what we can from the original stamp
            copy_h = min(h, stamp_region.shape[0])
            copy_w = min(w, stamp_region.shape[1])
            new_stamp[:copy_h, :copy_w] = stamp_region[:copy_h, :copy_w]
            stamp_region = new_stamp
        
        # Normalize color to 0-1 range for calculations
        color_array = np.array(color, dtype=np.float32) / 255.0
        
        # Apply stamp based on image type (RGBA vs RGB)
        if image.shape[2] == 4:  # RGBA
            # Create an efficient mask for non-zero alpha pixels
            mask = stamp_region > 0.01
            
            if np.any(mask):
                # Convert to float for calculations
                img_float = img_region.astype(np.float32) / 255.0
                
                # Create result array
                result = img_float.copy()
                
                # Apply brush color with opacity and stamp alpha to RGB channels
                for c in range(3):  # RGB channels
                    result[:, :, c][mask] = (
                        img_float[:, :, c][mask] * (1.0 - stamp_region[mask] * opacity) +
                        color_array[c] * stamp_region[mask] * opacity
                    )
                
                # Apply alpha: new pixel alpha = max(original alpha, brush alpha * opacity)
                brush_alpha = stamp_region * opacity
                result[:, :, 3][mask] = np.maximum(
                    img_float[:, :, 3][mask],
                    brush_alpha[mask]
                )
                
                # Convert back to uint8 and update the image
                image[top:bottom, left:right] = np.clip(result * 255.0, 0, 255).astype(np.uint8)
        
        else:  # RGB
            # Create mask for non-zero alpha pixels
            mask = stamp_region > 0.01
            
            if np.any(mask):
                # Convert to float for calculations
                img_float = img_region.astype(np.float32) / 255.0
                
                # Create result array
                result = img_float.copy()
                
                # Apply brush color with opacity and stamp alpha
                for c in range(3):  # RGB channels
                    result[:, :, c][mask] = (
                        img_float[:, :, c][mask] * (1.0 - stamp_region[mask] * opacity) +
                        color_array[c] * stamp_region[mask] * opacity
                    )
                
                # Convert back to uint8 and update the image
                image[top:bottom, left:right] = np.clip(result * 255.0, 0, 255).astype(np.uint8)
    
    def _update_overlay_display(self):
        """Update the canvas to display the temporary overlay."""
        if not self.canvas or self.temp_overlay is None or not self.active:
            return
            
        # Get current view parameters
        scale = self.app_state.view_scale
        offset_x, offset_y = self.app_state.view_offset
        
        # Size check for overlay
        if self.temp_overlay.size == 0 or self.temp_overlay.shape[0] == 0 or self.temp_overlay.shape[1] == 0:
            logger.warning("Invalid overlay size, skipping display update")
            return
            
        try:
            # Only resize the display image if zoom is not 1:1
            if abs(scale - 1.0) > 0.001:
                # Calculate display dimensions
                height, width = self.temp_overlay.shape[:2]
                display_width = max(1, int(width * scale))
                display_height = max(1, int(height * scale))
                
                # Choose the right interpolation method
                if scale < 0.5:
                    interpolation = cv2.INTER_NEAREST  # Faster for small sizes
                else:
                    interpolation = cv2.INTER_LINEAR
                
                # Resize for display
                display_image = cv2.resize(
                    self.temp_overlay, 
                    (display_width, display_height),
                    interpolation=interpolation
                )
            else:
                display_image = self.temp_overlay
                
            # Create PIL Image from numpy array
            from PIL import Image, ImageTk
            if display_image.shape[2] == 4:  # RGBA
                pil_image = Image.fromarray(display_image, 'RGBA')
            else:  # RGB
                pil_image = Image.fromarray(display_image, 'RGB')
                
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Keep a reference to prevent garbage collection
            self._photo_ref = photo
            
            # Display on canvas
            if self.temp_overlay_id:
                try:
                    # Update existing image
                    self.canvas.itemconfig(self.temp_overlay_id, image=photo)
                    self.canvas.coords(self.temp_overlay_id, offset_x, offset_y)
                except tk.TclError:
                    # Handle the case where the item was deleted
                    self.temp_overlay_id = None
                    
            if not self.temp_overlay_id:
                # Create new image on canvas
                self.temp_overlay_id = self.canvas.create_image(
                    offset_x, offset_y,
                    image=photo,
                    anchor=tk.NW,
                    tags="brush_overlay"
                )
        except Exception as e:
            logger.error(f"Error updating overlay: {str(e)}")
    
    def _commit_stroke(self):
        """Commit the brush stroke to the active layer and create a history state."""
        if not self.canvas:
            return
            
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager:
            return
            
        layer = layer_manager.get_active_layer()
        if not layer:
            return
            
        # Create history state
        self.app_state.add_history_state(
            "Brush Stroke",
            {
                "layer_index": layer_manager.active_layer_index,
                "previous_image": layer.image_data.copy() if hasattr(layer, 'image_data') and layer.image_data is not None else None
            }
        )
        
        # Update the canvas display
        if self.canvas.main_window:
            self.canvas.main_window.refresh_view()
            
        logger.debug("Committed brush stroke") 