from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox,
                             QLabel, QCheckBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QGraphicsRectItem, QSpinBox, QComboBox)
from PyQt6.QtGui import QPixmap, QPen, QBrush, QColor, QCursor, QPainter
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSize
import logging
from PIL import Image
from .image_io import image_to_qpixmap
class ResizeHandleItem(QGraphicsRectItem):
    TOP_LEFT = 0
    TOP = 1
    TOP_RIGHT = 2
    RIGHT = 3
    BOTTOM_RIGHT = 4
    BOTTOM = 5
    BOTTOM_LEFT = 6
    LEFT = 7
    def __init__(self, handle_type, parent=None):
        super().__init__(parent)
        self.handle_type = handle_type
        self.setRect(-5, -5, 10, 10)
        self.setBrush(QBrush(QColor(0, 122, 204)))
        self.setPen(QPen(QColor(255, 255, 255), 1))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        if handle_type in [self.TOP_LEFT, self.BOTTOM_RIGHT]:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif handle_type in [self.TOP_RIGHT, self.BOTTOM_LEFT]:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif handle_type in [self.LEFT, self.RIGHT]:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif handle_type in [self.TOP, self.BOTTOM]:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange and self.scene():
            parent = self.parentItem()
            if isinstance(parent, ResizableImageItem) and not parent._is_programmatic_resize: 
                parent.handle_resize(self.handle_type, value, self.pos()) 
        return super().itemChange(change, value)
class ResizableImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, dialog, parent=None):
        super().__init__(pixmap, parent) 
        self.dialog = dialog 
        self.original_pixmap = pixmap
        self._is_programmatic_resize = False 
        pixmap_height = pixmap.height()
        if pixmap_height > 0:
             self.aspect_ratio = pixmap.width() / pixmap_height
        else:
             self.aspect_ratio = 1.0 
             logging.warning("ResizableImageItem created with zero height pixmap.")
        self.keep_aspect_ratio = True
        self.min_size = 20  
        self.handles = []
        for i in range(8):
            handle = ResizeHandleItem(i, self)
            self.handles.append(handle)
        self.updateHandlePositions()
    def setKeepAspectRatio(self, keep):
        self.keep_aspect_ratio = keep
    def updateHandlePositions(self):
        rect = self.boundingRect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        if len(self.handles) != 8:
             logging.error("updateHandlePositions: Incorrect number of handles.")
             return
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
        rect = self.boundingRect()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        if self.aspect_ratio <= 0:
             logging.error("handle_resize: Invalid aspect ratio (<= 0). Aborting resize.")
             handle_to_reset = self.handles[handle_type]
             handle_to_reset.setPos(original_handle_pos)
             return 
        nx, ny = handle_new_pos.x(), handle_new_pos.y()
        if handle_type == ResizeHandleItem.TOP_LEFT:
            new_w = max(self.min_size, w - (nx - x))
            new_h = max(self.min_size, h - (ny - y))
            if self.keep_aspect_ratio:
                if new_w / self.aspect_ratio >= self.min_size:
                    new_h = new_w / self.aspect_ratio
                elif new_h * self.aspect_ratio >= self.min_size:
                     new_w = new_h * self.aspect_ratio
                else: 
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
            new_h = h 
            if self.keep_aspect_ratio:
                 new_h_cand = new_w / self.aspect_ratio
                 if new_h_cand >= self.min_size:
                     new_h = new_h_cand
                 else:
                     new_w = max(self.min_size * self.aspect_ratio, new_w) 
                     new_h = new_w / self.aspect_ratio
            new_h = max(self.min_size, new_h) 
        elif handle_type == ResizeHandleItem.RIGHT:
            new_w = max(self.min_size, nx - x)
            new_h = h 
            if self.keep_aspect_ratio:
                 new_h_cand = new_w / self.aspect_ratio
                 if new_h_cand >= self.min_size:
                     new_h = new_h_cand
                 else:
                     new_w = max(self.min_size * self.aspect_ratio, new_w) 
                     new_h = new_w / self.aspect_ratio
            new_h = max(self.min_size, new_h) 
        elif handle_type == ResizeHandleItem.TOP:
            new_h = max(self.min_size, h - (ny - y))
            new_w = w 
            if self.keep_aspect_ratio:
                new_w_cand = new_h * self.aspect_ratio
                if new_w_cand >= self.min_size:
                    new_w = new_w_cand
                else:
                    new_h = max(self.min_size / self.aspect_ratio, new_h) 
                    new_w = new_h * self.aspect_ratio
            new_w = max(self.min_size, new_w) 
        elif handle_type == ResizeHandleItem.BOTTOM:
            new_h = max(self.min_size, ny - y)
            new_w = w 
            if self.keep_aspect_ratio:
                new_w_cand = new_h * self.aspect_ratio
                if new_w_cand >= self.min_size:
                    new_w = new_w_cand
                else:
                    new_h = max(self.min_size / self.aspect_ratio, new_h) 
                    new_w = new_h * self.aspect_ratio
            new_w = max(self.min_size, new_w) 
            new_h = max(self.min_size, new_h) 
        else:
             logging.warning(f"handle_resize: Unknown handle_type {handle_type}")
             handle_to_reset = self.handles[handle_type]
             handle_to_reset.setPos(original_handle_pos)
             return
        new_w = int(new_w)
        new_h = int(new_h)
        self._is_programmatic_resize = True
        if hasattr(self.dialog, 'relay_resize_signal'):
            self.dialog.relay_resize_signal(new_w, new_h)
        else:
             logging.error("handle_resize: Dialog object does not have relay_resize_signal method.")
        pass 
