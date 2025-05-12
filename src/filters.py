import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageChops
import colorsys
import logging
import torch
import torch.nn.functional as F
from .gpu_utils import pil_to_tensor, tensor_to_pil, check_gpu_memory

# Global flag to check if GPU is available - başlangıçta kontrol et
USE_GPU = torch.cuda.is_available()

# GPU kullanım durumunu logla
if USE_GPU:
    device_name = torch.cuda.get_device_name(0)
    logging.info(f"GPU bulundu ve aktif: {device_name}")
    logging.info(f"CUDA sürümü: {torch.version.cuda}")
else:
    logging.warning("GPU bulunamadı veya CUDA kullanılamıyor. CPU modu kullanılacak.")

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
        
        # GPU implementation if available
        if USE_GPU and check_gpu_memory(200):  # Require 200MB free memory
            try:
                logging.info(f"Blur filtresi GPU ile uygulanıyor, radius={radius}")
                # Convert to tensor and move to GPU
                tensor = pil_to_tensor(img)
                
                # Add batch dimension and adjust channels for GPU processing
                tensor = tensor.unsqueeze(0) / 255.0
                
                # Calculate kernel size (must be odd)
                kernel_size = int(2 * radius) + 1
                kernel_size = max(3, kernel_size)
                
                # Apply gaussian blur
                if tensor.shape[1] == 4:  # RGBA image
                    # Process RGB and Alpha separately
                    rgb = tensor[:, :3]
                    alpha = tensor[:, 3:4]
                    
                    # Apply blur to RGB
                    rgb_blurred = F.gaussian_blur(rgb, kernel_size=[kernel_size, kernel_size], 
                                                sigma=[radius, radius])
                    
                    # Recombine with original alpha
                    blurred = torch.cat([rgb_blurred, alpha], dim=1)
                else:
                    blurred = F.gaussian_blur(tensor, kernel_size=[kernel_size, kernel_size], 
                                             sigma=[radius, radius])
                
                # Convert back to PIL
                blurred = (blurred * 255).byte().squeeze(0)
                result = tensor_to_pil(blurred)
                
                # Ensure RGBA mode
                if result.mode != 'RGBA':
                    result = result.convert('RGBA')
                
                logging.info("Blur filtresi GPU ile başarıyla uygulandı")
                return result
            except Exception as e:
                logging.warning(f"GPU blur failed, falling back to CPU: {e}")
                # Fall back to CPU implementation
        else:
            if USE_GPU:
                logging.info("Yeterli GPU belleği yok, CPU kullanılıyor")
            else:
                logging.info("GPU bulunamadı, CPU ile blur uygulanıyor")
        
        # CPU implementation (original)
        logging.info("Blur filtresi CPU ile uygulanıyor")
        result = img.filter(ImageFilter.GaussianBlur(radius=radius))

        # RGBA moduna dönüştür
        if result.mode != 'RGBA':
            result = result.convert('RGBA')

        return result
    except Exception as e:
        logging.error(f"apply_blur error: {e}")
        return img

def apply_sharpen(img, amount=1.0):
    """Applies sharpening with adjustable amount."""
    try:
        if img is None:
            logging.error("apply_sharpen: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_sharpen: Geçersiz görüntü tipi: {type(img)}")
            return None

        # Ensure RGBA for blending
        if img.mode != 'RGBA':
            img_rgba = img.convert('RGBA')
        else:
            img_rgba = img

        # GPU implementation if available
        if USE_GPU and check_gpu_memory(200):
            try:
                # Convert to tensor
                tensor = pil_to_tensor(img_rgba)
                tensor = tensor.unsqueeze(0) / 255.0
                
                # Split RGB and Alpha channels
                if tensor.shape[1] == 4:  # RGBA image
                    rgb = tensor[:, :3]
                    alpha = tensor[:, 3:4]
                else:
                    rgb = tensor
                    alpha = None
                
                # Create simple sharpening kernel
                kernel = torch.tensor([
                    [0, -1, 0],
                    [-1, 5, -1],
                    [0, -1, 0]
                ], dtype=torch.float32, device=tensor.device).unsqueeze(0).unsqueeze(0)
                
                # Expand kernel for each channel
                kernel = kernel.expand(3, 1, 3, 3)
                
                # Apply convolution
                padded = F.pad(rgb, (1, 1, 1, 1), mode='reflect')
                sharpened = F.conv2d(padded, kernel, groups=3)
                
                # Clamp values
                sharpened = torch.clamp(sharpened, 0, 1)
                
                # If amount is less than 1, blend with original
                if amount < 1.0:
                    sharpened = rgb * (1 - amount) + sharpened * amount
                
                # Recombine with alpha if needed
                if alpha is not None:
                    result_tensor = torch.cat([sharpened, alpha], dim=1)
                else:
                    result_tensor = sharpened
                
                # Convert back to PIL
                result_tensor = (result_tensor * 255).byte().squeeze(0)
                result = tensor_to_pil(result_tensor)
                
                # Ensure RGBA mode
                if result.mode != 'RGBA':
                    result = result.convert('RGBA')
                
                return result
            except Exception as e:
                logging.warning(f"GPU sharpen failed, falling back to CPU: {e}")
        
        # CPU implementation (original)
        # Apply sharpen filter
        sharpened_img = img_rgba.filter(ImageFilter.SHARPEN)

        # Ensure sharpened image is RGBA (should be, but double-check)
        if sharpened_img.mode != 'RGBA':
            sharpened_img = sharpened_img.convert('RGBA')

        # Blend original and sharpened based on amount
        # amount=0.0 -> original, amount=1.0 -> fully sharpened
        amount = max(0.0, min(amount, 1.0)) # Clamp amount
        result = Image.blend(img_rgba, sharpened_img, amount)

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

