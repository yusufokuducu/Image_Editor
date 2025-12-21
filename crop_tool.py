from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QRect, pyqtSignal

class CropTool(QLabel):
    crop_finished = pyqtSignal(int, int, int, int)  # x1, y1, x2, y2
    
    def __init__(self):
        super().__init__()
        self.crop_mode = False
        self.start_pos = None
        self.end_pos = None
        self.original_pixmap = None
        self.setCursor(Qt.CrossCursor)
    
    def set_crop_mode(self, enabled):
        """Enable/disable crop mode"""
        self.crop_mode = enabled
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)
    
    def set_pixmap(self, pixmap):
        """Set pixmap for cropping"""
        super().setPixmap(pixmap)
        self.original_pixmap = pixmap
        self.start_pos = None
        self.end_pos = None
    
    def mousePressEvent(self, event):
        """Start crop selection"""
        if self.crop_mode:
            self.start_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        """Draw crop rectangle while dragging"""
        if self.crop_mode and self.start_pos:
            self.end_pos = event.pos()
            self.draw_crop_rectangle()
    
    def mouseReleaseEvent(self, event):
        """Finish crop selection"""
        if self.crop_mode and self.start_pos and self.end_pos:
            x1 = min(self.start_pos.x(), self.end_pos.x())
            y1 = min(self.start_pos.y(), self.end_pos.y())
            x2 = max(self.start_pos.x(), self.end_pos.x())
            y2 = max(self.start_pos.y(), self.end_pos.y())
            
            self.crop_finished.emit(x1, y1, x2, y2)
            self.crop_mode = False
            self.start_pos = None
            self.end_pos = None
    
    def draw_crop_rectangle(self):
        """Draw crop selection rectangle"""
        if not self.original_pixmap or not self.start_pos or not self.end_pos:
            return
        
        pixmap = self.original_pixmap.copy()
        painter = QPainter(pixmap)
        
        # Semi-transparent overlay
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 100))
        
        # Clear crop area
        crop_rect = QRect(
            min(self.start_pos.x(), self.end_pos.x()),
            min(self.start_pos.y(), self.end_pos.y()),
            abs(self.end_pos.x() - self.start_pos.x()),
            abs(self.end_pos.y() - self.start_pos.y())
        )
        painter.fillRect(crop_rect, QColor(0, 0, 0, 0))
        
        # Draw border
        pen = QPen(QColor(76, 158, 255), 2)
        painter.setPen(pen)
        painter.drawRect(crop_rect)
        
        # Draw handles
        handle_size = 8
        for pos in [crop_rect.topLeft(), crop_rect.topRight(), 
                   crop_rect.bottomLeft(), crop_rect.bottomRight()]:
            painter.fillRect(pos.x() - handle_size//2, pos.y() - handle_size//2,
                            handle_size, handle_size, QColor(76, 158, 255))
        
        painter.end()
        super().setPixmap(pixmap)
