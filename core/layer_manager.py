"""
Layer Manager Module
Handles the management of image layers, including blending modes, masking, and layer operations.
"""

import logging
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import cv2

logger = logging.getLogger("Image_Editor.LayerManager")

class Layer:
    """
    Class representing a single image layer.
    """
    
    def __init__(self, name: str, image_data: np.ndarray, 
                visible: bool = True, opacity: float = 1.0,
                blend_mode: str = "normal", locked: bool = False):
        """
        Initialize a new layer.
        
        Args:
            name: Layer name
            image_data: NumPy array containing the image data
            visible: Whether the layer is visible
            opacity: Layer opacity (0.0 to 1.0)
            blend_mode: Blending mode for the layer
            locked: Whether the layer is locked for editing
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.image_data = image_data.copy()
        self.visible = visible
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp to 0-1
        self.blend_mode = blend_mode
        self.locked = locked
        self.mask = None  # Layer mask (None = no mask)

    def set_mask(self, mask: Optional[np.ndarray] = None):
        """Set a layer mask (grayscale image)."""
        if mask is not None:
            # Ensure mask is grayscale and same size as layer
            if len(mask.shape) > 2 and mask.shape[2] > 1:
                mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            
            height, width = self.image_data.shape[:2]
            mask_height, mask_width = mask.shape[:2]
            
            if mask_height != height or mask_width != width:
                mask = cv2.resize(mask, (width, height))
        
        self.mask = mask

    def resize(self, width: int, height: int, interpolation: int = cv2.INTER_LANCZOS4):
        """Resize the layer to new dimensions."""
        self.image_data = cv2.resize(self.image_data, (width, height), interpolation=interpolation)
        if self.mask is not None:
            self.mask = cv2.resize(self.mask, (width, height), interpolation=interpolation)


class LayerManager:
    """
    Class to manage multiple layers, their ordering, visibility, and blending.
    """
    
    # Define supported blending modes
    BLEND_MODES = [
        "normal", "multiply", "screen", "overlay", "darken", "lighten", 
        "color_dodge", "color_burn", "hard_light", "soft_light", "difference", 
        "exclusion", "hue", "saturation", "color", "luminosity"
    ]
    
    def __init__(self, width: int, height: int):
        """
        Initialize the layer manager.
        
        Args:
            width: Canvas width
            height: Canvas height
        """
        self.layers: List[Layer] = []
        self.active_layer_index: int = -1
        self.width = width
        self.height = height
        
        logger.info(f"LayerManager initialized with canvas size {width}x{height}")
    
    def add_layer(self, layer: Layer, position: int = None) -> int:
        """
        Add a layer to the stack.
        
        Args:
            layer: Layer object to add
            position: Position in the stack (None = top)
            
        Returns:
            Index of the added layer
        """
        if position is None or position >= len(self.layers):
            self.layers.append(layer)
            position = len(self.layers) - 1
        else:
            # Insert at specific position
            self.layers.insert(position, layer)
        
        # Set as active layer
        self.active_layer_index = position
        
        logger.info(f"Added layer '{layer.name}' at position {position}")
        return position
    
    def delete_layer(self, index: int) -> bool:
        """
        Delete a layer by index.
        
        Args:
            index: Index of the layer to delete
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.layers):
            layer_name = self.layers[index].name
            del self.layers[index]
            
            # Update active layer index
            if self.active_layer_index == index:
                if len(self.layers) > 0:
                    self.active_layer_index = max(0, min(index, len(self.layers) - 1))
                else:
                    self.active_layer_index = -1
            elif self.active_layer_index > index:
                self.active_layer_index -= 1
            
            logger.info(f"Deleted layer '{layer_name}' at position {index}")
            return True
        
        logger.warning(f"Failed to delete layer at index {index}: invalid index")
        return False
    
    def move_layer(self, from_index: int, to_index: int) -> bool:
        """
        Move a layer from one position to another.
        
        Args:
            from_index: Current index of the layer
            to_index: Target index for the layer
            
        Returns:
            True if successful, False otherwise
        """
        if not (0 <= from_index < len(self.layers)):
            logger.warning(f"Invalid from_index: {from_index}")
            return False
        
        # Clamp to_index to valid range
        to_index = max(0, min(to_index, len(self.layers) - 1))
        
        if from_index == to_index:
            return True  # No change needed
        
        # Move the layer
        layer = self.layers.pop(from_index)
        self.layers.insert(to_index, layer)
        
        # Update active layer index if needed
        if self.active_layer_index == from_index:
            self.active_layer_index = to_index
        elif from_index < self.active_layer_index <= to_index:
            self.active_layer_index -= 1
        elif to_index <= self.active_layer_index < from_index:
            self.active_layer_index += 1
        
        logger.info(f"Moved layer '{layer.name}' from position {from_index} to {to_index}")
        return True
    
    def duplicate_layer(self, index: int) -> int:
        """
        Duplicate a layer.
        
        Args:
            index: Index of the layer to duplicate
            
        Returns:
            Index of the new layer, or -1 if failed
        """
        if 0 <= index < len(self.layers):
            source_layer = self.layers[index]
            new_name = f"{source_layer.name} copy"
            
            # Create a new layer with the same properties
            new_layer = Layer(
                name=new_name,
                image_data=source_layer.image_data.copy(),
                visible=source_layer.visible,
                opacity=source_layer.opacity,
                blend_mode=source_layer.blend_mode,
                locked=source_layer.locked
            )
            
            # Copy mask if it exists
            if source_layer.mask is not None:
                new_layer.mask = source_layer.mask.copy()
            
            # Add the new layer after the source layer
            new_index = self.add_layer(new_layer, index + 1)
            logger.info(f"Duplicated layer '{source_layer.name}' to '{new_name}'")
            return new_index
        
        logger.warning(f"Failed to duplicate layer at index {index}: invalid index")
        return -1
    
    def merge_layers(self, indices: List[int]) -> int:
        """
        Merge multiple layers into a single layer.
        
        Args:
            indices: List of layer indices to merge
            
        Returns:
            Index of the merged layer, or -1 if failed
        """
        # Validate indices
        if not indices or not all(0 <= i < len(self.layers) for i in indices):
            logger.warning("Invalid layer indices for merging")
            return -1
        
        # Sort indices in descending order
        sorted_indices = sorted(indices, reverse=True)
        
        # Create a composite of the selected layers
        bottom_layer_index = min(indices)
        layers_to_merge = [self.layers[i] for i in sorted_indices]
        
        # Start with a blank image
        merged_image = np.zeros(
            (self.height, self.width, 4), dtype=np.uint8
        )
        
        # Composite the layers
        for layer in reversed(layers_to_merge):
            if layer.visible and layer.opacity > 0:
                merged_image = self._blend_images(
                    merged_image, layer.image_data, 
                    layer.blend_mode, layer.opacity, layer.mask
                )
        
        # Create a new layer with the merged result
        merged_layer = Layer(
            name="Merged Layer",
            image_data=merged_image,
            visible=True,
            opacity=1.0,
            blend_mode="normal",
            locked=False
        )
        
        # Remove the merged layers (in reverse order to not mess with indices)
        for index in sorted_indices:
            self.delete_layer(index)
        
        # Add the merged layer at the position of the bottom-most layer
        merged_index = self.add_layer(merged_layer, bottom_layer_index)
        logger.info(f"Merged {len(indices)} layers into a new layer at position {merged_index}")
        
        return merged_index
    
    def set_active_layer(self, index: int) -> bool:
        """
        Set the active layer.
        
        Args:
            index: Index of the layer to set as active
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.layers):
            self.active_layer_index = index
            logger.info(f"Set active layer to '{self.layers[index].name}' at position {index}")
            return True
        
        logger.warning(f"Failed to set active layer to index {index}: invalid index")
        return False
    
    def get_active_layer(self) -> Optional[Layer]:
        """
        Get the active layer.
        
        Returns:
            Active layer or None if no active layer
        """
        if 0 <= self.active_layer_index < len(self.layers):
            return self.layers[self.active_layer_index]
        return None
    
    def resize_canvas(self, width: int, height: int, 
                     anchor: str = "center", 
                     background_color: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> None:
        """
        Resize the canvas and all layers.
        
        Args:
            width: New canvas width
            height: New canvas height
            anchor: Anchor point for resizing ("center", "top-left", etc.)
            background_color: Background color (RGBA)
        """
        old_width, old_height = self.width, self.height
        
        # Update canvas dimensions
        self.width, self.height = width, height
        
        # Calculate offsets based on anchor
        if anchor == "center":
            offset_x = (width - old_width) // 2
            offset_y = (height - old_height) // 2
        elif anchor == "top-left":
            offset_x, offset_y = 0, 0
        elif anchor == "top-right":
            offset_x, offset_y = width - old_width, 0
        elif anchor == "bottom-left":
            offset_x, offset_y = 0, height - old_height
        elif anchor == "bottom-right":
            offset_x, offset_y = width - old_width, height - old_height
        else:
            # Default to center
            offset_x = (width - old_width) // 2
            offset_y = (height - old_height) // 2
        
        # Resize each layer
        for layer in self.layers:
            # Create a new image with the desired size and background color
            new_image = np.zeros((height, width, 4), dtype=np.uint8)
            if layer.image_data.shape[2] == 4:  # RGBA
                new_image[:, :] = background_color
            else:  # RGB
                new_image[:, :, :3] = background_color[:3]
            
            # Calculate paste coordinates
            paste_x = max(0, offset_x)
            paste_y = max(0, offset_y)
            
            # Calculate source coordinates
            src_x = max(0, -offset_x)
            src_y = max(0, -offset_y)
            
            # Calculate width and height to copy
            copy_width = min(old_width - src_x, width - paste_x)
            copy_height = min(old_height - src_y, height - paste_y)
            
            if copy_width > 0 and copy_height > 0:
                source_slice = layer.image_data[src_y:src_y+copy_height, src_x:src_x+copy_width]
                new_image[paste_y:paste_y+copy_height, paste_x:paste_x+copy_width] = source_slice
            
            # Update the layer image
            layer.image_data = new_image
            
            # Update mask if present
            if layer.mask is not None:
                new_mask = np.zeros((height, width), dtype=np.uint8)
                
                if copy_width > 0 and copy_height > 0:
                    mask_slice = layer.mask[src_y:src_y+copy_height, src_x:src_x+copy_width]
                    new_mask[paste_y:paste_y+copy_height, paste_x:paste_x+copy_width] = mask_slice
                
                layer.mask = new_mask
        
        logger.info(f"Resized canvas from {old_width}x{old_height} to {width}x{height}")
    
    def render_composite(self, start_index: int = 0, end_index: int = None) -> np.ndarray:
        """
        Render a composite image from all visible layers.
        
        Args:
            start_index: Starting layer index (inclusive)
            end_index: Ending layer index (inclusive, None = last layer)
            
        Returns:
            Composite image as NumPy array
        """
        if end_index is None:
            end_index = len(self.layers) - 1
        
        # Clamp indices to valid range
        start_index = max(0, min(start_index, len(self.layers) - 1))
        end_index = max(start_index, min(end_index, len(self.layers) - 1))
        
        # Start with a transparent canvas
        result = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        # Optimization: Skip invisible layers and collect visible ones
        visible_layers = []
        for i in range(start_index, end_index + 1):
            layer = self.layers[i]
            if layer.visible and layer.opacity > 0:
                visible_layers.append((i, layer))
        
        # Skip blending if no visible layers
        if not visible_layers:
            return result
            
        # Optimization: If only one layer with 100% opacity and normal blend mode, return it directly
        if len(visible_layers) == 1 and visible_layers[0][1].opacity == 1.0 and visible_layers[0][1].blend_mode == "normal":
            layer = visible_layers[0][1]
            # Check if we need to convert RGB to RGBA
            if layer.image_data.shape[2] == 3:
                # Convert RGB to RGBA
                rgba = np.zeros((self.height, self.width, 4), dtype=np.uint8)
                rgba[:, :, :3] = layer.image_data
                rgba[:, :, 3] = 255  # Full opacity
                return rgba
            else:
                # Already RGBA
                return layer.image_data.copy()
        
        # Blend visible layers from bottom to top
        for i, layer in visible_layers:
            result = self._blend_images(
                result, layer.image_data, 
                layer.blend_mode, layer.opacity, layer.mask
            )
        
        return result
    
    def _blend_images(self, base: np.ndarray, top: np.ndarray, 
                     blend_mode: str, opacity: float, 
                     mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Blend two images according to the specified blend mode.
        
        Args:
            base: Base image (RGBA)
            top: Top image to blend (RGBA or RGB)
            blend_mode: Blending mode
            opacity: Opacity of the top image (0.0-1.0)
            mask: Optional mask for the top image
            
        Returns:
            Blended image
        """
        # Early exit for 0 opacity layers
        if opacity <= 0.001:
            return base.copy()
        
        # Optimization: Skip computations for completely transparent regions
        if top.shape[2] == 4:
            # Check if entire top image is transparent
            if np.max(top[:, :, 3]) == 0:
                return base.copy()
        
        # Convert to float for calculations
        base_f = base.astype(np.float32) / 255.0
        top_f = top.astype(np.float32) / 255.0
        
        # Get alpha channels (if they exist)
        if base.shape[2] == 4:
            base_alpha = base_f[:, :, 3]
            base_rgb = base_f[:, :, :3]
        else:
            base_alpha = np.ones((base.shape[0], base.shape[1]), dtype=np.float32)
            base_rgb = base_f
        
        if top.shape[2] == 4:
            top_alpha = top_f[:, :, 3] * opacity
            top_rgb = top_f[:, :, :3]
        else:
            top_alpha = np.ones((top.shape[0], top.shape[1]), dtype=np.float32) * opacity
            top_rgb = top_f
        
        # Apply mask if provided
        if mask is not None:
            mask_f = mask.astype(np.float32) / 255.0
            top_alpha = top_alpha * mask_f
        
        # Optimization: For normal blend mode with full opacity, use faster operations
        if blend_mode == "normal" and opacity >= 0.999 and mask is None:
            # Use in-place operations where possible
            result = base.copy()
            
            # Find non-transparent pixels in top image
            if top.shape[2] == 4:
                non_transparent = top[:, :, 3] > 0
                result[non_transparent] = top[non_transparent]
            else:
                # Assume fully opaque RGB
                result[:, :, :3] = top
                result[:, :, 3] = 255
                
            return result
        
        # Initialize result with base image
        result_rgb = base_rgb.copy()
        
        # Apply blending mode
        if blend_mode == "normal":
            for c in range(3):
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    top_rgb[:, :, c] * top_alpha
                )
        
        elif blend_mode == "multiply":
            for c in range(3):
                blend = base_rgb[:, :, c] * top_rgb[:, :, c]
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    blend * top_alpha
                )
        
        elif blend_mode == "screen":
            for c in range(3):
                blend = 1 - (1 - base_rgb[:, :, c]) * (1 - top_rgb[:, :, c])
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    blend * top_alpha
                )
        
        elif blend_mode == "overlay":
            for c in range(3):
                mask_dark = base_rgb[:, :, c] < 0.5
                blend = np.zeros_like(base_rgb[:, :, c])
                
                # For dark base pixels: 2 * base * top
                blend[mask_dark] = 2 * base_rgb[:, :, c][mask_dark] * top_rgb[:, :, c][mask_dark]
                
                # For light base pixels: 1 - 2 * (1 - base) * (1 - top)
                blend[~mask_dark] = 1 - 2 * (1 - base_rgb[:, :, c][~mask_dark]) * (1 - top_rgb[:, :, c][~mask_dark])
                
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    blend * top_alpha
                )
        
        elif blend_mode == "darken":
            for c in range(3):
                blend = np.minimum(base_rgb[:, :, c], top_rgb[:, :, c])
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    blend * top_alpha
                )
        
        elif blend_mode == "lighten":
            for c in range(3):
                blend = np.maximum(base_rgb[:, :, c], top_rgb[:, :, c])
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    blend * top_alpha
                )
        
        else:
            # For unsupported modes, fall back to normal blending
            logger.warning(f"Unsupported blend mode: {blend_mode}, falling back to normal")
            for c in range(3):
                result_rgb[:, :, c] = (
                    base_rgb[:, :, c] * (1 - top_alpha) + 
                    top_rgb[:, :, c] * top_alpha
                )
        
        # Calculate result alpha channel
        result_alpha = base_alpha + top_alpha * (1 - base_alpha)
        
        # Clip to ensure values are in valid range
        result_rgb = np.clip(result_rgb, 0, 1)
        result_alpha = np.clip(result_alpha, 0, 1)
        
        # Create final result
        result = np.zeros((base.shape[0], base.shape[1], 4), dtype=np.uint8)
        for c in range(3):
            result[:, :, c] = (result_rgb[:, :, c] * 255).astype(np.uint8)
        result[:, :, 3] = (result_alpha * 255).astype(np.uint8)
        
        return result 