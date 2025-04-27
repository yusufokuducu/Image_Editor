import logging
from PIL import Image
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt

def compose_layers_pixmap(layers, image_to_qpixmap_func):
    """Composes visible layers into a QPixmap."""
    try:
        # Check layers
        if not hasattr(layers, 'layers') or not layers.layers:
            return None

        # Get visible layers
        visible_layers = [layer for layer in layers.layers if layer.visible]
        if not visible_layers:
            logging.warning("compose_layers_pixmap: No visible layers")
            return None

        # Convert layers to pixmaps
        pixmaps = []
        for layer in visible_layers:
            try:
                if not hasattr(layer, 'image') or layer.image is None:
                    continue

                pm = image_to_qpixmap_func(layer.image)
                if pm and not pm.isNull():
                    pixmaps.append(pm)
            except Exception as e:
                logging.error(f"Error converting layer to pixmap: {e}")
                continue

        if not pixmaps:
            return None

        # Get dimensions from first pixmap
        width = pixmaps[0].width()
        height = pixmaps[0].height()

        # Create result pixmap
        result = QPixmap(width, height)
        result.fill(Qt.GlobalColor.transparent)

        # Draw layers
        painter = QPainter(result)
        for pm in pixmaps:
            if not pm.isNull():
                painter.drawPixmap(0, 0, pm)
        painter.end()

        return result
    except Exception as e:
        logging.error(f"compose_layers_pixmap error: {e}")
        return None

def validate_layer_operation(layers, message="Operation failed"):
    """Validates if layer operation can be performed."""
    if not hasattr(layers, 'layers'):
        raise ValueError(f"{message}: No layers available")
    
    layer = layers.get_active_layer()
    if layer is None or layer.image is None:
        raise ValueError(f"{message}: No active layer or image")
    
    return layer

def create_command(do_func, undo_func, description):
    """Creates a Command object for undo/redo functionality."""
    from .history import Command
    return Command(do_func, undo_func, description)

def ensure_rgba(image):
    """Ensures an image is in RGBA mode."""
    if image.mode != 'RGBA':
        return image.convert('RGBA')
    return image

def create_transparent_image(size):
    """Creates a new transparent image of the given size."""
    return Image.new('RGBA', size, (0, 0, 0, 0))
