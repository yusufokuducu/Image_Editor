import logging
import tkinter as tk
from typing import Optional, Tuple, Dict, Any
import numpy as np
from PIL import Image

from tools.base_tool import BaseTool
from core.app_state import AppState

logger = logging.getLogger("Image_Editor.CropTool")

class CropTool(BaseTool):
    """Tool for cropping images."""
    
    def __init__(self, app_state: AppState):
        super().__init__(app_state, "crop")
        self.crop_rect = None  # (x1, y1, x2, y2)
        self.drag_start = None
        self.is_dragging = False
        self.drag_handle = None  # corner being dragged (tl, tr, bl, br)
        self.handle_size = 10  # size of resize handles
        
        # Crop tool settings
        self.settings = {
            "aspect_ratio": None,  # None for free-form, or tuple (width, height)
            "show_guides": True,   # Show the rule of thirds guides
            "show_dimensions": True  # Show current dimensions
        }
        
        # Canvas elements
        self.canvas_elements = {
            "rectangle": None,
            "handles": {},
            "guides": [],
            "dimension_text": None
        }
    
    def activate(self):
        """Activate the crop tool."""
        logger.info("Crop tool activated")
        self.active = True
        self.app_state.set_cursor("crosshair")
        
        # Set up event bindings
        canvas = self.app_state.get_active_canvas()
        if canvas:
            canvas.bind("<Button-1>", self.on_mouse_down)
            canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
            canvas.bind("<B1-Motion>", self.on_mouse_drag)
            canvas.bind("<Motion>", self.on_mouse_move)
    
    def deactivate(self):
        """Deactivate the crop tool."""
        logger.info("Crop tool deactivated")
        self.active = False
        
        # Remove crop UI
        self._remove_crop_ui()
        
        # Remove event bindings
        canvas = self.app_state.get_active_canvas()
        if canvas:
            canvas.unbind("<Button-1>")
            canvas.unbind("<ButtonRelease-1>")
            canvas.unbind("<B1-Motion>")
            canvas.unbind("<Motion>")
    
    def on_mouse_down(self, event):
        """Handle mouse button press."""
        if not self.active:
            return
        
        canvas = self.app_state.get_active_canvas()
        if not canvas:
            return
        
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        
        # Check if clicking on a handle
        if self.crop_rect:
            handle = self._get_handle_at_position(x, y)
            if handle:
                self.is_dragging = True
                self.drag_handle = handle
                self.drag_start = (x, y)
                return
                
        # Start a new crop rectangle or drag the existing one
        if self.crop_rect:
            # Check if clicking inside the crop rectangle to move it
            if self._point_in_rect(x, y, self.crop_rect):
                self.is_dragging = True
                self.drag_start = (x, y)
                return
            
        # Start a new crop rectangle
        self._remove_crop_ui()
        self.crop_rect = (x, y, x, y)  # Initial rectangle is just a point
        self.is_dragging = True
        self.drag_start = (x, y)
        self.drag_handle = None
        
        # Draw the initial crop rectangle
        self._update_crop_ui()
    
    def on_mouse_up(self, event):
        """Handle mouse button release."""
        if not self.active or not self.is_dragging:
            return
        
        self.is_dragging = False
        self.drag_start = None
        self.drag_handle = None
        
        # Ensure the rectangle has non-zero area and positive dimensions
        if self.crop_rect:
            x1, y1, x2, y2 = self.crop_rect
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            self.crop_rect = (x1, y1, x2, y2)
            
            # Update the UI
            self._update_crop_ui()
    
    def on_mouse_drag(self, event):
        """Handle mouse drag."""
        if not self.active or not self.is_dragging or not self.crop_rect:
            return
        
        canvas = self.app_state.get_active_canvas()
        if not canvas:
            return
        
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        x1, y1, x2, y2 = self.crop_rect
        
        if self.drag_handle:
            # Resize by dragging a corner handle
            if self.drag_handle == "tl":  # Top-left
                x1, y1 = x, y
            elif self.drag_handle == "tr":  # Top-right
                x2, y1 = x, y
            elif self.drag_handle == "bl":  # Bottom-left
                x1, y2 = x, y
            elif self.drag_handle == "br":  # Bottom-right
                x2, y2 = x, y
                
            # Apply aspect ratio if set
            if self.settings["aspect_ratio"]:
                aspect_w, aspect_h = self.settings["aspect_ratio"]
                desired_ratio = aspect_w / aspect_h
                
                # Calculate current dimensions
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                
                if self.drag_handle in ["tr", "br"]:
                    # Adjust height based on width
                    if width > 0:
                        height = width / desired_ratio
                        if self.drag_handle == "tr":
                            y1 = y2 - height if y2 > y1 else y2 + height
                        else:
                            y2 = y1 + height if y2 > y1 else y1 - height
                else:
                    # Adjust width based on height
                    if height > 0:
                        width = height * desired_ratio
                        if self.drag_handle == "tl":
                            x1 = x2 - width if x2 > x1 else x2 + width
                        else:
                            x1 = x2 - width if x2 > x1 else x2 + width
        else:
            # Move the crop rectangle
            if self.drag_start:
                dx = x - self.drag_start[0]
                dy = y - self.drag_start[1]
                
                x1 += dx
                y1 += dy
                x2 += dx
                y2 += dy
                
                self.drag_start = (x, y)
        
        self.crop_rect = (x1, y1, x2, y2)
        self._update_crop_ui()
    
    def on_mouse_move(self, event):
        """Handle mouse movement."""
        if not self.active or self.is_dragging:
            return
        
        canvas = self.app_state.get_active_canvas()
        if not canvas or not self.crop_rect:
            return
        
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        
        # Check if mouse is over a handle and update cursor
        handle = self._get_handle_at_position(x, y)
        if handle:
            if handle in ["tl", "br"]:
                canvas.config(cursor="nwse-resize")
            else:
                canvas.config(cursor="nesw-resize")
        elif self._point_in_rect(x, y, self.crop_rect):
            canvas.config(cursor="move")
        else:
            canvas.config(cursor="crosshair")
    
    def apply_crop(self):
        """Apply the crop to the current image."""
        if not self.crop_rect:
            logger.warning("No crop area defined")
            return
        
        # Get the current image
        current_layer = self.app_state.get_active_layer()
        if not current_layer:
            logger.warning("No active layer to crop")
            return
        
        # Get the original image
        original_image = current_layer.get_image()
        if original_image is None:
            logger.warning("No image data in active layer")
            return
        
        # Convert canvas coordinates to image coordinates
        canvas = self.app_state.get_active_canvas()
        if not canvas:
            return
        
        # Get the crop rectangle in screen coordinates
        x1, y1, x2, y2 = self.crop_rect
        
        # Ensure correct ordering
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Convert canvas coordinates to image coordinates
        scale = self.app_state.view_scale
        offset_x, offset_y = self.app_state.view_offset
        
        # Convert to image coordinates
        img_x1 = int((x1 - offset_x) / scale)
        img_y1 = int((y1 - offset_y) / scale)
        img_x2 = int((x2 - offset_x) / scale)
        img_y2 = int((y2 - offset_y) / scale)
        
        # Ensure coordinates are within image bounds
        img_width, img_height = original_image.size
        img_x1 = max(0, min(img_x1, img_width))
        img_y1 = max(0, min(img_y1, img_height))
        img_x2 = max(0, min(img_x2, img_width))
        img_y2 = max(0, min(img_y2, img_height))
        
        # Crop the image
        try:
            # Handle both PIL Image and numpy array
            if isinstance(original_image, np.ndarray):
                # For numpy array
                cropped_image = original_image[img_y1:img_y2, img_x1:img_x2]
                # Convert back to PIL
                cropped_image = Image.fromarray(cropped_image)
            else:
                # For PIL Image
                cropped_image = original_image.crop((img_x1, img_y1, img_x2, img_y2))
            
            # Update the layer with the cropped image
            current_layer.set_image(cropped_image)
            
            # Update the document size if this is the background layer
            if current_layer.is_background:
                self.app_state.resize_document(cropped_image.width, cropped_image.height)
            
            # Clear the crop UI
            self._remove_crop_ui()
            self.crop_rect = None
            
            # Refresh the view
            self.app_state.refresh_view()
            
            logger.info(f"Applied crop: {img_x1},{img_y1} to {img_x2},{img_y2}")
            
        except Exception as e:
            logger.error(f"Error applying crop: {str(e)}")
    
    def _update_crop_ui(self):
        """Update the crop rectangle and handles on the canvas."""
        if not self.crop_rect:
            return
        
        canvas = self.app_state.get_active_canvas()
        if not canvas:
            return
        
        x1, y1, x2, y2 = self.crop_rect
        
        # Ensure correct ordering for display
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Remove existing UI elements
        self._remove_crop_ui()
        
        # Draw the crop rectangle
        self.canvas_elements["rectangle"] = canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="white",
            width=2,
            dash=(5, 5)
        )
        
        # Draw handles at the corners
        handle_size = self.handle_size
        handles = {
            "tl": (x1, y1),  # Top-left
            "tr": (x2, y1),  # Top-right
            "bl": (x1, y2),  # Bottom-left
            "br": (x2, y2)   # Bottom-right
        }
        
        for handle_name, (hx, hy) in handles.items():
            handle_id = canvas.create_rectangle(
                hx - handle_size/2, hy - handle_size/2,
                hx + handle_size/2, hy + handle_size/2,
                fill="white",
                outline="black",
                width=1
            )
            self.canvas_elements["handles"][handle_name] = handle_id
        
        # Draw guides if enabled
        if self.settings["show_guides"]:
            # Rule of thirds guides
            third_x1 = x1 + (x2 - x1) / 3
            third_x2 = x1 + 2 * (x2 - x1) / 3
            third_y1 = y1 + (y2 - y1) / 3
            third_y2 = y1 + 2 * (y2 - y1) / 3
            
            # Vertical guides
            self.canvas_elements["guides"].append(
                canvas.create_line(third_x1, y1, third_x1, y2, fill="white", dash=(2, 2))
            )
            self.canvas_elements["guides"].append(
                canvas.create_line(third_x2, y1, third_x2, y2, fill="white", dash=(2, 2))
            )
            
            # Horizontal guides
            self.canvas_elements["guides"].append(
                canvas.create_line(x1, third_y1, x2, third_y1, fill="white", dash=(2, 2))
            )
            self.canvas_elements["guides"].append(
                canvas.create_line(x1, third_y2, x2, third_y2, fill="white", dash=(2, 2))
            )
        
        # Show dimensions if enabled
        if self.settings["show_dimensions"]:
            # Convert to image coordinates for accurate dimensions
            scale = self.app_state.view_scale
            offset_x, offset_y = self.app_state.view_offset
            
            img_x1 = int((x1 - offset_x) / scale)
            img_y1 = int((y1 - offset_y) / scale)
            img_x2 = int((x2 - offset_x) / scale)
            img_y2 = int((y2 - offset_y) / scale)
            
            width = abs(img_x2 - img_x1)
            height = abs(img_y2 - img_y1)
            
            dimension_text = f"{width} x {height}px"
            self.canvas_elements["dimension_text"] = canvas.create_text(
                (x1 + x2) / 2, y1 - 10,
                text=dimension_text,
                fill="white",
                font=("Arial", 10),
                anchor=tk.S
            )
    
    def _remove_crop_ui(self):
        """Remove all crop-related UI elements."""
        canvas = self.app_state.get_active_canvas()
        if not canvas:
            return
        
        # Remove rectangle
        if self.canvas_elements["rectangle"]:
            canvas.delete(self.canvas_elements["rectangle"])
            self.canvas_elements["rectangle"] = None
        
        # Remove handles
        for handle_id in self.canvas_elements["handles"].values():
            canvas.delete(handle_id)
        self.canvas_elements["handles"] = {}
        
        # Remove guides
        for guide_id in self.canvas_elements["guides"]:
            canvas.delete(guide_id)
        self.canvas_elements["guides"] = []
        
        # Remove dimension text
        if self.canvas_elements["dimension_text"]:
            canvas.delete(self.canvas_elements["dimension_text"])
            self.canvas_elements["dimension_text"] = None
    
    def _get_handle_at_position(self, x, y):
        """Return the handle name if position is over a handle, None otherwise."""
        if not self.crop_rect:
            return None
            
        x1, y1, x2, y2 = self.crop_rect
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        handle_size = self.handle_size
        handles = {
            "tl": (x1, y1),  # Top-left
            "tr": (x2, y1),  # Top-right
            "bl": (x1, y2),  # Bottom-left
            "br": (x2, y2)   # Bottom-right
        }
        
        for handle_name, (hx, hy) in handles.items():
            if (abs(x - hx) <= handle_size/2 and 
                abs(y - hy) <= handle_size/2):
                return handle_name
                
        return None
    
    def _point_in_rect(self, x, y, rect):
        """Check if point (x,y) is inside rectangle rect."""
        x1, y1, x2, y2 = rect
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        return (x1 < x < x2) and (y1 < y < y2)
    
    def set_aspect_ratio(self, width: int, height: int):
        """Set the aspect ratio constraint for the crop."""
        if width <= 0 or height <= 0:
            self.settings["aspect_ratio"] = None
        else:
            self.settings["aspect_ratio"] = (width, height)
            
        # Update UI if there's an active crop
        if self.crop_rect:
            self._update_crop_ui()
            
    def reset(self):
        """Reset the crop tool to its initial state."""
        self._remove_crop_ui()
        self.crop_rect = None
        self.drag_start = None
        self.is_dragging = False
        self.drag_handle = None 