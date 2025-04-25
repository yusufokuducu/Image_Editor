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
    try:
        from PIL import Image
        if not isinstance(img, Image.Image):
            # Try to create a new RGBA image from the data
            data = np.array(img)
            img = Image.fromarray(data, 'RGBA')
        if not hasattr(img, 'mode') or img.mode != 'RGBA':
            img = img.convert('RGBA')
        # Disk kaydını debug için kaldırdık
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        qt_img = QImage.fromData(buf.getvalue(), 'PNG')
        return QPixmap.fromImage(qt_img)
    except Exception as e:
        print(f'image_to_qpixmap error: {e}')  # Logging yerine print
        return None


def save_image(img, file_path):
    try:
        img.save(file_path)
        return True
    except Exception as e:
        logging.error(f'Resim kaydedilemedi: {e}')
        return False
