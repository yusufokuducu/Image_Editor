# -*- coding: utf-8 -*-
"""
Contains image filtering functions.

Each function takes a Pillow Image object, applies a specific filter,
and returns the processed Pillow Image object.
This modular approach keeps the image processing algorithms separate from the
application's state management.
"""

from PIL import Image, ImageFilter, ImageEnhance

def apply_grayscale(image: Image.Image) -> Image.Image:
    """Converts an image to grayscale."""
    # .convert("L") creates a grayscale image, .convert("RGBA") brings it back to the format we use
    return image.convert("L").convert("RGBA")

def apply_blur(image: Image.Image, radius: float) -> Image.Image:
    """Applies a Gaussian blur to the image."""
    if radius <= 0:
        return image
    return image.filter(ImageFilter.GaussianBlur(radius=radius))

def apply_sharpen(image: Image.Image, factor: float) -> Image.Image:
    """Applies a sharpness enhancement to the image."""
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)
