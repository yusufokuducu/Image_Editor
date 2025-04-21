"""
Image Handler Module
Provides core functionality for image manipulation and processing.
Handles loading, saving, and converting between different image formats.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import cv2

logger = logging.getLogger("PhotoForge.ImageHandler")

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
            
            # Save the image based on the extension
            if ext in ['.jpg', '.jpeg']:
                # Convert RGBA to RGB for JPEG (which doesn't support alpha)
                if image_array.shape[2] == 4:
                    pil_image = pil_image.convert('RGB')
                pil_image.save(file_path, quality=quality)
            elif ext == '.png':
                pil_image.save(file_path, compress_level=min(9, 10 - quality // 10))
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
    def create_blank_image(width: int, height: int, color: Tuple[int, int, int] = (255, 255, 255),
                          with_alpha: bool = True) -> np.ndarray:
        """
        Create a new blank image with specified dimensions and background color.
        
        Args:
            width: Width of the new image in pixels.
            height: Height of the new image in pixels.
            color: RGB tuple for the background color.
            with_alpha: Whether to include an alpha channel.
            
        Returns:
            NumPy array containing the new image.
        """
        if with_alpha:
            # Create RGBA image
            color_with_alpha = (*color, 255)  # Add full opacity
            image = np.ones((height, width, 4), dtype=np.uint8) * np.array(color_with_alpha, dtype=np.uint8)
        else:
            # Create RGB image
            image = np.ones((height, width, 3), dtype=np.uint8) * np.array(color, dtype=np.uint8)
        
        logger.debug(f"Created blank {width}x{height} image")
        return image
    
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
        return cv2.resize(image, (width, height), interpolation=interpolation)
    
    @staticmethod
    def crop_image(image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """
        Crop an image to the specified rectangle.
        
        Args:
            image: NumPy array containing the image data.
            x: X-coordinate of the top-left corner.
            y: Y-coordinate of the top-left corner.
            width: Width of the crop rectangle.
            height: Height of the crop rectangle.
            
        Returns:
            Cropped image as NumPy array.
        """
        # Ensure crop region is within image bounds
        img_height, img_width = image.shape[:2]
        
        # Adjust coordinates to be within bounds
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        width = max(1, min(width, img_width - x))
        height = max(1, min(height, img_height - y))
        
        return image[y:y+height, x:x+width].copy()
    
    @staticmethod
    def rotate_image(image: np.ndarray, angle: float, 
                    keep_dims: bool = True, 
                    border_mode: int = cv2.BORDER_CONSTANT,
                    border_value: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> np.ndarray:
        """
        Rotate an image by the specified angle.
        
        Args:
            image: NumPy array containing the image data.
            angle: Rotation angle in degrees (positive = counterclockwise).
            keep_dims: Whether to maintain the original image dimensions.
            border_mode: Border handling mode.
            border_value: Border color to use with BORDER_CONSTANT.
            
        Returns:
            Rotated image as NumPy array.
        """
        height, width = image.shape[:2]
        center = (width / 2, height / 2)
        
        # Get the rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        if keep_dims:
            # Apply the rotation while maintaining the original dimensions
            rotated_image = cv2.warpAffine(
                image, rotation_matrix, (width, height),
                flags=cv2.INTER_LINEAR, borderMode=border_mode,
                borderValue=border_value
            )
        else:
            # Calculate new dimensions
            cos = abs(rotation_matrix[0, 0])
            sin = abs(rotation_matrix[0, 1])
            
            new_width = int((height * sin) + (width * cos))
            new_height = int((height * cos) + (width * sin))
            
            # Adjust the rotation matrix
            rotation_matrix[0, 2] += (new_width / 2) - center[0]
            rotation_matrix[1, 2] += (new_height / 2) - center[1]
            
            # Apply the rotation with the new dimensions
            rotated_image = cv2.warpAffine(
                image, rotation_matrix, (new_width, new_height),
                flags=cv2.INTER_LINEAR, borderMode=border_mode,
                borderValue=border_value
            )
        
        return rotated_image
    
    @staticmethod
    def flip_image(image: np.ndarray, horizontal: bool = True) -> np.ndarray:
        """
        Flip an image horizontally or vertically.
        
        Args:
            image: NumPy array containing the image data.
            horizontal: If True, flip horizontally; if False, flip vertically.
            
        Returns:
            Flipped image as NumPy array.
        """
        if horizontal:
            return cv2.flip(image, 1)  # 1 = horizontal flip
        else:
            return cv2.flip(image, 0)  # 0 = vertical flip
    
    @staticmethod
    def adjust_brightness_contrast(image: np.ndarray, brightness: float, contrast: float) -> np.ndarray:
        """
        Adjust image brightness and contrast.
        
        Args:
            image: NumPy array containing the image data.
            brightness: Brightness adjustment factor (0.0 to 2.0, where 1.0 is original).
            contrast: Contrast adjustment factor (0.0 to 2.0, where 1.0 is original).
            
        Returns:
            Adjusted image as NumPy array.
        """
        # Convert to PIL Image for these adjustments
        pil_image = Image.fromarray(image)
        
        # Apply brightness adjustment
        enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = enhancer.enhance(brightness)
        
        # Apply contrast adjustment
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(contrast)
        
        # Convert back to NumPy array
        return np.array(pil_image)
    
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