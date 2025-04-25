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
    """
    PIL Image nesnesini QPixmap'e dönüştürür.
    Özyinelemeli referans sorunlarını önlemek için optimize edilmiştir.
    """
    from PyQt6.QtGui import QImage, QPixmap
    import io
    import sys

    # Özyineleme derinliğini geçici olarak artır
    old_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(2000)  # Daha yüksek bir limit belirle

    try:
        # Giriş kontrolü
        if img is None:
            return None

        # PIL Image'e dönüştür
        from PIL import Image

        # Görüntü tipini kontrol et ve kopyasını al
        if isinstance(img, Image.Image):
            # Görüntünün kopyasını al (özyinelemeli referansları önlemek için)
            img_copy = img.copy()
        else:
            try:
                # Numpy array ise PIL görüntüsüne dönüştür
                data = np.array(img)
                if data.ndim == 3 and data.shape[2] == 4:  # RGBA
                    img_copy = Image.fromarray(data, 'RGBA')
                elif data.ndim == 3 and data.shape[2] == 3:  # RGB
                    img_copy = Image.fromarray(data, 'RGB').convert('RGBA')
                elif data.ndim == 2:  # Grayscale
                    img_copy = Image.fromarray(data, 'L').convert('RGBA')
                else:
                    # Desteklenmeyen format için boş görüntü döndür
                    img_copy = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            except Exception:
                # Hata durumunda boş görüntü döndür
                img_copy = Image.new('RGBA', (100, 100), (0, 0, 0, 0))

        # RGBA moduna dönüştür
        if img_copy.mode != 'RGBA':
            img_copy = img_copy.convert('RGBA')

        # Alternatif yöntem: Doğrudan numpy array'den QImage oluştur
        try:
            # Numpy array'e dönüştür
            arr = np.array(img_copy)

            # QImage oluştur
            height, width, channels = arr.shape
            bytes_per_line = channels * width

            # RGBA formatında QImage oluştur
            qt_img = QImage(arr.data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888)

            # QPixmap'e dönüştür
            return QPixmap.fromImage(qt_img)
        except Exception:
            # Alternatif yöntem başarısız olursa, klasik yöntemi dene
            try:
                # Bellek içinde PNG formatına dönüştür
                buf = io.BytesIO()
                img_copy.save(buf, format='PNG')
                buf.seek(0)

                # Qt görüntüsüne dönüştür
                qt_img = QImage.fromData(buf.getvalue(), 'PNG')
                if qt_img.isNull():
                    return QPixmap()  # Boş pixmap döndür

                return QPixmap.fromImage(qt_img)
            except Exception:
                return QPixmap()  # Boş pixmap döndür
    except Exception:
        return QPixmap()  # Boş pixmap döndür
    finally:
        # Özyineleme limitini eski haline getir
        sys.setrecursionlimit(old_recursion_limit)


def save_image(img, file_path):
    try:
        img.save(file_path)
        return True
    except Exception as e:
        logging.error(f'Resim kaydedilemedi: {e}')
        return False
