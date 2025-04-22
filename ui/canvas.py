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
        
        # Store reference to main window (will be set by the MainWindow)
        self.main_window = None
        
        # Canvas state
        self.image = None  # Original image data
        self.tk_image = None  # Tkinter PhotoImage for display
        self.image_id = None  # Canvas item ID for the image
        
        # Register this canvas with the app_state
        self.app_state.active_canvas = self
        
        # Initialize view state in app_state
        self.app_state.view_scale = 1.0  # Current zoom level
        self.app_state.view_offset = (0, 0)  # (x, y) offset for panning
        
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
        
        # If the MainWindow has a callback for canvas ready, call it
        if hasattr(parent, 'main_window') and hasattr(parent.main_window, 'on_canvas_ready'):
            parent.main_window.on_canvas_ready(self)
            
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
        self.app_state.view_scale = 1.0
        self.center_image()
        
        # Update scrollregion
        self.update_scroll_region()
        
        logger.info(f"Set image on canvas, shape: {image_data.shape}")
    
    def update_display(self):
        """Update the displayed image based on current zoom and state."""
        if self.image is None:
            return
        
        # Performance optimization: Cache resized images at different zoom levels
        current_scale = self.app_state.view_scale
        
        # Use cached image if available (for common zoom levels)
        cached_scale = getattr(self, '_cached_scale', None)
        cached_image = getattr(self, '_cached_image', None)
        
        # Check if we can use the cached image
        if cached_scale == current_scale and cached_image is not None:
            self.tk_image = cached_image
            
            # Update or create image on canvas
            offset_x, offset_y = self.app_state.view_offset
            if self.image_id is not None:
                self.coords(self.image_id, offset_x, offset_y)
            else:
                self.image_id = self.create_image(
                    offset_x, offset_y, image=self.tk_image, anchor=tk.NW
                )
            return
        
        # Convert NumPy array to PIL Image
        if self.image.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(self.image, 'RGBA')
        else:  # RGB
            pil_image = Image.fromarray(self.image, 'RGB')
        
        # Apply zoom
        if current_scale != 1.0:
            new_width = int(pil_image.width * current_scale)
            new_height = int(pil_image.height * current_scale)
            
            # Ensure minimum size
            new_width = max(1, new_width)
            new_height = max(1, new_height)
            
            # Performance optimization: Use faster resize for smaller scales
            if current_scale < 0.25:
                # For very low zoom levels, use fastest but lowest quality resize
                resample = Image.NEAREST
            elif current_scale < 0.5:
                # For low zoom levels, use faster but lower quality resize
                resample = Image.NEAREST
            elif current_scale < 1.0:
                # For medium zoom out, use bilinear
                resample = Image.BILINEAR
            else:
                # For zoom in, use higher quality
                resample = Image.LANCZOS
                
            # Resize the image
            pil_image = pil_image.resize((new_width, new_height), resample)
        
        # Convert to Tkinter PhotoImage
        self.tk_image = ImageTk.PhotoImage(pil_image)
        
        # Cache for future use (only cache common zoom levels to save memory)
        common_zoom_levels = [0.25, 0.5, 1.0, 1.5, 2.0]
        if any(abs(current_scale - level) < 0.01 for level in common_zoom_levels):
            # Clear previous cache if needed to prevent memory leaks
            if hasattr(self, '_cached_image'):
                self._cached_image = None
                
            self._cached_scale = current_scale
            self._cached_image = self.tk_image
        
        # Update or create image on canvas
        offset_x, offset_y = self.app_state.view_offset
        if self.image_id is not None:
            self.itemconfig(self.image_id, image=self.tk_image)
            self.coords(self.image_id, offset_x, offset_y)
        else:
            self.image_id = self.create_image(
                offset_x, offset_y, image=self.tk_image, anchor=tk.NW
            )
    
    def set_zoom(self, zoom_level: float):
        """
        Set the canvas zoom level.
        
        Args:
            zoom_level: Zoom level to set (1.0 = 100%)
        """
        # Limit minimum and maximum zoom
        zoom_level = max(0.05, min(10.0, zoom_level))
        
        # Avoid redundant updates for very similar zoom levels
        if abs(self.app_state.view_scale - zoom_level) < 0.001:
            return
            
        # Get center of view
        view_width = self.winfo_width()
        view_height = self.winfo_height()
        center_x = view_width / 2
        center_y = view_height / 2
        
        # Convert center to image coordinates before zoom
        old_scale = self.app_state.view_scale
        old_offset_x, old_offset_y = self.app_state.view_offset
        
        if self.image is not None:
            # Calculate the image coordinates of the center point
            img_center_x = (center_x - old_offset_x) / old_scale
            img_center_y = (center_y - old_offset_y) / old_scale
            
            # Calculate new offsets to keep the center point fixed
            new_offset_x = center_x - img_center_x * zoom_level
            new_offset_y = center_y - img_center_y * zoom_level
            
            # Set new scale and offset
            self.app_state.view_scale = zoom_level
            self.app_state.view_offset = (new_offset_x, new_offset_y)
            
            # Update display
            self.update_display()
            
            # Update scroll region
            self.update_scroll_region()
            
            # Update zoom information in status bar
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.set_zoom_level(zoom_level)
    
    def zoom_in(self, factor: float = 1.25):
        """
        Zoom in by the specified factor.
        
        Args:
            factor: Zoom increase factor (e.g., 1.25 = 25% increase)
        """
        new_zoom = self.app_state.view_scale * factor
        self.set_zoom(new_zoom)
    
    def zoom_out(self, factor: float = 1.25):
        """
        Zoom out by the specified factor.
        
        Args:
            factor: Zoom decrease factor (e.g., 1.25 = 20% decrease)
        """
        new_zoom = self.app_state.view_scale / factor
        self.set_zoom(new_zoom)
    
    def zoom_to_fit(self):
        """Adjust zoom to fit the image in the visible area."""
        if self.image is None:
            return
        
        # Get image dimensions
        img_width, img_height = self.image.shape[1], self.image.shape[0]
        
        # Get canvas dimensions
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        # Calculate zoom level to fit
        zoom_x = canvas_width / img_width if img_width > 0 else 1.0
        zoom_y = canvas_height / img_height if img_height > 0 else 1.0
        
        # Use the smaller factor to ensure whole image fits
        zoom = min(zoom_x, zoom_y) * 0.95  # 5% margin
        
        # Set new zoom level
        self.app_state.view_scale = zoom
        
        # Center the image
        self.center_image()
        
        # Update display
        self.update_display()
        
        # Update scroll region
        self.update_scroll_region()
        
        # Update UI
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.set_zoom_level(self.app_state.view_scale)
        
        logger.debug(f"Zoomed to fit: {zoom:.2f}")
    
    def center_image(self):
        """Center the image in the canvas view."""
        if self.image is None:
            return
            
        # Get canvas size
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        # Get image size at current scale
        image_height, image_width = self.image.shape[:2]
        scaled_width = image_width * self.app_state.view_scale
        scaled_height = image_height * self.app_state.view_scale
        
        # Calculate offset to center
        offset_x = max(0, (canvas_width - scaled_width) / 2)
        offset_y = max(0, (canvas_height - scaled_height) / 2)
        
        # Set new offset
        self.app_state.view_offset = (offset_x, offset_y)
        
        # Update image position
        if self.image_id:
            self.coords(self.image_id, offset_x, offset_y)
            
        # Update scroll region
        self.update_scroll_region()
        
    def update_scroll_region(self):
        """Update the scroll region based on current image size and zoom."""
        if self.image is None:
            self.configure(scrollregion=(0, 0, 0, 0))
            return
            
        # Calculate scaled image dimensions
        image_height, image_width = self.image.shape[:2]
        scaled_width = image_width * self.app_state.view_scale
        scaled_height = image_height * self.app_state.view_scale
        
        # Get current offsets
        offset_x, offset_y = self.app_state.view_offset
        
        # Set scroll region to cover the entire image plus padding
        padding = 100  # Add padding around the image
        self.configure(
            scrollregion=(
                -padding + offset_x,
                -padding + offset_y,
                scaled_width + padding + offset_x,
                scaled_height + padding + offset_y
            )
        )
    
    def screen_to_image_coords(self, x: int, y: int) -> Tuple[int, int]:
        """
        Convert screen (canvas) coordinates to image coordinates.
        
        Args:
            x: X coordinate in screen space
            y: Y coordinate in screen space
            
        Returns:
            Tuple of (x, y) in image space
        """
        offset_x, offset_y = self.app_state.view_offset
        
        # Calculate image coordinates
        img_x = int((x - offset_x) / self.app_state.view_scale)
        img_y = int((y - offset_y) / self.app_state.view_scale)
        
        # Ensure coordinates are within bounds
        if self.image is not None:
            img_width, img_height = self.image.shape[1], self.image.shape[0]
            img_x = max(0, min(img_x, img_width - 1))
            img_y = max(0, min(img_y, img_height - 1))
        
        return img_x, img_y
    
    def image_to_screen_coords(self, x: int, y: int) -> Tuple[int, int]:
        """
        Convert image coordinates to screen (canvas) coordinates.
        
        Args:
            x: X coordinate in image space
            y: Y coordinate in image space
            
        Returns:
            Tuple of (x, y) in screen space
        """
        offset_x, offset_y = self.app_state.view_offset
        
        # Calculate screen coordinates
        screen_x = int(x * self.app_state.view_scale + offset_x)
        screen_y = int(y * self.app_state.view_scale + offset_y)
        
        return screen_x, screen_y
    
    def on_mouse_down(self, event):
        """
        Handle mouse button press.
        
        Args:
            event: Mouse event
        """
        # Store the initial position for potential dragging
        self.last_x = event.x
        self.last_y = event.y
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Handle tool interactions
        if self.space_pressed:
            # Space + click = pan mode
            self.dragging = True
            self.config(cursor="fleur")
        elif self.app_state.active_tool:
            # Let the active tool handle the event
            # The tool itself should handle the event from its event binding
            pass
        else:
            # Default behavior - start dragging the canvas
            self.dragging = True
            self.config(cursor="fleur")
    
    def on_mouse_up(self, event):
        """
        Handle mouse button release.
        
        Args:
            event: Mouse event
        """
        # Reset dragging state
        self.dragging = False
        
        # Reset cursor if we were in drag mode
        if self.space_pressed:
            self.config(cursor="fleur")
        elif not self.app_state.active_tool:
            self.config(cursor="")
    
    def on_mouse_drag(self, event):
        """
        Handle mouse drag.
        
        Args:
            event: Mouse event
        """
        # Calculate movement delta
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        
        # Handle based on current mode
        if self.dragging or self.space_pressed:
            # Pan the view
            offset_x, offset_y = self.app_state.view_offset
            new_offset_x = offset_x + dx
            new_offset_y = offset_y + dy
            
            # Update offset
            self.app_state.view_offset = (new_offset_x, new_offset_y)
            
            # Update image position
            if self.image_id:
                self.coords(self.image_id, new_offset_x, new_offset_y)
            
            # Update grid
            self.update_background_grid()
        elif self.app_state.active_tool:
            # Tool is handling the event through its own bindings
            pass
        
        # Update last position
        self.last_x = event.x
        self.last_y = event.y
    
    def on_mouse_move(self, event):
        """
        Handle mouse movement without dragging.
        
        Args:
            event: Mouse event
        """
        # Update cursor position in main window status bar
        if hasattr(self, 'main_window') and self.main_window:
            img_x, img_y = self.screen_to_image_coords(event.x, event.y)
            self.main_window.update_cursor_position(img_x, img_y)
        
        # Let tool handle mouse move if active
        if self.app_state.active_tool:
            # Tool is handling the event through its own bindings
            pass
    
    def on_mouse_wheel(self, event):
        """
        Handle mouse wheel events for zooming.
        
        Args:
            event: Mouse wheel event
        """
        # Determine zoom direction and delta
        delta = 0
        
        # Windows or macOS with Shift
        if event.num == 0:
            # Windows/macOS
            if event.delta > 0:
                delta = 1
            elif event.delta < 0:
                delta = -1
        # Linux
        elif event.num == 4:
            delta = 1
        elif event.num == 5:
            delta = -1
            
        if delta == 0:
            return
            
        # Calculate new zoom level
        zoom_factor = 1.2 if delta > 0 else 1/1.2
        new_zoom = self.app_state.view_scale * zoom_factor
        
        # Get mouse position
        mouse_x = event.x
        mouse_y = event.y
            
        # Convert mouse position to image coordinates before zoom
        old_scale = self.app_state.view_scale
        old_offset_x, old_offset_y = self.app_state.view_offset
        
        # Calculate the image coordinates under the mouse
        img_x = (mouse_x - old_offset_x) / old_scale
        img_y = (mouse_y - old_offset_y) / old_scale
        
        # Calculate new offsets to keep the mouse position fixed
        new_offset_x = mouse_x - img_x * new_zoom
        new_offset_y = mouse_y - img_y * new_zoom
        
        # Set new scale and offset
        self.app_state.view_scale = new_zoom
        self.app_state.view_offset = (new_offset_x, new_offset_y)
        
        # Update display
        self.update_display()
        
        # Update scroll region
        self.update_scroll_region()
        
        # Update zoom information in status bar
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.set_zoom_level(new_zoom)
    
    def on_space_press(self, event):
        """
        Handle space key press to enable pan mode.
        
        Args:
            event: Key event
        """
        if not self.space_pressed:
            self.space_pressed = True
            
            # Store previous tool for restoration later
            self.previous_tool = self.app_state.current_tool
            
            # Set cursor for pan mode
            self.config(cursor="fleur")
    
    def on_space_release(self, event):
        """
        Handle space key release to disable pan mode.
        
        Args:
            event: Key event
        """
        if self.space_pressed:
            self.space_pressed = False
            
            # Restore previous tool
            if self.previous_tool and self.previous_tool in self.app_state.tools:
                self.app_state.set_active_tool(self.previous_tool)
            else:
                # Reset cursor
                self.config(cursor="")
    
    def on_right_click(self, event):
        """
        Handle right-click for context menu.
        
        Args:
            event: Mouse event
        """
        # TODO: Implement context menu
        pass
    
    def on_resize(self, event):
        """
        Handle window resize events.
        
        Args:
            event: Configure event
        """
        self.update_background_grid()
        
    def set_main_window(self, main_window):
        """
        Set the reference to the main window.
        
        Args:
            main_window: Reference to the main window
        """
        self.main_window = main_window 