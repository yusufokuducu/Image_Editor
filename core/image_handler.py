"""
Image Handler Module
Provides core functionality for image manipulation and processing.
Handles loading, saving, and converting between different image formats.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union
from functools import lru_cache

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import cv2

logger = logging.getLogger("Image_Editor.ImageHandler")

class ImageHandler:
    """
    Class for handling image operations in the application.
    Acts as an abstraction layer over Pillow, NumPy, and OpenCV for image processing.
    """
    
    # Supported file formats
    SUPPORTED_FORMATS = {
        'open': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'],
        'save': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp']
    }
    
    # Cache for processed images - Use a weak reference dictionary to avoid memory leaks
    _cache = {}
    _max_cache_size = 10  # Maximum number of items to keep in cache
    _cache_hits = 0
    _cache_misses = 0
    
    def __init__(self):
        """Initialize the image handler."""
        logger.info("ImageHandler initialized")
    
    @staticmethod
    def load_image(file_path: str) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """
        Load an image from a file path.
        
        Args:
            file_path: Path to the image file.
            
        Returns:
            Tuple containing:
            - NumPy array containing the image data (or None if failed)
            - Error message (or None if successful)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return None, f"File not found: {file_path}"
            
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ImageHandler.SUPPORTED_FORMATS['open']:
                return None, f"Unsupported file format: {ext}"
            
            # Performance optimization: Check file size
            file_size = os.path.getsize(file_path)
            large_file_threshold = 50 * 1024 * 1024  # 50MB
            
            if file_size > large_file_threshold:
                logger.warning(f"Loading large image ({file_size / (1024*1024):.1f}MB): {file_path}")
            
            # Load the image
            if ext == '.gif':
                # Special handling for GIF files
                pil_image = Image.open(file_path)
                # For GIFs, just take the first frame for now
                if pil_image.is_animated:
                    pil_image.seek(0)
                image_array = np.array(pil_image.convert('RGBA'))
            else:
                # For other formats, use OpenCV for potentially better performance
                image_array = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
                
                # Convert BGR to RGB if necessary
                if image_array is not None and len(image_array.shape) >= 3 and image_array.shape[2] == 3:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
                
                # If the image is grayscale, convert to RGB
                if image_array is not None and len(image_array.shape) == 2:
                    image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            
            if image_array is None:
                return None, f"Failed to load image: {file_path}"
            
            logger.info(f"Loaded image from {file_path}, shape: {image_array.shape}")
            return image_array, None
            
        except Exception as e:
            logger.error(f"Error loading image {file_path}: {str(e)}")
            return None, f"Error loading image: {str(e)}"
    
    @staticmethod
    def save_image(image_array: np.ndarray, file_path: str, quality: int = 95) -> Optional[str]:
        """
        Save an image to a file.
        
        Args:
            image_array: NumPy array containing the image data.
            file_path: Path where the image should be saved.
            quality: Quality for lossy compression formats (0-100).
            
        Returns:
            Error message or None if successful.
        """
        try:
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ImageHandler.SUPPORTED_FORMATS['save']:
                return f"Unsupported file format for saving: {ext}"
            
            # Convert NumPy array to PIL Image
            if image_array.shape[2] == 4:  # RGBA
                pil_image = Image.fromarray(image_array, 'RGBA')
            elif image_array.shape[2] == 3:  # RGB
                pil_image = Image.fromarray(image_array, 'RGB')
            else:
                return f"Unsupported image format: {image_array.shape}"
            
            # Optimization: Resize very large images before saving to JPEG
            if ext in ['.jpg', '.jpeg'] and quality < 100:
                # Check if dimensions exceed a threshold
                width, height = pil_image.size
                max_dimension = 8000  # Maximum dimension we'll save at full resolution
                
                if width > max_dimension or height > max_dimension:
                    scale_factor = max_dimension / max(width, height)
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    logger.info(f"Resizing large image from {width}x{height} to {new_width}x{new_height} for saving")
                    pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
            
            # Save the image based on the extension
            if ext in ['.jpg', '.jpeg']:
                # Convert RGBA to RGB for JPEG (which doesn't support alpha)
                if image_array.shape[2] == 4:
                    pil_image = pil_image.convert('RGB')
                pil_image.save(file_path, quality=quality)
            elif ext == '.png':
                # Optimize PNG for smaller files
                pil_image.save(file_path, compress_level=min(9, 10 - quality // 10), optimize=True)
            elif ext in ['.tiff', '.tif']:
                pil_image.save(file_path, compression='tiff_deflate')
            else:
                pil_image.save(file_path)
            
            logger.info(f"Saved image to {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error saving image to {file_path}: {str(e)}")
            return f"Error saving image: {str(e)}"
    
    @staticmethod
    def create_blank_image(width: int, height: int, color: Union[Tuple[int, int, int], Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Create a new blank image with specified dimensions and background color.
        
        Args:
            width: Width of the new image in pixels.
            height: Height of the new image in pixels.
            color: RGB or RGBA tuple for the background color.
            
        Returns:
            NumPy array containing the new image.
        """
        try:
            # Create a blank image with the specified color
            if len(color) == 3:
                # RGB color
                image = np.zeros((height, width, 3), dtype=np.uint8)
                image[:, :] = color
            elif len(color) == 4:
                # RGBA color
                image = np.zeros((height, width, 4), dtype=np.uint8)
                image[:, :] = color
            else:
                raise ValueError(f"Invalid color format: {color}. Expected RGB or RGBA tuple.")
            
            logger.debug(f"Created blank {width}x{height} image")
            return image
            
        except Exception as e:
            logger.error(f"Error creating blank image: {str(e)}")
            raise
    
    @classmethod
    def clear_cache(cls):
        """Clear the image cache to free memory."""
        cls._cache.clear()
        cls._cache_hits = 0
        cls._cache_misses = 0
        
    @classmethod
    def get_cache_stats(cls):
        """Get cache statistics."""
        return {
            "size": len(cls._cache),
            "max_size": cls._max_cache_size,
            "hits": cls._cache_hits,
            "misses": cls._cache_misses,
            "hit_ratio": cls._cache_hits / max(1, cls._cache_hits + cls._cache_misses)
        }
    
    @staticmethod
    def resize_image(image: np.ndarray, width: int, height: int, interpolation: int = cv2.INTER_LANCZOS4) -> np.ndarray:
        """
        Resize an image to new dimensions.
        
        Args:
            image: NumPy array containing the image data.
            width: Target width in pixels.
            height: Target height in pixels.
            interpolation: Interpolation method to use.
            
        Returns:
            Resized image as NumPy array.
        """
        # Simple cache key based on image shape, size, and interpolation
        # This avoids converting the whole image to bytes which is expensive
        cache_key = f"resize_{image.shape}_{width}_{height}_{interpolation}_{hash(image.tobytes()[:1000])}"
        
        # Check cache
        if cache_key in ImageHandler._cache:
            ImageHandler._cache_hits += 1
            return ImageHandler._cache[cache_key]
        
        ImageHandler._cache_misses += 1
        
        # Fast path for exact size match
        if image.shape[1] == width and image.shape[0] == height:
            return image.copy()
            
        # Pick best interpolation method based on the resize operation
        if width * height < image.shape[1] * image.shape[0]:
            # Downscaling - use area interpolation for better quality
            if interpolation == cv2.INTER_LANCZOS4:
                interpolation = cv2.INTER_AREA
        
        # Perform resize
        result = cv2.resize(image, (width, height), interpolation=interpolation)
        
        # Add to cache with management
        if len(ImageHandler._cache) >= ImageHandler._max_cache_size:
            # Remove a random entry when cache is full
            try:
                key_to_remove = next(iter(ImageHandler._cache))
                del ImageHandler._cache[key_to_remove]
            except (StopIteration, RuntimeError):
                # Handle case where cache is modified during iteration
                ImageHandler._cache.clear()
        
        ImageHandler._cache[cache_key] = result
        return result
    
    @staticmethod
    def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """
        Crop an image to the specified rectangle.
        
        Args:
            image: NumPy array containing the image data.
            x: Left coordinate of the crop rectangle.
            y: Top coordinate of the crop rectangle.
            width: Width of the crop rectangle.
            height: Height of the crop rectangle.
            
        Returns:
            Cropped image as NumPy array.
        """
        # Ensure coordinates are valid
        img_height, img_width = image.shape[:2]
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        width = max(1, min(width, img_width - x))
        height = max(1, min(height, img_height - y))
        
        return image[y:y+height, x:x+width].copy()  # Use copy() to avoid reference to original
    
    @staticmethod
    def rotate_image(image: np.ndarray, angle: float, expand: bool = True) -> np.ndarray:
        """
        Rotate an image by the specified angle.
        
        Args:
            image: NumPy array containing the image data.
            angle: Rotation angle in degrees (counterclockwise).
            expand: Whether to expand the output image to fit the rotated content.
            
        Returns:
            Rotated image as NumPy array.
        """
        # Convert to PIL for rotation to handle alpha properly
        if image.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(image, 'RGBA')
        else:  # RGB
            pil_image = Image.fromarray(image, 'RGB')
        
        # Rotate the image
        rotated = pil_image.rotate(angle, expand=expand, resample=Image.BILINEAR)
        
        # Convert back to NumPy array
        return np.array(rotated)
    
    @staticmethod
    def flip_image(image: np.ndarray, horizontal: bool = True) -> np.ndarray:
        """
        Flip an image horizontally or vertically.
        
        Args:
            image: NumPy array containing the image data.
            horizontal: If True, flip horizontally, else vertically.
            
        Returns:
            Flipped image as NumPy array.
        """
        if horizontal:
            return cv2.flip(image, 1)  # 1 for horizontal flip
        else:
            return cv2.flip(image, 0)  # 0 for vertical flip
    
    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, brightness: float = 1.0, contrast: float = 1.0) -> np.ndarray:
        """
        Adjust image brightness and contrast.
        
        Args:
            image: NumPy array containing the image data.
            brightness: Brightness factor (0.0 to 2.0, 1.0 is neutral).
            contrast: Contrast factor (0.0 to 2.0, 1.0 is neutral).
            
        Returns:
            Adjusted image as NumPy array.
        """
        # Create cache key
        cache_key = f"bc_{hash(image.tobytes())}_{brightness}_{contrast}"
        
        # Check cache
        if cache_key in ImageHandler._cache:
            return ImageHandler._cache[cache_key]
        
        # Performance optimization: work with uint8 for most operations
        # Only use floating point where necessary
        
        # Create a copy to avoid modifying the original
        result = image.copy()
        
        # Separate alpha channel if it exists
        if image.shape[2] == 4:
            alpha = image[:, :, 3].copy()
            rgb = result[:, :, :3]
        else:
            rgb = result
        
        # Apply brightness
        if brightness != 1.0:
            # Convert to float for calculation
            rgb_float = rgb.astype(np.float32)
            
            # Apply brightness
            rgb_float = rgb_float * brightness
            
            # Clip values
            rgb = np.clip(rgb_float, 0, 255).astype(np.uint8)
        
        # Apply contrast
        if contrast != 1.0:
            # Calculate mean value for contrast adjustment
            mean_value = 128
            
            # Convert to float for calculation
            rgb_float = rgb.astype(np.float32)
            
            # Apply contrast formula: (value - mean) * contrast + mean
            rgb_float = (rgb_float - mean_value) * contrast + mean_value
            
            # Clip values
            rgb = np.clip(rgb_float, 0, 255).astype(np.uint8)
        
        # Restore alpha channel if it exists
        if image.shape[2] == 4:
            result[:, :, :3] = rgb
            result[:, :, 3] = alpha
        else:
            result = rgb
        
        # Cache the result
        if len(ImageHandler._cache) >= ImageHandler._max_cache_size:
            # Remove a random entry if cache is full
            ImageHandler._cache.pop(next(iter(ImageHandler._cache)))
        
        ImageHandler._cache[cache_key] = result
        return result
    
    @staticmethod
    def adjust_hue_saturation(image: np.ndarray, hue: float, saturation: float) -> np.ndarray:
        """
        Adjust image hue and saturation.
        
        Args:
            image: NumPy array containing the image data.
            hue: Hue adjustment (0.0 to 1.0, applied as rotation from -180 to +180 degrees).
            saturation: Saturation adjustment factor (0.0 to 2.0, where 1.0 is original).
            
        Returns:
            Adjusted image as NumPy array.
        """
        # Convert RGB to HSV
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        # Adjust hue (H)
        hue_shift = int(hue * 180)  # Scale 0-1 to 0-180
        hsv_image[:, :, 0] = (hsv_image[:, :, 0] + hue_shift) % 180
        
        # Adjust saturation (S)
        hsv_image[:, :, 1] = np.clip(hsv_image[:, :, 1] * saturation, 0, 255)
        
        # Convert back to uint8
        hsv_image = hsv_image.astype(np.uint8)
        
        # Convert HSV back to RGB
        rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)
        
        return rgb_image
    
    @staticmethod
    def apply_blur(image: np.ndarray, radius: int, blur_type: str = 'gaussian') -> np.ndarray:
        """
        Apply blur effect to an image.
        
        Args:
            image: NumPy array containing the image data.
            radius: Blur radius (kernel size = 2*radius + 1).
            blur_type: Type of blur ('gaussian', 'box', 'median').
            
        Returns:
            Blurred image as NumPy array.
        """
        # Ensure radius is positive
        radius = max(1, radius)
        
        # Ensure kernel size is odd
        kernel_size = 2 * radius + 1
        
        if blur_type == 'gaussian':
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        elif blur_type == 'box':
            return cv2.blur(image, (kernel_size, kernel_size))
        elif blur_type == 'median':
            return cv2.medianBlur(image, kernel_size)
        else:
            logger.warning(f"Unsupported blur type: {blur_type}, using gaussian")
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    
    @staticmethod
    def apply_sharpen(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Apply sharpening to an image.
        
        Args:
            image: NumPy array containing the image data.
            strength: Sharpening strength multiplier.
            
        Returns:
            Sharpened image as NumPy array.
        """
        # Create sharpening kernel
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ], dtype=np.float32) * strength
        
        # Adjust the center value to ensure sum of kernel is 1
        kernel[1, 1] = 9.0 * strength - 8.0 * strength
        
        # Apply the kernel
        return cv2.filter2D(image, -1, kernel)
    
    @staticmethod
    def apply_edge_detection(image: np.ndarray, threshold1: float = 100, threshold2: float = 200) -> np.ndarray:
        """
        Apply Canny edge detection to an image.
        
        Args:
            image: NumPy array containing the image data.
            threshold1: First threshold for the hysteresis procedure.
            threshold2: Second threshold for the hysteresis procedure.
            
        Returns:
            Edge detected image as NumPy array.
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3 and image.shape[2] >= 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, threshold1, threshold2)
        
        # Convert back to RGB for consistent return type
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        
        return edges_rgb
    
    @staticmethod
    def apply_threshold(image: np.ndarray, threshold: int = 127, max_value: int = 255) -> np.ndarray:
        """
        Apply binary thresholding to an image.
        
        Args:
            image: NumPy array containing the image data.
            threshold: Threshold value.
            max_value: Maximum value to use.
            
        Returns:
            Thresholded image as NumPy array.
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3 and image.shape[2] >= 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply threshold
        _, thresholded = cv2.threshold(gray, threshold, max_value, cv2.THRESH_BINARY)
        
        # Convert back to RGB for consistent return type
        thresholded_rgb = cv2.cvtColor(thresholded, cv2.COLOR_GRAY2RGB)
        
        return thresholded_rgb
    
    @staticmethod
    def adjust_levels(image: np.ndarray, 
                     in_black: int, in_white: int, 
                     out_black: int, out_white: int, 
                     gamma: float = 1.0) -> np.ndarray:
        """
        Adjust image levels (similar to Photoshop's levels adjustment).
        
        Args:
            image: NumPy array containing the image data.
            in_black: Input black point (0-255).
            in_white: Input white point (0-255).
            out_black: Output black point (0-255).
            out_white: Output white point (0-255).
            gamma: Gamma correction value.
            
        Returns:
            Level-adjusted image as NumPy array.
        """
        # Create a copy of the image to avoid modifying the original
        result = image.copy().astype(np.float32)
        
        # Scale the input black and white points
        in_range = in_white - in_black
        out_range = out_white - out_black
        
        if in_range == 0:
            in_range = 1  # Avoid division by zero
        
        # Apply the levels adjustment to each channel
        for c in range(image.shape[2]):
            # First apply input levels (stretch contrast)
            channel = result[:, :, c]
            channel = np.clip((channel - in_black) / in_range, 0, 1)
            
            # Apply gamma correction
            if gamma != 1.0:
                channel = np.power(channel, 1.0 / gamma)
            
            # Apply output levels
            channel = out_black + (channel * out_range)
            
            # Clip values to the valid range
            result[:, :, c] = np.clip(channel, 0, 255)
        
        return result.astype(np.uint8)
    
    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Convert an image to grayscale.
        
        Args:
            image: NumPy array containing the image data.
            
        Returns:
            Grayscale image as NumPy array (3 channel RGB).
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Convert back to RGB for consistent return type
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    
    @staticmethod
    def convert_to_sepia(image: np.ndarray, intensity: float = 1.0) -> np.ndarray:
        """
        Apply a sepia tone effect to an image.
        
        Args:
            image: NumPy array containing the image data.
            intensity: Intensity of the sepia effect (0.0 to 1.0).
            
        Returns:
            Sepia-toned image as NumPy array.
        """
        # Convert to float for matrix operations
        img_float = image.astype(np.float32) / 255.0
        
        # Define the sepia transformation matrix
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        
        # Apply the sepia transform
        sepia_img = np.zeros_like(img_float)
        for i in range(3):
            sepia_img[:, :, i] = np.sum(img_float * sepia_matrix[i, :], axis=2)
        
        # Clip values
        sepia_img = np.clip(sepia_img, 0, 1)
        
        # Blend with original based on intensity
        blended = img_float * (1 - intensity) + sepia_img * intensity
        
        # Convert back to uint8
        return (blended * 255).astype(np.uint8)
    
    @staticmethod
    def add_text(image: np.ndarray, text: str, position: Tuple[int, int], font=cv2.FONT_HERSHEY_SIMPLEX,
                font_scale: float = 1.0, color: Tuple[int, int, int] = (0, 0, 0),
                thickness: int = 2, line_type: int = cv2.LINE_AA) -> np.ndarray:
        """
        Add text to an image.
        
        Args:
            image: NumPy array containing the image data.
            text: Text to add.
            position: (x, y) coordinates of the bottom-left corner of the text.
            font: Font type.
            font_scale: Font scale factor.
            color: Text color (BGR format).
            thickness: Line thickness.
            line_type: Line type.
            
        Returns:
            Image with text as NumPy array.
        """
        # Create a copy of the image to avoid modifying the original
        result = image.copy()
        
        # Add text
        cv2.putText(result, text, position, font, font_scale, color, thickness, line_type)
        
        return result
    
    @staticmethod
    def apply_perspective_transform(image: np.ndarray, 
                                  src_points: np.ndarray, 
                                  dst_points: np.ndarray) -> np.ndarray:
        """
        Apply a perspective transformation to an image.
        
        Args:
            image: NumPy array containing the image data.
            src_points: Array of 4 source points [x, y].
            dst_points: Array of 4 destination points [x, y].
            
        Returns:
            Perspective-transformed image as NumPy array.
        """
        # Get the transformation matrix
        perspective_matrix = cv2.getPerspectiveTransform(src_points.astype(np.float32), 
                                                       dst_points.astype(np.float32))
        
        # Apply the transformation
        height, width = image.shape[:2]
        warped_image = cv2.warpPerspective(image, perspective_matrix, (width, height))
        
        return warped_image
    
    @staticmethod
    def get_histogram(image: np.ndarray, channel: Optional[int] = None) -> np.ndarray:
        """
        Calculate image histogram.
        
        Args:
            image: NumPy array containing the image data.
            channel: Specific channel to calculate histogram for 
                    (0=Red, 1=Green, 2=Blue, None=all channels).
            
        Returns:
            Histogram data as NumPy array.
        """
        if channel is not None:
            # Calculate histogram for a specific channel
            hist = cv2.calcHist([image], [channel], None, [256], [0, 256])
            return hist.flatten()
        else:
            # Calculate histogram for all channels
            hist_r = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten()
            hist_g = cv2.calcHist([image], [1], None, [256], [0, 256]).flatten()
            hist_b = cv2.calcHist([image], [2], None, [256], [0, 256]).flatten()
            
            # Calculate luminance histogram (0.299R + 0.587G + 0.114B)
            if image.shape[2] >= 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                hist_l = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
            else:
                hist_l = np.zeros(256)
            
            return np.vstack((hist_r, hist_g, hist_b, hist_l))
    
    @staticmethod
    def apply_curves(image: np.ndarray, curves: Dict[str, List[Tuple[int, int]]]) -> np.ndarray:
        """
        Apply curves adjustment to an image (similar to Photoshop's curves).
        
        Args:
            image: NumPy array containing the image data.
            curves: Dictionary with keys 'r', 'g', 'b' or 'rgb' and values as lists of point tuples.
                Each tuple is (input, output) where both values are in the range 0-255.
            
        Returns:
            Curves-adjusted image as NumPy array.
        """
        # Create lookup tables for each channel
        lookups = {}
        all_channels = image.shape[2] if len(image.shape) > 2 else 1
        
        # Process the curves for each channel
        for channel in ['r', 'g', 'b']:
            if channel in curves:
                # Sort points by input value
                points = sorted(curves[channel], key=lambda x: x[0])
                
                # Create a lookup array
                lookup = np.zeros(256, dtype=np.uint8)
                
                # Process each pair of points to create a piecewise linear function
                for i in range(1, len(points)):
                    x0, y0 = points[i-1]
                    x1, y1 = points[i]
                    
                    # Ensure values are within valid range
                    x0 = max(0, min(255, x0))
                    x1 = max(0, min(255, x1))
                    y0 = max(0, min(255, y0))
                    y1 = max(0, min(255, y1))
                    
                    # Calculate values for this segment using linear interpolation
                    if x1 > x0:  # Avoid division by zero
                        for x in range(x0, x1 + 1):
                            y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                            lookup[x] = int(min(255, max(0, y)))
                
                lookups[channel] = lookup
                
        # Apply lookups to each channel
        result = image.copy()
        
        # Check if we have a general RGB curve
        if 'rgb' in curves:
            rgb_lookup = np.zeros(256, dtype=np.uint8)
            rgb_points = sorted(curves['rgb'], key=lambda x: x[0])
            
            for i in range(1, len(rgb_points)):
                x0, y0 = rgb_points[i-1]
                x1, y1 = rgb_points[i]
                
                x0 = max(0, min(255, x0))
                x1 = max(0, min(255, x1))
                y0 = max(0, min(255, y0))
                y1 = max(0, min(255, y1))
                
                if x1 > x0:
                    for x in range(x0, x1 + 1):
                        y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                        rgb_lookup[x] = int(min(255, max(0, y)))
            
            # Apply RGB curve to all channels
            for c in range(min(3, all_channels)):
                result[:, :, c] = rgb_lookup[result[:, :, c]]
        
        # Apply channel-specific curves
        channel_map = {'r': 0, 'g': 1, 'b': 2}
        for channel, lookup in lookups.items():
            c = channel_map.get(channel)
            if c is not None and c < all_channels:
                result[:, :, c] = lookup[result[:, :, c]]
        
        return result 