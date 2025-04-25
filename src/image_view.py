from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox
from PyQt6.QtGui import QPixmap, QPainterPath, QPen, QColor, QBrush, QFont, QPainter, QFontMetrics, QImage
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize

class ImageView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        if pixmap is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, 'Hata', 'Görüntü yüklenemedi veya oluşturulamadı!')
            return
        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        # PyQt6: pixmap.rect() -> QRect, fakat setSceneRect QRectF bekler
        rect = pixmap.rect()
        self.setSceneRect(QRectF(rect))
        self._zoom = 0
        self.resetTransform()
        self.clear_selection()

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
        import numpy as np
        mask = np.zeros((img_shape[1], img_shape[0]), dtype=np.uint8)
        if self.selection_mode == 'rectangle':
            box = self.get_selected_box()
            if box:
                x1, y1, x2, y2 = box
                mask[y1:y2, x1:x2] = 1
        elif self.selection_mode == 'ellipse':
            box = self.get_selected_box()
            if box:
                x1, y1, x2, y2 = box
                cy, cx = (y1 + y2) // 2, (x1 + x2) // 2
                ry, rx = abs(y2 - y1) // 2, abs(x2 - x1) // 2
                yy, xx = np.ogrid[:img_shape[1], :img_shape[0]]
                ellipse = ((yy - y1) / (y2 - y1) - 0.5) ** 2 + ((xx - x1) / (x2 - x1) - 0.5) ** 2 <= 0.25
                mask[ellipse] = 1
        elif self.selection_mode == 'lasso' and self.lasso_points:
            from matplotlib.path import Path
            import numpy as np
            pts = [(pt.x(), pt.y()) for pt in self.lasso_points]
            poly = Path(pts)
            yy, xx = np.mgrid[:img_shape[1], :img_shape[0]]
            points = np.vstack((xx.flatten(), yy.flatten())).T
            mask_flat = poly.contains_points(points)
            mask = mask_flat.reshape(mask.shape)
        return mask

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
