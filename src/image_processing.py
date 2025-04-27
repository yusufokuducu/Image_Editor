import logging
from PIL import Image
from .filters import (apply_blur, apply_sharpen, apply_edge_enhance, apply_grayscale,
                      apply_noise, apply_brightness, apply_contrast, apply_saturation,
                      apply_hue)

def get_filtered_image(img, filter_type, param):
    """
    Applies a specified filter or adjustment to a PIL Image.

    Args:
        img (Image.Image): The input PIL Image.
        filter_type (str): The type of filter/adjustment to apply
                           ('blur', 'sharpen', 'edge', 'grayscale', 'noise',
                           'brightness', 'contrast', 'saturation', 'hue').
        param: The parameter required for the filter (e.g., radius for blur,
               factor for brightness). Can be None for filters without parameters.

    Returns:
        Image.Image or None: The processed PIL Image in RGBA format, or None if an
                             error occurs or the filter type is unknown.
    """
    # Ensure we have a valid image to work with
    if img is None or not isinstance(img, Image.Image):
        logging.error(f"get_filtered_image: Invalid input image for {filter_type}")
        return None

    # Make a copy to avoid modifying the input directly during filtering
    img_copy = img.copy()

    try:
        if filter_type == 'blur':
            radius = param if param is not None else 2
            radius = param if param is not None else 2
            new_img = apply_blur(img_copy, radius)
        elif filter_type == 'sharpen':
            amount = param if param is not None else 1.0 # Default to full sharpen if no param
            new_img = apply_sharpen(img_copy, amount)
        elif filter_type == 'edge_enhance': # Match the name used elsewhere
            new_img = apply_edge_enhance(img_copy) # Edge enhance doesn't have amount yet
        elif filter_type == 'grayscale':
            amount = param if param is not None else 1.0 # Default to full grayscale if no param
            new_img = apply_grayscale(img_copy, amount)
        elif filter_type == 'noise':
            amount = param if param is not None else 0.1
            new_img = apply_noise(img_copy, amount)
        elif filter_type == 'brightness':
            factor = param if param is not None else 1.0
            new_img = apply_brightness(img_copy, factor)
        elif filter_type == 'contrast':
            factor = param if param is not None else 1.0
            new_img = apply_contrast(img_copy, factor)
        elif filter_type == 'saturation':
            factor = param if param is not None else 1.0
            new_img = apply_saturation(img_copy, factor)
        elif filter_type == 'hue':
            shift = param if param is not None else 0.0
            new_img = apply_hue(img_copy, shift)
        else:
            logging.warning(f"Unknown filter/adjustment type: {filter_type}")
            return None # Return None for unknown types

        # Ensure RGBA output
        if new_img and (not hasattr(new_img, 'mode') or new_img.mode != 'RGBA'):
            new_img = new_img.convert('RGBA')

        return new_img
    except Exception as e:
        logging.error(f"Error applying filter {filter_type} in get_filtered_image: {e}")
        return None # Return None on error
