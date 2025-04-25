from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox
from PyQt6.QtGui import QPixmap, QPainterPath, QPen, QColor, QBrush, QFont, QPainter, QFontMetrics, QImage
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal # Added pyqtSignal
import numpy as np
import logging

class ImageView(QGraphicsView):
    # Signal to request text input at a specific scene point
    textToolClicked = pyqtSignal(QPointF)

    def __init__(self, main_window, parent=None): # Add main_window parameter
        super().__init__(parent)
        self.main_window = main_window # Store reference to main window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._zoom = 0
        # Seçim araçları
        self.selecting = False
        self.selection_rect_item = None
        self.selection_start = None
        self.selection_end = None
        self.selection_mode = 'rectangle'  # 'rectangle', 'ellipse', 'lasso'
        self.lasso_points = []
        self.selection_path_item = None

    def set_image(self, pixmap: QPixmap):
        try:
            if pixmap is None:
                QMessageBox.critical(self, 'Hata', 'Görüntü yüklenemedi veya oluşturulamadı!')
                return

            # Mevcut seçimleri temizle
            self.clear_selection()

            # Sahneyi temizle
            self.scene.clear()

            # Pixmap'i ekle
            self.pixmap_item = self.scene.addPixmap(pixmap)

            # Sahne boyutunu ayarla
            rect = pixmap.rect()
            self.setSceneRect(QRectF(rect))

            # Zoom'u sıfırla
            self._zoom = 0
            self.resetTransform()

            # Görünümü ortala
            self.centerOn(self.pixmap_item)
        except Exception as e:
            logging.error(f"Görüntü ayarlanırken hata: {e}")
            QMessageBox.critical(self, 'Hata', f'Görüntü ayarlanırken hata oluştu: {e}')

    def set_selection_mode(self, mode):
        self.selection_mode = mode
        self.clear_selection()

    def wheelEvent(self, event):
        if self.pixmap_item is None:
            return
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8
        if event.angleDelta().y() > 0:
            factor = zoom_in_factor
            self._zoom += 1
        else:
            factor = zoom_out_factor
            self._zoom -= 1
        if self._zoom < -10:
            self._zoom = -10
            return
        if self._zoom > 20:
            self._zoom = 20
            return
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap_item:
            self.selecting = True
            point = self.mapToScene(event.pos()).toPoint()
            self.selection_start = point
            self.selection_end = point
            if self.selection_mode == 'lasso':
                self.lasso_points = [point]
            if self.selection_rect_item:
                self.scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            if self.selection_path_item:
                self.scene.removeItem(self.selection_path_item)
                self.selection_path_item = None

            # Handle Text Tool click
            if self.main_window.current_tool == 'text':
                scene_point = self.mapToScene(event.pos())
                logging.info(f"Text tool clicked at scene coordinates: {scene_point.x()}, {scene_point.y()}")
                self.textToolClicked.emit(scene_point) # Emit signal with click position
                self.selecting = False # Don't start selection
                # Don't call super().mousePressEvent(event) for text tool to avoid ScrollHandDrag
                return # Stop further processing for text tool click

        # If not text tool, proceed with default behavior (selection or drag)
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.selecting and self.pixmap_item:
            point = self.mapToScene(event.pos()).toPoint()
            self.selection_end = point
            if self.selection_mode == 'rectangle':
                rect = self._get_selection_rect()
                if self.selection_rect_item:
                    self.scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = self.scene.addRect(rect, pen=QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
            elif self.selection_mode == 'ellipse':
                rect = self._get_selection_rect()
                if self.selection_rect_item:
                    self.scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = self.scene.addEllipse(rect, pen=QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine))
            elif self.selection_mode == 'lasso':
                self.lasso_points.append(point)
                if self.selection_path_item:
                    self.scene.removeItem(self.selection_path_item)
                path = QPainterPath()
                if self.lasso_points:
                    pt0 = self.lasso_points[0]
                    if isinstance(pt0, QPointF):
                        path.moveTo(pt0)
                    else:
                        path.moveTo(QPointF(pt0))
                    for pt in self.lasso_points[1:]:
                        if isinstance(pt, QPointF):
                            path.lineTo(pt)
                        else:
                            path.lineTo(QPointF(pt))
                self.selection_path_item = self.scene.addPath(path, pen=QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.selecting:
            self.selecting = False
        super().mouseReleaseEvent(event)

    def _get_selection_rect(self):
        if not self.selection_start or not self.selection_end:
            return QRectF()
        x1, y1 = self.selection_start.x(), self.selection_start.y()
        x2, y2 = self.selection_end.x(), self.selection_end.y()
        left, top = min(x1, x2), min(y1, y2)
        right, bottom = max(x1, x2), max(y1, y2)
        return QRectF(left, top, right - left, bottom - top)

    def get_selected_box(self):
        rect = self._get_selection_rect()
        if self.selection_mode in ['rectangle', 'ellipse'] and rect.width() > 0 and rect.height() > 0:
            return int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom())
        return None

    def get_selection_mask(self, img_shape):
        try:
            mask = np.zeros((img_shape[1], img_shape[0]), dtype=np.uint8)
            if self.selection_mode == 'rectangle':
                box = self.get_selected_box()
                if box:
                    x1, y1, x2, y2 = box
                    # Sınırları kontrol et
                    x1 = max(0, min(x1, img_shape[0]-1))
                    y1 = max(0, min(y1, img_shape[1]-1))
                    x2 = max(0, min(x2, img_shape[0]))
                    y2 = max(0, min(y2, img_shape[1]))
                    if x2 > x1 and y2 > y1:
                        mask[y1:y2, x1:x2] = 1
            elif self.selection_mode == 'ellipse':
                box = self.get_selected_box()
                if box:
                    x1, y1, x2, y2 = box
                    # Sınırları kontrol et
                    if x2 <= x1 or y2 <= y1:
                        return mask
                    try:
                        cy, cx = (y1 + y2) // 2, (x1 + x2) // 2
                        ry, rx = max(1, abs(y2 - y1) // 2), max(1, abs(x2 - x1) // 2)
                        yy, xx = np.ogrid[:img_shape[1], :img_shape[0]]
                        ellipse = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1
                        mask[ellipse] = 1
                    except Exception as e:
                        logging.error(f"Elips maskesi oluşturulurken hata: {e}")
            elif self.selection_mode == 'lasso' and len(self.lasso_points) > 2:
                try:
                    # Matplotlib Path kullanarak lasso seçimi
                    try:
                        from matplotlib.path import Path
                    except ImportError:
                        logging.error("Lasso seçimi için matplotlib kütüphanesi gerekli")
                        return mask

                    pts = [(pt.x(), pt.y()) for pt in self.lasso_points]
                    poly = Path(pts)

                    # Büyük görüntüler için optimize edilmiş yaklaşım
                    # Tüm pikselleri kontrol etmek yerine, sınırlayıcı kutuyu kullan
                    x_min = max(0, int(min(pt[0] for pt in pts)))
                    y_min = max(0, int(min(pt[1] for pt in pts)))
                    x_max = min(img_shape[0], int(max(pt[0] for pt in pts)) + 1)
                    y_max = min(img_shape[1], int(max(pt[1] for pt in pts)) + 1)

                    if x_max > x_min and y_max > y_min:
                        # Sadece sınırlayıcı kutu içindeki pikselleri kontrol et
                        y, x = np.mgrid[y_min:y_max, x_min:x_max]
                        points = np.vstack((x.flatten(), y.flatten())).T
                        mask_region = poly.contains_points(points).reshape(y_max-y_min, x_max-x_min)
                        mask[y_min:y_max, x_min:x_max] = mask_region
                except Exception as e:
                    logging.error(f"Lasso maskesi oluşturulurken hata: {e}")
            return mask
        except Exception as e:
            logging.error(f"Seçim maskesi oluşturulurken hata: {e}")
            return np.zeros((img_shape[1], img_shape[0]), dtype=np.uint8)

    def clear_selection(self):
        if self.selection_rect_item:
            self.scene.removeItem(self.selection_rect_item)
            self.selection_rect_item = None
        if self.selection_path_item:
            self.scene.removeItem(self.selection_path_item)
            self.selection_path_item = None
        self.selection_start = None
        self.selection_end = None
        self.lasso_points = []
