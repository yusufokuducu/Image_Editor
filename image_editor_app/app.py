"""
Main Image Editor Application
"""
import os
import gc
import time
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
import numpy as np
import cv2

# Import our modules
from image_editor_app.utils.constants import *
from image_editor_app.utils.image_effects import *
from image_editor_app.widgets.tooltip import ToolTip
from image_editor_app.widgets.toggle_button import ToggleButton
from image_editor_app.widgets.effect_intensity import EffectIntensityFrame

# Advanced filters ve app_icon modülleri artık utils içerisine taşınmalı
from image_editor_app.utils.advanced_effects import *

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "system", "dark" veya "light" - Koyu moda ayarlandı
ctk.set_default_color_theme("dark-blue")  # "blue", "green", "dark-blue" - Koyu mavi temaya güncellendi

class ImageEditor(ctk.CTk):
    """Pro Image Editor application main class"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Pro Image Editor")
        self.geometry("1300x800")
        self.minsize(1000, 700)
        
        # Set icon
        self.set_app_icon()
        
        # Variables
        self.current_image = None
        self.original_image = None
        self.working_image = None
        self.image_path = None
        self.filename = None
        self.current_effect = None
        self.last_edited_time = None  # Son düzenleme zamanı
        
        # Performans iyileştirmeleri için önbellek ve işlem durumu değişkenleri
        self.preview_cache = {}  # Önizleme sonuçlarını önbelleğe almak için
        self.processing = False  # İşlem durumunu izlemek için
        self.processing_animation_frame = 0  # Yükleniyor animasyonu için
        
        self.effect_params = {
            # Gelişmiş filtreler
            "sepia": {"intensity": 1.0},
            "cartoon": {"edge_intensity": 3, "simplify": 5},
            "vignette": {"amount": 0.5},
            "pixelate": {"pixel_size": 10},
            "red_splash": {"intensity": 1.0, "color": "red"},
            "oil": {"brush_size": 3, "levels": 8},
            "noise": {"amount": 0.5},
            # Temel filtreler
            "blur": {"radius": 2.0},
            "sharpen": {"intensity": 1.0},
            "contour": {"intensity": 1.0},
            "emboss": {"intensity": 1.0},
            "bw": {"threshold": 128},
            "invert": {"intensity": 1.0}
        }
        
        # Create UI
        self.create_ui()
        
        # Effect intensity controls (created hidden initially)
        self.create_effect_controls()
        
        # Effect control frame'ini gizle, ancak henüz hide_effect_controls() metodu tanımlanmadı
        if hasattr(self, 'effect_control_frame'):
            self.effect_control_frame.grid_forget() 
            self.current_effect = None
            
        # Uygulamanın hazır olduğunu göster
        self.after(500, lambda: self.show_status("Uygulama hazır. Görüntü açmak için 'Dosya Aç' düğmesine tıklayın."))
    
    def set_app_icon(self):
        """Set the application icon"""
        icon_path = os.path.join('resources', 'app_icon.png')
        # Check if icon exists, create if it doesn't
        if not os.path.exists(icon_path):
            from image_editor_app.utils.app_icon import create_app_icon
            icon_path = create_app_icon()
        
        # Load the icon
        icon_image = Image.open(icon_path)
        # Convert to PhotoImage
        self.icon_photo = ImageTk.PhotoImage(icon_image)
        # Set the window icon
        self.iconphoto(True, self.icon_photo)
    
    def create_ui(self):
        """Create the main user interface"""
        # Ana çerçeve düzeni - düzgün ölçekleme için ağırlık kullan
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)
        self.grid_rowconfigure(0, weight=1)
        
        # Sol panel (Sidebar) oluştur
        self.create_sidebar()
        
        # Ana içerik alanı (resim tuvali) oluştur
        self.create_main_view()
        
        # Durum çubuğu oluştur
        self.create_status_bar()
    
    # Import other methods from separate files
    from image_editor_app.ui.sidebar import create_sidebar, create_section, create_collapsible_section, toggle_filter_tab, _create_basic_filters, _create_advanced_filters
    from image_editor_app.ui.main_view import create_main_view, create_status_bar
    from image_editor_app.ui.effects import (create_effect_controls, 
                                           hide_all_effect_controls,
                                           show_effect_controls, 
                                           add_preview_controls,
                                           update_effect_param)
    
    from image_editor_app.core.file_operations import (open_image, 
                                                     _threaded_load_image,
                                                     _finalize_image_loading,
                                                     save_image,
                                                     reset_image)
    
    from image_editor_app.core.image_display import (display_image,
                                                   update_canvas_size,
                                                   start_pan,
                                                   pan_image,
                                                   zoom_image)
    
    from image_editor_app.core.effect_processing import (apply_filter,
                                                       apply_advanced_filter,
                                                       toggle_preview,
                                                       apply_effect,
                                                       _create_cache_key,
                                                       _start_loading_animation,
                                                       _stop_loading_animation,
                                                       _update_loading_animation,
                                                       _threaded_preview_effect,
                                                       _update_preview_result,
                                                       process_effect,
                                                       preview_effect)
    
    from image_editor_app.core.basic_adjustments import (update_brightness,
                                                       update_contrast,
                                                       update_saturation,
                                                       rotate_image,
                                                       flip_image)
    
    def show_status(self, message):
        """Durum çubuğu mesajını güncelle"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            
            # Durum mesajını 5 saniye sonra temizle
            self.after(5000, lambda: self.status_label.configure(text="Hazır") if self.status_label.cget("text") == message else None) 