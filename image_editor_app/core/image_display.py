"""
Image display and canvas management functions
"""
from PIL import ImageTk, Image
import tkinter as tk
import math
from image_editor_app.utils.constants import MAX_PREVIEW_WIDTH, MAX_PREVIEW_HEIGHT

def display_image(self, img=None, update_canvas=True, reset_zoom=False):
    """Display an image on the canvas"""
    if img is None:
        # If no image provided, use current image
        if self.current_image is None:
            return
        img = self.current_image
    
    try:
        # Store image dimensions
        width, height = img.size
        
        # Update info label
        if hasattr(self, 'image_info_label'):
            self.image_info_label.configure(text=f"{width}×{height} px")
        
        if update_canvas:
            # Clear canvas
            self.canvas.delete("all")
            
            # Resize if needed for display
            display_image = img
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # If canvas is not initialized yet, use parent frame size
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = self.canvas_frame.winfo_width()
                canvas_height = self.canvas_frame.winfo_height()
            
            # If still not initialized, use default size
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600
            
            # Calculate how to fit image in canvas
            if reset_zoom or not hasattr(self, 'scale_factor') or self.scale_factor == 1.0:
                # Calculate scale to fit image within canvas
                scale_x = canvas_width / width if width > canvas_width else 1.0
                scale_y = canvas_height / height if height > canvas_height else 1.0
                scale = min(scale_x, scale_y)
                
                if scale < 1.0:
                    # Resize image for better performance
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    display_image = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Update scale factor for zoom
                    self.scale_factor = scale
                else:
                    self.scale_factor = 1.0
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(display_image)
            
            # Store reference to avoid garbage collection
            self._photo_image = photo
            
            # Display on canvas
            x = canvas_width // 2
            y = canvas_height // 2
            self.canvas_image_item = self.canvas.create_image(x, y, image=photo, anchor=tk.CENTER)
            
            # Bind canvas resize event
            self.canvas.bind("<Configure>", self.update_canvas_size)
    
    except Exception as e:
        self.show_status(f"Görüntü gösterme hatası: {str(e)}")

def update_canvas_size(self, event=None):
    """Update canvas and image when window is resized"""
    if not self.current_image or not self.canvas_image_item:
        return
    
    # Get the current image position
    if hasattr(self, 'canvas_image_item') and self.canvas_image_item:
        try:
            # Get current image coordinates
            x1, y1, x2, y2 = self.canvas.coords(self.canvas_image_item)
            current_width = x2 - x1
            current_height = y2 - y1
            
            # Get new canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Center image if canvas is larger than image
            if canvas_width > current_width:
                x_center = canvas_width // 2
                x_offset = x_center - (x1 + x2) // 2
                self.canvas.move(self.canvas_image_item, x_offset, 0)
            
            if canvas_height > current_height:
                y_center = canvas_height // 2
                y_offset = y_center - (y1 + y2) // 2
                self.canvas.move(self.canvas_image_item, 0, y_offset)
        
        except Exception as e:
            self.show_status(f"Canvas güncelleme hatası: {str(e)}")

def start_pan(self, event):
    """Start panning the image"""
    self.pan_start_x = event.x
    self.pan_start_y = event.y

def pan_image(self, event):
    """Pan the image by dragging"""
    if self.canvas_image_item:
        # Calculate how much we've moved
        delta_x = event.x - self.pan_start_x
        delta_y = event.y - self.pan_start_y
        
        # Move the image
        self.canvas.move(self.canvas_image_item, delta_x, delta_y)
        
        # Update the starting position for the next drag
        self.pan_start_x = event.x
        self.pan_start_y = event.y

def zoom_image(self, event):
    """Zoom the image using mouse wheel"""
    if not self.current_image or not self.canvas_image_item:
        return
    
    # Determine zoom direction
    if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
        # Zoom in
        factor = 1.1
    elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
        # Zoom out
        factor = 0.9
    else:
        return
    
    # Update scale factor
    self.scale_factor *= factor
    
    # Get current dimensions
    canvas_width = self.canvas.winfo_width()
    canvas_height = self.canvas.winfo_height()
    
    # Get mouse position relative to canvas
    x = self.canvas.canvasx(event.x)
    y = self.canvas.canvasy(event.y)
    
    # Get image position and dimensions
    x1, y1, x2, y2 = self.canvas.coords(self.canvas_image_item)
    width = x2 - x1
    height = y2 - y1
    
    # Calculate new dimensions
    new_width = width * factor
    new_height = height * factor
    
    # Calculate new coordinates to zoom toward mouse
    new_x1 = x - (x - x1) * factor
    new_y1 = y - (y - y1) * factor
    new_x2 = new_x1 + new_width
    new_y2 = new_y1 + new_height
    
    # Update image
    self.canvas.coords(self.canvas_image_item, new_x1, new_y1, new_x2, new_y2) 