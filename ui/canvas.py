"""
Canvas Module
Provides the main editing canvas for the application.
"""

import tkinter as tk
import logging
from typing import Optional, Tuple, Callable, Any

import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk

from core.app_state import AppState

logger = logging.getLogger("Image_Editor.Canvas")

class EditCanvas(tk.Canvas):
    """
    Custom canvas for image editing.
    Extends tk.Canvas to provide image display, zooming, panning, and tool interactions.
    """
    
    def __init__(self, parent, app_state: AppState, **kwargs):
        """
        Initialize the edit canvas.
        
        Args:
            parent: Parent widget
            app_state: Application state
            **kwargs: Additional arguments for the canvas
        """
        # Default background color
        bg_color = kwargs.pop('bg', '#1A1A1A')
        
        # Initialize the base canvas
        super().__init__(parent, bg=bg_color, **kwargs)
        
        # Store references
        self.app_state = app_state
        self.parent = parent
        
        # Canvas state
        self.image = None  # Original image data
        self.tk_image = None  # Tkinter PhotoImage for display
        self.image_id = None  # Canvas item ID for the image
        self.zoom = 1.0  # Current zoom level
        self.offset_x = 0  # Horizontal offset for panning
        self.offset_y = 0  # Vertical offset for panning
        
        # Mouse state
        self.dragging = False
        self.last_x = 0
        self.last_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Tool state
        self.active_tool = None
        self.tool_overlay_id = None  # Canvas item ID for tool overlay
        
        # Set up mouse bindings
        self.bind("<ButtonPress-1>", self.on_mouse_down)
        self.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        
        # Set up keyboard bindings
        self.bind("<space>", self.on_space_press)
        self.bind("<KeyRelease-space>", self.on_space_release)
        
        # Right-click context menu
        self.bind("<ButtonPress-3>", self.on_right_click)
        
        # Window resize handling
        self.bind("<Configure>", self.on_resize)
        
        # Space key for temporary pan mode
        self.space_pressed = False
        self.previous_tool = None
        
        # Background grid for transparent images
        self.grid_size = 16
        self.create_background_grid()
        
        logger.info("EditCanvas initialized")
    
    def create_background_grid(self):
        """Create a checkerboard pattern to display transparent areas."""
        # Create a pattern image
        pattern_size = self.grid_size * 2
        pattern = Image.new('RGBA', (pattern_size, pattern_size), (0, 0, 0, 0))
        
        # Draw the pattern
        for y in range(0, pattern_size, self.grid_size):
            for x in range(0, pattern_size, self.grid_size):
                # Alternate light and dark squares
                color = "#AAAAAA" if (x // self.grid_size + y // self.grid_size) % 2 == 0 else "#666666"
                box = (x, y, x + self.grid_size, y + self.grid_size)
                
                # Draw rectangle
                pattern_draw = Image.new('RGBA', (self.grid_size, self.grid_size), color)
                pattern.paste(pattern_draw, (x, y))
        
        # Convert to PhotoImage
        self.pattern_image = ImageTk.PhotoImage(pattern)
        
        # Create pattern on canvas
        self.bg_pattern_id = self.create_rectangle(
            0, 0, self.winfo_width(), self.winfo_height(),
            fill="", outline="", stipple="gray50", tags="bg_pattern"
        )
        
        # Create pattern on canvas using an image
        # self.bg_pattern_id = self.create_image(
        #     0, 0, image=self.pattern_image, anchor=tk.NW, tags="bg_pattern"
        # )
        
        # Send to back
        self.lower(self.bg_pattern_id)
    
    def update_background_grid(self):
        """Update the background grid size and position."""
        # Update size of the background rectangle
        self.coords(
            self.bg_pattern_id,
            0, 0, self.winfo_width(), self.winfo_height()
        )
    
    def set_image(self, image_data: np.ndarray):
        """
        Set the image to display on the canvas.
        
        Args:
            image_data: NumPy array containing the image data
        """
        if image_data is None:
            logger.warning("Attempted to set None as image data")
            return
        
        # Store the original image data
        self.image = image_data
        
        # Convert image for display
        self.update_display()
        
        # Reset view
        self.zoom = 1.0
        self.center_image()
        
        # Update scrollregion
        self.update_scroll_region()
        
        logger.info(f"Set image on canvas, shape: {image_data.shape}")
    
    def update_display(self):
        """Update the displayed image based on current zoom and state."""
        if self.image is None:
            return
        
        # Convert NumPy array to PIL Image
        if self.image.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(self.image, 'RGBA')
        else:  # RGB
            pil_image = Image.fromarray(self.image, 'RGB')
        
        # Apply zoom
        if self.zoom != 1.0:
            new_width = int(pil_image.width * self.zoom)
            new_height = int(pil_image.height * self.zoom)
            
            # Ensure minimum size
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            
            # Resize the image
            pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to Tkinter PhotoImage
        self.tk_image = ImageTk.PhotoImage(pil_image)
        
        # Update or create image on canvas
        if self.image_id is not None:
            self.itemconfig(self.image_id, image=self.tk_image)
            self.coords(self.image_id, self.offset_x, self.offset_y)
        else:
            self.image_id = self.create_image(
                self.offset_x, self.offset_y,
                image=self.tk_image, anchor=tk.NW, tags="image"
            )
    
    def set_zoom(self, zoom_level: float):
        """
        Set the zoom level for the image.
        
        Args:
            zoom_level: New zoom level (as a float, e.g., 1.0 = 100%)
        """
        # Ensure zoom level is within reasonable bounds
        zoom_level = max(0.01, min(32.0, zoom_level))
        
        # Store center point before zoom change
        if self.image is not None:
            canvas_center_x = self.winfo_width() / 2
            canvas_center_y = self.winfo_height() / 2
            
            # Convert center point to image coordinates
            image_x = (canvas_center_x - self.offset_x) / self.zoom
            image_y = (canvas_center_y - self.offset_y) / self.zoom
            
            # Update zoom level
            self.zoom = zoom_level
            
            # Calculate new offset to keep the center point at the same image position
            self.offset_x = canvas_center_x - (image_x * self.zoom)
            self.offset_y = canvas_center_y - (image_y * self.zoom)
            
            # Update display
            self.update_display()
            self.update_scroll_region()
            
            logger.info(f"Set zoom level to {zoom_level:.2f}")
    
    def zoom_in(self, factor: float = 1.25):
        """
        Zoom in by the specified factor.
        
        Args:
            factor: Zoom factor (e.g., 1.25 = zoom in by 25%)
        """
        new_zoom = self.zoom * factor
        self.set_zoom(new_zoom)
    
    def zoom_out(self, factor: float = 1.25):
        """
        Zoom out by the specified factor.
        
        Args:
            factor: Zoom factor (e.g., 1.25 = zoom out by 25%)
        """
        new_zoom = self.zoom / factor
        self.set_zoom(new_zoom)
    
    def zoom_to_fit(self):
        """Zoom to fit the image in the visible canvas area."""
        if self.image is None:
            return
        
        # Get canvas dimensions
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        # Get image dimensions
        image_width, image_height = self.image.shape[1], self.image.shape[0]
        
        # Calculate scaling factors
        scale_x = canvas_width / image_width
        scale_y = canvas_height / image_height
        
        # Use the smaller scaling factor to fit the image
        zoom = min(scale_x, scale_y) * 0.9  # 90% of fit to leave some margin
        
        # Set zoom and center the image
        self.set_zoom(zoom)
        self.center_image()
        
        logger.info(f"Zoomed to fit: {zoom:.2f}")
    
    def center_image(self):
        """Center the image in the canvas."""
        if self.image is None:
            return
        
        # Get canvas dimensions
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        # Get zoomed image dimensions
        image_width = int(self.image.shape[1] * self.zoom)
        image_height = int(self.image.shape[0] * self.zoom)
        
        # Calculate offsets to center the image
        self.offset_x = max(0, (canvas_width - image_width) // 2)
        self.offset_y = max(0, (canvas_height - image_height) // 2)
        
        # Update image position
        if self.image_id is not None:
            self.coords(self.image_id, self.offset_x, self.offset_y)
            
        # Update scroll region
        self.update_scroll_region()
    
    def update_scroll_region(self):
        """Update the canvas scroll region based on the image size and position."""
        if self.image is None:
            return
        
        # Calculate the bounds
        image_width = int(self.image.shape[1] * self.zoom)
        image_height = int(self.image.shape[0] * self.zoom)
        
        # Set scroll region to cover the image plus some padding
        padding = 100
        self.configure(
            scrollregion=(
                -padding,
                -padding,
                max(self.winfo_width(), self.offset_x + image_width) + padding,
                max(self.winfo_height(), self.offset_y + image_height) + padding
            )
        )
    
    def screen_to_image_coords(self, x: int, y: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to image coordinates.
        
        Args:
            x: X-coordinate in screen space
            y: Y-coordinate in screen space
            
        Returns:
            Tuple of (x, y) coordinates in image space
        """
        if self.image is None:
            return (0, 0)
        
        # Adjust for canvas scrolling
        x = self.canvasx(x)
        y = self.canvasy(y)
        
        # Convert to image coordinates
        image_x = int((x - self.offset_x) / self.zoom)
        image_y = int((y - self.offset_y) / self.zoom)
        
        # Ensure coordinates are within image bounds
        image_width = self.image.shape[1]
        image_height = self.image.shape[0]
        
        image_x = max(0, min(image_width - 1, image_x))
        image_y = max(0, min(image_height - 1, image_y))
        
        return (image_x, image_y)
    
    def image_to_screen_coords(self, x: int, y: int) -> Tuple[int, int]:
        """
        Convert image coordinates to screen coordinates.
        
        Args:
            x: X-coordinate in image space
            y: Y-coordinate in image space
            
        Returns:
            Tuple of (x, y) coordinates in screen space
        """
        if self.image is None:
            return (0, 0)
        
        # Convert to screen coordinates
        screen_x = self.offset_x + (x * self.zoom)
        screen_y = self.offset_y + (y * self.zoom)
        
        return (int(screen_x), int(screen_y))
    
    def on_mouse_down(self, event):
        """Handle mouse button press event."""
        # Store initial click position
        self.dragging = True
        self.last_x = self.canvasx(event.x)
        self.last_y = self.canvasy(event.y)
        self.drag_start_x = self.last_x
        self.drag_start_y = self.last_y
        
        # Convert to image coordinates
        image_x, image_y = self.screen_to_image_coords(event.x, event.y)
        
        # If space is pressed, we're in pan mode
        if self.space_pressed:
            # Pan mode
            self.config(cursor="fleur")
        else:
            # Normal mode - delegate to active tool
            if self.active_tool:
                self.active_tool.on_mouse_down(image_x, image_y, event)
    
    def on_mouse_up(self, event):
        """Handle mouse button release event."""
        self.dragging = False
        
        # Convert to image coordinates
        image_x, image_y = self.screen_to_image_coords(event.x, event.y)
        
        # If space is pressed, we're in pan mode
        if self.space_pressed:
            # Pan mode
            self.config(cursor="fleur")
        else:
            # Normal mode - delegate to active tool
            if self.active_tool:
                self.active_tool.on_mouse_up(image_x, image_y, event)
    
    def on_mouse_drag(self, event):
        """Handle mouse drag event."""
        if not self.dragging:
            return
        
        # Get current mouse position
        current_x = self.canvasx(event.x)
        current_y = self.canvasy(event.y)
        
        # Calculate movement delta
        delta_x = current_x - self.last_x
        delta_y = current_y - self.last_y
        
        # If space is pressed or middle mouse button, we're in pan mode
        if self.space_pressed or event.state & 0x0200:  # Check for middle mouse button
            # Pan the image
            self.offset_x += delta_x
            self.offset_y += delta_y
            
            # Update image position
            if self.image_id is not None:
                self.coords(self.image_id, self.offset_x, self.offset_y)
            
            # Update scroll region
            self.update_scroll_region()
        else:
            # Normal mode - delegate to active tool
            if self.active_tool:
                # Convert to image coordinates
                image_x, image_y = self.screen_to_image_coords(event.x, event.y)
                self.active_tool.on_mouse_drag(image_x, image_y, event)
        
        # Update last position
        self.last_x = current_x
        self.last_y = current_y
    
    def on_mouse_move(self, event):
        """Handle mouse movement event (without dragging)."""
        # Convert to image coordinates
        image_x, image_y = self.screen_to_image_coords(event.x, event.y)
        
        # Update cursor position in parent's status bar
        if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'update_cursor_position'):
            self.parent.master.update_cursor_position(image_x, image_y)
        
        # If space is pressed, we're in pan mode
        if self.space_pressed:
            # Pan mode
            self.config(cursor="fleur")
        else:
            # Normal mode - delegate to active tool
            if self.active_tool:
                cursor = self.active_tool.get_cursor()
                if cursor:
                    self.config(cursor=cursor)
                
                self.active_tool.on_mouse_move(image_x, image_y, event)
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel event for zooming."""
        # Determine the direction and amount to zoom
        if event.num == 4 or event.delta > 0:  # Scroll up
            factor = 1.1
        elif event.num == 5 or event.delta < 0:  # Scroll down
            factor = 0.9
        else:
            return
        
        # Get the mouse position
        mouse_x = self.canvasx(event.x)
        mouse_y = self.canvasy(event.y)
        
        # Convert mouse position to image coordinates before zoom
        img_x = (mouse_x - self.offset_x) / self.zoom
        img_y = (mouse_y - self.offset_y) / self.zoom
        
        # Update zoom level
        new_zoom = self.zoom * factor
        new_zoom = max(0.01, min(32.0, new_zoom))
        self.zoom = new_zoom
        
        # Update offsets to keep mouse position over the same image point
        self.offset_x = mouse_x - (img_x * self.zoom)
        self.offset_y = mouse_y - (img_y * self.zoom)
        
        # Update display
        self.update_display()
        self.update_scroll_region()
        
        # Update zoom label in the parent's status bar
        if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'set_zoom_level'):
            self.parent.master.set_zoom_level(self.zoom)
    
    def on_space_press(self, event):
        """Handle space key press for temporary pan mode."""
        if not self.space_pressed:
            self.space_pressed = True
            
            # Store the current tool
            self.previous_tool = self.active_tool
            
            # Set cursor for pan mode
            self.config(cursor="fleur")
    
    def on_space_release(self, event):
        """Handle space key release to exit temporary pan mode."""
        if self.space_pressed:
            self.space_pressed = False
            
            # Restore the previous tool
            self.active_tool = self.previous_tool
            
            # Reset cursor
            if self.active_tool:
                cursor = self.active_tool.get_cursor()
                if cursor:
                    self.config(cursor=cursor)
                else:
                    self.config(cursor="")
            else:
                self.config(cursor="")
    
    def on_right_click(self, event):
        """Handle right-click for context menu."""
        # TODO: Implement context menu
        pass
    
    def on_resize(self, event):
        """Handle canvas resize event."""
        self.update_background_grid()
        self.update_scroll_region()
    
    def set_tool(self, tool):
        """
        Set the active tool for the canvas.
        
        Args:
            tool: Tool instance to activate
        """
        # Deactivate current tool if exists
        if self.active_tool:
            self.active_tool.deactivate()
        
        # Set new tool
        self.active_tool = tool
        
        # Activate new tool
        if tool:
            tool.activate(self)
            
            # Set cursor
            cursor = tool.get_cursor()
            if cursor:
                self.config(cursor=cursor)
            else:
                self.config(cursor="")
        else:
            self.config(cursor="") 