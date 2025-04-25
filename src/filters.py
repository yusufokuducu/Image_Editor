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

def apply_noise(img, amount=0.1):
    # Kullanıcıdan gelen amount [0.0, 1.0] arası float ise, 0-50 arası sigma'ya çevir
    # (0.0 çok az, 1.0 çok fazla noise)
    try:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        if amount <= 1.0:
            sigma = int(amount * 50)
        else:
            sigma = int(amount)
        sigma = max(1, sigma)  # 0 olmasın
        arr = np.array(img).astype(np.float32)
        # RGBA shape kontrolü
        if arr.ndim != 3 or arr.shape[2] != 4:
            raise ValueError(f'apply_noise: Beklenen shape (h, w, 4), gelen {arr.shape}')
        noise = np.random.normal(0, sigma, arr.shape).astype(np.float32)
        noisy = arr + noise
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        result = Image.fromarray(noisy, mode='RGBA')
        return result
    except Exception as e:
        import logging
        logging.error(f'apply_noise error: {e}')
        return img
