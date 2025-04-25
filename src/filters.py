import numpy as np
from PIL import Image, ImageFilter
import cv2
import logging

def apply_blur(img, radius=2):
    try:
        if img is None:
            logging.error("apply_blur: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_blur: Geçersiz görüntü tipi: {type(img)}")
            return None

        # Radius değerini sınırla
        radius = max(0, min(radius, 100))

        # Filtreyi uygula
        result = img.filter(ImageFilter.GaussianBlur(radius=radius))

        # RGBA moduna dönüştür
        if result.mode != 'RGBA':
            result = result.convert('RGBA')

        return result
    except Exception as e:
        logging.error(f"apply_blur error: {e}")
        return img

def apply_sharpen(img):
    try:
        if img is None:
            logging.error("apply_sharpen: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_sharpen: Geçersiz görüntü tipi: {type(img)}")
            return None

        # Filtreyi uygula
        result = img.filter(ImageFilter.SHARPEN)

        # RGBA moduna dönüştür
        if result.mode != 'RGBA':
            result = result.convert('RGBA')

        return result
    except Exception as e:
        logging.error(f"apply_sharpen error: {e}")
        return img

def apply_edge_enhance(img):
    try:
        if img is None:
            logging.error("apply_edge_enhance: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_edge_enhance: Geçersiz görüntü tipi: {type(img)}")
            return None

        # Filtreyi uygula
        result = img.filter(ImageFilter.EDGE_ENHANCE)

        # RGBA moduna dönüştür
        if result.mode != 'RGBA':
            result = result.convert('RGBA')

        return result
    except Exception as e:
        logging.error(f"apply_edge_enhance error: {e}")
        return img

def apply_grayscale(img):
    try:
        if img is None:
            logging.error("apply_grayscale: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_grayscale: Geçersiz görüntü tipi: {type(img)}")
            return None

        # Gri tona dönüştür ve sonra RGBA'ya geri dön
        result = img.convert('L').convert('RGBA')

        return result
    except Exception as e:
        logging.error(f"apply_grayscale error: {e}")
        return img

def apply_noise(img, amount=0.1):
    # Kullanıcıdan gelen amount [0.0, 1.0] arası float ise, 0-50 arası sigma'ya çevir
    # (0.0 çok az, 1.0 çok fazla noise)
    try:
        if img is None:
            logging.error("apply_noise: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_noise: Geçersiz görüntü tipi: {type(img)}")
            return None

        # RGBA moduna dönüştür
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Amount değerini sınırla
        amount = max(0.01, min(amount, 1.0))

        # Sigma değerini hesapla
        sigma = int(amount * 50)
        sigma = max(1, sigma)  # 0 olmasın

        # Görüntüyü numpy array'e dönüştür
        try:
            arr = np.array(img).astype(np.float32)
        except Exception as e:
            logging.error(f"Görüntü numpy array'e dönüştürülemedi: {e}")
            return img

        # RGBA shape kontrolü
        if arr.ndim != 3 or arr.shape[2] != 4:
            logging.error(f'apply_noise: Beklenen shape (h, w, 4), gelen {arr.shape}')
            return img

        # Bellek kullanımını optimize et
        try:
            # Sadece RGB kanallara noise ekle, alpha kanalını koru
            rgb_arr = arr[:, :, :3]
            alpha_channel = arr[:, :, 3:4]

            # Noise oluştur ve ekle
            noise = np.random.normal(0, sigma, rgb_arr.shape).astype(np.float32)
            rgb_noisy = rgb_arr + noise
            rgb_noisy = np.clip(rgb_noisy, 0, 255)

            # Kanalları birleştir
            noisy = np.concatenate((rgb_noisy, alpha_channel), axis=2).astype(np.uint8)

            # PIL görüntüsüne dönüştür
            result = Image.fromarray(noisy, mode='RGBA')
            return result
        except Exception as e:
            logging.error(f"Noise uygulanırken hata: {e}")
            return img
    except Exception as e:
        logging.error(f'apply_noise error: {e}')
        return img