class ResizeDialog(QDialog):
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.original_image = layer.image.copy()
        self.original_size = self.original_image.size
        self.setWindowTitle("Görüntü Yeniden Boyutlandır")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
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
        self.keep_aspect_checkbox = QCheckBox("En-boy oranını koru")
        self.keep_aspect_checkbox.setChecked(True)
        self.keep_aspect_checkbox.stateChanged.connect(self.on_keep_aspect_changed)
        resample_layout = QHBoxLayout()
        resample_layout.addWidget(QLabel("Yeniden Örnekleme:"))
        self.resample_combo = QComboBox()
        self.resample_options = {
            "Nearest Neighbor": Image.Resampling.NEAREST,
            "Bilinear": Image.Resampling.BILINEAR,
            "Bicubic": Image.Resampling.BICUBIC,
            "Lanczos": Image.Resampling.LANCZOS, 
        }
        for name in self.resample_options.keys():
            self.resample_combo.addItem(name)
        self.resample_combo.setCurrentText("Lanczos") 
        resample_layout.addWidget(self.resample_combo)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(self.view)
        layout.addLayout(size_layout)
        layout.addWidget(self.keep_aspect_checkbox)
        layout.addLayout(resample_layout) 
        layout.addWidget(button_box)
        self.setup_image()
    def setup_image(self):
        pixmap = image_to_qpixmap(self.original_image)
        if pixmap is None or pixmap.isNull():
            logging.error("ResizeDialog.setup_image: image_to_qpixmap geçersiz bir pixmap döndürdü. Önizleme ayarlanamıyor.")
            return 
        self.resize_item = ResizableImageItem(pixmap, self)
        self.scene.addItem(self.resize_item)
        self.view.setScene(self.scene)
        self.view.fitInView(self.resize_item, Qt.AspectRatioMode.KeepAspectRatio)
    def on_spin_value_changed(self, value):
        sender = self.sender()
        if not self.resize_item: return 
        aspect_ratio = self.resize_item.aspect_ratio
        if aspect_ratio <= 0:
             logging.warning("on_spin_value_changed: Invalid aspect ratio. Cannot maintain ratio.")
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
                self.height_spin.setValue(max(1, new_height))
                self.height_spin.blockSignals(False)
            else:
                new_height = self.height_spin.value()
        else:  
            new_height = value
            if self.keep_aspect_checkbox.isChecked():
                new_width = int(new_height * aspect_ratio)
                self.width_spin.blockSignals(True)
                self.width_spin.setValue(max(1, new_width))
                self.width_spin.blockSignals(False)
            else:
                new_width = self.width_spin.value()
        self._update_preview(new_width, new_height)
    def on_handle_resize(self, new_width, new_height):
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(new_width)
        self.height_spin.setValue(new_height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self._update_preview(new_width, new_height)
    def relay_resize_signal(self, new_width, new_height):
        self.on_handle_resize(new_width, new_height)
    def _update_preview(self, width, height):
        if not self.resize_item or not self.resize_item.original_pixmap: 
             logging.error("_update_preview: resize_item or original_pixmap is missing.")
             return
        width = max(1, width)
        height = max(1, height)
        render_hint = QPainter.RenderHint.SmoothPixmapTransform 
        try:
            original_pixmap = self.resize_item.original_pixmap
            source_rect = QRectF(0, 0, original_pixmap.width(), original_pixmap.height())
            target_rect = QRectF(0, 0, width, height)
            scaled_pixmap = QPixmap(QSize(width, height)) 
            scaled_pixmap.fill(QColor(Qt.GlobalColor.transparent)) 
            painter = QPainter(scaled_pixmap)
            painter.setRenderHint(render_hint)
            painter.drawPixmap(target_rect, original_pixmap, source_rect)
            painter.end()
            self.resize_item.setPixmap(scaled_pixmap)
            self.resize_item.updateHandlePositions() 
            self.resize_item._is_programmatic_resize = False 
        except Exception as e:
            logging.error(f"_update_preview error scaling pixmap: {e}", exc_info=True) 
    def on_keep_aspect_changed(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        if not self.resize_item: return
        self.resize_item.setKeepAspectRatio(is_checked)
        if is_checked:
            current_width = self.width_spin.value()
            current_height = self.height_spin.value()
            if current_height > 0: 
                self.resize_item.aspect_ratio = current_width / current_height
                logging.debug(f"Aspect ratio recalculated and locked to: {self.resize_item.aspect_ratio}")
                self.on_spin_value_changed(current_width)
            else:
                 logging.warning("Cannot lock aspect ratio with zero height.")
    def get_resize_parameters(self):
        keep_aspect = self.keep_aspect_checkbox.isChecked()
        selected_resample_name = self.resample_combo.currentText()
        resample_method = self.resample_options.get(selected_resample_name, Image.Resampling.LANCZOS) 
        return self.width_spin.value(), self.height_spin.value(), keep_aspect, resample_method
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'resize_item') and self.resize_item:
            if not self.scene.sceneRect().isEmpty():
                 self.view.fitInView(self.resize_item, Qt.AspectRatioMode.KeepAspectRatio)
            else:
                 pass 