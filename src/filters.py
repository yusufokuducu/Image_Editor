import numpy as np
from PIL import Image, ImageFilter
import cv2

def apply_blur(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius=radius))

def apply_sharpen(img):
    return img.filter(ImageFilter.SHARPEN)

def apply_edge_enhance(img):
    return img.filter(ImageFilter.EDGE_ENHANCE)

def apply_grayscale(img):
    return img.convert('L').convert('RGBA')

def apply_noise(img, sigma=25):
    # Gelişmiş Gaussian noise ekleyici (OpenCV + NumPy)
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, sigma, arr.shape).astype(np.float32)
    noisy = arr + noise
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy, mode=img.mode)
