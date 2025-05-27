import logging
from PIL import Image
from PyQt6.QtGui import QPixmap, QPainter, QColor 
from PyQt6.QtCore import Qt
from .layers import BLEND_MODES 
def compose_layers_pixmap(layers, image_to_qpixmap_func):
    try:
        if not hasattr(layers, 'layers') or not layers.layers:
            return None
        visible_layers = [layer for layer in layers.layers if layer.visible]
        if not visible_layers:
            logging.warning("compose_layers_pixmap: No visible layers")
            return None
        merged_img = layers.merge_visible()
        if merged_img is None:
            logging.warning("compose_layers_pixmap: merge_visible returned None")
            return None
        return image_to_qpixmap_func(merged_img)
    except Exception as e:
        logging.error(f"compose_layers_pixmap error: {e}")
        return None
def validate_layer_operation(layers, message="Operation failed"):
    if not hasattr(layers, 'layers'):
        raise ValueError(f"{message}: No layers available")
    layer = layers.get_active_layer()
    if layer is None or layer.image is None:
        raise ValueError(f"{message}: No active layer or image")
    return layer
def create_command(do_func, undo_func, description):
    from .history import Command
    return Command(do_func, undo_func, description)
def ensure_rgba(image):
    if image.mode != 'RGBA':
        return image.convert('RGBA')
    return image
def create_transparent_image(size):
    return Image.new('RGBA', size, (0, 0, 0, 0))