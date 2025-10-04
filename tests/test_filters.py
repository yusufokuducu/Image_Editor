# -*- coding: utf-8 -*-
"""
Unit tests for the filter functions in core/filters.py.
"""

import pytest
from PIL import Image, ImageDraw
import numpy as np
from core import filters

@pytest.fixture
def create_dummy_image():
    """Creates a simple 4x4 image with varied colors for testing."""
    img = Image.new("RGBA", (4, 4))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 1, 1], fill="red")
    draw.rectangle([2, 2, 3, 3], fill="blue")
    draw.rectangle([0, 2, 1, 3], fill="green")
    return img

def test_apply_grayscale(create_dummy_image):
    """Tests the grayscale filter."""
    img = create_dummy_image
    gray_img = filters.apply_grayscale(img)
    
    # Check that the image mode is correct
    assert gray_img.mode == "RGBA"
    
    # Check that the pixels are grayscale (R=G=B)
    pixel_data = np.array(gray_img)
    r, g, b, a = pixel_data[0, 0]
    assert r == g == b

def test_apply_blur(create_dummy_image):
    """Tests the blur filter."""
    img = create_dummy_image
    blurred_img = filters.apply_blur(img, radius=2)
    
    # Check that the image has changed
    assert not np.array_equal(np.array(img), np.array(blurred_img))

def test_apply_sharpen(create_dummy_image):
    """Tests the sharpen filter."""
    img = create_dummy_image
    sharpened_img = filters.apply_sharpen(img, factor=2.0)
    
    # Check that the image has changed
    assert not np.array_equal(np.array(img), np.array(sharpened_img))