def apply_grayscale(img, amount=1.0):
    """Applies grayscale effect with adjustable amount."""
    try:
        if img is None:
            logging.error("apply_grayscale: Görüntü None")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_grayscale: Geçersiz görüntü tipi: {type(img)}")
            return None
        if not isinstance(img, Image.Image):
            logging.error(f"apply_grayscale: Geçersiz görüntü tipi: {type(img)}")
            return None

        # Ensure RGBA for blending
        if img.mode != 'RGBA':
            img_rgba = img.convert('RGBA')
        else:
            img_rgba = img

        # Convert to grayscale and back to RGBA
        grayscale_img = img_rgba.convert('L').convert('RGBA')

        # Blend original and grayscale based on amount
        # amount=0.0 -> original, amount=1.0 -> fully grayscale
        amount = max(0.0, min(amount, 1.0)) # Clamp amount
        result = Image.blend(img_rgba, grayscale_img, amount)

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
        
        # GPU implementation if available
        if USE_GPU and check_gpu_memory(200):
            try:
                # Convert to tensor
                tensor = pil_to_tensor(img)
                tensor = tensor.unsqueeze(0) / 255.0
                
                # Split RGB and Alpha channels
                if tensor.shape[1] == 4:  # RGBA image
                    rgb = tensor[:, :3]
                    alpha = tensor[:, 3:4]
                else:
                    rgb = tensor
                    alpha = None
                
                # Generate noise on GPU
                device = tensor.device
                noise = torch.randn_like(rgb, device=device) * (sigma / 255.0)
                
                # Add noise to RGB channels
                rgb_noisy = rgb + noise
                
                # Clamp values to valid range
                rgb_noisy = torch.clamp(rgb_noisy, 0, 1)
                
                # Recombine with alpha if needed
                if alpha is not None:
                    result_tensor = torch.cat([rgb_noisy, alpha], dim=1)
                else:
                    result_tensor = rgb_noisy
                
                # Convert back to PIL
                result_tensor = (result_tensor * 255).byte().squeeze(0)
                result = tensor_to_pil(result_tensor)
                
                return result
            except Exception as e:
                logging.warning(f"GPU noise application failed, falling back to CPU: {e}")

        # CPU implementation (original)
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
        
        # GPU implementation if available
        if USE_GPU and check_gpu_memory(200):
            try:
                # Convert to tensor
                tensor = pil_to_tensor(img)
                tensor = tensor.unsqueeze(0) / 255.0
                
                # Split RGB and Alpha channels
                if tensor.shape[1] == 4:  # RGBA image
                    rgb = tensor[:, :3]
                    alpha = tensor[:, 3:4]
                else:
                    rgb = tensor
                    alpha = None
                
                # Apply brightness adjustment
                rgb_adjusted = rgb * factor
                
                # Clamp values
                rgb_adjusted = torch.clamp(rgb_adjusted, 0, 1)
                
                # Recombine with alpha if needed
                if alpha is not None:
                    result_tensor = torch.cat([rgb_adjusted, alpha], dim=1)
                else:
                    result_tensor = rgb_adjusted
                
                # Convert back to PIL
                result_tensor = (result_tensor * 255).byte().squeeze(0)
                result = tensor_to_pil(result_tensor)
                
                return result
            except Exception as e:
                logging.warning(f"GPU brightness adjustment failed, falling back to CPU: {e}")
        
        # CPU implementation (original)
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
        alpha = img_arr[:, :, 3:4] # Keep shape (h, w, 1) for dstack

        # --- Vectorized RGB to HSV ---
        max_c = np.max(rgb, axis=2)
        min_c = np.min(rgb, axis=2)
        delta = max_c - min_c

        # Value (V)
        v = max_c

        # Saturation (S)
        s = np.zeros_like(max_c)
        non_zero_max = max_c != 0
        s[non_zero_max] = delta[non_zero_max] / max_c[non_zero_max]

        # Hue (H)
        h = np.zeros_like(max_c)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        # Avoid division by zero where delta is zero
        delta_is_zero = delta == 0
        delta_not_zero = ~delta_is_zero

        # Calculate hue where delta is not zero
        idx_r = (max_c == r) & delta_not_zero
        idx_g = (max_c == g) & delta_not_zero
        idx_b = (max_c == b) & delta_not_zero

        h[idx_r] = (((g[idx_r] - b[idx_r]) / delta[idx_r]) % 6) / 6.0
        h[idx_g] = (((b[idx_g] - r[idx_g]) / delta[idx_g]) + 2) / 6.0
        h[idx_b] = (((r[idx_b] - g[idx_b]) / delta[idx_b]) + 4) / 6.0

        # Where delta is zero, hue is undefined (or 0)
        h[delta_is_zero] = 0

        # Apply hue shift (H is in range [0, 1])
        h = (h + shift) % 1.0

        # --- Vectorized HSV to RGB ---
        i = np.floor(h * 6).astype(int)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)

        # Prepare rgb_shifted array
        rgb_shifted = np.zeros_like(rgb)

        i %= 6 # Ensure i is within 0-5

        # Assign values based on sector i
        idx_0 = i == 0
        rgb_shifted[idx_0] = np.dstack((v[idx_0], t[idx_0], p[idx_0]))
        idx_1 = i == 1
        rgb_shifted[idx_1] = np.dstack((q[idx_1], v[idx_1], p[idx_1]))
        idx_2 = i == 2
        rgb_shifted[idx_2] = np.dstack((p[idx_2], v[idx_2], t[idx_2]))
        idx_3 = i == 3
        rgb_shifted[idx_3] = np.dstack((p[idx_3], q[idx_3], v[idx_3]))
        idx_4 = i == 4
        rgb_shifted[idx_4] = np.dstack((t[idx_4], p[idx_4], v[idx_4]))
        idx_5 = i == 5
        rgb_shifted[idx_5] = np.dstack((v[idx_5], p[idx_5], q[idx_5]))

        # Combine RGB and Alpha
        # Ensure alpha has the same dimensions for dstack if needed
        if alpha.shape[:2] != rgb_shifted.shape[:2]:
             # This shouldn't happen if slicing was correct, but as a safeguard
             alpha = np.broadcast_to(alpha, rgb_shifted.shape[:2] + (1,))

        rgba_shifted = np.dstack((rgb_shifted, alpha[:,:,0])) # alpha was (h,w,1), need (h,w) for dstack

        # Clip and convert back to uint8
        rgba_shifted = np.clip(rgba_shifted * 255.0, 0, 255).astype(np.uint8)

        return Image.fromarray(rgba_shifted, 'RGBA')

    except Exception as e:
        logging.error(f"apply_hue error: {e}")
        return img


