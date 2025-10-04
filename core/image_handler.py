# -*- coding: utf-8 -*-
"""
Handles all low-level image operations using Pillow and NumPy.

This class is responsible for loading, processing, and preparing image data
for display in the Dear PyGui texture registry.
"""

from PIL import Image, ImageEnhance, ImageDraw
import numpy as np
from . import filters

class ImageHandler:
    """Manages image data and its conversion for the UI."""
    def __init__(self):
        self.image_path = None
        self.image_pil = None  # Current image state as a Pillow object
        self.width = 0
        self.height = 0
        self.undo_stack = []
        self.redo_stack = []

    def load_image(self, path: str) -> bool:
        """Loads an image from a file path."""
        try:
            self.image_path = path
            self.image_pil = Image.open(path).convert("RGBA") # Ensure RGBA from the start
            self.width, self.height = self.image_pil.size
            
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.push_to_undo(self.image_pil.copy())

            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False

    def _get_base_image(self) -> Image.Image:
        """Returns the last committed state from the undo stack."""
        if not self.undo_stack:
            return None
        return self.undo_stack[-1].copy() # Return a copy to draw on

    def apply_brightness(self, factor: float, is_final: bool = True):
        """Applies a brightness enhancement to the image."""
        base_image = self._get_base_image()
        if not base_image:
            return
        
        enhancer = ImageEnhance.Brightness(base_image)
        self.image_pil = enhancer.enhance(factor)

        if is_final:
            self.push_to_undo(self.image_pil.copy())

    def apply_blur(self, radius: float, is_final: bool = True):
        """Applies a blur filter to the image."""
        base_image = self._get_base_image()
        if not base_image:
            return

        self.image_pil = filters.apply_blur(base_image, radius)

        if is_final:
            self.push_to_undo(self.image_pil.copy())
    
    def apply_grayscale(self, is_final: bool = True):
        """Applies a grayscale filter to the image."""
        base_image = self._get_base_image()
        if not base_image:
            return

        self.image_pil = filters.apply_grayscale(base_image)

        if is_final:
            self.push_to_undo(self.image_pil.copy())

    def resize_image(self, width: int, height: int, is_final: bool = True):
        """Resizes the image to new dimensions."""
        base_image = self._get_base_image()
        if not base_image:
            return
        
        self.image_pil = base_image.resize((width, height), Image.Resampling.LANCZOS)
        self.width = width
        self.height = height

        if is_final:
            self.push_to_undo(self.image_pil.copy())



    def get_texture_data(self):
        """Converts the current Pillow image to a format suitable for DPG textures.
        
        Returns:
            A flat list of float values (RGBA) between 0.0 and 1.0.
        """
        if not self.image_pil:
            return None
        
        # Ensure image is in RGBA format
        rgba_image = self.image_pil.convert("RGBA")
        # Convert to a NumPy array and normalize to 0-1 float values
        np_array = np.array(rgba_image, dtype=np.float32) / 255.0
        return np_array.flatten()

    def push_to_undo(self, image_state):
        """Pushes an image state onto the undo stack."""
        self.undo_stack.append(image_state)
        # A new action clears the redo stack
        self.redo_stack.clear()

    def undo(self):
        """Reverts to the previous image state."""
        if len(self.undo_stack) > 1: # At least one state to revert to
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            self.image_pil = self.undo_stack[-1].copy()
            return True
        return False

    def redo(self):
        """Re-applies an undone image state."""
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.undo_stack.append(next_state)
            self.image_pil = next_state.copy()
            return True
        return False
