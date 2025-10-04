import cv2
import numpy as np

def apply_brightness_contrast(image, brightness, contrast):
    if brightness != 0:
        img = np.int16(image) + brightness
        image = np.uint8(np.clip(img, 0, 255))
    if contrast != 1.0:
        img = np.float32(image) * contrast
        image = np.uint8(np.clip(img, 0, 255))
    return image

def apply_saturation(image, saturation):
    if saturation == 1.0:
        return image
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype("float32")
    h, s, v = cv2.split(hsv)
    s = np.clip(s * saturation, 0, 255)
    hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

def apply_noise(image, noise_level):
    if noise_level == 0:
        return image
    row, col, ch = image.shape
    gauss = np.random.normal(0, noise_level, (row, col, ch))
    noisy_image = np.clip(image + gauss, 0, 255)
    return noisy_image.astype(np.uint8)
