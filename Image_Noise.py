import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageChops, ImageDraw
from skimage import exposure, restoration, filters, util, color, segmentation, feature
from scipy import ndimage, signal
import customtkinter as ctk
from customtkinter import filedialog
import io
import logging
from typing import Dict, Optional, Tuple, List, Any, Union, Callable
import gc
from tkinter import messagebox, Canvas
import time
import threading
import os
import tkinter as tk
from PIL import ImageTk
import functools
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_editor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ImageEditor(ctk.CTkToplevel):
    """
    Advanced Image Editor application for applying various effects and filters to images.
    Supports multiple image formats and provides real-time preview of effects with
    optimized performance through threading and caching.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("Image_Noise")
        
        # Initialize image variables with type hints
        self.image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.display_photo: Optional[ctk.CTkImage] = None
        self.cached_images: Dict[str, Image.Image] = {}
        self.edit_history: List[Dict[str, float]] = []
        self.history_position: int = -1
        self.current_file_path: Optional[str] = None
        
        # Enhanced caching system with LRU (Least Recently Used) strategy
        self.cache_size_limit = 10  # Maximum number of cached images
        self.cache_memory_limit = 500 * 1024 * 1024  # 500 MB limit
        self.cache_hits = 0
        self.cache_misses = 0
        self.ordered_cache = OrderedDict()
        
        # For threading support
        self.processing_thread: Optional[threading.Thread] = None
        self.processing_lock = threading.Lock()
        self.is_processing = False
        
        # ThreadPool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=max(2, multiprocessing.cpu_count()-1))
        
        # Store parent window reference
        self.parent = args[0] if args else None
        
        # Define supported formats with proper MIME types
        self.supported_formats: Dict[str, str] = {
            "PNG": "*.png",
            "JPEG": "*.jpg *.jpeg *.jpe *.jfif",
            "BMP": "*.bmp",
            "GIF": "*.gif",
            "TIFF": "*.tiff *.tif",
            "WebP": "*.webp",
            "ICO": "*.ico",
            "PPM": "*.ppm",
            "PGM": "*.pgm",
            "HEIC": "*.heic",
            "SVG": "*.svg"
        }
        
        # Initialize expanded settings with default values
        self.current_settings: Dict[str, float] = {
            # Basic adjustments
            'brightness': 0.0,
            'contrast': 0.0,
            'saturation': 0.0,
            'sharpness': 0.0,
            
            # Advanced adjustments
            'noise': 0.0,
            'denoise': 0.0,
            'clarity': 0.0,
            'vibrance': 0.0,
            'highlights': 0.0,
            'shadows': 0.0,
            'temperature': 0.0,
            'tint': 0.0,
            
            # Color adjustments
            'hue': 0.0,
            'exposure': 0.0, 
            'gamma': 0.0,
            'blacks': 0.0,
            'whites': 0.0,
            
            # Effects
            'blur': 0.0,
            'vignette': 0.0,
            'grain': 0.0,
            'emboss': 0.0,
            'sepia': 0.0,
            'invert': 0.0,
            'posterize': 0.0,
            'solarize': 0.0,
            
            # New artistic effects
            'pencil_sketch': 0.0,
            'cartoon': 0.0,
            'watercolor': 0.0,
            'oil_painting': 0.0,
            'pixelate': 0.0,
            'halftone': 0.0,
            'duotone': 0.0,
            'glitch': 0.0,
            
            # Transforms
            'rotation': 0.0,
            'crop_left': 0.0,
            'crop_top': 0.0,
            'crop_right': 0.0,
            'crop_bottom': 0.0,
            'perspective': 0.0
        }
        
        # Performance settings
        self.preview_quality: str = "medium"  # low, medium, high
        self.update_delay: int = 100  # ms delay for debouncing updates
        self.use_threading: bool = True
        self.last_update_time: float = 0
        self.pending_update: bool = False
        
        # Set up flags for optimization
        self.adaptive_preview = True  # Automatically reduce preview quality during rapid adjustments
        self.use_gpu = False  # Will be set to True if GPU acceleration is available
        
        # Check for GPU acceleration via OpenCV
        try:
            cv_build_info = cv2.getBuildInformation()
            if 'CUDA' in cv_build_info and 'YES' in cv_build_info.split('CUDA')[1].split('\n')[0]:
                self.use_gpu = True
                self.logger.info("GPU acceleration is available and enabled")
        except Exception as e:
            self.logger.warning(f"Could not check for GPU acceleration: {e}")
        
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure window
        self.title("Advanced Image Editor Pro")
        self.geometry("1200x800")
        
        # Center window on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        self.geometry(f"1200x800+{x}+{y}")
        
        # Ensure window is on top and focused
        self.lift()
        self.focus_force()
        
    def setup_ui(self):
        """Set up the main user interface"""
        # Configure window
        self.title("Advanced Image Editor Pro")
        self.geometry("1200x800")
        
        # Create master frame to hold everything
        self.master_frame = ctk.CTkFrame(self)
        self.master_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create left sidebar for controls (30% width)
        self.control_sidebar = ctk.CTkFrame(self.master_frame, width=320)
        self.control_sidebar.pack(side="left", fill="y", padx=(0, 10), pady=0)
        self.control_sidebar.pack_propagate(False)  # Don't shrink
        
        # Create right area for image display (70% width)
        self.image_area = ctk.CTkFrame(self.master_frame)
        self.image_area.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        # Setup the sidebar with tabs
        self.setup_sidebar()
        
        # Setup the image area
        self.setup_image_area()
        
        # Setup the action bar at the bottom
        self.setup_action_bar()
        
        # Setup menu
        self.setup_menu()
        
        # Initialize status bar
        self.status_frame = ctk.CTkFrame(self, height=30)
        self.status_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        # Status text on left
        self.status_bar = ctk.CTkLabel(self.status_frame, text="Ready")
        self.status_bar.pack(side="left", padx=10)
        
        # Performance metrics display
        self.metrics_label = ctk.CTkLabel(self.status_frame, text="")
        self.metrics_label.pack(side="right", padx=10)
        
        # Processing indicator
        self.processing_indicator = ctk.CTkLabel(self.status_frame, text="")
        self.processing_indicator.pack(side="right", padx=10)
        
        # Setup keyboard shortcuts
        self.bind("<Control-z>", lambda e: self.undo_action())
        self.bind("<Control-y>", lambda e: self.redo_action())
        self.bind("<Control-o>", lambda e: self.open_image())
        self.bind("<Control-s>", lambda e: self.save_image())
        
    def setup_menu(self):
        """Set up application menu"""
        self.menu_bar = tk.Menu(self)
        self.configure(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=lambda: self.save_image(None))
        file_menu.add_separator()
        file_menu.add_command(label="Export...", command=self.export_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo_action, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo_action, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset All", command=self.reset_all)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Submenu for preview quality
        preview_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Preview Quality", menu=preview_menu)
        
        # Create variable for radio buttons
        self.preview_var = tk.StringVar(value=self.preview_quality)
        
        # Add radio buttons for preview quality
        preview_menu.add_radiobutton(label="Low (Faster)", 
                                    variable=self.preview_var, 
                                    value="low",
                                    command=lambda: self.set_preview_quality("low"))
        preview_menu.add_radiobutton(label="Medium", 
                                    variable=self.preview_var, 
                                    value="medium",
                                    command=lambda: self.set_preview_quality("medium"))
        preview_menu.add_radiobutton(label="High (Slower)", 
                                    variable=self.preview_var, 
                                    value="high",
                                    command=lambda: self.set_preview_quality("high"))
        
        view_menu.add_separator()
        
        # Create variable for adaptive preview checkbox
        self.adaptive_preview_var = tk.BooleanVar(value=self.adaptive_preview)
        view_menu.add_checkbutton(label="Adaptive Preview", 
                                 variable=self.adaptive_preview_var,
                                 command=self.toggle_adaptive_preview)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        
    def setup_sidebar(self):
        """Set up the tabbed sidebar for controls"""
        # Create the header
        self.sidebar_header("Advanced Image Editor Pro")
        
        # Create notebook (tabbed interface)
        self.tab_view = ctk.CTkTabview(self.control_sidebar)
        self.tab_view.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add tabs
        self.tab_view.add("Basic")
        self.tab_view.add("Color")
        self.tab_view.add("Advanced")
        self.tab_view.add("Effects")
        self.tab_view.add("Artistic")
        self.tab_view.add("Transform")
        
        # Set default tab
        self.tab_view.set("Basic")
        
        # Setup controls for each tab
        self.setup_basic_controls(self.tab_view.tab("Basic"))
        self.setup_color_controls(self.tab_view.tab("Color"))
        self.setup_advanced_controls(self.tab_view.tab("Advanced"))
        self.setup_effects_controls(self.tab_view.tab("Effects"))
        self.setup_artistic_controls(self.tab_view.tab("Artistic"))
        self.setup_transform_controls(self.tab_view.tab("Transform"))
    
    def sidebar_header(self, text):
        """Create a header for the sidebar"""
        header_frame = ctk.CTkFrame(self.control_sidebar)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        header = ctk.CTkLabel(
            header_frame, 
            text=text,
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(fill="x", padx=5, pady=5)
    
    def setup_basic_controls(self, parent):
        """Set up basic image adjustment controls"""
        # Brightness
        self.create_slider(parent, "Brightness", "brightness", -100, 100, 0)
        
        # Contrast
        self.create_slider(parent, "Contrast", "contrast", -100, 100, 0)
        
        # Saturation
        self.create_slider(parent, "Saturation", "saturation", -100, 100, 0)
        
        # Sharpness
        self.create_slider(parent, "Sharpness", "sharpness", 0, 100, 0)
        
        # Exposure
        self.create_slider(parent, "Exposure", "exposure", -100, 100, 0)
        
        # Reset button for this tab
        self.create_reset_button(parent, ["brightness", "contrast", "saturation", "sharpness", "exposure"])
    
    def setup_color_controls(self, parent):
        """Set up color adjustment controls"""
        # Hue
        self.create_slider(parent, "Hue", "hue", -180, 180, 0)
        
        # White Balance - Temperature
        self.create_slider(parent, "Temperature", "temperature", -100, 100, 0)
        
        # White Balance - Tint (Magenta/Green)
        self.create_slider(parent, "Tint", "tint", -100, 100, 0)
        
        # Vibrance
        self.create_slider(parent, "Vibrance", "vibrance", 0, 100, 0)
        
        # Highlights
        self.create_slider(parent, "Highlights", "highlights", -100, 100, 0)
        
        # Shadows
        self.create_slider(parent, "Shadows", "shadows", -100, 100, 0)
        
        # Whites
        self.create_slider(parent, "Whites", "whites", -100, 100, 0)
        
        # Blacks
        self.create_slider(parent, "Blacks", "blacks", -100, 100, 0)
        
        # Reset button for this tab
        self.create_reset_button(parent, ["hue", "temperature", "tint", "vibrance", 
                                        "highlights", "shadows", "whites", "blacks"])
    
    def create_reset_button(self, parent, params):
        """Create a reset button for a specific set of parameters"""
        reset_btn = ctk.CTkButton(
            parent,
            text="Reset Tab",
            command=lambda: self.reset_params(params),
            fg_color="gray30",
            hover_color="gray40",
            height=30
        )
        reset_btn.pack(padx=10, pady=(20, 10), fill="x")

    def setup_image_area(self):
        """Set up the image display area"""
        # Create top toolbar for image area
        self.image_toolbar = ctk.CTkFrame(self.image_area)
        self.image_toolbar.pack(side="top", fill="x", padx=5, pady=5)
        
        # Add zoom controls
        zoom_in_btn = ctk.CTkButton(
            self.image_toolbar,
            text="🔍+",
            width=40,
            command=lambda: self.zoom_image("in")
        )
        zoom_in_btn.pack(side="left", padx=5, pady=5)
        
        zoom_out_btn = ctk.CTkButton(
            self.image_toolbar,
            text="🔍-",
            width=40,
            command=lambda: self.zoom_image("out")
        )
        zoom_out_btn.pack(side="left", padx=5, pady=5)
        
        # Zoom level label
        self.zoom_label = ctk.CTkLabel(self.image_toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5, pady=5)
        
        # Fit to window button
        fit_btn = ctk.CTkButton(
            self.image_toolbar,
            text="Fit to Window",
            width=100,
            command=self.fit_to_window
        )
        fit_btn.pack(side="left", padx=15, pady=5)
        
        # Show original button
        self.show_original_var = tk.BooleanVar(value=False)
        show_original_btn = ctk.CTkButton(
            self.image_toolbar,
            text="Show Original",
            width=100,
            command=self.toggle_show_original
        )
        show_original_btn.pack(side="right", padx=5, pady=5)
        
        # Image info display
        self.image_info = ctk.CTkLabel(self.image_toolbar, text="No image loaded")
        self.image_info.pack(side="right", padx=15, pady=5)
        
        # Create scrollable frame for image canvas
        self.scrollable_frame = ctk.CTkScrollableFrame(self.image_area)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create canvas for image display with scrolling
        self.image_canvas = Canvas(
            self.scrollable_frame,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.image_canvas.pack(fill="both", expand=True)
        
        # Bind canvas events
        self.image_canvas.bind("<Configure>", self.on_canvas_configure)
        self.image_canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.image_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.image_canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.image_canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.image_canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
        
        # Default display message (shows before an image is loaded)
        self.canvas_text_id = self.image_canvas.create_text(
            300, 200,
            text="No Image Loaded\nUse File > Open to load an image",
            font=("Segoe UI", 14),
            fill="white"
        )
        
    def setup_action_bar(self):
        """Set up action buttons at the bottom of the window"""
        self.action_bar = ctk.CTkFrame(self)
        self.action_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        
        # Undo button
        self.undo_btn = ctk.CTkButton(
            self.action_bar,
            text="↶ Undo",
            command=self.undo_action,
            state="disabled",
            width=80
        )
        self.undo_btn.pack(side="left", padx=5, pady=5)
        
        # Redo button
        self.redo_btn = ctk.CTkButton(
            self.action_bar,
            text="↷ Redo",
            command=self.redo_action,
            state="disabled",
            width=80
        )
        self.redo_btn.pack(side="left", padx=5, pady=5)
        
        # Reset button
        self.reset_btn = ctk.CTkButton(
            self.action_bar,
            text="Reset All",
            command=self.reset_all,
            fg_color="gray30",
            hover_color="gray40",
            width=100
        )
        self.reset_btn.pack(side="left", padx=5, pady=5)
        
        # Open button
        open_btn = ctk.CTkButton(
            self.action_bar,
            text="Open Image",
            command=self.open_image,
            width=100
        )
        open_btn.pack(side="left", padx=15, pady=5)
        
        # Export button
        export_btn = ctk.CTkButton(
            self.action_bar,
            text="Export",
            command=self.export_image,
            width=100
        )
        export_btn.pack(side="right", padx=5, pady=5)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            self.action_bar,
            text="Save",
            command=self.save_image,
            width=100
        )
        self.save_btn.pack(side="right", padx=5, pady=5)

    def update_image_info(self):
        """Update the image information display"""
        if self.image:
            size = self.image.size
            mode = self.image.mode
            self.image_info.configure(text=f"Format: {mode}")
        else:
            self.image_info.configure(text="No image loaded")

    def open_image(self):
        """Open and load an image file"""
        try:
            # Pencereyi öne getir
            self.lift()
            self.focus_force()
            
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[
                    ("All supported formats", " ".join(self.supported_formats.values())),
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg *.jpe *.jfif"),
                    ("All files", "*.*")
                ],
                parent=self  # Parent pencere olarak ImageEditor'ı belirt
            )
            
            if file_path:
                self.load_image(file_path)
                
                # Dosya seçildikten sonra tekrar pencereyi öne getir
                self.after(100, lambda: (self.lift(), self.focus_force()))
                
        except Exception as e:
            self.logger.error(f"Error opening image: {str(e)}")
            messagebox.showerror("Error", f"Failed to open image: {str(e)}")

    def save_image(self, file_path=None):
        """Save the current edited image to a file"""
        if self.image is None:
            self.show_error("No image to save")
            return False
            
        try:
            # If no file path provided, open a save dialog
            if file_path is None:
                filetypes = [
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg;*.jpeg"),
                    ("BMP files", "*.bmp"),
                    ("TIFF files", "*.tiff;*.tif"),
                    ("All files", "*.*")
                ]
                
                file_path = filedialog.asksaveasfilename(
                    title="Save Image",
                    filetypes=filetypes,
                    defaultextension=".png"
                )
                
                if not file_path:  # User cancelled
                    return False
            
            # Check and add extension if needed
            if not any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']):
                file_path += '.png'  # Default to PNG
                
            # Save the processed image
            self.image.save(file_path)
            self.status_bar.configure(text=f"Image saved to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving image: {str(e)}")
            self.show_error(f"Error saving image: {str(e)}")
            return False

    def create_slider(self, parent, label_text, param, min_val, max_val, default_val, step=None):
        """Create a labeled slider control with improved responsiveness"""
        # Frame to hold label and value
        header_frame = ctk.CTkFrame(parent)
        header_frame.pack(fill="x", padx=5, pady=(10, 0))
        
        # Label on left
        label = ctk.CTkLabel(header_frame, text=label_text)
        label.pack(side="left", padx=5)
        
        # Value display on right
        value_var = tk.StringVar(value=str(default_val))
        value_label = ctk.CTkLabel(header_frame, textvariable=value_var, width=40)
        value_label.pack(side="right", padx=5)
        
        # Determine number of steps
        if step is not None:
            num_steps = int((max_val - min_val) / step)
        else:
            num_steps = 100
        
        # Slider
        slider = ctk.CTkSlider(
            parent,
            from_=min_val,
            to=max_val,
            number_of_steps=num_steps,
            command=lambda val, p=param, v=value_var: self._on_slider_change(val, p, v)
        )
        slider.pack(fill="x", padx=10, pady=5)
        slider.set(default_val)
        
        # Store slider in dictionary for later access
        if not hasattr(self, 'sliders'):
            self.sliders = {}
        self.sliders[param] = slider
        
        # Store value labels for updating
        if not hasattr(self, 'value_labels'):
            self.value_labels = {}
        self.value_labels[param] = value_var
        
        return slider
        
    def create_toggle(self, parent, label_text, param):
        """Create a toggle switch control"""
        # Frame to hold toggle and label
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=5)
        
        # Toggle variable
        var = tk.BooleanVar(value=False)
        
        # Toggle switch
        toggle = ctk.CTkSwitch(
            frame, 
            text=label_text,
            variable=var,
            command=lambda: self._on_toggle_change(param, var.get())
        )
        toggle.pack(side="left", padx=10, pady=10)
        
        # Store toggle in dictionary for later access
        if not hasattr(self, 'toggles'):
            self.toggles = {}
        self.toggles[param] = (toggle, var)
        
        return toggle
        
    def debounced_update(self, param, value):
        """Update with debouncing to avoid too frequent updates"""
        current_time = time.time()
        self.current_settings[param] = float(value)
        
        # Use adaptive preview quality based on update frequency
        if self.adaptive_preview and current_time - self.last_update_time < 0.1:
            self._set_temp_preview_quality("low")
        elif self.adaptive_preview and current_time - self.last_update_time < 0.3:
            self._set_temp_preview_quality("medium")
        
        # If not using threading, update directly with longer debounce
        if not self.use_threading:
            if current_time - self.last_update_time > 0.2:
                self.last_update_time = current_time
                self.process_image(param, value)
            else:
                # Cancel any pending updates
                if hasattr(self, '_update_timer'):
                    self.after_cancel(self._update_timer)
                
                # Schedule new update
                self._update_timer = self.after(300, lambda: self.process_image(param, value))
            return
            
        # For threaded updates, use shorter debounce time and queue updates
        if current_time - self.last_update_time > 0.1:
            self.last_update_time = current_time
            self.process_image(param, value)
        else:
            # Flag that an update is pending
            self.pending_update = True
            
            # Cancel any pending updates
            if hasattr(self, '_update_timer'):
                self.after_cancel(self._update_timer)
            
            # Schedule new update
            self._update_timer = self.after(100, lambda: self._process_pending_update())
    
    def _set_temp_preview_quality(self, quality):
        """Temporarily set preview quality during rapid adjustments"""
        self._original_quality = self.preview_quality
        self.preview_quality = quality
        
        # Schedule restoration of original quality
        if hasattr(self, '_quality_timer'):
            self.after_cancel(self._quality_timer)
        
        self._quality_timer = self.after(500, self._restore_preview_quality)
    
    def _restore_preview_quality(self):
        """Restore original preview quality after rapid adjustments"""
        if hasattr(self, '_original_quality'):
            self.preview_quality = self._original_quality
            self.process_image("_quality_update", 0)
    
    def process_image(self, param: str, value: float):
        """Update image with new effect parameters"""
        if self.original_image is None:
            return
            
        try:
            self.current_settings[param] = float(value)
            
            # Add to history only if this is a new edit (not during undo/redo operations)
            if param != "_history_update" and param != "_quality_update":
                self._add_to_history()
            
            # Check cache first for identical settings
            cache_key = self._generate_cache_key()
            if cache_key in self.ordered_cache:
                # Cache hit - use cached image
                self.image = self.ordered_cache[cache_key]
                self.cache_hits += 1
                # Move to end of OrderedDict (most recently used)
                self.ordered_cache.move_to_end(cache_key)
                self.update_image_display()
                self._show_processing_indicator(False)
                self._update_metrics()
                return
            
            self.cache_misses += 1
            
            # Use threading for better performance if enabled
            if self.use_threading and not self.is_processing:
                self._show_processing_indicator(True)
                self.is_processing = True
                
                # Start processing in a separate thread
                self.processing_thread = threading.Thread(target=self._threaded_apply_effects)
                self.processing_thread.daemon = True
                self.processing_thread.start()
            else:
                # Direct processing without threading
                self._show_processing_indicator(True)
                self.apply_effects()
                self.update_image_display()
                self._show_processing_indicator(False)
                self._update_metrics()
        except Exception as e:
            self.logger.error(f"Error updating image: {str(e)}")
            self.show_error("Error applying effects")
    
    def _update_metrics(self):
        """Update performance metrics display"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            hit_rate = (self.cache_hits / total_cache_requests) * 100
        else:
            hit_rate = 0
            
        cache_size = len(self.ordered_cache)
        metrics_text = f"Cache: {hit_rate:.1f}% hit rate ({cache_size} images)"
        
        if hasattr(self, 'metrics_label'):
            self.metrics_label.configure(text=metrics_text)
            
    def _generate_cache_key(self):
        """Generate a unique key for the current settings"""
        # Create a sorted tuple of parameter values
        settings_tuple = tuple(sorted((k, round(v, 2)) for k, v in self.current_settings.items()))
        return hash(settings_tuple)
    
    def _manage_cache(self, new_image):
        """Add image to cache and manage cache size"""
        cache_key = self._generate_cache_key()
        
        # Check current cache size in bytes
        current_size = sum(self._get_image_memory_size(img) for img in self.ordered_cache.values())
        
        # If adding this would exceed limit, remove least recently used items
        new_image_size = self._get_image_memory_size(new_image)
        while (current_size + new_image_size > self.cache_memory_limit or 
               len(self.ordered_cache) >= self.cache_size_limit) and self.ordered_cache:
            # Remove oldest item
            removed_key, removed_image = self.ordered_cache.popitem(last=False)
            current_size -= self._get_image_memory_size(removed_image)
            
        # Add to cache
        self.ordered_cache[cache_key] = new_image
    
    def _get_image_memory_size(self, img):
        """Estimate memory size of a PIL image in bytes"""
        if img is None:
            return 0
            
        # Get image dimensions and mode
        width, height = img.size
        mode = img.mode
        
        # Calculate bytes per pixel based on mode
        if mode == '1':  # 1-bit pixels
            bytes_per_pixel = 1/8
        elif mode == 'L':  # 8-bit pixels
            bytes_per_pixel = 1
        elif mode == 'RGB':  # 3x8-bit pixels
            bytes_per_pixel = 3
        elif mode == 'RGBA':  # 4x8-bit pixels
            bytes_per_pixel = 4
        else:
            bytes_per_pixel = 4  # Default to RGBA if unknown
            
        # Calculate total memory
        memory_size = width * height * bytes_per_pixel
        
        # Add overhead for PIL image object (estimation)
        overhead = 64  # Approximate overhead in bytes
        
        return int(memory_size + overhead)
        
    def apply_effects(self):
        """Apply all effects to the image"""
        if self.original_image is None:
            return
            
        try:
            # Start with a fresh copy of the original image
            self.image = self.original_image.copy()
            
            # For preview quality adjustment
            preview_scale = 1.0
            if self.preview_quality == "low":
                # Smaller image for faster processing
                preview_scale = 0.5
            elif self.preview_quality == "medium":
                preview_scale = 0.75
                
            # Resize if needed for preview
            if preview_scale < 1.0:
                w, h = self.image.size
                new_size = (int(w * preview_scale), int(h * preview_scale))
                self.image = self.image.resize(new_size, Image.LANCZOS)
                
            # Apply rotation if needed
            if self.current_settings['rotation'] != 0:
                rotation = self.current_settings['rotation']
                self.image = self.image.rotate(
                    rotation,
                    resample=Image.BICUBIC,
                    expand=False
                )
                
            # Apply effects in optimal order for quality
            
            # Apply black and white first if enabled
            if hasattr(self, 'toggles') and 'black_and_white' in self.toggles:
                _, var = self.toggles['black_and_white']
                if var.get():
                    self.image = self.image.convert('L').convert('RGB')
            
            # 1. Exposure adjustments
            if self.current_settings['exposure'] != 0:
                # Convert to numpy for better exposure control
                img_array = np.array(self.image)
                factor = 2 ** (self.current_settings['exposure'] / 100)
                img_array = img_array * factor
                img_array = np.clip(img_array, 0, 255).astype(np.uint8)
                self.image = Image.fromarray(img_array)
            
            # 2. White balance (temperature/tint)
            if self.current_settings['temperature'] != 0 or self.current_settings['tint'] != 0:
                self._apply_white_balance(
                    self.current_settings['temperature'], 
                    self.current_settings['tint']
                )
            
            # 3. Basic adjustments
            if self.current_settings['brightness'] != 0:
                enhancer = ImageEnhance.Brightness(self.image)
                factor = 1 + (self.current_settings['brightness'] / 100)
                self.image = enhancer.enhance(factor)
                
            if self.current_settings['contrast'] != 0:
                enhancer = ImageEnhance.Contrast(self.image)
                factor = 1 + (self.current_settings['contrast'] / 100)
                self.image = enhancer.enhance(factor)
            
            # 4. Color adjustments
            if self.current_settings['saturation'] != 0:
                enhancer = ImageEnhance.Color(self.image)
                factor = 1 + (self.current_settings['saturation'] / 100)
                self.image = enhancer.enhance(factor)
                
            # Apply hue adjustment if needed
            if self.current_settings['hue'] != 0:
                self._apply_hue_shift(self.current_settings['hue'])
                
            # 5. Local adjustments
            # Apply highlights/shadows adjustment
            if (self.current_settings['highlights'] != 0 or 
                self.current_settings['shadows'] != 0 or
                self.current_settings['whites'] != 0 or
                self.current_settings['blacks'] != 0):
                self._apply_tone_mapping()
                
            # 6. Clarity (local contrast)
            if self.current_settings['clarity'] != 0:
                self._apply_clarity(self.current_settings['clarity'])
                
            # 7. Detail adjustments
            if self.current_settings['sharpness'] != 0:
                enhancer = ImageEnhance.Sharpness(self.image)
                factor = 1 + (self.current_settings['sharpness'] / 100 * 2)  # More pronounced effect
                self.image = enhancer.enhance(factor)
                
            # 8. Noise reduction if needed
            if self.current_settings['denoise'] != 0:
                self._apply_denoise(self.current_settings['denoise'])
                
            # 9. Effects
            # Apply sepia if enabled
            if hasattr(self, 'toggles') and 'sepia' in self.toggles:
                _, var = self.toggles['sepia']
                if var.get():
                    self._apply_sepia()
                    
            # Apply invert if enabled
            if hasattr(self, 'toggles') and 'invert' in self.toggles:
                _, var = self.toggles['invert']
                if var.get():
                    self.image = ImageOps.invert(self.image)
                    
            # Apply blur
            if self.current_settings['blur'] > 0:
                blur_radius = self.current_settings['blur'] / 10
                self.image = self.image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                
            # Apply emboss
            if self.current_settings['emboss'] > 0:
                strength = self.current_settings['emboss'] / 100
                self.image = self.image.filter(ImageFilter.EMBOSS)
                if strength < 1.0:
                    # Blend with original for lower strength
                    orig_copy = self.original_image.copy()
                    if preview_scale < 1.0:
                        w, h = orig_copy.size
                        new_size = (int(w * preview_scale), int(h * preview_scale))
                        orig_copy = orig_copy.resize(new_size, Image.LANCZOS)
                    self.image = Image.blend(orig_copy, self.image, strength)
                
            # Apply posterize
            if self.current_settings['posterize'] > 0:
                levels = 8 - int(self.current_settings['posterize'])
                if levels < 2:
                    levels = 2
                self.image = ImageOps.posterize(self.image, levels)
                
            # Apply solarize
            if self.current_settings['solarize'] > 0:
                threshold = int(self.current_settings['solarize'])
                self.image = ImageOps.solarize(self.image, threshold)
                
            # Apply noise
            if self.current_settings['noise'] > 0:
                self._apply_noise(self.current_settings['noise'])
                
            # Apply grain if needed
            if self.current_settings['grain'] > 0:
                self._apply_grain(self.current_settings['grain'])
                
            # Apply vignette effect
            if self.current_settings['vignette'] > 0:
                self._apply_vignette(self.current_settings['vignette'])
                
            # 10. Artistic effects
            
            # Apply pencil sketch
            if self.current_settings['pencil_sketch'] > 0:
                self._apply_pencil_sketch(self.current_settings['pencil_sketch'])
                
            # Apply cartoon effect
            if self.current_settings['cartoon'] > 0:
                self._apply_cartoon(self.current_settings['cartoon'])
                
            # Apply watercolor
            if self.current_settings['watercolor'] > 0:
                self._apply_watercolor(self.current_settings['watercolor'])
                
            # Apply oil painting
            if self.current_settings['oil_painting'] > 0:
                self._apply_oil_painting(self.current_settings['oil_painting'])
                
            # Apply pixelate
            if self.current_settings['pixelate'] > 0:
                self._apply_pixelate(self.current_settings['pixelate'])
                
            # Apply halftone
            if self.current_settings['halftone'] > 0:
                self._apply_halftone(self.current_settings['halftone'])
                
            # Apply duotone
            if self.current_settings['duotone'] > 0:
                self._apply_duotone(self.current_settings['duotone'])
                
            # Apply glitch
            if self.current_settings['glitch'] > 0:
                self._apply_glitch(self.current_settings['glitch'])
            
            # If we resized for preview, resize back to original size
            if preview_scale < 1.0:
                self.image = self.image.resize(self.original_image.size, Image.LANCZOS)
                
            # Cache the processed image
            self._manage_cache(self.image.copy())
                
        except Exception as e:
            self.logger.error(f"Error applying effects: {str(e)}")
            self.show_error("Error applying effects")
            
    def _threaded_apply_effects(self):
        """Apply effects in a separate thread for better performance"""
        try:
            with self.processing_lock:
                self.apply_effects()
                
                # Use after() to update UI from the main thread
                self.after(0, self._finish_processing)
        except Exception as e:
            self.logger.error(f"Error in threaded processing: {str(e)}")
            self.after(0, lambda: self._show_processing_indicator(False))
            self.is_processing = False
    
    def _finish_processing(self):
        """Finish the threaded processing and update UI"""
        self.update_image_display()
        self._show_processing_indicator(False)
        self.is_processing = False
        self._update_metrics()
        
    def _process_pending_update(self):
        """Process any pending updates"""
        if self.pending_update:
            self.pending_update = False
            self.last_update_time = time.time()
            self.process_image("_update", 0)
            
    def _on_slider_change(self, value, param, value_var):
        """Handle slider value changes"""
        # Update the value label
        if param == "gamma":
            # Special case for gamma which uses smaller increments
            rounded_value = round(float(value), 2)
        else:
            rounded_value = round(float(value))
            
        value_var.set(str(rounded_value))
        
        # Update the image with debouncing
        self.debounced_update(param, rounded_value)
        
    def _on_toggle_change(self, param, value):
        """Handle toggle switch changes"""
        # Convert boolean to 0.0 or 100.0 for consistency with sliders
        numeric_value = 100.0 if value else 0.0
        self.current_settings[param] = numeric_value
        
        # Update image immediately
        self.process_image(param, numeric_value)

    def update_image_display(self, event=None):
        """Update the image display with the processed image"""
        if self.image is None:
            return
            
        # Calculate zoom factor
        if not hasattr(self, 'zoom_level'):
            self.zoom_level = 100  # Initialize to 100%
            
        zoom_factor = self.zoom_level / 100.0
            
        # Get the canvas dimensions
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # Get the image dimensions
        img_width, img_height = self.image.size
        
        # Apply zoom
        zoomed_width = int(img_width * zoom_factor)
        zoomed_height = int(img_height * zoom_factor)
        
        # Resize the image for display
        self.display_image = self.image.copy()
        self.display_image.thumbnail((zoomed_width, zoomed_height), Image.LANCZOS)
        
        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(self.display_image)
        
        # Clear the canvas and display the image
        self.image_canvas.delete("all")
        
        # Center the image on the canvas
        x_pos = max(0, (canvas_width - self.display_image.width) // 2)
        y_pos = max(0, (canvas_height - self.display_image.height) // 2)
        
        self.image_canvas.create_image(x_pos, y_pos, anchor="nw", image=self.photo_image)
        
        # Update image info
        if hasattr(self, 'image_info_label'):
            self.image_info_label.configure(
                text=f"Size: {img_width}x{img_height} | Zoom: {int(self.zoom_level)}%"
            )
            
    def zoom_image(self, direction):
        """Zoom in or out of the displayed image"""
        if not hasattr(self, 'zoom_level'):
            self.zoom_level = 100  # Initialize zoom level to 100%
            
        # Calculate new zoom level
        if direction == "in":
            self.zoom_level = min(self.zoom_level * 1.2, 400)  # Max 400%
        else:  # out
            self.zoom_level = max(self.zoom_level / 1.2, 20)   # Min 20%
            
        # Update zoom label if exists
        if hasattr(self, 'zoom_label'):
            self.zoom_label.configure(text=f"{int(self.zoom_level)}%")
        
        # Update display with new zoom level
        self.update_image_display()

    def on_window_resize(self, event=None):
        """Handle window resize events"""
        if hasattr(self, 'image') and self.image:
            # Add a small delay to prevent too frequent updates
            if hasattr(self, '_resize_timer'):
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(100, self.update_image_display)

    def reset_effects(self):
        """Reset all effects to their default values"""
        try:
            for param, slider in self.sliders.items():
                slider.set(0)
                self.current_settings[param] = 0
                
            if self.original_image:
                self.image = self.original_image.copy()
                self.update_image_display()
        except Exception as e:
            self.logger.error(f"Error resetting effects: {str(e)}")
            self.show_error("Error resetting effects")
            
    def show_error(self, message: str):
        """Display error message to user"""
        messagebox.showerror("Error", message)

    def on_closing(self):
        """Clean up resources before closing"""
        try:
            # Clean up resources
            if self.image:
                self.image = None
            if self.original_image:
                self.original_image = None
            if self.display_photo:
                self.display_photo = None
                
            # Force garbage collection
            gc.collect()
            
            # Destroy window
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.destroy()

    def _adjust_color(self, color: str, amount: int) -> str:
        """Adjust hex color brightness"""
        if not color.startswith('#'):
            return color
            
        # Convert hex to RGB
        color = color.lstrip('#')
        r = int(color[:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:], 16)
        
        # Adjust brightness
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'

    def load_image(self, file_path: str):
        """Load and prepare image for editing"""
        try:
            # Open and convert image to RGB mode
            img = Image.open(file_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Store original and working copies
            self.original_image = img
            self.image = img.copy()
            
            # Reset all effect sliders
            self.reset_effects()
            
            # Update display
            self.update_image_display()
            self.update_image_info()
            
            self.logger.info(f"Successfully loaded image: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading image: {str(e)}")
            raise

    def _process_pending_update(self):
        """Process any pending updates"""
        if self.pending_update:
            self.pending_update = False
            self.last_update_time = time.time()
            self.process_image("_update", 0)
    
    def _threaded_apply_effects(self):
        """Apply effects in a separate thread for better performance"""
        try:
            with self.processing_lock:
                self.apply_effects()
                
                # Use after() to update UI from the main thread
                self.after(0, self._finish_processing)
        except Exception as e:
            self.logger.error(f"Error in threaded processing: {str(e)}")
            self.after(0, lambda: self._show_processing_indicator(False))
            self.is_processing = False
    
    def _finish_processing(self):
        """Finish the threaded processing and update UI"""
        self.update_image_display()
        self._show_processing_indicator(False)
        self.is_processing = False

    def _show_processing_indicator(self, show=True):
        """Show or hide the processing indicator"""
        if show:
            self.processing_indicator.configure(text="Processing...")
        else:
            self.processing_indicator.configure(text="")

    # Advanced image processing methods
    
    def _apply_white_balance(self, temperature, tint):
        """Apply temperature and tint adjustments"""
        try:
            if temperature == 0 and tint == 0:
                return
                
            # Convert to numpy array
            img_array = np.array(self.image).astype(np.float32)
            
            # Apply temperature (blue-yellow) adjustment
            if temperature != 0:
                # Normalize to range -1 to 1
                temp = temperature / 100
                
                # Adjust blue-yellow balance
                if temp > 0:  # Warm (more yellow)
                    img_array[:, :, 2] -= temp * 30  # Less blue
                    img_array[:, :, 0] += temp * 20  # More red
                else:  # Cool (more blue)
                    img_array[:, :, 2] += abs(temp) * 30  # More blue
                    img_array[:, :, 0] -= abs(temp) * 20  # Less red
            
            # Apply tint (green-magenta) adjustment
            if tint != 0:
                # Normalize to range -1 to 1
                t = tint / 100
                
                # Adjust green-magenta balance
                if t > 0:  # More magenta
                    img_array[:, :, 1] -= t * 30  # Less green
                else:  # More green
                    img_array[:, :, 1] += abs(t) * 30  # More green
            
            # Ensure values stay in valid range
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(img_array)
            
        except Exception as e:
            self.logger.error(f"Error applying white balance: {str(e)}")
            raise
            
    def _apply_hue_shift(self, amount):
        """Apply hue shift to the image"""
        try:
            # Convert to HSV color space
            img_hsv = self.image.convert('HSV')
            
            # Get individual channels
            h, s, v = img_hsv.split()
            
            # Calculate hue shift (0-255 range for PIL HSV)
            shift = int((amount / 180) * 255)
            
            # Apply shift using numpy for performance
            h_array = np.array(h)
            h_array = np.mod(h_array + shift, 255).astype(np.uint8)
            
            # Create new hue channel
            new_h = Image.fromarray(h_array)
            
            # Merge channels back
            img_hsv = Image.merge('HSV', (new_h, s, v))
            
            # Convert back to RGB
            self.image = img_hsv.convert('RGB')
            
        except Exception as e:
            self.logger.error(f"Error applying hue shift: {str(e)}")
            raise
            
    def _apply_tone_mapping(self):
        """Apply highlights, shadows, whites and blacks adjustments"""
        try:
            # Convert to numpy array
            img_array = np.array(self.image).astype(np.float32)
            
            # Calculate luminance (simple average method)
            luminance = img_array.mean(axis=2) / 255.0  # Normalize to 0-1
            
            # Apply highlights adjustment (affects bright areas)
            if self.current_settings['highlights'] != 0:
                # Get highlight mask (high luminance areas)
                highlight_mask = np.clip((luminance - 0.5) * 2, 0, 1)
                highlight_factor = self.current_settings['highlights'] / 100
                
                # Apply adjustment based on mask
                for i in range(3):  # For each RGB channel
                    if highlight_factor > 0:
                        # Increase highlights
                        img_array[:, :, i] += highlight_mask * highlight_factor * 50
                    else:
                        # Decrease highlights
                        img_array[:, :, i] = img_array[:, :, i] * (1 - highlight_mask * abs(highlight_factor) * 0.5)
            
            # Apply shadows adjustment (affects dark areas)
            if self.current_settings['shadows'] != 0:
                # Get shadow mask (low luminance areas)
                shadow_mask = np.clip((0.5 - luminance) * 2, 0, 1)
                shadow_factor = self.current_settings['shadows'] / 100
                
                # Apply adjustment based on mask
                for i in range(3):  # For each RGB channel
                    if shadow_factor > 0:
                        # Increase shadows (brighten dark areas)
                        img_array[:, :, i] += shadow_mask * shadow_factor * 50
                    else:
                        # Decrease shadows (darken dark areas more)
                        img_array[:, :, i] = img_array[:, :, i] * (1 - shadow_mask * abs(shadow_factor) * 0.5)
            
            # Apply whites adjustment (affects extreme highlights)
            if self.current_settings['whites'] != 0:
                whites_mask = np.clip((luminance - 0.8) * 5, 0, 1)
                whites_factor = self.current_settings['whites'] / 100
                
                for i in range(3):
                    if whites_factor > 0:
                        # Increase whites
                        img_array[:, :, i] += whites_mask * whites_factor * 70
                    else:
                        # Decrease whites
                        img_array[:, :, i] = img_array[:, :, i] * (1 - whites_mask * abs(whites_factor) * 0.6)
            
            # Apply blacks adjustment (affects extreme shadows)
            if self.current_settings['blacks'] != 0:
                blacks_mask = np.clip((0.2 - luminance) * 5, 0, 1)
                blacks_factor = self.current_settings['blacks'] / 100
                
                for i in range(3):
                    if blacks_factor < 0:
                        # Increase blacks (darker)
                        img_array[:, :, i] = img_array[:, :, i] * (1 - blacks_mask * abs(blacks_factor) * 0.7)
                    else:
                        # Decrease blacks (brighter)
                        img_array[:, :, i] += blacks_mask * blacks_factor * 50
            
            # Ensure values stay in valid range
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(img_array)
            
        except Exception as e:
            self.logger.error(f"Error applying tone mapping: {str(e)}")
            raise
            
    def _apply_clarity(self, amount):
        """Apply clarity (local contrast) to the image"""
        try:
            if amount <= 0:
                return
                
            # Convert amount to a radius between 1 and 10
            radius = int(1 + (amount / 100) * 9)
            amount = amount / 100  # Normalize to 0-1
            
            # Create a blurred version of the image for local contrast
            blurred = self.image.filter(ImageFilter.GaussianBlur(radius=radius))
            
            # Convert both to numpy arrays
            img_array = np.array(self.image).astype(np.float32)
            blur_array = np.array(blurred).astype(np.float32)
            
            # Calculate the local contrast mask (difference between image and blurred version)
            diff = img_array - blur_array
            
            # Apply local contrast enhancement
            enhanced = img_array + diff * amount * 2
            
            # Ensure values stay in valid range
            enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(enhanced)
            
        except Exception as e:
            self.logger.error(f"Error applying clarity: {str(e)}")
            raise
            
    def _apply_denoise(self, amount):
        """Apply noise reduction"""
        try:
            if amount <= 0:
                return
                
            strength = amount / 100.0
            
            # Use skimage for higher quality denoising with adaptive strength
            img_array = np.array(self.image)
            
            # Apply fast non-local means denoising
            if self.use_gpu:
                # Use OpenCV GPU-accelerated algorithm if available
                img_array = cv2.fastNlMeansDenoisingColored(
                    img_array,
                    None,
                    strength * 15,  # h parameter (controls strength)
                    strength * 15,  # hColor parameter
                    7,              # templateWindowSize
                    21              # searchWindowSize
                )
            else:
                # For lower strength, use Gaussian filter (fast)
                if strength < 0.3:
                    img_array = filters.gaussian(
                        img_array,
                        sigma=strength * 2,
                        multichannel=True,
                        preserve_range=True
                    ).astype(np.uint8)
                # For medium strength, use bilateral filter (better edge preservation)
                elif strength < 0.7:
                    img_array = restoration.denoise_bilateral(
                        img_array,
                        sigma_color=0.1,
                        sigma_spatial=strength * 5,
                        multichannel=True
                    )
                    img_array = (img_array * 255).astype(np.uint8)
                # For higher strength, use non-local means (best quality but slower)
                else:
                    img_array = restoration.denoise_nl_means(
                        img_array,
                        h=strength * 0.2,
                        fast_mode=True,
                        patch_size=5,
                        patch_distance=6,
                        multichannel=True
                    )
                    img_array = (img_array * 255).astype(np.uint8)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(img_array)
            
        except Exception as e:
            self.logger.error(f"Error applying denoise: {str(e)}")
            raise
    
    def _apply_noise(self, amount):
        """Apply noise effect to the image"""
        try:
            if amount <= 0:
                return
                
            # Convert to numpy array
            img_array = np.array(self.image)
            
            # Scale noise amount
            noise_amount = amount / 2  # Scale down for better control
            
            # Add Gaussian noise
            noise = np.random.normal(0, noise_amount, img_array.shape)
            noisy_img = img_array + noise
            
            # Ensure values stay in valid range
            noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(noisy_img)
            
        except Exception as e:
            self.logger.error(f"Error applying noise: {str(e)}")
            raise
            
    def _apply_grain(self, amount):
        """Apply film grain effect to the image"""
        try:
            if amount <= 0:
                return
                
            # Convert to numpy array
            img_array = np.array(self.image)
            
            # Convert to YCbCr colorspace
            img_ycbcr = color.rgb2ycbcr(img_array)
            
            # Only apply grain to Y channel (luminance)
            y_channel = img_ycbcr[:,:,0]
            
            # Generate grain pattern
            grain = np.random.normal(0, amount / 5, y_channel.shape)
            
            # Apply grain with varying strength based on luminance
            y_factor = y_channel / 255.0  # Normalize to 0-1
            
            # Apply more grain in midtones, less in shadows and highlights
            midtone_mask = 1 - 2 * np.abs(y_factor - 0.5)
            
            # Apply grain
            y_channel = y_channel + grain * midtone_mask * 2
            y_channel = np.clip(y_channel, 0, 255)
            
            # Replace luminance channel
            img_ycbcr[:,:,0] = y_channel
            
            # Convert back to RGB
            img_rgb = color.ycbcr2rgb(img_ycbcr)
            img_rgb = np.clip(img_rgb * 255, 0, 255).astype(np.uint8)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(img_rgb)
            
        except Exception as e:
            self.logger.error(f"Error applying grain: {str(e)}")
            raise
            
    def _apply_vignette(self, amount):
        """Apply vignette effect to the image"""
        try:
            if amount <= 0:
                return
                
            # Get image dimensions
            width, height = self.image.size
            
            # Create radial gradient mask
            x, y = np.meshgrid(np.arange(width), np.arange(height))
            
            # Calculate distance from center (normalized)
            center_x, center_y = width / 2, height / 2
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_distance = np.sqrt(center_x**2 + center_y**2)
            
            # Normalize distance to range 0-1
            distance = distance / max_distance
            
            # Create vignette mask (1 at center, 0 at edges)
            # Adjust falloff based on amount
            falloff = 2.0 - (amount / 100) * 1.5  # Higher amount = faster falloff
            mask = 1 - np.clip(distance ** falloff, 0, 1)
            
            # Scale the effect based on amount
            vignette_strength = amount / 100
            mask = 1 - (1 - mask) * vignette_strength
            
            # Expand mask to 3 channels
            mask = np.stack([mask] * 3, axis=2)
            
            # Apply mask to image
            img_array = np.array(self.image).astype(np.float32)
            img_array = img_array * mask
            
            # Convert back to PIL Image
            self.image = Image.fromarray(np.uint8(img_array))
            
        except Exception as e:
            self.logger.error(f"Error applying vignette: {str(e)}")
            raise
    
    def _apply_sepia(self):
        """Apply sepia tone effect to the image"""
        try:
            # Convert to grayscale
            grayscale = self.image.convert('L')
            
            # Apply sepia tone
            sepia = np.array(grayscale).astype(np.float32)
            sepia_r = sepia * 1.08
            sepia_g = sepia * 0.82
            sepia_b = sepia * 0.6
            
            # Ensure values stay in valid range
            sepia_r = np.clip(sepia_r, 0, 255).astype(np.uint8)
            sepia_g = np.clip(sepia_g, 0, 255).astype(np.uint8)
            sepia_b = np.clip(sepia_b, 0, 255).astype(np.uint8)
            
            # Merge channels
            sepia_img = np.stack([sepia_r, sepia_g, sepia_b], axis=2)
            
            # Convert back to PIL Image
            self.image = Image.fromarray(sepia_img)
            
        except Exception as e:
            self.logger.error(f"Error applying sepia: {str(e)}")
            raise
            
    # Artistic Effects
            
    def _apply_pencil_sketch(self, amount):
        """Apply pencil sketch effect to the image"""
        try:
            if amount <= 0:
                return
                
            # Convert to OpenCV format
            img_array = np.array(self.image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Create pencil sketch
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Detect edges
            edges = cv2.Canny(blur, 50, 150)
            
            # Invert edges
            edges = 255 - edges
            
            # Create sketch by combining edges with grayscale
            sketch = cv2.divide(gray, blur, scale=256.0)
            
            # Combine original and sketch based on amount
            strength = amount / 100.0
            
            # Create color sketch
            if strength < 0.5:
                # Blend between original and color pencil effect
                color_sketch = cv2.applyColorMap(sketch, cv2.COLORMAP_BONE)
                result = cv2.addWeighted(img_bgr, 1 - strength * 2, color_sketch, strength * 2, 0)
            else:
                # Blend between color pencil and pure sketch
                pure_strength = (strength - 0.5) * 2
                color_sketch = cv2.applyColorMap(sketch, cv2.COLORMAP_BONE)
                edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                result = cv2.addWeighted(color_sketch, 1 - pure_strength, edges_bgr, pure_strength, 0)
            
            # Convert back to RGB and PIL
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            self.image = Image.fromarray(result_rgb)
            
        except Exception as e:
            self.logger.error(f"Error applying pencil sketch: {str(e)}")
            raise
            
    def _apply_cartoon(self, amount):
        """Apply cartoon effect to the image"""
        try:
            if amount <= 0:
                return
                
            # Convert to OpenCV format
            img_array = np.array(self.image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Calculate edge mask
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                cv2.THRESH_BINARY, 9, 8
            )
            
            # Apply bilateral filter for cartoon-like effect
            num_iters = 1 + int((amount / 100.0) * 6)  # More iterations for stronger effect
            color = img_bgr
            for _ in range(num_iters):
                color = cv2.bilateralFilter(color, 9, 9, 7)
            
            # Combine edges with filtered image
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            
            # Adjust color saturation
            hsv = cv2.cvtColor(cartoon, cv2.COLOR_BGR2HSV)
            hsv[:,:,1] = cv2.add(hsv[:,:,1], int(amount / 2))
            cartoon = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            # Blend with original based on amount for smoother transition
            strength = amount / 100.0
            if strength < 1.0:
                result = cv2.addWeighted(img_bgr, 1 - strength, cartoon, strength, 0)
            else:
                result = cartoon
            
            # Convert back to RGB and PIL
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            self.image = Image.fromarray(result_rgb)
            
        except Exception as e:
            self.logger.error(f"Error applying cartoon effect: {str(e)}")
            raise
            
    def _apply_watercolor(self, amount):
        """Apply watercolor effect to the image"""
        try:
            if amount <= 0:
                return
                
            # Convert to OpenCV format
            img_array = np.array(self.image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Apply bilateral filter for initial smoothing
            bilateral1 = cv2.bilateralFilter(img_bgr, 9, 75, 75)
            
            # Apply median blur to further remove details
            median = cv2.medianBlur(bilateral1, 5)
            
            # Apply bilateral filter again
            bilateral2 = cv2.bilateralFilter(median, 9, 75, 75)
            
            # Create edge-aware mask
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                cv2.THRESH_BINARY, 9, 2
            )
            edges = cv2.bitwise_not(edges)
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            # Overlay edges on watercolor effect
            watercolor = cv2.addWeighted(bilateral2, 0.9, edges_bgr, 0.1, 0)
            
            # Adjust color saturation
            hsv = cv2.cvtColor(watercolor, cv2.COLOR_BGR2HSV)
            hsv[:,:,1] = cv2.multiply(hsv[:,:,1], 1.2)
            watercolor = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            # Blend with original based on amount
            strength = amount / 100.0
            if strength < 1.0:
                result = cv2.addWeighted(img_bgr, 1 - strength, watercolor, strength, 0)
            else:
                result = watercolor
            
            # Convert back to RGB and PIL
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            self.image = Image.fromarray(result_rgb)
            
        except Exception as e:
            self.logger.error(f"Error applying watercolor effect: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        app = ImageEditor()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)