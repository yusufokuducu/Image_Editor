"""
Image effect processing functions including filters and effects
"""
import threading
import time
import json
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np
from image_editor_app.utils.image_effects import *
from image_editor_app.utils.advanced_effects import *

def apply_filter(self, filter_name):
    """Apply a basic filter to the current image"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    self.show_status(f"{filter_name} filtresi uygulanıyor...")
    
    try:
        # Basic filters apply immediately (no preview)
        if filter_name == "blur":
            result = self.current_image.filter(ImageFilter.GaussianBlur(radius=self.effect_params[filter_name]["radius"]))
        elif filter_name == "sharpen":
            # Use UnsharpMask for better sharpening
            result = self.current_image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150))
        elif filter_name == "contour":
            result = self.current_image.filter(ImageFilter.CONTOUR)
        elif filter_name == "emboss":
            result = self.current_image.filter(ImageFilter.EMBOSS)
        elif filter_name == "bw":
            # Use L mode for better black and white conversion
            result = ImageOps.grayscale(self.current_image)
            # Convert back to RGB mode for consistency
            result = result.convert("RGB")
        elif filter_name == "invert":
            result = ImageOps.invert(self.current_image)
        else:
            self.show_status(f"Bilinmeyen filtre: {filter_name}")
            return
        
        # Apply the result
        self.current_image = result
        self.display_image(self.current_image)
        self.show_status(f"{filter_name} filtresi uygulandı")
        
    except Exception as e:
        self.show_status(f"Filtre uygulama hatası: {str(e)}")

def apply_advanced_filter(self, filter_name):
    """Show controls for advanced filter"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    # Show appropriate effect controls
    self.show_effect_controls(filter_name)
    self.show_status(f"{filter_name} efekti için ayarları yapın")

def toggle_preview(self):
    """Toggle effect preview on/off"""
    if not self.current_image or not self.current_effect:
        return
    
    if self.preview_var.get():
        # Show preview
        self.preview_effect()
    else:
        # Reset to original
        self.display_image(self.current_image)

def apply_effect(self):
    """Apply the current effect permanently"""
    if not self.current_image or not self.current_effect:
        self.show_status("Uygulanacak efekt yok")
        return
    
    effect_name = self.current_effect
    self.show_status(f"{effect_name} efekti uygulanıyor...")
    
    try:
        # Process the effect
        result = self.process_effect(self.current_image)
        
        if result:
            # Update current image
            self.current_image = result
            self.display_image(self.current_image)
            
            # Hide effect controls after applying
            self.hide_all_effect_controls()
            
            self.show_status(f"{effect_name} efekti uygulandı")
        else:
            self.show_status("Efekt uygulanamadı")
    
    except Exception as e:
        self.show_status(f"Efekt uygulama hatası: {str(e)}")

def _create_cache_key(self):
    """Create a unique key for effect caching based on parameters"""
    if not self.current_effect:
        return None
    
    # Create a string of parameters for the current effect
    param_str = json.dumps(self.effect_params[self.current_effect], sort_keys=True)
    return f"{self.current_effect}_{param_str}"

def _start_loading_animation(self):
    """Start the loading animation"""
    self.processing = True
    self.processing_animation_frame = 0
    self._update_loading_animation()

def _stop_loading_animation(self):
    """Stop the loading animation"""
    self.processing = False

def _update_loading_animation(self):
    """Update the loading animation frames"""
    if not self.processing:
        return
    
    # Simple loading animation sequence
    loading_frames = ["|", "/", "—", "\\"]
    frame = loading_frames[self.processing_animation_frame % len(loading_frames)]
    
    # Update status
    if hasattr(self, 'status_label'):
        self.status_label.configure(text=f"İşleniyor {frame}")
    
    # Update frame counter
    self.processing_animation_frame += 1
    
    # Schedule next update
    if self.processing:
        self.after(100, self._update_loading_animation)

def _threaded_preview_effect(self, cache_key=None):
    """Process effect in a separate thread to prevent UI freezing"""
    if not self.current_image or not self.current_effect:
        return
    
    try:
        # Process the effect with original image
        result = self.process_effect(self.current_image)
        
        # Cache the result
        if cache_key:
            self.preview_cache[cache_key] = result
        
        # Update UI in the main thread
        self.after(10, lambda: self._update_preview_result(result))
    
    except Exception as e:
        # Show error in main thread
        self.after(10, lambda: self.show_status(f"Önizleme hatası: {str(e)}"))
    
    finally:
        # Stop loading animation
        self.after(10, self._stop_loading_animation)

def _update_preview_result(self, result_image):
    """Update the display with the preview result"""
    if result_image:
        self.display_image(result_image, update_canvas=True, reset_zoom=False)

def process_effect(self, img):
    """Process the current effect with current parameters"""
    if not img or not self.current_effect:
        return None
    
    effect_name = self.current_effect
    params = self.effect_params[effect_name]
    
    # Process the appropriate effect
    try:
        if effect_name == "sepia":
            return apply_sepia(img, intensity=params["intensity"])
        
        elif effect_name == "cartoon":
            return apply_cartoon(img, edge_intensity=params["edge_intensity"], simplify=params["simplify"])
        
        elif effect_name == "vignette":
            return apply_vignette(img, amount=params["amount"])
        
        elif effect_name == "pixelate":
            return apply_pixelate(img, pixel_size=params["pixel_size"])
        
        elif effect_name == "red_splash":
            return apply_color_splash(img, color=params["color"], intensity=params["intensity"])
        
        elif effect_name == "oil":
            return apply_oil_painting(img, brush_size=params["brush_size"], levels=params["levels"])
        
        elif effect_name == "noise":
            return apply_noise(
                img, 
                amount=params["amount"], 
                noise_type=params["noise_type"],
                channels=params["channels"]
            )
        
        else:
            self.show_status(f"Bilinmeyen efekt: {effect_name}")
            return None
    
    except Exception as e:
        self.show_status(f"Efekt işleme hatası: {str(e)}")
        return None

def preview_effect(self):
    """Show a preview of the current effect"""
    if not self.current_image or not self.current_effect:
        return
    
    # Check if preview is active
    if not hasattr(self, 'preview_var') or not self.preview_var.get():
        # If not previewing, show original
        self.display_image(self.current_image)
        return
    
    # Start loading animation
    self._start_loading_animation()
    
    # Create a cache key
    cache_key = self._create_cache_key()
    
    # Check if we have a cached result
    if cache_key in self.preview_cache:
        # Use cached result
        self._update_preview_result(self.preview_cache[cache_key])
        self._stop_loading_animation()
    else:
        # Process in a separate thread
        threading.Thread(
            target=self._threaded_preview_effect,
            args=(cache_key,),
            daemon=True
        ).start() 