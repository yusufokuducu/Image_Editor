from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize, QRectF, QLineF
from PIL import Image, ImageDraw
import numpy as np
import logging

class DrawingTool:
    """Tüm çizim araçları için temel sınıf."""
    
    def __init__(self, color=QColor(0, 0, 0, 255), size=5):
        self.color = color
        self.size = size
        self.prev_point = None
        
    def start(self, point):
        """Çizim başlangıcı."""
        self.prev_point = point
        
    def move_to(self, point):
        """Çizim hareketi, varsayılan olarak doğrusal çizgiyi temsil eder."""
        if self.prev_point is None:
            self.prev_point = point
            return None
            
        line = QLineF(self.prev_point, point)
        self.prev_point = point
        return line
        
    def end(self):
        """Çizim sonu."""
        self.prev_point = None
        
    def set_color(self, color):
        """Renk ayarla."""
        self.color = color
        
    def set_size(self, size):
        """Boyut ayarla."""
        self.size = max(1, size)  # En az 1 piksel olmalı
        
    def apply_to_layer(self, layer, path):
        """Çizimi katmana uygula (PIL Image)."""
        pass

class Brush(DrawingTool):
    """Fırça aracı - yumuşak kenarlı kalın çizgiler."""
    
    def __init__(self, color=QColor(0, 0, 0, 255), size=15):
        super().__init__(color, size)
        self.hardness = 0.7  # 0.0 (çok yumuşak) ile 1.0 (çok sert) arasında
        
    def move_to(self, point):
        """Yumuşak fırça çizgisi oluştur."""
        if self.prev_point is None:
            self.prev_point = point
            return None
            
        # Çizgi oluştur
        path = QPainterPath()
        path.moveTo(self.prev_point)
        path.lineTo(point)
        
        # Bir sonraki çizim için önceki noktayı güncelle
        prev_point = self.prev_point
        self.prev_point = point
        
        return path
        
    def apply_to_layer(self, layer, paths):
        """Fırça çizimini katmana uygula."""
        try:
            # PIL görüntüsü al
            pil_image = layer.image
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
            
            # Çizim için hazırla
            draw = ImageDraw.Draw(pil_image)
            
            # Çizgileri çiz
            for path in paths:
                if isinstance(path, QPainterPath):
                    # Yol üzerindeki tüm noktaları al (basitleştirilmiş)
                    for i in range(0, path.elementCount()-1):
                        start = QPointF(path.elementAt(i).x, path.elementAt(i).y)
                        end = QPointF(path.elementAt(i+1).x, path.elementAt(i+1).y)
                        
                        # Çizgiyi çiz
                        draw.line(
                            [(start.x(), start.y()), (end.x(), end.y())],
                            fill=(
                                self.color.red(), 
                                self.color.green(), 
                                self.color.blue(), 
                                int(self.color.alpha() * self.hardness)
                            ),
                            width=self.size
                        )
            
            # Değiştirilmiş görüntüyü geri yükle
            layer.image = pil_image
            return True
        except Exception as e:
            logging.error(f"Fırça katmana uygulanırken hata: {e}")
            return False

class Pencil(DrawingTool):
    """Kalem aracı - ince ve keskin kenarlı çizgiler."""
    
    def __init__(self, color=QColor(0, 0, 0, 255), size=2):
        super().__init__(color, size)
        
    def move_to(self, point):
        """Kalem çizgisi oluştur."""
        if self.prev_point is None:
            self.prev_point = point
            return None
            
        # Çizgi oluştur
        path = QPainterPath()
        path.moveTo(self.prev_point)
        path.lineTo(point)
        
        # Bir sonraki çizim için önceki noktayı güncelle
        prev_point = self.prev_point
        self.prev_point = point
        
        return path
        
    def apply_to_layer(self, layer, paths):
        """Kalem çizimini katmana uygula."""
        try:
            # PIL görüntüsü al
            pil_image = layer.image
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
            
            # Çizim için hazırla
            draw = ImageDraw.Draw(pil_image)
            
            # Çizgileri çiz
            for path in paths:
                if isinstance(path, QPainterPath):
                    # Yol üzerindeki tüm noktaları al (basitleştirilmiş)
                    for i in range(0, path.elementCount()-1):
                        start = QPointF(path.elementAt(i).x, path.elementAt(i).y)
                        end = QPointF(path.elementAt(i+1).x, path.elementAt(i+1).y)
                        
                        # Çizgiyi çiz - kalem için tam opaklık
                        draw.line(
                            [(start.x(), start.y()), (end.x(), end.y())],
                            fill=(
                                self.color.red(), 
                                self.color.green(), 
                                self.color.blue(), 
                                self.color.alpha()
                            ),
                            width=self.size
                        )
            
            # Değiştirilmiş görüntüyü geri yükle
            layer.image = pil_image
            return True
        except Exception as e:
            logging.error(f"Kalem katmana uygulanırken hata: {e}")
            return False

