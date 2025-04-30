from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsPathItem, QGraphicsRectItem
from PyQt6.QtGui import QPixmap, QPainterPath, QPen, QColor, QBrush, QFont, QPainter, QFontMetrics, QImage, QPolygonF, QCursor
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal # Added pyqtSignal
import numpy as np
import logging
from .drawing_tools import DrawingTool, Brush, Pencil, Eraser, FillBucket

class ImageView(QGraphicsView):
    # Signal to request text input at a specific scene point
    textToolClicked = pyqtSignal(QPointF)
    # Signal for drawing actions
    drawingComplete = pyqtSignal(object, object)  # tool, paths list
    
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
        self.selection_start = QPointF() # Use QPointF
        self.selection_end = QPointF()   # Use QPointF
        self.selection_mode = 'rectangle'  # 'rectangle', 'ellipse', 'lasso'
        self.lasso_points = [] # List of QPointF
        self.selection_path_item = None # Temporary item for lasso drag
        
        # Persistent selection state
        self.current_selection_path = QPainterPath() # The combined selection
        self.final_selection_item = None # The item displaying the combined path
        self.selection_operation = 'new' # 'new', 'add', 'subtract'
        self.space_pressed = False # Track if spacebar is held
        
        # Çizim araçları
        self.drawing_tool = None
        self.is_drawing = False
        self.temp_path_item = None
        self.current_paths = []  # Çizim yollarını tut

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
            
            # Aspect ratio'yu güncelle
            if pixmap.height() > 0:
                self.aspect_ratio = pixmap.width() / pixmap.height()
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
        if self.pixmap_item is None:
            return
            
        is_selection_tool = self.main_window.current_tool in ['select', 'rectangle', 'ellipse', 'lasso']
        is_text_tool = self.main_window.current_tool == 'text'
        is_drawing_tool = self.main_window.current_tool in ['brush', 'pencil', 'eraser']
        is_fill_tool = self.main_window.current_tool == 'fill'

        if event.button() == Qt.MouseButton.LeftButton:
            # Priority 1: Panning with Spacebar
            if self.space_pressed:
                self.selecting = False # Ensure selection doesn't start/continue
                self.is_drawing = False  # Çizimi durdur
                super().mousePressEvent(event) # Allow default panning
                return # Handled

            # Priority 2: Text Tool Click
            if is_text_tool:
                scene_point = self.mapToScene(event.pos())
                logging.info(f"Text tool clicked at scene coordinates: {scene_point.x()}, {scene_point.y()}")
                self.textToolClicked.emit(scene_point)
                self.selecting = False
                self.is_drawing = False  # Çizimi durdur
                # Don't call super() for text tool to prevent unwanted drag
                return # Handled
                
            # Priority 3: Drawing Tools
            if is_drawing_tool:
                self.selecting = False
                self.is_drawing = True
                scene_point = self.mapToScene(event.pos())
                
                # Temp path item'i temizle
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                    self.temp_path_item = None
                
                # Çizim aracını başlat
                self.drawing_tool.start(scene_point)
                self.current_paths = []  # Yeni bir çizim başlıyor
                return # Handled
                
            # Priority 4: Fill Tool
            if is_fill_tool:
                self.selecting = False
                self.is_drawing = False
                scene_point = self.mapToScene(event.pos())
                
                # Fill işlemi doğrudan uygulanır
                if self.drawing_tool and isinstance(self.drawing_tool, FillBucket):
                    active_layer = self.main_window.layers.get_active_layer()
                    if active_layer:
                        self.drawing_tool.apply_to_layer(active_layer, scene_point)
                        self.main_window.refresh_layers()  # UI'yi yenile
                return # Handled

            # Priority 5: Selection Tool Click (No Spacebar)
            if is_selection_tool:
                self.selecting = True
                self.is_drawing = False  # Çizimi durdur
                # Use QPointF for potentially more precision if needed later, though mask uses int
                point = self.mapToScene(event.pos())
                self.selection_start = point
                self.selection_end = point

                # Determine selection operation based on modifiers
                modifiers = event.modifiers()
                if modifiers == Qt.KeyboardModifier.ShiftModifier:
                    self.selection_operation = 'add'
                    logging.debug("Selection operation: ADD")
                elif modifiers == Qt.KeyboardModifier.ControlModifier: # Use Control (Cmd on Mac handled by Qt)
                    self.selection_operation = 'subtract'
                    logging.debug("Selection operation: SUBTRACT")
                else:
                    self.selection_operation = 'new'
                    logging.debug("Selection operation: NEW")
                    # If starting a new selection, clear the old final selection path visually
                    # Do this *before* clearing temporary items
                    if self.selection_operation == 'new':
                        if self.final_selection_item:
                            self.scene.removeItem(self.final_selection_item)
                            self.final_selection_item = None
                        self.current_selection_path = QPainterPath() # Clear internal path too

                # Clear temporary drag graphics from previous operations
                if self.selection_rect_item:
                    self.scene.removeItem(self.selection_rect_item)
                    self.selection_rect_item = None
                if self.selection_path_item:
                    self.scene.removeItem(self.selection_path_item)
                    self.selection_path_item = None

                if self.selection_mode == 'lasso':
                    self.lasso_points = [point] # Start with QPointF

                # Don't call super() for selection tools to prevent ScrollHandDrag
                return # Handled

            # Fallback: Other tools or situations (allow default behavior)
            self.selecting = False
            self.is_drawing = False
            super().mousePressEvent(event)

        else:
            # Handle other mouse buttons (e.g., middle mouse for panning if configured differently)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Only draw selection if selecting AND space is NOT pressed
        if self.selecting and not self.space_pressed and self.pixmap_item:
            point = self.mapToScene(event.pos()).toPoint() # Use toPoint for integer coords
            self.selection_end = point

            # --- Rectangle Selection ---
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
                # Use QPointF for lasso points
                point_f = self.mapToScene(event.pos())
                self.lasso_points.append(point_f)
                if self.selection_path_item:
                    self.scene.removeItem(self.selection_path_item)
                # Create temporary path for lasso drag visualization
                temp_path = QPainterPath()
                if len(self.lasso_points) > 0:
                    temp_path.moveTo(self.lasso_points[0])
                    for pt in self.lasso_points[1:]:
                        temp_path.lineTo(pt)
                # Optionally close the path visually during drag? No, keep it open.
                self.selection_path_item = self.scene.addPath(temp_path, pen=QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine))

            # Do NOT call super().mouseMoveEvent(event) when drawing selection
        elif self.is_drawing and not self.space_pressed and self.pixmap_item and self.drawing_tool:
            # Çizim yolunu oluştur ve göster
            scene_point = self.mapToScene(event.pos())
            
            # Çizgi oluştur
            path = self.drawing_tool.move_to(scene_point)
            if path:
                # Path'i listeye ekle
                self.current_paths.append(path)
                
                # Temp path item'i temizle ve yenisini oluştur
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                
                # Tüm yolları birleştir ve göster
                combined_path = QPainterPath()
                for p in self.current_paths:
                    if isinstance(p, QPainterPath):
                        combined_path.addPath(p)
                
                # Çizim aracına göre çizgi rengini belirle
                pen_color = self.drawing_tool.color
                pen_width = self.drawing_tool.size
                
                # Silgi için özel görselleştirme
                if isinstance(self.drawing_tool, Eraser):
                    pen_color = QColor(255, 0, 0, 128)  # Yarı şeffaf kırmızı (silgileri daha görünür yapar)
                
                # Temp path'i göster
                self.temp_path_item = self.scene.addPath(
                    combined_path, 
                    pen=QPen(pen_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                )
        else:
            # Allow default panning behavior if space is pressed or not actively selecting/drawing
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_selecting = self.selecting # Store state before potential change by super()
        was_drawing = self.is_drawing  # Çizim durumunu kaydet

        # Always call super first to handle default release behavior (like stopping pan)
        super().mouseReleaseEvent(event)

        # Now, finalize selection if we *were* selecting and didn't just release space
        if event.button() == Qt.MouseButton.LeftButton and was_selecting and not self.space_pressed:
            # --- Create path for the shape just drawn ---
            new_shape_path = QPainterPath()
            if self.selection_mode == 'rectangle':
                rect = self._get_selection_rect()
                # Only add if valid and has area
                if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                    new_shape_path.addRect(rect)
            elif self.selection_mode == 'ellipse':
                rect = self._get_selection_rect()
                 # Only add if valid and has area
                if rect.isValid() and rect.width() > 0 and rect.height() > 0:
                    new_shape_path.addEllipse(rect)
            elif self.selection_mode == 'lasso' and len(self.lasso_points) > 2:
                # Close the lasso path
                poly = QPolygonF(self.lasso_points)
                new_shape_path.addPolygon(poly)
                new_shape_path.closeSubpath() # Ensure it's closed for proper combination/filling

            # --- Combine with existing selection path ---
            # current_selection_path might be empty if 'new' operation started
            if not new_shape_path.isEmpty():
                if self.selection_operation == 'add':
                    # Combine even if current_selection_path was empty
                    self.current_selection_path = self.current_selection_path.united(new_shape_path)
                elif self.selection_operation == 'subtract':
                     # Subtract even if current_selection_path was empty (results in empty)
                    self.current_selection_path = self.current_selection_path.subtracted(new_shape_path)
                elif self.selection_operation == 'new':
                    # Path was cleared in press, so just assign the new shape
                    self.current_selection_path = new_shape_path
                else: # Should not happen, but default to 'new'
                     self.current_selection_path = new_shape_path

            # --- Update the visual representation ---
            # Remove temporary drag items FIRST
            if self.selection_rect_item:
                self.scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            if self.selection_path_item:
                self.scene.removeItem(self.selection_path_item)
                self.selection_path_item = None

            # Remove old final item if it exists (it might have been removed in press if 'new')
            if self.final_selection_item:
                self.scene.removeItem(self.final_selection_item)
                self.final_selection_item = None

            # Add the new combined path if it's not empty
            if not self.current_selection_path.isEmpty():
                # Simplify path for cleaner rendering and potentially better performance
                self.current_selection_path = self.current_selection_path.simplified()
                pen = QPen(QColor(0, 0, 255, 180), 1, Qt.PenStyle.DashLine) # Slightly more opaque blue dash
                self.final_selection_item = self.scene.addPath(self.current_selection_path, pen)
                # Ensure the final selection item is properly created before setting ZValue
                if self.final_selection_item:
                    self.final_selection_item.setZValue(10) # Ensure it's drawn on top
                else:
                    logging.error("Failed to create final_selection_item QGraphicsPathItem")


            # Reset selection state for the next operation
            self.selecting = False # Crucial: set selecting to False *after* processing
            self.lasso_points = []
            self.selection_start = QPointF()
            self.selection_end = QPointF()
            # Keep self.selection_operation as is, it's determined on press
            logging.debug(f"Selection finalized. Operation: {self.selection_operation}. Path empty: {self.current_selection_path.isEmpty()}")
                
        # Çizimi sonlandır
        elif event.button() == Qt.MouseButton.LeftButton and was_drawing and not self.space_pressed:
            if self.drawing_tool:
                # Çizimi sonlandır
                self.drawing_tool.end()
                
                # Temp çizim görseli sil
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                    self.temp_path_item = None
                
                # Çizimi uygulamak için sinyal gönder
                if self.current_paths:
                    self.drawingComplete.emit(self.drawing_tool, self.current_paths)
                    self.current_paths = []  # Path listesini temizle
            
            self.is_drawing = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = True
            # Change cursor and drag mode only if a selection tool is active?
            # Or rely on mousePressEvent logic to handle it. Let's keep it simple for now.
            # self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) # Ensure panning is active
            # self.setCursor(Qt.CursorShape.OpenHandCursor)
            logging.debug("Space pressed, enabling pan")
            event.accept() # Indicate event was handled
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = False
            # Restore cursor/drag mode if changed in keyPressEvent
            # self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) # Should already be default
            # self.unsetCursor()
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
        # Return bounding box of the *current* combined selection path
        if self.current_selection_path.isEmpty():
            return None
        # Use controlPointRect for potentially tighter bounds than boundingRect
        rect = self.current_selection_path.controlPointRect()
        # Return as integers. Clamping to image bounds might be needed depending on usage.
        left, top = int(rect.left()), int(rect.top())
        right, bottom = int(rect.right()), int(rect.bottom())
        return left, top, right, bottom


    def get_selection_mask(self, img_shape):
        """ Generates a boolean numpy mask from the current_selection_path. """
        try:
            # Note: PIL uses (width, height), numpy uses (height, width)
            # img_shape comes from PIL Image, so it's (width, height)
            width, height = img_shape[0], img_shape[1]
            
            # Check if there's a selection path and if the image shape is valid
            if self.current_selection_path.isEmpty() or width <= 0 or height <= 0:
                logging.debug(f"get_selection_mask: No selection path or invalid img_shape ({width}x{height}).")
                # Return boolean mask (height, width) matching numpy convention
                return np.zeros((height, width), dtype=bool)

            # Create an empty boolean mask (height, width)
            mask = np.zeros((height, width), dtype=bool)

            # Get the bounding box of the selection path in scene coordinates
            # Use controlPointRect for potentially tighter bounds
            bounding_rect = self.current_selection_path.controlPointRect()

            # Determine the pixel range to check within the image bounds
            # Convert scene coordinates to integer pixel indices, clamping to image boundaries
            # Add a small margin (+1) to ensure boundary pixels are included
            min_x = max(0, int(bounding_rect.left()))
            max_x = min(width, int(bounding_rect.right()) + 1) # Exclusive upper bound for range
            min_y = max(0, int(bounding_rect.top()))
            max_y = min(height, int(bounding_rect.bottom()) + 1) # Exclusive upper bound for range

            logging.debug(f"Checking pixels in range x:[{min_x}-{max_x}), y:[{min_y}-{max_y})")

            # Iterate through the relevant pixel coordinates
            for y in range(min_y, max_y):
                for x in range(min_x, max_x):
                    # Convert pixel center (x+0.5, y+0.5) to scene coordinates
                    # Note: Image coordinates (0,0) correspond to scene coordinates (0,0) top-left
                    scene_point = QPointF(x + 0.5, y + 0.5)
                    
                    # Check if the center of the pixel is inside the path
                    if self.current_selection_path.contains(scene_point):
                        # Set the corresponding pixel in the mask to True
                        # Numpy indexing is [row, column] -> [y, x]
                        mask[y, x] = True

            selected_pixels = np.sum(mask)
            logging.debug(f"get_selection_mask: Mask created with {selected_pixels} selected pixels.")
            
            # Ensure the mask shape matches the expected (height, width)
            if mask.shape != (height, width):
                 logging.error(f"Mask shape mismatch! Expected ({height},{width}), got {mask.shape}")
                 # Return an empty mask in case of error
                 return np.zeros((height, width), dtype=bool)

            return mask

        except Exception as e:
            logging.error(f"Error creating selection mask: {e}", exc_info=True)
            # Return an empty boolean mask on error, matching numpy shape convention
            # Use provided img_shape to determine dimensions
            w, h = img_shape[0], img_shape[1]
            return np.zeros((h, w), dtype=bool)


    def clear_selection(self):
        # Clear temporary items
        if self.selection_rect_item:
            self.scene.removeItem(self.selection_rect_item)
            self.selection_rect_item = None
        if self.selection_path_item:
            self.scene.removeItem(self.selection_path_item)
            self.selection_path_item = None
        # Clear final selection item
        if self.final_selection_item:
            self.scene.removeItem(self.final_selection_item)
            self.final_selection_item = None

        # Reset selection state variables
        self.selection_start = QPointF()
        self.selection_end = QPointF()
        self.lasso_points = []
        self.current_selection_path = QPainterPath() # Reset the path
        self.selecting = False
        self.selection_operation = 'new'
        logging.debug("Selection cleared.")

