from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox,
                             QLabel, QCheckBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QGraphicsRectItem, QSpinBox, QComboBox)
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor, QCursor, QPainter
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSize
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
            # Check parent type and if resize is not programmatic
            if isinstance(parent, ResizableImageItem) and not parent._is_programmatic_resize: # Type check and flag check
                parent.handle_resize(self.handle_type, value, self.pos()) # Orijinal pozisyonu da gönder
        
        return super().itemChange(change, value)


class ResizableImageItem(QGraphicsPixmapItem):
    """Boyutlandırılabilir görüntü öğesi."""
    
    def __init__(self, pixmap, dialog, parent=None):
        # Call only QGraphicsPixmapItem initializer
        super().__init__(pixmap, parent) 
        self.dialog = dialog # Store reference to the dialog
        
        self.original_pixmap = pixmap
        self._is_programmatic_resize = False # Flag to prevent recursion
        
        # Check if height is zero before calculating aspect ratio
        pixmap_height = pixmap.height()
        if pixmap_height > 0:
             self.aspect_ratio = pixmap.width() / pixmap_height
        else:
             self.aspect_ratio = 1.0 # Default or handle error appropriately
             logging.warning("ResizableImageItem created with zero height pixmap.")
             
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
        
        # Check if handles list is populated correctly
        if len(self.handles) != 8:
             logging.error("updateHandlePositions: Incorrect number of handles.")
             return
             
        # 8 tutamacın pozisyonlarını ayarla
        try:
            self.handles[ResizeHandleItem.TOP_LEFT].setPos(x, y)
            self.handles[ResizeHandleItem.TOP].setPos(x + w/2, y)
            self.handles[ResizeHandleItem.TOP_RIGHT].setPos(x + w, y)
            self.handles[ResizeHandleItem.RIGHT].setPos(x + w, y + h/2)
            self.handles[ResizeHandleItem.BOTTOM_RIGHT].setPos(x + w, y + h)
            self.handles[ResizeHandleItem.BOTTOM].setPos(x + w/2, y + h)
            self.handles[ResizeHandleItem.BOTTOM_LEFT].setPos(x, y + h)
            self.handles[ResizeHandleItem.LEFT].setPos(x, y + h/2)
        except IndexError:
             logging.error("updateHandlePositions: Index error accessing handles. List might be empty or incomplete.")
        
    def handle_resize(self, handle_type, handle_new_pos, original_handle_pos):
        """Tutamaç hareket ettiğinde yeniden boyutlandırma işlemi"""
        rect = self.boundingRect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        # Prevent division by zero if aspect ratio is invalid
        if self.aspect_ratio <= 0:
             logging.error("handle_resize: Invalid aspect ratio (<= 0). Aborting resize.")
             # Optionally reset handle position
             handle_to_reset = self.handles[handle_type]
             handle_to_reset.setPos(original_handle_pos)
             return 
             
        # Yeni pozisyonu al
        nx, ny = handle_new_pos.x(), handle_new_pos.y()
        
        # --- Calculate new_w and new_h based on handle_type --- 
        # (Existing logic seems okay, but ensure min_size is respected)
        if handle_type == ResizeHandleItem.TOP_LEFT:
            new_w = max(self.min_size, w - (nx - x))
            new_h = max(self.min_size, h - (ny - y))
            if self.keep_aspect_ratio:
                if new_w / self.aspect_ratio >= self.min_size:
                    new_h = new_w / self.aspect_ratio
                elif new_h * self.aspect_ratio >= self.min_size:
                     new_w = new_h * self.aspect_ratio
                else: # Cannot maintain aspect ratio and min size
                    # Decide on a strategy: prioritize min_size? Reset?
                    # For now, let's prioritize min_size, aspect ratio might break slightly
                    new_w = max(self.min_size, new_w)
                    new_h = max(self.min_size, new_h)
                    
        elif handle_type == ResizeHandleItem.TOP_RIGHT:
            new_w = max(self.min_size, nx - x)
            new_h = max(self.min_size, h - (ny - y))
            if self.keep_aspect_ratio:
                if new_w / self.aspect_ratio >= self.min_size:
                    new_h = new_w / self.aspect_ratio
                elif new_h * self.aspect_ratio >= self.min_size:
                     new_w = new_h * self.aspect_ratio
                else:
                    new_w = max(self.min_size, new_w)
                    new_h = max(self.min_size, new_h)

        elif handle_type == ResizeHandleItem.BOTTOM_RIGHT:
            new_w = max(self.min_size, nx - x)
            new_h = max(self.min_size, ny - y)
            if self.keep_aspect_ratio:
                if new_w / self.aspect_ratio >= self.min_size:
                    new_h = new_w / self.aspect_ratio
                elif new_h * self.aspect_ratio >= self.min_size:
                     new_w = new_h * self.aspect_ratio
                else:
                    new_w = max(self.min_size, new_w)
                    new_h = max(self.min_size, new_h)

        elif handle_type == ResizeHandleItem.BOTTOM_LEFT:
            new_w = max(self.min_size, w - (nx - x))
            new_h = max(self.min_size, ny - y)
            if self.keep_aspect_ratio:
                if new_w / self.aspect_ratio >= self.min_size:
                    new_h = new_w / self.aspect_ratio
                elif new_h * self.aspect_ratio >= self.min_size:
                     new_w = new_h * self.aspect_ratio
                else:
                    new_w = max(self.min_size, new_w)
                    new_h = max(self.min_size, new_h)

        elif handle_type == ResizeHandleItem.LEFT:
            new_w = max(self.min_size, w - (nx - x))
            new_h = h # Keep height constant initially
            if self.keep_aspect_ratio:
                 new_h_cand = new_w / self.aspect_ratio
                 if new_h_cand >= self.min_size:
                     new_h = new_h_cand
                 else:
                     new_w = max(self.min_size * self.aspect_ratio, new_w) # Recalc W based on min H
                     new_h = new_w / self.aspect_ratio
            new_h = max(self.min_size, new_h) # Ensure min height

        elif handle_type == ResizeHandleItem.RIGHT:
            new_w = max(self.min_size, nx - x)
            new_h = h # Keep height constant initially
            if self.keep_aspect_ratio:
                 new_h_cand = new_w / self.aspect_ratio
                 if new_h_cand >= self.min_size:
                     new_h = new_h_cand
                 else:
                     new_w = max(self.min_size * self.aspect_ratio, new_w) # Recalc W based on min H
                     new_h = new_w / self.aspect_ratio
            new_h = max(self.min_size, new_h) # Ensure min height

        elif handle_type == ResizeHandleItem.TOP:
            new_h = max(self.min_size, h - (ny - y))
            new_w = w # Keep width constant initially
            if self.keep_aspect_ratio:
                new_w_cand = new_h * self.aspect_ratio
                if new_w_cand >= self.min_size:
                    new_w = new_w_cand
                else:
                    new_h = max(self.min_size / self.aspect_ratio, new_h) # Recalc H based on min W
                    new_w = new_h * self.aspect_ratio
            new_w = max(self.min_size, new_w) # Ensure min width
            
        elif handle_type == ResizeHandleItem.BOTTOM:
            new_h = max(self.min_size, ny - y)
            new_w = w # Keep width constant initially
            if self.keep_aspect_ratio:
                new_w_cand = new_h * self.aspect_ratio
                if new_w_cand >= self.min_size:
                    new_w = new_w_cand
                else:
                    new_h = max(self.min_size / self.aspect_ratio, new_h) # Recalc H based on min W
                    new_w = new_h * self.aspect_ratio
            new_w = max(self.min_size, new_w) # Ensure min width
            new_h = max(self.min_size, new_h) # Ensure min height after adjustment
        else:
             # Should not happen, but good to handle
             logging.warning(f"handle_resize: Unknown handle_type {handle_type}")
             # Reset handle position
             handle_to_reset = self.handles[handle_type]
             handle_to_reset.setPos(original_handle_pos)
             return
             
        # --- End Calculation --- 

        # Yeni boyutları tamsayıya çevir
        new_w = int(new_w)
        new_h = int(new_h)

        # Set flag before potentially recursive update path
        self._is_programmatic_resize = True
        # Call the dialog's relay method instead of emitting a signal
        if hasattr(self.dialog, 'relay_resize_signal'):
            self.dialog.relay_resize_signal(new_w, new_h)
        else:
             logging.error("handle_resize: Dialog object does not have relay_resize_signal method.")

        # Tutamacı eski pozisyonuna geri döndür (hareketi iptal et)
        # self.handles[handle_type].setPos(original_handle_pos) # Let dialog handle update
        # Returning the original position from itemChange might be implicitly doing this.
        # Let's rely on itemChange return value for now.
        pass # Explicitly do nothing here regarding handle position


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
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
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
        
        # Yeniden örnekleme metodu
        resample_layout = QHBoxLayout()
        resample_layout.addWidget(QLabel("Yeniden Örnekleme:"))
        self.resample_combo = QComboBox()
        # Add resampling options from PIL.Image.Resampling
        # Using descriptive names
        self.resample_options = {
            "Nearest Neighbor": Image.Resampling.NEAREST,
            "Bilinear": Image.Resampling.BILINEAR,
            "Bicubic": Image.Resampling.BICUBIC,
            "Lanczos": Image.Resampling.LANCZOS, # Default often
            # "Hamming": Image.Resampling.HAMMING, # Less common
            # "Box": Image.Resampling.BOX, # Usually low quality
        }
        for name in self.resample_options.keys():
            self.resample_combo.addItem(name)
        # Set default (e.g., Lanczos)
        self.resample_combo.setCurrentText("Lanczos") 
        resample_layout.addWidget(self.resample_combo)
        
        
        # Dialog butonları
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Layout'a ekle
        layout.addWidget(self.view)
        layout.addLayout(size_layout)
        layout.addWidget(self.keep_aspect_checkbox)
        layout.addLayout(resample_layout) # Add resample options
        layout.addWidget(button_box)
        
        # Görüntüyü hazırla ve göster
        self.setup_image()
        
    def setup_image(self):
        """Görüntüyü diyalogda göster"""
        pixmap = image_to_qpixmap(self.original_image)
        
        if pixmap is None or pixmap.isNull():
            logging.error("ResizeDialog.setup_image: image_to_qpixmap geçersiz bir pixmap döndürdü. Önizleme ayarlanamıyor.")
            return 
            
        # Pass self (the dialog) to ResizableImageItem
        self.resize_item = ResizableImageItem(pixmap, self)
        self.scene.addItem(self.resize_item)
        self.view.setScene(self.scene)
        self.view.fitInView(self.resize_item, Qt.AspectRatioMode.KeepAspectRatio)
        
    def on_spin_value_changed(self, value):
        """Spin box değerleri değiştiğinde görüntüyü yeniden boyutlandır"""
        sender = self.sender()
        if not self.resize_item: return # Ensure resize_item exists

        # Prevent division by zero if aspect ratio is invalid
        aspect_ratio = self.resize_item.aspect_ratio
        if aspect_ratio <= 0:
             logging.warning("on_spin_value_changed: Invalid aspect ratio. Cannot maintain ratio.")
             # Update preview directly without ratio calculation
             if sender == self.width_spin:
                 self._update_preview(value, self.height_spin.value())
             else:
                 self._update_preview(self.width_spin.value(), value)
             return
             
        if sender == self.width_spin:
            new_width = value
            if self.keep_aspect_checkbox.isChecked():
                new_height = int(new_width / aspect_ratio)
                self.height_spin.blockSignals(True)
                # Ensure height doesn't go below 1
                self.height_spin.setValue(max(1, new_height))
                self.height_spin.blockSignals(False)
            else:
                new_height = self.height_spin.value()
        else:  # sender == self.height_spin
            new_height = value
            if self.keep_aspect_checkbox.isChecked():
                new_width = int(new_height * aspect_ratio)
                self.width_spin.blockSignals(True)
                # Ensure width doesn't go below 1
                self.width_spin.setValue(max(1, new_width))
                self.width_spin.blockSignals(False)
            else:
                new_width = self.width_spin.value()
                
        # Görüntü önizlemesini güncelle
        self._update_preview(new_width, new_height)

    # This is now called by relay_resize_signal
    def on_handle_resize(self, new_width, new_height):
        """Handle resize updates originating from ResizableImageItem"""
        # SpinBox'ları güncelle (sinyal döngüsünü engelle)
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(new_width)
        self.height_spin.setValue(new_height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)

        # Görüntü önizlemesini güncelle
        self._update_preview(new_width, new_height)
        
    # New method called by ResizableImageItem
    def relay_resize_signal(self, new_width, new_height):
        """Relays the resize request from ResizableImageItem to the dialog's handler."""
        self.on_handle_resize(new_width, new_height)

    def _update_preview(self, width, height):
        """Önizleme görüntüsünü verilen boyutlarla güncelle"""
        if not self.resize_item or not self.resize_item.original_pixmap: 
             logging.error("_update_preview: resize_item or original_pixmap is missing.")
             return
             
        # Ensure width and height are at least 1
        width = max(1, width)
        height = max(1, height)

        # Choose resampling method for preview (Use FastTransformation for Painter)
        # Note: QPainter's SmoothPixmapTransform hint corresponds to Bilinear filtering
        render_hint = QPainter.RenderHint.SmoothPixmapTransform 
        # render_hint = QPainter.RenderHint.Antialiasing # Optional

        try:
            # Manual scaling using QPainter instead of QPixmap.scaled
            original_pixmap = self.resize_item.original_pixmap
            source_rect = QRectF(0, 0, original_pixmap.width(), original_pixmap.height())
            target_rect = QRectF(0, 0, width, height)
            
            # Create a new pixmap for the target size
            scaled_pixmap = QPixmap(QSize(width, height)) # Use QSize here
            scaled_pixmap.fill(QColor(Qt.GlobalColor.transparent)) # Start with transparent background
            
            # Paint the original onto the new scaled pixmap
            painter = QPainter(scaled_pixmap)
            painter.setRenderHint(render_hint)
            painter.drawPixmap(target_rect, original_pixmap, source_rect)
            painter.end()
            
            self.resize_item.setPixmap(scaled_pixmap)
            self.resize_item.updateHandlePositions() # Update handles after setting pixmap
            # Reset the flag after updates are done
            self.resize_item._is_programmatic_resize = False 
        except Exception as e:
            logging.error(f"_update_preview error scaling pixmap: {e}", exc_info=True) # Add exc_info
        
    def on_keep_aspect_changed(self, state):
        """En-boy oranını koruma seçeneği değiştiğinde"""
        # Use Qt.CheckState enum directly for comparison
        is_checked = (state == Qt.CheckState.Checked.value)
        if not self.resize_item: return
        self.resize_item.setKeepAspectRatio(is_checked)
        
        if is_checked:
            # Recalculate aspect ratio based on current spin box values
            current_width = self.width_spin.value()
            current_height = self.height_spin.value()
            if current_height > 0: # Avoid division by zero
                self.resize_item.aspect_ratio = current_width / current_height
                logging.debug(f"Aspect ratio recalculated and locked to: {self.resize_item.aspect_ratio}")
                # Trigger recalculation based on width (arbitrarily chosen)
                # Need to ensure spin value change triggers preview update correctly
                self.on_spin_value_changed(current_width)
            else:
                 logging.warning("Cannot lock aspect ratio with zero height.")
        
    # Update this method to return resampling method as well
    def get_resize_parameters(self):
        """Yeni boyutları, en-boy oranı koruma durumunu ve yeniden örnekleme metodunu döndür"""
        keep_aspect = self.keep_aspect_checkbox.isChecked()
        selected_resample_name = self.resample_combo.currentText()
        resample_method = self.resample_options.get(selected_resample_name, Image.Resampling.LANCZOS) # Default to Lanczos if not found
        return self.width_spin.value(), self.height_spin.value(), keep_aspect, resample_method

    def resizeEvent(self, event):
        """Diyalog yeniden boyutlandırıldığında görüntüyü uyarla"""
        super().resizeEvent(event)
        if hasattr(self, 'resize_item') and self.resize_item:
            # Ensure scene rect is set before fitting
            if not self.scene.sceneRect().isEmpty():
                 self.view.fitInView(self.resize_item, Qt.AspectRatioMode.KeepAspectRatio)
            else:
                 # If scene rect is empty (e.g., item not fully added yet), maybe queue the fitInView
                 # Or ensure setup_image completes fully before resizeEvent is processed heavily
                 pass # Avoid fitting if scene rect is empty
