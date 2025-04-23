"""
File operations for opening, saving, and loading images
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

def open_image(self):
    """Open an image file"""
    if self.processing:
        self.show_status("Lütfen mevcut işlemin tamamlanmasını bekleyin")
        return
    
    # Ask user to select an image file
    file_types = [
        ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
        ("JPEG files", "*.jpg *.jpeg"),
        ("PNG files", "*.png"),
        ("All files", "*.*")
    ]
    
    file_path = filedialog.askopenfilename(
        title="Görüntü Aç",
        filetypes=file_types
    )
    
    if not file_path:
        return  # User cancelled
    
    # Store file path and extract filename
    self.image_path = file_path
    self.filename = os.path.basename(file_path)
    
    # Show loading status
    self.show_status(f"{self.filename} yükleniyor...")
    
    # Start loading in a separate thread
    self._start_loading_animation()
    threading.Thread(
        target=self._threaded_load_image,
        args=(file_path,),
        daemon=True
    ).start()

def _threaded_load_image(self, file_path):
    """Load image in a background thread to avoid freezing the UI"""
    try:
        # Load the image
        img = Image.open(file_path)
        
        # Convert to RGB if necessary (to handle RGBA, CMYK etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Schedule UI update in the main thread
        self.after(10, lambda: self._finalize_image_loading(img))
    
    except Exception as e:
        # Handle errors in the main thread
        self.after(10, lambda: self.show_status(f"Görüntü yükleme hatası: {str(e)}"))
        self.after(10, self._stop_loading_animation)

def _finalize_image_loading(self, img):
    """Finalize image loading in the main thread"""
    try:
        # Store original and working images
        self.original_image = img
        self.current_image = img.copy()
        
        # Display the image
        self.display_image(img, reset_zoom=True)
        
        # Update status
        self.show_status(f"{self.filename} yüklendi")
        
        # Clear preview cache
        self.preview_cache.clear()
    
    except Exception as e:
        self.show_status(f"Görüntü işleme hatası: {str(e)}")
    
    finally:
        self._stop_loading_animation()

def save_image(self):
    """Save the current image"""
    if not self.current_image:
        self.show_status("Kaydetmek için önce bir görüntü açmalısınız")
        return
    
    if self.processing:
        self.show_status("Lütfen mevcut işlemin tamamlanmasını bekleyin")
        return
    
    # Get suggested filename
    suggested_name = "edited_" + (self.filename if self.filename else "image.jpg")
    
    # Ask user for save location and format
    file_types = [
        ("JPEG files", "*.jpg"),
        ("PNG files", "*.png"),
        ("BMP files", "*.bmp"),
        ("All files", "*.*")
    ]
    
    save_path = filedialog.asksaveasfilename(
        title="Görüntüyü Kaydet",
        defaultextension=".jpg",
        initialfile=suggested_name,
        filetypes=file_types
    )
    
    if not save_path:
        return  # User cancelled
    
    try:
        # Save the image
        self.current_image.save(save_path)
        
        # Update status
        self.show_status(f"Görüntü kaydedildi: {os.path.basename(save_path)}")
    
    except Exception as e:
        self.show_status(f"Kaydetme hatası: {str(e)}")

def reset_image(self):
    """Reset the image to its original state"""
    if not self.original_image:
        self.show_status("Sıfırlamak için önce bir görüntü açmalısınız")
        return
    
    if self.processing:
        self.show_status("Lütfen mevcut işlemin tamamlanmasını bekleyin")
        return
    
    # Reset to original
    self.current_image = self.original_image.copy()
    
    # Hide any open effect controls
    self.hide_all_effect_controls()
    
    # Update display
    self.display_image(self.current_image, reset_zoom=True)
    
    # Update status
    self.show_status("Görüntü orijinal haline sıfırlandı")
    
    # Clear preview cache
    self.preview_cache.clear() 