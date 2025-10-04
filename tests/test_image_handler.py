# -*- coding: utf-8 -*-
"""
Unit tests for the ImageHandler class in core/image_handler.py.
"""

import pytest
from PIL import Image, ImageDraw
import numpy as np
from core.image_handler import ImageHandler
import os

@pytest.fixture
def handler():
    """Returns an instance of ImageHandler."""
    return ImageHandler()

@pytest.fixture
def dummy_image_path():
    """Creates a dummy image file with varied colors and returns its path."""
    path = "_test_dummy_image.png"
    img = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 4, 4], fill=(100, 50, 20, 255)) # Use a mid-range color
    img.save(path)
    yield path
    os.remove(path)

def test_load_image(handler, dummy_image_path):
    """Tests that an image is loaded correctly."""
    assert handler.load_image(dummy_image_path) is True
    assert handler.width == 10
    assert handler.height == 10
    assert handler.image_pil is not None
    # Loading should create the first undo state
    assert len(handler.undo_stack) == 1

def test_undo_redo_cycle(handler, dummy_image_path):
    """Tests the full undo/redo cycle."""
    handler.load_image(dummy_image_path)
    original_img_data = np.array(handler.image_pil)
    
    # 1. Apply an operation
    handler.apply_brightness(factor=1.5, is_final=True)
    bright_img_data = np.array(handler.image_pil)
    assert not np.array_equal(original_img_data, bright_img_data)
    assert len(handler.undo_stack) == 2
    assert len(handler.redo_stack) == 0

    # 2. Undo the operation
    assert handler.undo() is True
    undo_img_data = np.array(handler.image_pil)
    assert np.array_equal(original_img_data, undo_img_data)
    assert len(handler.undo_stack) == 1
    assert len(handler.redo_stack) == 1

    # 3. Redo the operation
    assert handler.redo() is True
    redo_img_data = np.array(handler.image_pil)
    assert np.array_equal(bright_img_data, redo_img_data)
    assert len(handler.undo_stack) == 2
    assert len(handler.redo_stack) == 0

    # 4. Test invalid undo/redo
    assert handler.redo() is False # No more redos
    handler.undo()
    assert handler.undo() is False # No more undos
