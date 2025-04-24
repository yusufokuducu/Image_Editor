from PIL import Image
import numpy as np
import logging

def load_image(file_path):
    try:
        img = Image.open(file_path)
        img = img.convert('RGBA')  # Tüm resimleri RGBA olarak yükle
        return img
    except Exception as e:
        logging.error(f'Görüntü yüklenirken hata: {e}')
        return None


def image_to_qpixmap(img):
    from PyQt6.QtGui import QImage, QPixmap
    import io
    if img is None:
        return None
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qt_img = QImage.fromData(buf.getvalue(), 'PNG')
    return QPixmap.fromImage(qt_img)


def save_image(img, file_path):
    try:
        img.save(file_path)
        return True
    except Exception as e:
        logging.error(f'Resim kaydedilemedi: {e}')
        return False
