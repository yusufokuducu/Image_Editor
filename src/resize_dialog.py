from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox, 
                             QLabel, QCheckBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QGraphicsRectItem, QSpinBox)
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor, QCursor
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
import logging
from PIL import Image
from .image_io import image_to_qpixmap

class ResizeHandleItem(QGraphicsRectItem):
    """Yeniden boyutlandırma için kullanılan köşe ve kenar tutamaçları."""
    
    # Tutamaç pozisyonları
    TOP_LEFT = 0
    TOP = 1
    TOP_RIGHT = 2
    RIGHT = 3
    BOTTOM_RIGHT = 4
    BOTTOM = 5
    BOTTOM_LEFT = 6
    LEFT = 7
    
    def __init__(self, handle_type, parent=None):
        """handle_type: Tutamacın tipi (köşe veya kenar)"""
        super().__init__(parent)
        self.handle_type = handle_type
        self.setRect(-5, -5, 10, 10)
        self.setBrush(QBrush(QColor(0, 122, 204)))
        self.setPen(QPen(QColor(255, 255, 255), 1))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Tutamaç tipine göre imleç belirle
        if handle_type in [self.TOP_LEFT, self.BOTTOM_RIGHT]:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif handle_type in [self.TOP_RIGHT, self.BOTTOM_LEFT]:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif handle_type in [self.LEFT, self.RIGHT]:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif handle_type in [self.TOP, self.BOTTOM]:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            
    def itemChange(self, change, value):
        """Tutamaç hareket ettiğinde işle"""
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange and self.scene():
            # Parent öğenin (ResizableImage) yeniden boyutlandır metodunu çağır
            parent = self.parentItem()
            if parent:
                parent.handle_resize(self.handle_type, value)
        
        return super().itemChange(change, value)


class ResizableImageItem(QGraphicsPixmapItem):
    """Boyutlandırılabilir görüntü öğesi."""
    
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.original_pixmap = pixmap
        self.aspect_ratio = pixmap.width() / pixmap.height()
        self.keep_aspect_ratio = True
        self.min_size = 20  # Minimum boyut piksel olarak
        
        # Tutamaçları oluştur
        self.handles = []
        for i in range(8):
            handle = ResizeHandleItem(i, self)
            self.handles.append(handle)
        
        self.updateHandlePositions()
        
    def setKeepAspectRatio(self, keep):
        """En-boy oranının korunup korunmayacağını ayarla"""
        self.keep_aspect_ratio = keep
        
    def updateHandlePositions(self):
        """Tutamaçların pozisyonlarını güncelle"""
        rect = self.boundingRect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        # 8 tutamacın pozisyonlarını ayarla
        self.handles[ResizeHandleItem.TOP_LEFT].setPos(x, y)
        self.handles[ResizeHandleItem.TOP].setPos(x + w/2, y)
        self.handles[ResizeHandleItem.TOP_RIGHT].setPos(x + w, y)
        self.handles[ResizeHandleItem.RIGHT].setPos(x + w, y + h/2)
        self.handles[ResizeHandleItem.BOTTOM_RIGHT].setPos(x + w, y + h)
        self.handles[ResizeHandleItem.BOTTOM].setPos(x + w/2, y + h)
        self.handles[ResizeHandleItem.BOTTOM_LEFT].setPos(x, y + h)
        self.handles[ResizeHandleItem.LEFT].setPos(x, y + h/2)
        
    def handle_resize(self, handle_type, new_pos):
        """Tutamaç hareket ettiğinde yeniden boyutlandırma işlemi"""
        rect = self.boundingRect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        # Yeni pozisyonu al
        nx, ny = new_pos.x(), new_pos.y()
        
        # Tutamaç tipine göre yeniden boyutlandırma
        if handle_type == ResizeHandleItem.TOP_LEFT:
            # Sol üst köşe: X ve Y değişir, genişlik ve yükseklik de değişir
            new_w = max(self.min_size, w - (nx - x))
            new_h = max(self.min_size, h - (ny - y))
            
            if self.keep_aspect_ratio:
                # En-boy oranını koru
                if new_w / new_h > self.aspect_ratio:
                    new_w = new_h * self.aspect_ratio
                else:
                    new_h = new_w / self.aspect_ratio
            
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.TOP_RIGHT:
            # Sağ üst köşe: Y değişir, genişlik ve yükseklik değişir
            new_w = max(self.min_size, nx - x)
            new_h = max(self.min_size, h - (ny - y))
            
            if self.keep_aspect_ratio:
                if new_w / new_h > self.aspect_ratio:
                    new_w = new_h * self.aspect_ratio
                else:
                    new_h = new_w / self.aspect_ratio
                    
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.BOTTOM_RIGHT:
            # Sağ alt köşe: Genişlik ve yükseklik değişir
            new_w = max(self.min_size, nx - x)
            new_h = max(self.min_size, ny - y)
            
            if self.keep_aspect_ratio:
                if new_w / new_h > self.aspect_ratio:
                    new_w = new_h * self.aspect_ratio
                else:
                    new_h = new_w / self.aspect_ratio
                    
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.BOTTOM_LEFT:
            # Sol alt köşe: X değişir, genişlik ve yükseklik değişir
            new_w = max(self.min_size, w - (nx - x))
            new_h = max(self.min_size, ny - y)
            
            if self.keep_aspect_ratio:
                if new_w / new_h > self.aspect_ratio:
                    new_w = new_h * self.aspect_ratio
                else:
                    new_h = new_w / self.aspect_ratio
                    
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.LEFT:
            # Sol kenar: X değişir, genişlik değişir
            new_w = max(self.min_size, w - (nx - x))
            new_h = h
            
            if self.keep_aspect_ratio:
                new_h = new_w / self.aspect_ratio
                
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.RIGHT:
            # Sağ kenar: Genişlik değişir
            new_w = max(self.min_size, nx - x)
            new_h = h
            
            if self.keep_aspect_ratio:
                new_h = new_w / self.aspect_ratio
                
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.TOP:
            # Üst kenar: Y değişir, yükseklik değişir
            new_w = w
            new_h = max(self.min_size, h - (ny - y))
            
            if self.keep_aspect_ratio:
                new_w = new_h * self.aspect_ratio
                
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        elif handle_type == ResizeHandleItem.BOTTOM:
            # Alt kenar: Yükseklik değişir
            new_w = w
            new_h = max(self.min_size, ny - y)
            
            if self.keep_aspect_ratio:
                new_w = new_h * self.aspect_ratio
                
            self.setPixmap(self.original_pixmap.scaled(int(new_w), int(new_h), 
                                                      Qt.AspectRatioMode.IgnoreAspectRatio, 
                                                      Qt.TransformationMode.SmoothTransformation))
            
        # Tutamaçların pozisyonlarını güncelle
        self.updateHandlePositions()
        
        # Orijinal pozisyonda kal
        return QPointF(x, y)
    
    def get_new_size(self):
        """Yeni boyutları döndür"""
        return self.pixmap().width(), self.pixmap().height()


