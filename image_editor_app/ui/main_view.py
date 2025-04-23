"""
Main view UI components for displaying and manipulating images
"""
import customtkinter as ctk
from PIL import ImageTk
from image_editor_app.utils.constants import *

def create_main_view(self):
    """Create the main content area with canvas"""
    # Main content container with border
    self.content_frame = ctk.CTkFrame(self, corner_radius=0)
    self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
    
    # Configure content frame for dynamic sizing
    self.content_frame.grid_rowconfigure(0, weight=1)
    self.content_frame.grid_columnconfigure(0, weight=1)
    
    # Create canvas for image display
    self.canvas_frame = ctk.CTkFrame(self.content_frame)
    self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    self.canvas_frame.grid_rowconfigure(0, weight=1)
    self.canvas_frame.grid_columnconfigure(0, weight=1)
    
    # ThemeManager ile direkt renk alma sorunu yaşandığı için sabit bir koyu renk kullanıyoruz
    # Bu renk customtkinter koyu temaya uygun
    canvas_bg = "#242424"
    
    self.canvas = ctk.CTkCanvas(
        self.canvas_frame,
        bg=canvas_bg,
        highlightthickness=0
    )
    self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    
    # Scaling variables
    self.scale_factor = 1.0
    self.pan_start_x = 0
    self.pan_start_y = 0
    self.canvas_image_item = None
    
    # Bind mouse events for interaction
    self.canvas.bind("<ButtonPress-1>", self.start_pan)
    self.canvas.bind("<B1-Motion>", self.pan_image)
    self.canvas.bind("<MouseWheel>", self.zoom_image)  # Windows
    self.canvas.bind("<Button-4>", self.zoom_image)  # Linux scroll up
    self.canvas.bind("<Button-5>", self.zoom_image)  # Linux scroll down

def create_status_bar(self):
    """Create status bar at the bottom of the main view"""
    # Status bar
    self.status_bar = ctk.CTkFrame(self.content_frame, height=30, corner_radius=0)
    self.status_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 0))
    
    # Prevent automatic resizing of height
    self.status_bar.grid_propagate(False)
    
    # Status text
    self.status_label = ctk.CTkLabel(
        self.status_bar, 
        text="Hazır", 
        anchor="w",
        font=SMALL_FONT
    )
    self.status_label.grid(row=0, column=0, padx=10, pady=0, sticky="w")
    
    # Configure status bar grid
    self.status_bar.grid_columnconfigure(0, weight=1)
    
    # Image info display (right side)
    self.image_info_label = ctk.CTkLabel(
        self.status_bar, 
        text="", 
        font=SMALL_FONT
    )
    self.image_info_label.grid(row=0, column=1, padx=10, pady=0, sticky="e") 