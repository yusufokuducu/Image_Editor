import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageChops
import colorsys
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

# --- Image Adjustments ---

def apply_brightness(img, factor=1.0):
    """Adjusts image brightness."""
    try:
        if img is None: return None
        if not isinstance(img, Image.Image): return img
        # Ensure RGBA for consistency, but enhancer works on RGB
        img_rgb = img.convert('RGB')
        enhancer = ImageEnhance.Brightness(img_rgb)
        img_enhanced_rgb = enhancer.enhance(factor)
        # Restore alpha channel if it existed
        if 'A' in img.getbands():
            alpha = img.getchannel('A')
            img_enhanced = img_enhanced_rgb.convert('RGBA')
            img_enhanced.putalpha(alpha)
            return img_enhanced
        else:
            return img_enhanced_rgb.convert('RGBA') # Convert back to RGBA
    except Exception as e:
        logging.error(f"apply_brightness error: {e}")
        return img

def apply_contrast(img, factor=1.0):
    """Adjusts image contrast."""
    try:
        if img is None: return None
        if not isinstance(img, Image.Image): return img
        img_rgb = img.convert('RGB')
        enhancer = ImageEnhance.Contrast(img_rgb)
        img_enhanced_rgb = enhancer.enhance(factor)
        if 'A' in img.getbands():
            alpha = img.getchannel('A')
            img_enhanced = img_enhanced_rgb.convert('RGBA')
            img_enhanced.putalpha(alpha)
            return img_enhanced
        else:
            return img_enhanced_rgb.convert('RGBA')
    except Exception as e:
        logging.error(f"apply_contrast error: {e}")
        return img

def apply_saturation(img, factor=1.0):
    """Adjusts image saturation (color intensity)."""
    try:
        if img is None: return None
        if not isinstance(img, Image.Image): return img
        img_rgb = img.convert('RGB')
        enhancer = ImageEnhance.Color(img_rgb) # Color enhancer adjusts saturation
        img_enhanced_rgb = enhancer.enhance(factor)
        if 'A' in img.getbands():
            alpha = img.getchannel('A')
            img_enhanced = img_enhanced_rgb.convert('RGBA')
            img_enhanced.putalpha(alpha)
            return img_enhanced
        else:
            return img_enhanced_rgb.convert('RGBA')
    except Exception as e:
        logging.error(f"apply_saturation error: {e}")
        return img

def apply_hue(img, shift=0.0):
    """Adjusts image hue. shift is -1.0 to 1.0 (representing -180 to +180 degrees)."""
    try:
        if img is None: return None
        if not isinstance(img, Image.Image): return img

        # Ensure shift is within a reasonable range, e.g., -1.0 to 1.0
        shift = max(-1.0, min(shift, 1.0))

        img_rgba = img.convert('RGBA')
        img_arr = np.array(img_rgba).astype(np.float32) / 255.0

        # Separate RGB and Alpha
        rgb = img_arr[:, :, :3]
        alpha = img_arr[:, :, 3]

        # Convert RGB to HSV
        # Apply colorsys.rgb_to_hsv pixel by pixel (vectorization is complex)
        hsv = np.array([colorsys.rgb_to_hsv(p[0], p[1], p[2]) for row in rgb for p in row])
        hsv = hsv.reshape(rgb.shape) # Reshape back to (height, width, 3)

        # Apply hue shift (H is in range [0, 1])
        hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 1.0

        # Convert HSV back to RGB
        rgb_shifted = np.array([colorsys.hsv_to_rgb(p[0], p[1], p[2]) for row in hsv for p in row])
        rgb_shifted = rgb_shifted.reshape(rgb.shape) # Reshape back

        # Combine RGB and Alpha
        rgba_shifted = np.dstack((rgb_shifted, alpha))

        # Clip and convert back to uint8
        rgba_shifted = np.clip(rgba_shifted * 255.0, 0, 255).astype(np.uint8)

        return Image.fromarray(rgba_shifted, 'RGBA')

    except Exception as e:
        logging.error(f"apply_hue error: {e}")
        return img


# --- Filter Discovery ---

def get_available_filters():
    """
    Returns a dictionary of available filters/adjustments suitable for the Effects Panel.
    Keys are identifiers/names, values are the corresponding functions.
    Filters requiring parameters might need special handling later.
    """
    # TODO: Differentiate between filters needing dialogs (like blur, noise)
    # and those that can be applied directly (like sharpen, grayscale).
    # For now, list ones that *could* be applied directly or have simple dialogs.
    return {
        'blur': apply_blur, # Needs dialog
        'sharpen': apply_sharpen,
        'edge_enhance': apply_edge_enhance,
        'grayscale': apply_grayscale,
        'noise': apply_noise, # Needs dialog
        'brightness': apply_brightness, # Needs dialog
        'contrast': apply_contrast, # Needs dialog
        'saturation': apply_saturation, # Needs dialog
        'hue': apply_hue, # Needs dialog
    }
