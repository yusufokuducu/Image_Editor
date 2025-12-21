import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io

class HistogramData:
    """Calculate histogram data for display"""
    def __init__(self, image):
        self.image = image
        self.calc_histogram()
    
    def calc_histogram(self):
        """Calculate histogram for each channel"""
        if self.image is None:
            return
        
        self.red_hist = cv2.calcHist([self.image], [2], None, [256], [0, 256])
        self.green_hist = cv2.calcHist([self.image], [1], None, [256], [0, 256])
        self.blue_hist = cv2.calcHist([self.image], [0], None, [256], [0, 256])
        
        self.red_hist = cv2.normalize(self.red_hist, self.red_hist).flatten()
        self.green_hist = cv2.normalize(self.green_hist, self.green_hist).flatten()
        self.blue_hist = cv2.normalize(self.blue_hist, self.blue_hist).flatten()

class ImageProcessor:
    def __init__(self):
        self.current_image = None
        self.original_image = None
    
    def load_image(self, file_path):
        """Load image from file path"""
        self.original_image = cv2.imread(file_path)
        if self.original_image is None:
            raise ValueError("Image could not be loaded")
        self.current_image = self.original_image.copy()
        return self.current_image
    
    def get_pil_image(self, cv_image):
        """Convert CV2 image to PIL Image"""
        if cv_image is None:
            return None
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)
    
    def get_cv_image(self, pil_image):
        """Convert PIL Image to CV2 image"""
        rgb_array = np.array(pil_image)
        return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
    
    def brightness(self, value):
        """Adjust brightness (-100 to 100)"""
        pil_img = self.get_pil_image(self.current_image)
        enhancer = ImageEnhance.Brightness(pil_img)
        factor = 1 + (value / 100)
        enhanced = enhancer.enhance(factor)
        self.current_image = self.get_cv_image(enhanced)
        return self.current_image
    
    def contrast(self, value):
        """Adjust contrast (-100 to 100)"""
        pil_img = self.get_pil_image(self.current_image)
        enhancer = ImageEnhance.Contrast(pil_img)
        factor = 1 + (value / 100)
        enhanced = enhancer.enhance(factor)
        self.current_image = self.get_cv_image(enhanced)
        return self.current_image
    
    def saturation(self, value):
        """Adjust saturation (-100 to 100)"""
        pil_img = self.get_pil_image(self.current_image)
        enhancer = ImageEnhance.Color(pil_img)
        factor = 1 + (value / 100)
        enhanced = enhancer.enhance(factor)
        self.current_image = self.get_cv_image(enhanced)
        return self.current_image
    
    def blur(self, value):
        """Apply blur filter (1-50)"""
        if value < 1:
            value = 1
        if value % 2 == 0:
            value += 1
        self.current_image = cv2.GaussianBlur(self.current_image, (value, value), 0)
        return self.current_image
    
    def sharpen(self, value):
        """Apply sharpen filter (0-100)"""
        pil_img = self.get_pil_image(self.current_image)
        enhancer = ImageEnhance.Sharpness(pil_img)
        factor = 1 + (value / 100)
        enhanced = enhancer.enhance(factor)
        self.current_image = self.get_cv_image(enhanced)
        return self.current_image
    
    def grayscale(self):
        """Convert to grayscale"""
        gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)
        self.current_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return self.current_image
    
    def sepia(self):
        """Apply sepia filter"""
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        self.current_image = cv2.transform(self.current_image, kernel)
        self.current_image = np.clip(self.current_image, 0, 255).astype(np.uint8)
        return self.current_image
    
    def add_noise(self, value):
        """Add noise to image (0-50)"""
        noise = np.random.normal(0, value, self.current_image.shape)
        self.current_image = np.clip(self.current_image + noise, 0, 255).astype(np.uint8)
        return self.current_image
    
    def edge_detection(self):
        """Apply edge detection filter"""
        edges = cv2.Canny(self.current_image, 100, 200)
        self.current_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        return self.current_image
    
    def crop(self, x1, y1, x2, y2):
        """Crop image"""
        self.current_image = self.current_image[y1:y2, x1:x2]
        return self.current_image
    
    def resize(self, width, height):
        """Resize image"""
        self.current_image = cv2.resize(self.current_image, (width, height))
        return self.current_image
    
    def flip_horizontal(self):
        """Flip image horizontally"""
        self.current_image = cv2.flip(self.current_image, 1)
        return self.current_image
    
    def flip_vertical(self):
        """Flip image vertically"""
        self.current_image = cv2.flip(self.current_image, 0)
        return self.current_image
    
    def rotate(self, angle):
        """Rotate image"""
        h, w = self.current_image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        self.current_image = cv2.warpAffine(self.current_image, matrix, (w, h))
        return self.current_image
    
    def rotate_hue(self, value):
        """Rotate hue by value (-180 to 180)"""
        pil_img = self.get_pil_image(self.current_image)
        hsv = pil_img.convert('HSV')
        data = list(hsv.getdata())
        
        # Rotate hue
        new_data = []
        for h, s, v in data:
            h = (h + value * 255 / 360) % 256
            new_data.append((int(h), s, v))
        
        hsv.putdata(new_data)
        rgb = hsv.convert('RGB')
        self.current_image = self.get_cv_image(rgb)
        return self.current_image
    
    def reset(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.current_image = self.original_image.copy()
        return self.current_image
    
    def save_image(self, file_path):
        """Save current image"""
        cv2.imwrite(file_path, self.current_image)
    
    def get_current_image(self):
        """Get current image"""
        return self.current_image
    
    def get_histogram(self):
        """Get histogram data"""
        if self.current_image is None:
            return None
        return HistogramData(self.current_image)
    
    def apply_curves(self, points):
        """Apply curves adjustment
        points: list of (x, y) tuples defining the curve
        """
        if self.current_image is None:
            return
        
        # Create lookup table from curve points
        lut = np.arange(256, dtype=np.uint8)
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
            if x2 > x1:
                slope = (y2 - y1) / (x2 - x1)
                for x in range(int(x1), int(x2) + 1):
                    y = int(y1 + slope * (x - x1))
                    lut[x] = np.clip(y, 0, 255)
        
        # Apply LUT to each channel
        for i in range(3):
            self.current_image[:, :, i] = cv2.LUT(self.current_image[:, :, i], lut)
    
    def apply_levels(self, input_black, input_white, output_black, output_white):
        """Apply levels adjustment"""
        if self.current_image is None:
            return
        
        img = self.current_image.astype(np.float32)
        
        # Normalize to 0-1
        img = (img - input_black) / (input_white - input_black)
        img = np.clip(img, 0, 1)
        
        # Scale to output range
        img = img * (output_white - output_black) + output_black
        img = np.clip(img, 0, 255)
        
        self.current_image = img.astype(np.uint8)
    
    def apply_hsv_adjust(self, hue_shift, saturation_shift, value_shift):
        """Adjust HSV values"""
        if self.current_image is None:
            return
        
        hsv = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        hsv[:, :, 0] = (hsv[:, :, 0] + hue_shift) % 180
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] + saturation_shift, 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + value_shift, 0, 255)
        
        self.current_image = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
