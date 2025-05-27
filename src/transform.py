from PIL import Image
import numpy as np
import cv2
def rotate_image(img, angle):
    if angle in [90, 180, 270]:
        return img.rotate(-angle, expand=True)
    arr = np.array(img)
    (h, w) = arr.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(arr, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(rotated)
def flip_image(img, mode='horizontal'):
    if mode == 'horizontal':
        return img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif mode == 'vertical':
        return img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    else:
        return img
def resize_image(img, width, height, keep_aspect=True):
    if keep_aspect:
        img = img.copy()
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        return img
    else:
        return img.resize((width, height), Image.Resampling.LANCZOS)
def crop_image(img, box):
    return img.crop(box)