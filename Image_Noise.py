import sys
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import customtkinter as ctk
from customtkinter import filedialog
import io
import logging
from typing import Dict, Optional
import gc
from tkinter import messagebox
import time
import threading

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
    Image Editor application for applying various effects and filters to images.
    Supports multiple image formats and provides real-time preview of effects.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("Image_Noise")
        
        # Initialize image variables with type hints
        self.image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.display_photo: Optional[ctk.CTkImage] = None
        
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
        
        # Initialize settings with default values
        self.current_settings: Dict[str, float] = {
            'noise': 0.0,
            'transparency': 0.0,
            'contrast': 0.0,
            'sharpness': 0.0,
            'brightness': 0.0,
            'saturation': 0.0
        }
        
        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configure window
        self.title("Image Editor")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Center window on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        self.geometry(f"1400x900+{x}+{y}")
        
        # Ensure window is on top and focused
        self.lift()
        self.focus_force()
        
    def setup_ui(self):
        """Initialize and configure the user interface"""
        # Siyah-beyaz tema ayarları
        self.configure(fg_color=("#ffffff", "#000000"))
        
        # Configure main window grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Bind resize event
        self.bind('<Configure>', self.on_window_resize)

        # Create and setup sidebar with modern tasarım
        self._setup_sidebar()

        # Create main content area with modern styling
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=("#f8f8f8", "#0a0a0a"),
            corner_radius=15,
            border_width=1,
            border_color=("#d0d0d0", "#2a2a2a")
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Create top info bar with modern design
        self.info_frame = ctk.CTkFrame(
            self.main_frame,
            height=50,
            fg_color=("#f0f0f0", "#1a1a1a"),
            corner_radius=10
        )
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.info_frame.grid_columnconfigure(1, weight=1)

        # Image info labels with modern font
        self.image_info_label = ctk.CTkLabel(
            self.info_frame,
            text="No image loaded",
            font=ctk.CTkFont(family="Helvetica", size=13),
            text_color=("#1a1a1a", "#ffffff")
        )
        self.image_info_label.grid(row=0, column=0, padx=15, pady=10)
        
        self.image_size_label = ctk.CTkLabel(
            self.info_frame,
            text="Size: -",
            font=ctk.CTkFont(family="Helvetica", size=13),
            text_color=("#1a1a1a", "#ffffff")
        )
        self.image_size_label.grid(row=0, column=1, padx=15, pady=10)

        # Create image display area with modern border and shadow
        self.image_container = ctk.CTkFrame(
            self.main_frame,
            fg_color=("#f0f0f0", "#0f0f0f"),
            corner_radius=15,
            border_width=1,
            border_color=("#d0d0d0", "#2a2a2a")
        )
        self.image_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.image_container.grid_columnconfigure(0, weight=1)
        self.image_container.grid_rowconfigure(0, weight=1)

        # Inner frame for image with subtle shadow effect
        self.image_frame = ctk.CTkFrame(
            self.image_container,
            fg_color=("#e8e8e8", "#151515"),
            corner_radius=10
        )
        self.image_frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)

        # Modern image label with icon
        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="📸 Drag & Drop or Click 'Open Image' to Start",
            font=ctk.CTkFont(family="Helvetica", size=16),
            corner_radius=8,
            fg_color=("#e0e0e0", "#1a1a1a"),
            text_color=("#1a1a1a", "#ffffff")
        )
        self.image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Create bottom control panel with modern design
        self.bottom_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=("#f0f0f0", "#1a1a1a"),
            corner_radius=10
        )
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Setup controls in the bottom frame
        self._setup_controls()

    def _setup_sidebar(self):
        """Setup the sidebar with modern design"""
        # Create sidebar frame with gradient effect
        self.sidebar_frame = ctk.CTkFrame(
            self,
            width=280,
            corner_radius=15,
            fg_color=("#f0f0f0", "#0a0a0a"),
            border_width=1,
            border_color=("#d0d0d0", "#2a2a2a")
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(15, 0), pady=15)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # Modern app title and logo
        title_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(30, 15), sticky="ew")

        self.logo_label = ctk.CTkLabel(
            title_frame,
            text="Image Editor",
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"),
            text_color=("#1a1a1a", "#ffffff")
        )
        self.logo_label.pack(pady=5)
        
        version_label = ctk.CTkLabel(
            title_frame,
            text="Simple Edition",
            font=ctk.CTkFont(family="Helvetica", size=12),
            text_color=("#4a4a4a", "#b0b0b0")
        )
        version_label.pack()

        # Modern separator
        self.separator1 = ctk.CTkFrame(
            self.sidebar_frame,
            height=2,
            fg_color=("#d0d0d0", "#2a2a2a")
        )
        self.separator1.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 25))

        # Modern action buttons with monochrome colors
        button_configs = [
            {
                "text": "  Open Image",
                "command": self.open_image,
                "icon": "📂",
                "row": 2,
                "color": ("#2a2a2a", "#ffffff")
            },
            {
                "text": "  Save Image",
                "command": self.save_image,
                "icon": "💾",
                "row": 3,
                "color": ("#2a2a2a", "#ffffff")
            },
            {
                "text": "  Reset Effects",
                "command": self.reset_effects,
                "icon": "🔄",
                "row": 4,
                "color": ("#2a2a2a", "#ffffff")
            }
        ]

        for config in button_configs:
            button_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
            button_frame.grid(row=config["row"], column=0, padx=20, pady=5, sticky="ew")

            btn = ctk.CTkButton(
                button_frame,
                text=f"{config['icon']}{config['text']}",
                command=config["command"],
                height=45,
                corner_radius=10,
                fg_color=config["color"],
                hover_color=("#4a4a4a", "#b0b0b0"),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("#ffffff", "#000000")  # Ters renk kontrastı
            )
            btn.pack(fill="x", expand=True, padx=5)

        # Bottom separator
        self.separator2 = ctk.CTkFrame(
            self.sidebar_frame,
            height=2,
            fg_color=("#d0d0d0", "#2a2a2a")
        )
        self.separator2.grid(row=9, column=0, sticky="ew", padx=25, pady=25)

        # Modern info section
        self.info_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Image Editor v2.0\n© 2024 All rights reserved",
            font=ctk.CTkFont(family="Helvetica", size=12),
            text_color=("#4a4a4a", "#b0b0b0")
        )
        self.info_label.grid(row=10, column=0, padx=20, pady=15, sticky="s")

    def _setup_controls(self):
        """Setup the control panel with modern sliders"""
        # Main controls container
        self.controls_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", padx=10, pady=10)

        # Effect control groups
        self.sliders = {}
        slider_groups = [
            {
                "name": "Basic Adjustments",
                "controls": [
                    ("brightness", "Brightness", ""),
                    ("contrast", "Contrast", ""),
                    ("saturation", "Saturation", "")
                ]
            },
            {
                "name": "Effects",
                "controls": [
                    ("sharpness", "Sharpness", ""),
                    ("noise", "Noise", "")
                ]
            }
        ]

        for group_idx, group in enumerate(slider_groups):
            # Group frame
            group_frame = ctk.CTkFrame(self.controls_frame, fg_color=("gray85", "gray20"))
            group_frame.grid(row=0, column=group_idx, padx=10, pady=5, sticky="nsew")

            # Group title
            ctk.CTkLabel(
                group_frame,
                text=group["name"],
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(padx=10, pady=5)

            # Controls
            for control_idx, (param, label, icon) in enumerate(group["controls"]):
                control_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
                control_frame.pack(fill="x", padx=10, pady=2)

                # Icon and label
                label_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
                label_frame.pack(side="left", padx=(5, 10))

                ctk.CTkLabel(label_frame, text=icon, font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 5))
                ctk.CTkLabel(label_frame, text=label, font=("Helvetica", 12)).pack(side="left")

                # Slider
                slider = ctk.CTkSlider(
                    control_frame,
                    from_=-100,
                    to=100,
                    number_of_steps=200,
                    command=lambda value, p=param: self.debounced_update(p, value),
                    width=200,
                    height=16,
                    button_color=("gray60", "gray40"),
                    button_hover_color=("gray50", "gray30")
                )
                slider.pack(side="right", padx=10, pady=5)
                slider.set(0)
                self.sliders[param] = slider

    def update_image_info(self):
        """Update the image information display"""
        if self.image:
            size = self.image.size
            mode = self.image.mode
            self.image_info_label.configure(text=f"Format: {mode}")
            self.image_size_label.configure(text=f"Size: {size[0]}x{size[1]}px")
        else:
            self.image_info_label.configure(text="No image loaded")
            self.image_size_label.configure(text="Size: -")

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

    def save_image(self):
        """Save the processed image"""
        if not self.image:
            self.show_error("No image to save")
            return
            
        try:
            # Bring window to front
            self.lift()
            self.focus_force()
            
            file_types = [
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
            filename = filedialog.asksaveasfilename(
                title="Save Image As",
                filetypes=file_types,
                defaultextension=".png",
                parent=self  # Set parent window
            )
            
            if filename:
                self.logger.info(f"Saving image to: {filename}")
                self.image.save(filename)
                
                # Bring window back to front after saving
                self.after(100, lambda: (self.lift(), self.focus_force()))
                
        except Exception as e:
            self.logger.error(f"Error saving image: {str(e)}")
            self.show_error(f"Error saving image: {str(e)}")
            
    def debounced_update(self, param, value):
        """Update with debouncing to avoid too frequent updates"""
        current_time = time.time()
        self.current_settings[param] = float(value)
        
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
            
    def process_image(self, param: str, value: float):
        """Update image with new effect parameters"""
        if self.original_image is None:
            return
            
        try:
            self.current_settings[param] = float(value)
            
            # Add to history only if this is a new edit (not during undo/redo operations)
            if param != "_history_update":
                self._add_to_history()
            
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
                self.apply_effects()
                self.update_image_display()
        except Exception as e:
            self.logger.error(f"Error updating image: {str(e)}")
            self.show_error("Error applying effects")
            
    # Alias for backward compatibility
    update_image = process_image

    def apply_effects(self):
        """Apply all effects to the image"""
        if self.original_image is None:
            return
            
        try:
            # Start with a fresh copy of the original image
            self.image = self.original_image.copy()
            
            # Apply effects in optimal order
            if self.current_settings['brightness'] != 0:
                enhancer = ImageEnhance.Brightness(self.image)
                self.image = enhancer.enhance(1 + self.current_settings['brightness'] / 100)
                
            if self.current_settings['contrast'] != 0:
                enhancer = ImageEnhance.Contrast(self.image)
                self.image = enhancer.enhance(1 + self.current_settings['contrast'] / 100)
                
            if self.current_settings['saturation'] != 0:
                enhancer = ImageEnhance.Color(self.image)
                self.image = enhancer.enhance(1 + self.current_settings['saturation'] / 100)
                
            if self.current_settings['sharpness'] != 0:
                enhancer = ImageEnhance.Sharpness(self.image)
                self.image = enhancer.enhance(1 + self.current_settings['sharpness'] / 100)
                
            # Apply noise if needed
            if self.current_settings['noise'] != 0:
                self._apply_noise()
                
        except Exception as e:
            self.logger.error(f"Error applying effects: {str(e)}")
            self.show_error("Error applying effects")
            
    def _apply_noise(self):
        """Apply noise effect to the image"""
        try:
            img_array = np.array(self.image)
            noise = np.random.normal(0, abs(self.current_settings['noise']), img_array.shape)
            noisy_img = img_array + noise
            noisy_img = np.clip(noisy_img, 0, 255).astype(np.uint8)
            self.image = Image.fromarray(noisy_img)
        except Exception as e:
            self.logger.error(f"Error applying noise: {str(e)}")
            raise
            
    def update_image_display(self):
        """Update the display with the current image"""
        if not self.image:
            self.logger.warning("No image to display.")
            return

        try:
            # Get the frame dimensions, accounting for padding
            frame_width = self.image_frame.winfo_width() - 40  # Padding
            frame_height = self.image_frame.winfo_height() - 40  # Padding

            # If window is not yet properly sized, use default dimensions
            if frame_width <= 1 or frame_height <= 1:
                frame_width = 1000  # Increased default width
                frame_height = 800  # Increased default height

            # Get original image size
            img_width, img_height = self.image.size

            # Calculate scaling factors
            width_ratio = frame_width / img_width
            height_ratio = frame_height / img_height

            # Use the smaller ratio to maintain aspect ratio while fitting in frame
            scale_factor = min(width_ratio, height_ratio)

            # Calculate new dimensions
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)

            # Ensure minimum size
            min_size = 400
            if new_width < min_size or new_height < min_size:
                if img_width > img_height:
                    new_width = min_size
                    new_height = int(min_size * (img_height / img_width))
                else:
                    new_height = min_size
                    new_width = int(min_size * (img_width / img_height))

            # Create a copy and resize
            display_image = self.image.copy()
            display_image = display_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to RGB mode
            if display_image.mode != 'RGB':
                display_image = display_image.convert('RGB')

            # Clean up old photo if exists
            if hasattr(self, 'display_photo') and self.display_photo:
                del self.display_photo
                gc.collect()

            # Create new CTkImage with explicit size
            self.display_photo = ctk.CTkImage(
                light_image=display_image,
                dark_image=display_image,
                size=(new_width, new_height)
            )

            # Update label
            if self.image_label:
                self.image_label.configure(image=self.display_photo, text="")
                self.logger.info(f"Image displayed successfully: {new_width}x{new_height}")

            # Clean up
            del display_image
            gc.collect()

        except Exception as e:
            self.logger.error(f"Error updating display: {str(e)}")
            self.show_error(f"Error updating display: {str(e)}")

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

if __name__ == "__main__":
    try:
        app = ImageEditor()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}", exc_info=True)
        sys.exit(1)