class Eraser(DrawingTool):
    """Silgi aracı - şeffaf piksel çizen fırça."""
    
    def __init__(self, size=20):
        # Silgi için renk önemli değil, alfa 0 olmalı
        super().__init__(QColor(0, 0, 0, 0), size)
        self.hardness = 1.0  # Silgi keskin kenarlı olsun
        
    def move_to(self, point):
        """Silgi çizgisi oluştur."""
        if self.prev_point is None:
            self.prev_point = point
            return None
            
        # Çizgi oluştur
        path = QPainterPath()
        path.moveTo(self.prev_point)
        path.lineTo(point)
        
        # Bir sonraki çizim için önceki noktayı güncelle
        prev_point = self.prev_point
        self.prev_point = point
        
        return path
        
    def apply_to_layer(self, layer, paths):
        """Silgi çizimini katmana uygula (tamamen şeffaf pikseller çiz)."""
        try:
            # PIL görüntüsü al
            pil_image = layer.image
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
            
            # Çizim için hazırla
            draw = ImageDraw.Draw(pil_image)
            
            # Çizgileri çiz
            for path in paths:
                if isinstance(path, QPainterPath):
                    # Yol üzerindeki tüm noktaları al (basitleştirilmiş)
                    for i in range(0, path.elementCount()-1):
                        start = QPointF(path.elementAt(i).x, path.elementAt(i).y)
                        end = QPointF(path.elementAt(i+1).x, path.elementAt(i+1).y)
                        
                        # Şeffaf çizgiyi çiz (tamamen silgi)
                        draw.line(
                            [(start.x(), start.y()), (end.x(), end.y())],
                            fill=(0, 0, 0, 0),  # Tamamen şeffaf
                            width=self.size
                        )
            
            # Değiştirilmiş görüntüyü geri yükle
            layer.image = pil_image
            return True
        except Exception as e:
            logging.error(f"Silgi katmana uygulanırken hata: {e}")
            return False

class FillBucket(DrawingTool):
    """Kova aracı - alanları doldur."""
    
    def __init__(self, color=QColor(0, 0, 0, 255), tolerance=32):
        super().__init__(color, 1)  # Boyut kova için önemsiz
        self.tolerance = tolerance  # Doldurma toleransı (0-255)
        
    def start(self, point):
        """Kova başlatıldığında, tıklama noktasından doldurmaya başla."""
        self.prev_point = point
        # Doldurma tek bir noktadan başladığı için bir path oluşturulmuyor
        return None
        
    def apply_to_layer(self, layer, point):
        """Doldurma işlemini katmana uygula."""
        try:
            # Tıklama noktasını al
            if isinstance(point, QPointF):
                x, y = int(point.x()), int(point.y())
            else:
                x, y = int(point[0]), int(point[1])
                
            # PIL görüntüsü al
            pil_image = layer.image
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
                
            # Görüntü boyutlarını kontrol et
            width, height = pil_image.size
            if x < 0 or y < 0 or x >= width or y >= height:
                return False  # Resim dışında
                
            # Görüntüyü numpy dizisine dönüştür
            img_array = np.array(pil_image)
            
            # Tıklanan pikselin rengini al
            target_color = img_array[y, x]
            
            # 4 kanal için tolerans kontrolü (RGBA)
            def color_distance(c1, c2):
                return np.sqrt(np.sum((c1[:3] - c2[:3])**2))
                
            # Doldurma rengi
            fill_color = np.array([
                self.color.red(),
                self.color.green(),
                self.color.blue(),
                self.color.alpha()
            ])
            
            # Tıklanan pikselle yeni renk aynıysa, işlemi atla
            if np.array_equal(target_color, fill_color):
                return False
                
            # Doldurma algoritması (flood fill - queue based)
            queue = [(x, y)]
            visited = set([(x, y)])
            
            while queue:
                x, y = queue.pop(0)
                
                # Piksel rengini değiştir
                img_array[y, x] = fill_color
                
                # 4 komşu pikseli kontrol et
                neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
                
                for nx, ny in neighbors:
                    # Sınırlar içinde mi?
                    if 0 <= nx < width and 0 <= ny < height:
                        # Ziyaret edilmemiş mi?
                        if (nx, ny) not in visited:
                            # Renk benzer mi (tolerans dahilinde)?
                            if color_distance(img_array[ny, nx], target_color) <= self.tolerance:
                                # Kuyruğa ekle ve ziyaret edildi olarak işaretle
                                queue.append((nx, ny))
                                visited.add((nx, ny))
            
            # Değiştirilmiş diziyi görüntüye geri dönüştür
            layer.image = Image.fromarray(img_array)
            return True
        except Exception as e:
            logging.error(f"Kova aracı katmana uygulanırken hata: {e}")
            return False 