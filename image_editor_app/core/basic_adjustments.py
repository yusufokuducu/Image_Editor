"""
Basic image adjustment methods like brightness, contrast, rotation, etc.
"""
from PIL import ImageEnhance, ImageOps

def update_brightness(self, value):
    """Adjust image brightness with preview"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    try:
        # Store the adjustment factor
        self.effect_params["brightness"] = {"value": value}
        
        # Create enhancer
        enhancer = ImageEnhance.Brightness(self.current_image)
        
        # Apply enhancement
        result = enhancer.enhance(value)
        
        # Update display with preview
        self.display_image(result, reset_zoom=False)
        
        # Update status
        self.show_status(f"Parlaklık: {value:.2f}")
    
    except Exception as e:
        self.show_status(f"Parlaklık ayarlama hatası: {str(e)}")

def update_contrast(self, value):
    """Adjust image contrast with preview"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    try:
        # Store the adjustment factor
        self.effect_params["contrast"] = {"value": value}
        
        # Create enhancer
        enhancer = ImageEnhance.Contrast(self.current_image)
        
        # Apply enhancement
        result = enhancer.enhance(value)
        
        # Update display with preview
        self.display_image(result, reset_zoom=False)
        
        # Update status
        self.show_status(f"Kontrast: {value:.2f}")
    
    except Exception as e:
        self.show_status(f"Kontrast ayarlama hatası: {str(e)}")

def update_saturation(self, value):
    """Adjust image saturation with preview"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    try:
        # Store the adjustment factor
        self.effect_params["saturation"] = {"value": value}
        
        # Create enhancer
        enhancer = ImageEnhance.Color(self.current_image)
        
        # Apply enhancement
        result = enhancer.enhance(value)
        
        # Update display with preview
        self.display_image(result, reset_zoom=False)
        
        # Update status
        self.show_status(f"Doygunluk: {value:.2f}")
    
    except Exception as e:
        self.show_status(f"Doygunluk ayarlama hatası: {str(e)}")

def rotate_image(self, direction):
    """Rotate the image 90 degrees in the specified direction"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    try:
        # Determine rotation angle
        angle = -90 if direction == "right" else 90
        
        # Rotate image
        rotated = self.current_image.rotate(angle, expand=True)
        
        # Update current image
        self.current_image = rotated
        
        # Update display
        self.display_image(self.current_image, reset_zoom=True)
        
        # Update status
        direction_text = "sağa" if direction == "right" else "sola"
        self.show_status(f"Görüntü {direction_text} döndürüldü")
        
        # Clear preview cache since image dimensions changed
        self.preview_cache.clear()
    
    except Exception as e:
        self.show_status(f"Döndürme hatası: {str(e)}")

def flip_image(self, direction):
    """Flip the image in the specified direction"""
    if not self.current_image:
        self.show_status("Önce bir görüntü açmalısınız")
        return
    
    try:
        # Flip image
        if direction == "horizontal":
            flipped = ImageOps.mirror(self.current_image)
            direction_text = "yatay"
        else:  # vertical
            flipped = ImageOps.flip(self.current_image)
            direction_text = "dikey"
        
        # Update current image
        self.current_image = flipped
        
        # Update display
        self.display_image(self.current_image)
        
        # Update status
        self.show_status(f"Görüntü {direction_text} çevrildi")
        
        # Clear preview cache
        self.preview_cache.clear()
    
    except Exception as e:
        self.show_status(f"Çevirme hatası: {str(e)}") 