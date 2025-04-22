"""
Effects Tool Module
Provides a tool for applying various image effects and adjustments.
"""

import logging
import tkinter as tk
from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import cv2
from PIL import Image, ImageTk

from tools.base_tool import BaseTool

logger = logging.getLogger("Image_Editor.EffectsTool")

class EffectsTool(BaseTool):
    """
    Tool for applying various effects and adjustments to images.
    Includes noise, grain, contrast, brightness, saturation and more.
    """
    
    def __init__(self, app_state):
        """
        Initialize the effects tool.
        
        Args:
            app_state: Application state object
        """
        super().__init__(app_state, "effects")
        
        # Canvas reference
        self.canvas = None
        
        # Temporary overlay for preview
        self.temp_overlay = None
        self.temp_overlay_id = None
        
        # Initialize settings
        self.init_settings()
        
        logger.debug("EffectsTool initialized")
    
    def init_settings(self):
        """Initialize effects tool settings."""
        # Get default settings from app state
        self.settings = self.app_state.tool_settings.get("effects_tool", {}).copy()
        
        # Set defaults if not in app state
        if not self.settings:
            self.settings = {
                "effect_type": "noise",  # noise, brightness_contrast, hue_saturation, etc.
                "noise": {
                    "amount": 25,  # 0-100
                    "type": "gaussian"  # gaussian, salt_pepper, speckle
                },
                "brightness_contrast": {
                    "brightness": 1.0,  # 0.0-2.0
                    "contrast": 1.0  # 0.0-2.0
                },
                "hue_saturation": {
                    "hue": 0.0,  # 0.0-1.0
                    "saturation": 1.0  # 0.0-2.0
                },
                "blur": {
                    "radius": 5,
                    "type": "gaussian"  # gaussian, box, median
                },
                "sharpen": {
                    "strength": 1.0  # 0.0-3.0
                },
                "threshold": {
                    "value": 127,  # 0-255
                    "max_value": 255  # 0-255
                },
                "grain": {
                    "amount": 25,  # 0-100
                    "size": 1.0,   # 0.5-3.0
                    "color": False # monochrome or color grain
                }
            }
    
    def get_cursor(self) -> str:
        """
        Get the cursor to use when this tool is active.
        
        Returns:
            Cursor name
        """
        return "crosshair"  # Using a crosshair cursor for better precision
    
    def activate(self, canvas=None):
        """
        Activate the effects tool.
        
        Args:
            canvas: The canvas to activate the tool on
        """
        self.active = True
        self.canvas = canvas or self.app_state.get_active_canvas()
        
        if self.canvas:
            self.canvas.config(cursor=self.get_cursor())
            
            # Set up event bindings (even though we don't really use them)
            self.canvas.bind("<Button-1>", self.on_mouse_down)
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<Motion>", self.on_mouse_move)
        
        logger.debug("Effects tool activated")
    
    def deactivate(self):
        """Deactivate the effects tool."""
        self.active = False
        
        # Clean up any temporary overlays
        if self.temp_overlay_id and self.canvas:
            self.canvas.delete(self.temp_overlay_id)
            self.temp_overlay_id = None
            self.temp_overlay = None
        
        # Remove event bindings
        if self.canvas:
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<Motion>")
            self.canvas = None
        
        logger.debug("Effects tool deactivated")
    
    # Implement required abstract methods from BaseTool
    def on_mouse_down(self, event):
        """
        Handle mouse button press.
        
        Args:
            event: Original event object
        """
        # Effects tool doesn't need mouse interaction
        pass
    
    def on_mouse_up(self, event):
        """
        Handle mouse button release.
        
        Args:
            event: Original event object
        """
        # Effects tool doesn't need mouse interaction
        pass
    
    def on_mouse_drag(self, event):
        """
        Handle mouse drag.
        
        Args:
            event: Original event object
        """
        # Effects tool doesn't need mouse interaction
        pass
    
    def on_mouse_move(self, event):
        """
        Handle mouse movement.
        
        Args:
            event: Original event object
        """
        # Effects tool doesn't need mouse interaction
        pass
    
    def apply_effect(self, effect_type=None):
        """
        Apply the selected effect to the active layer.
        
        Args:
            effect_type: Optional override for the effect type
        """
        if not self.active or not self.canvas:
            return
        
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            return
        
        layer = layer_manager.get_active_layer()
        if layer is None or layer.image_data is None:
            return
        
        # Get the effect type to apply
        effect_type = effect_type or self.settings.get("effect_type", "noise")
        
        # Create a copy of the layer image
        original_image = layer.image_data.copy()
        
        # Apply the selected effect
        modified_image = self._apply_effect_to_image(original_image, effect_type)
        
        if modified_image is not None:
            # Create history state
            self.app_state.add_history_state(
                f"Apply {effect_type.replace('_', ' ').title()}",
                {
                    "layer_index": layer_manager.active_layer_index,
                    "previous_image": original_image
                }
            )
            
            # Update the layer with the modified image
            layer.image_data = modified_image
            
            # Update the canvas display
            if self.canvas.main_window:
                self.canvas.main_window.refresh_view()
                
            logger.debug(f"Applied {effect_type} effect")
    
    def preview_effect(self, effect_type=None):
        """
        Create a preview of the selected effect.
        
        Args:
            effect_type: Optional override for the effect type
        """
        if not self.active or not self.canvas:
            return
        
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager or layer_manager.active_layer_index < 0:
            return
        
        layer = layer_manager.get_active_layer()
        if layer is None or layer.image_data is None:
            return
        
        # Get the effect type to preview
        effect_type = effect_type or self.settings.get("effect_type", "noise")
        
        # For performance, use a downscaled image for preview if image is large
        original_image = layer.image_data
        height, width = original_image.shape[:2]
        max_preview_dimension = 1024  # Max dimension for preview processing
        
        # Downscale large images for preview to improve performance
        if width > max_preview_dimension or height > max_preview_dimension:
            scale_factor = min(max_preview_dimension / width, max_preview_dimension / height)
            preview_width = int(width * scale_factor)
            preview_height = int(height * scale_factor)
            
            # Use faster resize for preview
            from core.image_handler import ImageHandler
            small_image = ImageHandler.resize_image(
                original_image, preview_width, preview_height, 
                interpolation=cv2.INTER_NEAREST
            )
            
            # Apply effect to smaller image for faster processing
            self.temp_overlay = self._apply_effect_to_image(small_image, effect_type)
            
            # For display, resize back to original dimensions if needed
            if self.temp_overlay is not None:
                self.temp_overlay = ImageHandler.resize_image(
                    self.temp_overlay, width, height,
                    interpolation=cv2.INTER_LINEAR
                )
        else:
            # For smaller images, use the original size
            self.temp_overlay = self._apply_effect_to_image(original_image.copy(), effect_type)
        
        if self.temp_overlay is not None:
            # Update the preview display
            self._update_overlay_display()
    
    def clear_preview(self):
        """Clear the effect preview."""
        if self.temp_overlay_id and self.canvas:
            self.canvas.delete(self.temp_overlay_id)
            self.temp_overlay_id = None
        
        self.temp_overlay = None
        
        # Refresh the view to show the original image
        if self.canvas and self.canvas.main_window:
            self.canvas.main_window.refresh_view()
    
    def _apply_effect_to_image(self, image, effect_type):
        """
        Apply the specified effect to the image.
        
        Args:
            image: NumPy array containing the image data
            effect_type: Type of effect to apply
            
        Returns:
            Modified image as NumPy array
        """
        try:
            if effect_type == "noise":
                return self._apply_noise(image)
            elif effect_type == "grain":
                return self._apply_grain(image)
            elif effect_type == "brightness_contrast":
                return self._apply_brightness_contrast(image)
            elif effect_type == "hue_saturation":
                return self._apply_hue_saturation(image)
            elif effect_type == "blur":
                return self._apply_blur(image)
            elif effect_type == "sharpen":
                return self._apply_sharpen(image)
            elif effect_type == "threshold":
                return self._apply_threshold(image)
            else:
                logger.warning(f"Unsupported effect type: {effect_type}")
                return image
        except Exception as e:
            logger.error(f"Error applying effect {effect_type}: {str(e)}")
            return image
    
    def _apply_noise(self, image):
        """
        Apply noise to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Noisy image as NumPy array
        """
        # Get noise settings
        noise_settings = self.settings.get("noise", {})
        amount = noise_settings.get("amount", 25) / 100.0  # Convert to 0.0-1.0
        noise_type = noise_settings.get("type", "gaussian")
        
        # Make a copy of the image
        result = image.copy()
        
        if noise_type == "gaussian":
            # Apply Gaussian noise
            mean = 0
            sigma = amount * 50  # Scale to reasonable range
            
            # Generate noise for each channel and add directly
            noise = np.random.normal(mean, sigma, image.shape)
            # Convert to appropriate format for addition
            result = result.astype(np.float32)
            result = result + noise
            # Clip values to valid range
            result = np.clip(result, 0, 255).astype(np.uint8)
            
        elif noise_type == "salt_pepper":
            # Apply salt and pepper noise
            s_vs_p = 0.5  # Ratio of salt vs. pepper
            num_pixels = int(amount * image.shape[0] * image.shape[1])
            
            # Salt (white) mode
            salt_coords = [np.random.randint(0, i - 1, num_pixels) for i in image.shape[:2]]
            result[salt_coords[0], salt_coords[1], :] = 255
            
            # Pepper (black) mode
            pepper_coords = [np.random.randint(0, i - 1, num_pixels) for i in image.shape[:2]]
            result[pepper_coords[0], pepper_coords[1], :] = 0
            
        elif noise_type == "speckle":
            # Apply speckle noise (multiplicative noise)
            noise = np.random.normal(0, amount, image.shape)
            # Convert to float32 for multiplication
            result = result.astype(np.float32)
            result = result + result * noise
            result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def _apply_grain(self, image):
        """
        Apply film grain effect to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Grainy image as NumPy array
        """
        # Get grain settings
        grain_settings = self.settings.get("grain", {})
        amount = grain_settings.get("amount", 25) / 100.0  # Convert to 0.0-1.0
        size = grain_settings.get("size", 1.0)
        color_grain = grain_settings.get("color", False)
        
        # Make a copy of the image
        result = image.copy().astype(np.float32)  # Convert to float32 for calculations
        height, width = image.shape[:2]
        
        # Create grain texture
        if color_grain:
            # Color grain (create noise for each channel)
            grain = np.random.normal(0, 1, (height, width, image.shape[2]))
        else:
            # Monochrome grain (same noise for all channels)
            grain = np.random.normal(0, 1, (height, width, 1))
            grain = np.repeat(grain, image.shape[2], axis=2)
        
        # Apply blur to control grain size
        if size > 0.5:
            kernel_size = int(size * 2) * 2 + 1  # Ensure odd size
            grain = cv2.GaussianBlur(grain, (kernel_size, kernel_size), 0)
        
        # Scale grain and add to image
        grain = grain * amount * 50  # Scale amount
        
        # Add grain to image (direct addition with float32)
        result = result + grain
        
        # Clip values to valid range
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def _apply_brightness_contrast(self, image):
        """
        Apply brightness and contrast adjustment to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Adjusted image as NumPy array
        """
        # Get settings
        bc_settings = self.settings.get("brightness_contrast", {})
        brightness = bc_settings.get("brightness", 1.0)
        contrast = bc_settings.get("contrast", 1.0)
        
        # Use ImageHandler method for this operation
        from core.image_handler import ImageHandler
        return ImageHandler.adjust_brightness_contrast(image, brightness, contrast)
    
    def _apply_hue_saturation(self, image):
        """
        Apply hue and saturation adjustment to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Adjusted image as NumPy array
        """
        # Get settings
        hs_settings = self.settings.get("hue_saturation", {})
        hue = hs_settings.get("hue", 0.0)
        saturation = hs_settings.get("saturation", 1.0)
        
        # Use ImageHandler method for this operation
        from core.image_handler import ImageHandler
        return ImageHandler.adjust_hue_saturation(image, hue, saturation)
    
    def _apply_blur(self, image):
        """
        Apply blur to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Blurred image as NumPy array
        """
        # Get settings
        blur_settings = self.settings.get("blur", {})
        radius = blur_settings.get("radius", 5)
        blur_type = blur_settings.get("type", "gaussian")
        
        # Use ImageHandler method for this operation
        from core.image_handler import ImageHandler
        return ImageHandler.apply_blur(image, radius, blur_type)
    
    def _apply_sharpen(self, image):
        """
        Apply sharpening to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Sharpened image as NumPy array
        """
        # Get settings
        sharpen_settings = self.settings.get("sharpen", {})
        strength = sharpen_settings.get("strength", 1.0)
        
        # Use ImageHandler method for this operation
        from core.image_handler import ImageHandler
        return ImageHandler.apply_sharpen(image, strength)
    
    def _apply_threshold(self, image):
        """
        Apply threshold to an image.
        
        Args:
            image: NumPy array containing the image data
            
        Returns:
            Thresholded image as NumPy array
        """
        # Get settings
        threshold_settings = self.settings.get("threshold", {})
        threshold = threshold_settings.get("value", 127)
        max_value = threshold_settings.get("max_value", 255)
        
        # Use ImageHandler method for this operation
        from core.image_handler import ImageHandler
        return ImageHandler.apply_threshold(image, threshold, max_value)
    
    def _update_overlay_display(self):
        """Update the canvas to display the temporary overlay."""
        if not self.canvas or self.temp_overlay is None:
            return
        
        # Get current zoom and offset
        scale = self.app_state.view_scale
        offset_x, offset_y = self.app_state.view_offset
            
        # Only resize the display image if zoom is not 1:1
        if scale != 1.0:
            # Calculate the dimensions for the displayed image
            height, width = self.temp_overlay.shape[:2]
            display_width = int(width * scale)
            display_height = int(height * scale)
            
            # Create display version with appropriate size
            display_image = cv2.resize(
                self.temp_overlay, 
                (display_width, display_height),
                interpolation=cv2.INTER_NEAREST if scale < 1.0 else cv2.INTER_LINEAR
            )
        else:
            display_image = self.temp_overlay
            
        # Create PIL Image from numpy array
        from PIL import Image, ImageTk
        if display_image.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(display_image)
        else:  # RGB
            pil_image = Image.fromarray(display_image)
            
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(pil_image)
        
        # Keep a reference to prevent garbage collection
        self._photo_ref = photo
        
        # Display on canvas
        if self.temp_overlay_id:
            # Update existing image
            self.canvas.itemconfig(self.temp_overlay_id, image=photo)
        else:
            # Create new image on canvas
            self.temp_overlay_id = self.canvas.create_image(
                offset_x, offset_y,
                image=photo,
                anchor=tk.NW
            ) 