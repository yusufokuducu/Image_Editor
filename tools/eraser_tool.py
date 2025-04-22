"""
Eraser Tool Module
Provides eraser functionality by extending the BrushTool.
"""

import logging
import numpy as np
from typing import Tuple, Dict, Any, List, Optional

from tools.brush_tool import BrushTool

logger = logging.getLogger("Image_Editor.EraserTool")

class EraserTool(BrushTool):
    """
    Eraser tool for clearing pixels from the image.
    Extends the BrushTool with eraser-specific behavior.
    """
    
    def __init__(self, app_state):
        """Initialize the eraser tool."""
        super().__init__(app_state)
        self.name = "eraser"
        
        # Initialize settings
        self.init_settings()
        
        logger.info("EraserTool initialized")
    
    def init_settings(self):
        """Initialize eraser-specific settings."""
        # Get base brush settings
        self.settings = self.app_state.tool_settings.get("eraser_tool", {})
        
        # Use defaults if not set
        if not self.settings:
            self.settings = {
                "size": 20,
                "hardness": 0.8,
                "opacity": 1.0,
                "flow": 1.0,
                "spacing": 0.1
            }
            
            # Store in app state
            self.app_state.tool_settings["eraser_tool"] = self.settings
            
    def activate(self, canvas=None):
        """Activate the eraser tool."""
        super().activate(canvas)
        logger.info("Eraser tool activated")
    
    def _stamp_brush(self, image: np.ndarray, x: int, y: int, 
                    brush_stamp: np.ndarray, color: Tuple[int, int, int], 
                    opacity: float):
        """
        Apply an eraser stamp to the image at the specified position.
        
        Args:
            image: Image to apply the stamp to
            x, y: Position to center the stamp at
            brush_stamp: Brush stamp alpha mask
            color: RGB color tuple (not used for eraser)
            opacity: Opacity of the eraser stroke (0.0-1.0)
        """
        # Boundary checks - early return if coordinates are outside image
        if x < 0 or y < 0 or x >= image.shape[1] or y >= image.shape[0]:
            return
            
        # Get the size of the brush stamp
        stamp_height, stamp_width = brush_stamp.shape[:2]
        
        # Calculate the top-left position for the stamp
        center_x = x
        center_y = y
        left = max(0, center_x - stamp_width // 2)
        top = max(0, center_y - stamp_height // 2)
        right = min(image.shape[1], center_x + (stamp_width - stamp_width // 2))
        bottom = min(image.shape[0], center_y + (stamp_height - stamp_height // 2))
        
        # Calculate corresponding region in the stamp
        stamp_left = max(0, (stamp_width // 2) - center_x)
        stamp_top = max(0, (stamp_height // 2) - center_y)
        stamp_right = stamp_width - max(0, (center_x + (stamp_width - stamp_width // 2)) - image.shape[1])
        stamp_bottom = stamp_height - max(0, (center_y + (stamp_height - stamp_height // 2)) - image.shape[0])
        
        # Ensure we have valid regions
        if left >= right or top >= bottom or stamp_left >= stamp_right or stamp_top >= stamp_bottom:
            return  # Nothing to do
        
        # Get the target regions
        img_region = image[top:bottom, left:right]
        stamp_region = brush_stamp[stamp_top:stamp_bottom, stamp_left:stamp_right]
        
        # Safety check: ensure regions have same dimensions
        if img_region.shape[:2] != stamp_region.shape[:2]:
            # Resize stamp region to match image region
            h, w = img_region.shape[:2]
            if h <= 0 or w <= 0:  # Additional safety check
                return
                
            # Create new stamp region with matching dimensions
            new_stamp = np.zeros((h, w), dtype=np.float32)
            # Copy what we can from the original stamp
            copy_h = min(h, stamp_region.shape[0])
            copy_w = min(w, stamp_region.shape[1])
            new_stamp[:copy_h, :copy_w] = stamp_region[:copy_h, :copy_w]
            stamp_region = new_stamp
            
        # Handle RGBA vs RGB images differently
        if image.shape[2] == 4:  # RGBA
            # Apply the eraser with opacity - only affect alpha channel
            eraser_alpha = stamp_region * opacity
            
            # Create mask of non-zero alpha values for efficient processing
            eraser_mask = eraser_alpha > 0.001
            
            if np.any(eraser_mask):
                # Eraser reduces alpha only where mask is active
                img_alpha = img_region[:, :, 3:4].astype(np.float32) / 255.0
                new_alpha = img_alpha.copy()
                
                # Apply eraser only to masked pixels
                new_alpha[eraser_mask] = img_alpha[eraser_mask] * (1.0 - eraser_alpha[eraser_mask, np.newaxis])
                
                # Update alpha channel with new values
                img_region[:, :, 3] = np.clip(new_alpha[:, :, 0] * 255, 0, 255).astype(np.uint8)
            
        else:  # RGB image - blend with white or background
            # Apply stamp with opacity
            eraser_alpha = stamp_region[:, :, np.newaxis] * opacity
            
            # Create mask of non-zero alpha values
            eraser_mask = (eraser_alpha > 0.001).any(axis=2)
            
            if np.any(eraser_mask):
                # For RGB, blend with white where eraser is active
                white_color = np.ones_like(img_region) * 255
                
                # Process only pixels that need changing
                blended = img_region.copy()
                blended[eraser_mask] = (
                    img_region[eraser_mask] * (1.0 - eraser_alpha[eraser_mask]) + 
                    white_color[eraser_mask] * eraser_alpha[eraser_mask]
                ).astype(np.uint8)
                
                # Update the image region
                image[top:bottom, left:right] = blended
    
    def _commit_stroke(self):
        """Commit the eraser stroke to the active layer and create a history state."""
        if not self.canvas:
            return
            
        # Get the active layer
        layer_manager = self.canvas.main_window.layer_manager
        if not layer_manager:
            return
            
        layer = layer_manager.get_active_layer()
        if not layer:
            return
            
        # Create history state
        self.app_state.add_history_state(
            "Eraser Stroke",
            {
                "layer_index": layer_manager.active_layer_index,
                "previous_image": layer.image_data.copy() if hasattr(layer, 'image_data') and layer.image_data is not None else None
            }
        )
        
        # Update the canvas display
        if self.canvas.main_window:
            self.canvas.main_window.refresh_view()
            
        logger.debug("Committed eraser stroke")

    def get_cursor(self) -> str:
        """
        Get the cursor to use when this tool is active.
        
        Returns:
            Cursor name
        """
        return "crosshair"  # Using crosshair for precise erasing 