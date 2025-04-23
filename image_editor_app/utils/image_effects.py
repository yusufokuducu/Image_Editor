"""
Image effect processing utility functions
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def apply_brightness(img, value):
    """Apply brightness adjustment to image"""
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(value)


def apply_contrast(img, value):
    """Apply contrast adjustment to image"""
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(value)


def apply_saturation(img, value):
    """Apply saturation adjustment to image"""
    enhancer = ImageEnhance.Color(img)
    return enhancer.enhance(value)


def apply_blur(img, radius):
    """Apply gaussian blur to image"""
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_sharpen(img, intensity):
    """Apply sharpen filter with specified intensity"""
    iterations = max(1, int(intensity))
    result_img = img.copy()
    for _ in range(iterations):
        result_img = result_img.filter(ImageFilter.SHARPEN)
    return result_img


def apply_contour(img, intensity):
    """Apply contour filter with specified intensity"""
    iterations = max(1, int(intensity))
    result_img = img.copy()
    for _ in range(iterations):
        result_img = result_img.filter(ImageFilter.CONTOUR)
    return result_img


def apply_emboss(img, intensity):
    """Apply emboss filter with specified intensity"""
    iterations = max(1, int(intensity))
    result_img = img.copy()
    for _ in range(iterations):
        result_img = result_img.filter(ImageFilter.EMBOSS)
    return result_img


def apply_bw(img, threshold):
    """Apply black and white conversion with threshold"""
    return img.convert("L").point(lambda x: 255 if x > threshold else 0, mode='1')


def apply_invert(img, intensity):
    """Apply invert effect with intensity control"""
    if intensity >= 0.95:  # Full inversion
        return ImageOps.invert(img)
    else:
        # Partial inversion blends original and inverted
        inverted = ImageOps.invert(img.copy())
        return Image.blend(img, inverted, intensity)


def resize_for_preview(img, max_width=1200, max_height=800):
    """Resize image for preview if it exceeds maximum dimensions"""
    if img.width > max_width or img.height > max_height:
        ratio = min(max_width / img.width, max_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return img 