# --- Filter Discovery ---

def get_available_filters():
    """
    Return a list of available filters with their properties.
    
    Returns:
        list: List of dictionaries containing filter information
    """
    return [
        {"id": "blur", "name": "Blur", "has_param": True, "param_name": "Radius", "param_min": 0, "param_max": 20, "param_default": 2},
        {"id": "sharpen", "name": "Sharpen", "has_param": True, "param_name": "Amount", "param_min": 0, "param_max": 1, "param_default": 0.5},
        {"id": "edge_enhance", "name": "Edge Enhance", "has_param": False},
        {"id": "grayscale", "name": "Grayscale", "has_param": True, "param_name": "Amount", "param_min": 0, "param_max": 1, "param_default": 1.0},
        {"id": "noise", "name": "Noise", "has_param": True, "param_name": "Amount", "param_min": 0, "param_max": 1, "param_default": 0.1},
        {"id": "brightness", "name": "Brightness", "has_param": True, "param_name": "Factor", "param_min": 0, "param_max": 2, "param_default": 1.0},
        {"id": "contrast", "name": "Contrast", "has_param": True, "param_name": "Factor", "param_min": 0, "param_max": 2, "param_default": 1.0},
        {"id": "saturation", "name": "Saturation", "has_param": True, "param_name": "Factor", "param_min": 0, "param_max": 2, "param_default": 1.0},
        {"id": "hue", "name": "Hue", "has_param": True, "param_name": "Shift", "param_min": -1, "param_max": 1, "param_default": 0.0},
    ]
