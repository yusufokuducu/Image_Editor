import numpy as np
from PIL import Image, ImageOps, ImageFilter
import random

def apply_sepia(image, intensity=1.0):
    """Apply sepia tone filter to image with adjustable intensity"""
    img_array = np.array(image)
    
    # Create original sepia conversion
    sepia_matrix = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    
    # Apply sepia matrix transformation
    sepia_array = np.dot(img_array[...,:3], sepia_matrix.T)
    
    # Ensure values are in valid range
    sepia_array = np.clip(sepia_array, 0, 255).astype(np.uint8)
    
    # Create sepia image
    if img_array.shape[2] == 4:
        alpha = img_array[:, :, 3]
        sepia_img = np.dstack((sepia_array, alpha))
    else:
        sepia_img = sepia_array
    
    # If intensity is not full, blend with original
    if intensity < 1.0:
        # Convert back to PIL for blend
        sepia_pil = Image.fromarray(sepia_img)
        # Blend with original based on intensity
        return Image.blend(image, sepia_pil, intensity)
    
    return Image.fromarray(sepia_img)

def apply_vignette(image, amount=0.5):
    """Add vignette effect (darkened corners) to image with adjustable intensity"""
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # Create radial gradient mask
    x = np.abs(np.linspace(-1, 1, width))
    y = np.abs(np.linspace(-1, 1, height))
    xx, yy = np.meshgrid(x, y)
    
    # Calculate radial distance from center (normalized)
    r = np.sqrt(xx**2 + yy**2)
    
    # Create vignette mask (1 in center, decreasing to edges)
    mask = 1 - np.clip(r * amount * 1.5, 0, 1)
    
    # Apply mask to each color channel
    for i in range(3):
        img_array[:, :, i] = img_array[:, :, i] * mask
    
    return Image.fromarray(img_array.astype(np.uint8))

def apply_pixelate(image, pixel_size=10):
    """Pixelate effect by downsampling and upsampling with adjustable pixel size"""
    # Calculate new dimensions
    width, height = image.size
    small_width = max(1, width // pixel_size)
    small_height = max(1, height // pixel_size)
    
    # Downsample
    small_img = image.resize((small_width, small_height), Image.NEAREST)
    
    # Upsample
    pixelated = small_img.resize((width, height), Image.NEAREST)
    
    return pixelated

def apply_cartoon(image, edge_intensity=3, simplify=5):
    """Create cartoon-like effect with adjustable parameters"""
    # Create edge mask
    edges = image.filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.invert(edges)
    
    # Enhance edges and make them black
    edges = edges.point(lambda x: 0 if x < (255 - (edge_intensity * 25)) else 255)
    
    # Simplify colors
    simple = image.convert('P', palette=Image.ADAPTIVE, colors=simplify)
    simple = simple.convert('RGB')
    
    # Blend edges with simplified colors
    result = ImageOps.multiply(simple, edges)
    
    return result

def apply_color_splash(image, color='red', intensity=1.0):
    """Keep only one color channel, convert rest to grayscale with adjustable intensity"""
    # Convert to array
    img_array = np.array(image)
    
    # Create grayscale version
    gray_array = np.dot(img_array[..., :3], [0.2989, 0.5870, 0.1140])
    gray_image = np.zeros_like(img_array)
    
    # Set all channels to grayscale
    for i in range(3):
        gray_image[:, :, i] = gray_array
    
    # Keep selected color channel from original
    if color == 'red':
        gray_image[:, :, 0] = img_array[:, :, 0]
    elif color == 'green':
        gray_image[:, :, 1] = img_array[:, :, 1]
    elif color == 'blue':
        gray_image[:, :, 2] = img_array[:, :, 2]
    
    # Create color splash result
    result = Image.fromarray(gray_image.astype(np.uint8))
    
    # If intensity is not full, blend with original
    if intensity < 1.0:
        return Image.blend(image, result, intensity)
    
    return result

def apply_oil_painting(image, brush_size=5, levels=8):
    """Create oil painting effect using a more efficient approach"""
    # Resize the image to make processing faster for larger images
    orig_size = image.size
    if max(orig_size) > 800:
        scale_factor = 800 / max(orig_size)
        new_size = (int(orig_size[0] * scale_factor), int(orig_size[1] * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convert image to array
    img_array = np.array(image)
    
    # Apply a simple posterization effect to reduce colors
    img_array = ((img_array // (256 // levels)) * (256 // levels)).astype(np.uint8)
    
    # Apply a median filter for the oil paint effect
    # This is much faster than the pixel-by-pixel approach
    r_channel = Image.fromarray(img_array[:,:,0]).filter(ImageFilter.MedianFilter(brush_size))
    g_channel = Image.fromarray(img_array[:,:,1]).filter(ImageFilter.MedianFilter(brush_size))
    b_channel = Image.fromarray(img_array[:,:,2]).filter(ImageFilter.MedianFilter(brush_size))
    
    # Combine the channels back into an RGB image
    oil_img = Image.merge("RGB", (r_channel, g_channel, b_channel))
    
    # Apply a slight edge enhancement for the painting look
    oil_img = oil_img.filter(ImageFilter.EDGE_ENHANCE)
    
    # Resize back to original size if needed
    if max(orig_size) > 800:
        oil_img = oil_img.resize(orig_size, Image.Resampling.LANCZOS)
    
    return oil_img

def apply_noise(image, amount=0.5, noise_type="uniform", channels=None):
    """
    Add random noise to the image with adjustable intensity and type
    
    Parameters:
    - image: PIL Image
    - amount: float 0-1, noise intensity
    - noise_type: string, one of "uniform", "gaussian", "salt_pepper"
    - channels: list of strings, which channels to affect ("r", "g", "b")
    """
    if channels is None:
        channels = ["r", "g", "b"]  # Default to all channels
    
    # Convert to array
    img_array = np.array(image).copy()
    
    # Handle different noise types
    if noise_type == "uniform":
        # Calculate noise intensity (scale factor)
        noise_factor = int(amount * 50)  # Scale from 0 to 50
        
        # Add random uniform noise to selected channels
        for i, channel in enumerate(["r", "g", "b"]):
            if channel in channels:
                noise = np.random.randint(-noise_factor, noise_factor + 1, img_array.shape[:2])
                img_array[:, :, i] = np.clip(img_array[:, :, i] + noise, 0, 255)
    
    elif noise_type == "gaussian":
        # Calculate standard deviation from amount
        std_dev = amount * 25.0  # Scale from 0 to 25
        
        # Add Gaussian noise to selected channels
        for i, channel in enumerate(["r", "g", "b"]):
            if channel in channels:
                noise = np.random.normal(0, std_dev, img_array.shape[:2])
                img_array[:, :, i] = np.clip(img_array[:, :, i] + noise, 0, 255).astype(np.uint8)
    
    elif noise_type == "salt_pepper":
        # Calculate probability of salt and pepper
        prob = amount * 0.1  # Scale from 0 to 0.1
        
        # Create salt and pepper masks
        salt = np.random.random(img_array.shape[:2]) < prob/2
        pepper = np.random.random(img_array.shape[:2]) < prob/2
        
        # Apply salt and pepper to selected channels
        for i, channel in enumerate(["r", "g", "b"]):
            if channel in channels:
                # Salt: white pixels
                img_array[:, :, i][salt] = 255
                # Pepper: black pixels
                img_array[:, :, i][pepper] = 0
    
    return Image.fromarray(img_array.astype(np.uint8)) 