class ResizeDialog(QDialog):
    """Görüntü boyutlandırma diyalogu"""
    
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.original_image = layer.image.copy()
        self.original_size = self.original_image.size
        
        self.setWindowTitle("Görüntü Yeniden Boyutlandır")
        self.setMinimumSize(600, 500)
        
        # Ana layout
        layout = QVBoxLayout(self)
        
        # Görüntü önizleme alanı
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(self.view.RenderHint.Antialiasing)
        self.view.setRenderHint(self.view.RenderHint.SmoothPixmapTransform)
        
        # Boyut bilgisi alanı
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(self.original_size[0])
        self.width_spin.valueChanged.connect(self.on_spin_value_changed)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(self.original_size[1])
        self.height_spin.valueChanged.connect(self.on_spin_value_changed)
        
        size_layout.addWidget(QLabel("Genişlik:"))
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("Yükseklik:"))
        size_layout.addWidget(self.height_spin)
        
        # En-boy oranı korunsun mu checkbox'ı
        self.keep_aspect_checkbox = QCheckBox("En-boy oranını koru")
        self.keep_aspect_checkbox.setChecked(True)
        self.keep_aspect_checkbox.stateChanged.connect(self.on_keep_aspect_changed)
        
        # Dialog butonları
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Layout'a ekle
        layout.addWidget(self.view)
        layout.addLayout(size_layout)
        layout.addWidget(self.keep_aspect_checkbox)
        layout.addWidget(button_box)
        
        # Görüntüyü hazırla ve göster
        self.setup_image()
        
    def setup_image(self):
        """Görüntüyü diyalogda göster"""
        pixmap = image_to_qpixmap(self.original_image)
        self.resize_item = ResizableImageItem(pixmap)
        self.scene.addItem(self.resize_item)
        self.view.setScene(self.scene)
        self.view.fitInView(self.resize_item, Qt.AspectRatioMode.KeepAspectRatio)
        
    def on_spin_value_changed(self, value):
        """Spin box değerleri değiştiğinde görüntüyü yeniden boyutlandır"""
        sender = self.sender()
        if sender == self.width_spin:
            new_width = value
            if self.keep_aspect_checkbox.isChecked():
                # En-boy oranını koru
                new_height = int(new_width / self.resize_item.aspect_ratio)
                self.height_spin.blockSignals(True)
                self.height_spin.setValue(new_height)
                self.height_spin.blockSignals(False)
            else:
                new_height = self.height_spin.value()
        else:  # sender == self.height_spin
            new_height = value
            if self.keep_aspect_checkbox.isChecked():
                # En-boy oranını koru
                new_width = int(new_height * self.resize_item.aspect_ratio)
                self.width_spin.blockSignals(True)
                self.width_spin.setValue(new_width)
                self.width_spin.blockSignals(False)
            else:
                new_width = self.width_spin.value()
                
        # Görüntüyü yeniden boyutlandır
        self.resize_item.setPixmap(self.resize_item.original_pixmap.scaled(
            new_width, new_height, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        ))
        self.resize_item.updateHandlePositions()
        
    def on_keep_aspect_changed(self, state):
        """En-boy oranını koruma seçeneği değiştiğinde"""
        self.resize_item.setKeepAspectRatio(state == Qt.CheckState.Checked)
        
    def get_new_size(self):
        """Yeni boyutları döndür"""
        return self.width_spin.value(), self.height_spin.value()
    
    def resizeEvent(self, event):
        """Diyalog yeniden boyutlandırıldığında görüntüyü uyarla"""
        super().resizeEvent(event)
        if hasattr(self, 'resize_item'):
            self.view.fitInView(self.resize_item, Qt.AspectRatioMode.KeepAspectRatio) 