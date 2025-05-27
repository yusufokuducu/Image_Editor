from PIL import Image
import numpy as np
import logging
def load_image(file_path):
    try:
        img = Image.open(file_path)
        img = img.convert('RGBA')  
        return img
    except Exception as e:
        logging.error(f'Görüntü yüklenirken hata: {e}')
        return None
def image_to_qpixmap(img):
    from PyQt6.QtGui import QImage, QPixmap
    import io
    import sys
    old_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(2000)  
    try:
        if img is None:
            logging.warning("image_to_qpixmap: Girdi olarak None alındı.")
            return None
        from PIL import Image
        if isinstance(img, Image.Image):
            img_copy = img.copy()
        else:
            try:
                data = np.array(img)
                if data.ndim == 3 and data.shape[2] == 4:  
                    img_copy = Image.fromarray(data, 'RGBA')
                elif data.ndim == 3 and data.shape[2] == 3:  
                    img_copy = Image.fromarray(data, 'RGB').convert('RGBA')
                elif data.ndim == 2:  
                    img_copy = Image.fromarray(data, 'L').convert('RGBA')
                else:
                    logging.warning(f"image_to_qpixmap: Desteklenmeyen numpy array formatı: {data.shape}")
                    img_copy = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            except Exception as e:
                logging.error(f"image_to_qpixmap: Numpy array'den PIL'e dönüştürme hatası: {e}")
                img_copy = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        if img_copy.mode != 'RGBA':
            img_copy = img_copy.convert('RGBA')
        try:
            arr = np.array(img_copy)
            height, width, channels = arr.shape
            bytes_per_line = channels * width
            qt_img = QImage(arr.data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qt_img)
            if pixmap.isNull():
                 logging.warning("image_to_qpixmap: Numpy'dan QImage ile oluşturulan QPixmap boş.")
            return pixmap
        except Exception as e:
            logging.warning(f"image_to_qpixmap: Numpy'dan doğrudan QImage oluşturma başarısız: {e}. Alternatif yöntem deneniyor.")
            try:
                buf = io.BytesIO()
                img_copy.save(buf, format='PNG')
                buf.seek(0)
                qt_img = QImage.fromData(buf.getvalue(), 'PNG')
                if qt_img.isNull():
                    logging.error("image_to_qpixmap: PNG buffer'dan QImage oluşturulamadı.")
                    return QPixmap()  
                pixmap = QPixmap.fromImage(qt_img)
                if pixmap.isNull():
                    logging.warning("image_to_qpixmap: PNG buffer'dan QImage ile oluşturulan QPixmap boş.")
                return pixmap
            except Exception as e:
                logging.error(f"image_to_qpixmap: PNG buffer yöntemi başarısız: {e}")
                return QPixmap()  
    except Exception as e:
        logging.error(f"image_to_qpixmap: Genel hata: {e}")
        return QPixmap()  
    finally:
        sys.setrecursionlimit(old_recursion_limit)
def save_image(img, file_path):
    try:
        img.save(file_path)
        return True
    except Exception as e:
        logging.error(f'Resim kaydedilemedi: {e}')
        return False