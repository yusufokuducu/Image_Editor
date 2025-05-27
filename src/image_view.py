from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsPathItem, QGraphicsRectItem
from PyQt6.QtGui import QPixmap, QPainterPath, QPen, QColor, QBrush, QFont, QPainter, QFontMetrics, QImage, QPolygonF, QCursor
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal, QLineF
import numpy as np
import logging
from .drawing_tools import DrawingTool, Brush, Pencil, Eraser, FillBucket
class ImageView(QGraphicsView):
    textToolClicked = pyqtSignal(QPointF)
    drawingComplete = pyqtSignal(object, object)  
    def __init__(self, main_window, parent=None): 
        super().__init__(parent)
        self.main_window = main_window 
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._zoom = 0
        self._last_scale_factor = 1.0  
        self.selecting = False
        self.selection_rect_item = None
        self.selection_start = QPointF()  
        self.selection_end = QPointF()   
        self.selection_mode = 'rectangle'  
        self.lasso_points = [] 
        self.selection_path_item = None 
        self.current_selection_path = QPainterPath() 
        self.final_selection_item = None 
        self.selection_operation = 'new' 
        self.space_pressed = False 
        self.drawing_tool = None
        self.is_drawing = False
        self.temp_path_item = None
        self.current_paths = []  
    def set_image(self, pixmap: QPixmap):
        try:
            if pixmap is None:
                QMessageBox.critical(self, 'Hata', 'Görüntü yüklenemedi veya oluşturulamadı!')
                return
            self.clear_selection()
            self.scene.clear()
            self.pixmap_item = self.scene.addPixmap(pixmap)
            rect = pixmap.rect()
            self.setSceneRect(QRectF(rect))
            self._zoom = 0
            self.resetTransform()
            self.centerOn(self.pixmap_item)
            if pixmap.height() > 0:
                self.aspect_ratio = pixmap.width() / pixmap.height()
        except Exception as e:
            logging.error(f"Görüntü ayarlanırken hata: {e}")
            QMessageBox.critical(self, 'Hata', f'Görüntü ayarlanırken hata oluştu: {e}')
    def update_image(self, pixmap: QPixmap):
        try:
            if pixmap is None:
                logging.warning("update_image: Pixmap is None")
                return
            current_transform = self.transform()
            current_zoom = self._zoom
            current_scale_factor = self._last_scale_factor
            self.clear_selection()
            self.scene.clear()
            self.pixmap_item = self.scene.addPixmap(pixmap)
            rect = pixmap.rect()
            self.setSceneRect(QRectF(rect))
            self._zoom = current_zoom
            self._last_scale_factor = current_scale_factor
            self.setTransform(current_transform)
            if pixmap.height() > 0:
                self.aspect_ratio = pixmap.width() / pixmap.height()
            logging.debug(f"update_image: Image updated, zoom preserved at level {self._zoom}")
        except Exception as e:
            logging.error(f"Görüntü güncellenirken hata: {e}")
            self.set_image(pixmap)
    def set_selection_mode(self, mode):
        self.selection_mode = mode
        self.clear_selection()
    def wheelEvent(self, event):
        if self.pixmap_item is None:
            return
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            zoom_in_factor = 2.0
            zoom_out_factor = 0.5
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.1
            zoom_out_factor = 0.9
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
        self._last_scale_factor = factor
        self.scale(factor, factor)
    def mousePressEvent(self, event):
        if self.pixmap_item is None:
            return
        is_selection_tool = self.main_window.current_tool in ['select', 'rectangle', 'ellipse', 'lasso']
        is_text_tool = self.main_window.current_tool == 'text'
        is_drawing_tool = self.main_window.current_tool in ['brush', 'pencil', 'eraser']
        is_fill_tool = self.main_window.current_tool == 'fill'
        if event.button() == Qt.MouseButton.LeftButton:
            if self.space_pressed:
                self.selecting = False 
                self.is_drawing = False  
                super().mousePressEvent(event) 
                return 
            if is_text_tool:
                scene_point = self.mapToScene(event.pos())
                logging.info(f"Text tool clicked at scene coordinates: {scene_point.x()}, {scene_point.y()}")
                self.textToolClicked.emit(scene_point)
                self.selecting = False
                self.is_drawing = False
                return 
            if is_drawing_tool:
                self.selecting = False
                self.is_drawing = True
                scene_point = self.mapToScene(event.pos())
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                    self.temp_path_item = None
                self.drawing_tool.start(scene_point)
                self.current_paths = []  
                return 
            if is_fill_tool:
                self.selecting = False
                self.is_drawing = False
                scene_point = self.mapToScene(event.pos())
                if self.drawing_tool and isinstance(self.drawing_tool, FillBucket):
                    line = QLineF(scene_point, scene_point)
                    self.current_paths = [line]
                    self.drawingComplete.emit(self.drawing_tool, self.current_paths)
                    self.current_paths = []
                return 
            if is_selection_tool:
                modifiers = event.modifiers()
                if modifiers & Qt.KeyboardModifier.AltModifier:
                    self.selecting = True
                    self.is_drawing = False  
                    point = self.mapToScene(event.pos())
                    self.selection_start = point
                    self.selection_end = point
                    if modifiers & Qt.KeyboardModifier.ShiftModifier:
                        self.selection_operation = 'add'
                        logging.debug("Selection operation: ADD")
                    elif modifiers & Qt.KeyboardModifier.ControlModifier:
                        self.selection_operation = 'subtract'
                        logging.debug("Selection operation: SUBTRACT")
                    else:
                        self.selection_operation = 'new'
                        logging.debug("Selection operation: NEW")
                        if self.selection_operation == 'new':
                            if self.final_selection_item:
                                self.scene.removeItem(self.final_selection_item)
                                self.final_selection_item = None
                            self.current_selection_path = QPainterPath() 
                    if self.selection_rect_item:
                        self.scene.removeItem(self.selection_rect_item)
                        self.selection_rect_item = None
                    if self.selection_path_item:
                        self.scene.removeItem(self.selection_path_item)
                        self.selection_path_item = None
                    if self.selection_mode == 'lasso':
                        self.lasso_points = [point] 
                    return 
                else:
                    self.selecting = False
                    self.is_drawing = False
                    super().mousePressEvent(event) 
                    return 
            self.selecting = False
            self.is_drawing = False
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self.selecting and not self.space_pressed and self.pixmap_item:
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
                point_f = self.mapToScene(event.pos())
                self.lasso_points.append(point_f)
                if self.selection_path_item:
                    self.scene.removeItem(self.selection_path_item)
                temp_path = QPainterPath()
                if len(self.lasso_points) > 0:
                    temp_path.moveTo(self.lasso_points[0])
                    for pt in self.lasso_points[1:]:
                        temp_path.lineTo(pt)
                self.selection_path_item = self.scene.addPath(temp_path, pen=QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine))
        elif self.is_drawing and not self.space_pressed and self.pixmap_item and self.drawing_tool:
            scene_point = self.mapToScene(event.pos())
            path = self.drawing_tool.move_to(scene_point)
            if path:
                self.current_paths.append(path)
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                combined_path = QPainterPath()
                for p in self.current_paths:
                    if isinstance(p, QPainterPath):
                        combined_path.addPath(p)
                pen_color = self.drawing_tool.color
                pen_width = self.drawing_tool.size
                if isinstance(self.drawing_tool, Eraser):
                    pen_color = QColor(255, 0, 0, 128)  
                self.temp_path_item = self.scene.addPath(
                    combined_path,
                    pen=QPen(pen_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                )
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        was_selecting = self.selecting 
        was_drawing = self.is_drawing  
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and was_selecting and not self.space_pressed:
            new_shape_path = QPainterPath()
            if self.selection_mode == 'rectangle':
                rect = self._get_selection_rect()
                if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                    new_shape_path.addRect(rect)
            elif self.selection_mode == 'ellipse':
                rect = self._get_selection_rect()
                if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                    new_shape_path.addEllipse(rect)
            elif self.selection_mode == 'lasso' and len(self.lasso_points) > 2:
                poly = QPolygonF(self.lasso_points)
                new_shape_path.addPolygon(poly)
                new_shape_path.closeSubpath() 
            if not new_shape_path.isEmpty():
                if self.selection_operation == 'add':
                    self.current_selection_path = self.current_selection_path.united(new_shape_path)
                elif self.selection_operation == 'subtract':
                    self.current_selection_path = self.current_selection_path.subtracted(new_shape_path)
                elif self.selection_operation == 'new':
                    self.current_selection_path = new_shape_path
                else: 
                     self.current_selection_path = new_shape_path
            if self.selection_rect_item:
                self.scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            if self.selection_path_item:
                self.scene.removeItem(self.selection_path_item)
                self.selection_path_item = None
            if self.final_selection_item:
                self.scene.removeItem(self.final_selection_item)
                self.final_selection_item = None
            if not self.current_selection_path.isEmpty():
                self.current_selection_path = self.current_selection_path.simplified()
                pen = QPen(QColor(0, 0, 255, 180), 1, Qt.PenStyle.DashLine) 
                self.final_selection_item = self.scene.addPath(self.current_selection_path, pen)
                if self.final_selection_item:
                    self.final_selection_item.setZValue(10) 
                else:
                    logging.error("Failed to create final_selection_item QGraphicsPathItem")
            self.selecting = False 
            self.lasso_points = []
            self.selection_start = QPointF()
            self.selection_end = QPointF()
            logging.debug(f"Selection finalized. Operation: {self.selection_operation}. Path empty: {self.current_selection_path.isEmpty()}")
        elif event.button() == Qt.MouseButton.LeftButton and was_drawing and not self.space_pressed:
            if self.drawing_tool:
                self.drawing_tool.end()
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                    self.temp_path_item = None
                if self.current_paths:
                    self.drawingComplete.emit(self.drawing_tool, self.current_paths)
                    self.current_paths = []  
            self.is_drawing = False
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            logging.debug("Space pressed, enabling pan")
            event.accept() 
        elif event.key() == Qt.Key.Key_R:
            self.resetZoom()
            event.accept()
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                self.zoom_in()
                event.accept()
            elif event.key() == Qt.Key.Key_Minus:
                self.zoom_out()
                event.accept()
            elif event.key() == Qt.Key.Key_0:
                self.fit_to_window()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = False
            if self.main_window.current_tool in ['brush', 'pencil', 'eraser', 'fill']:
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                if hasattr(self.main_window, '_create_brush_cursor'):
                    if self.main_window.current_tool == 'brush':
                        self.setCursor(self.main_window._create_brush_cursor(self.main_window.current_brush_size))
                    elif self.main_window.current_tool == 'pencil':
                        self.setCursor(self.main_window._create_brush_cursor(self.main_window.current_pencil_size))
                    elif self.main_window.current_tool == 'eraser':
                        self.setCursor(self.main_window._create_brush_cursor(self.main_window.current_eraser_size))
                    elif self.main_window.current_tool == 'fill':
                        self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                self.unsetCursor()
            logging.debug("Space released, disabling pan override")
            event.accept()
        else:
            super().keyReleaseEvent(event)
    def _get_selection_rect(self):
        if not self.selection_start or not self.selection_end:
            return QRectF()
        x1, y1 = self.selection_start.x(), self.selection_start.y()
        x2, y2 = self.selection_end.x(), self.selection_end.y()
        left, top = min(x1, x2), min(y1, y2)
        right, bottom = max(x1, x2), max(y1, y2)
        return QRectF(left, top, right - left, bottom - top)
    def get_selected_box(self):
        if self.current_selection_path.isEmpty():
            return None
        rect = self.current_selection_path.controlPointRect()
        left, top = int(rect.left()), int(rect.top())
        right, bottom = int(rect.right()), int(rect.bottom())
        return left, top, right, bottom
    def get_selection_mask(self, img_shape):
        try:
            width, height = img_shape[0], img_shape[1]
            if self.current_selection_path.isEmpty() or width <= 0 or height <= 0:
                logging.debug(f"get_selection_mask: No selection path or invalid img_shape ({width}x{height}).")
                return np.zeros((height, width), dtype=bool)
            mask = np.zeros((height, width), dtype=bool)
            bounding_rect = self.current_selection_path.controlPointRect()
            min_x = max(0, int(bounding_rect.left()))
            max_x = min(width, int(bounding_rect.right()) + 1) 
            min_y = max(0, int(bounding_rect.top()))
            max_y = min(height, int(bounding_rect.bottom()) + 1) 
            logging.debug(f"Checking pixels in range x:[{min_x}-{max_x}), y:[{min_y}-{max_y})")
            for y in range(min_y, max_y):
                for x in range(min_x, max_x):
                    scene_point = QPointF(x + 0.5, y + 0.5)
                    if self.current_selection_path.contains(scene_point):
                        mask[y, x] = True
            selected_pixels = np.sum(mask)
            logging.debug(f"get_selection_mask: Mask created with {selected_pixels} selected pixels.")
            if mask.shape != (height, width):
                 logging.error(f"Mask shape mismatch! Expected ({height},{width}), got {mask.shape}")
                 return np.zeros((height, width), dtype=bool)
            return mask
        except Exception as e:
            logging.error(f"Error creating selection mask: {e}", exc_info=True)
            w, h = img_shape[0], img_shape[1]
            return np.zeros((h, w), dtype=bool)
    def clear_selection(self):
        if self.selection_rect_item:
            self.scene.removeItem(self.selection_rect_item)
            self.selection_rect_item = None
        if self.selection_path_item:
            self.scene.removeItem(self.selection_path_item)
            self.selection_path_item = None
        if self.final_selection_item:
            self.scene.removeItem(self.final_selection_item)
            self.final_selection_item = None
        self.selection_start = QPointF()
        self.selection_end = QPointF()
        self.lasso_points = []
        self.current_selection_path = QPainterPath() 
        self.selecting = False
        self.selection_operation = 'new'
        logging.debug("Selection cleared.")
    def resetZoom(self):
        if not self.pixmap_item:
            return
        self.resetTransform()
        self._zoom = 0
        self._last_scale_factor = 1.0
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.centerOn(self.pixmap_item)
    def zoom_in(self):
        if not self.pixmap_item:
            return
        factor = 1.25
        self._zoom += 1
        if self._zoom > 20:
            self._zoom = 20
            return
        self._last_scale_factor = factor
        self.scale(factor, factor)
    def zoom_out(self):
        if not self.pixmap_item:
            return
        factor = 0.8
        self._zoom -= 1
        if self._zoom < -10:
            self._zoom = -10
            return
        self._last_scale_factor = factor
        self.scale(factor, factor)
    def fit_to_window(self):
        if not self.pixmap_item:
            return
        self.resetTransform()
        self._zoom = 0
        self._last_scale_factor = 1.0
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.centerOn(self.pixmap_item)