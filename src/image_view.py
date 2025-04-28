from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox, QGraphicsPathItem
from PyQt6.QtGui import QPixmap, QPainterPath, QPen, QColor, QBrush, QFont, QPainter, QFontMetrics, QImage, QPolygonF # Keep existing imports
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
        self.selection_start = QPointF() # Use QPointF
        self.selection_end = QPointF()   # Use QPointF
        self.selection_mode = 'rectangle'  # 'rectangle', 'ellipse', 'lasso'
        self.lasso_points = [] # List of QPointF
        self.selection_path_item = None # Temporary item for lasso drag
        # self.selection_rect_item is already defined above

        # Persistent selection state
        self.current_selection_path = QPainterPath() # The combined selection
        self.final_selection_item = None # The item displaying the combined path
        self.selection_operation = 'new' # 'new', 'add', 'subtract'
        self.space_pressed = False # Track if spacebar is held

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
        is_selection_tool = self.main_window.current_tool in ['rectangle', 'ellipse', 'lasso']
        is_text_tool = self.main_window.current_tool == 'text'

        if event.button() == Qt.MouseButton.LeftButton and self.pixmap_item:
            # Priority 1: Panning with Spacebar
            if self.space_pressed:
                self.selecting = False # Ensure selection doesn't start/continue
                super().mousePressEvent(event) # Allow default panning
                return # Handled

            # Priority 2: Text Tool Click
            if is_text_tool:
                scene_point = self.mapToScene(event.pos())
                logging.info(f"Text tool clicked at scene coordinates: {scene_point.x()}, {scene_point.y()}")
                self.textToolClicked.emit(scene_point)
                self.selecting = False
                # Don't call super() for text tool to prevent unwanted drag
                return # Handled

            # Priority 3: Selection Tool Click (No Spacebar)
            if is_selection_tool:
                self.selecting = True
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
        else:
            # Allow default panning behavior if space is pressed or not actively selecting
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_selecting = self.selecting # Store state before potential change by super()

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
            # Check if there's a selection path and if the image shape is valid
            if self.current_selection_path.isEmpty() or img_shape[0] <= 0 or img_shape[1] <= 0:
                logging.debug(f"get_selection_mask: No selection path or invalid img_shape {img_shape}.")
                return np.zeros((img_shape[1], img_shape[0]), dtype=bool) # Return boolean mask

            # Create a QImage to render the path onto
            q_img_size = QSize(img_shape[0], img_shape[1])
            # Use Format_Grayscale8 for compatibility and easy numpy conversion
            mask_image = QImage(q_img_size, QImage.Format.Format_Grayscale8)
            if mask_image.isNull():
                logging.error("get_selection_mask: Failed to create mask QImage.")
                return np.zeros((img_shape[1], img_shape[0]), dtype=bool)
            mask_image.fill(Qt.GlobalColor.black) # Fill with 0 (False)

            painter = QPainter(mask_image)
            if not painter.isActive():
                 logging.error("get_selection_mask: Failed to create QPainter for mask.")
                 # Clean up the image if painter creation failed
                 del mask_image
                 return np.zeros((img_shape[1], img_shape[0]), dtype=bool)

            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing) # Smoother mask edges
                painter.setPen(Qt.PenStyle.NoPen) # No outline needed for mask
                painter.setBrush(QBrush(Qt.GlobalColor.white)) # Fill with 1 (True = 255 for Grayscale8)

                # The path coordinates are scene coordinates. Draw it directly.
                painter.drawPath(self.current_selection_path)
            finally:
                # Ensure painter.end() is called even if errors occur during drawing
                painter.end()

            logging.debug(f"get_selection_mask: Path drawn onto QImage ({img_shape[0]}x{img_shape[1]})")

            # Convert QImage to numpy array
            ptr = mask_image.constBits()
            if ptr is None:
                 logging.error("get_selection_mask: Failed to get image bits.")
                 del mask_image # Clean up
                 return np.zeros((img_shape[1], img_shape[0]), dtype=bool)

            # Calculate bytes per line to handle potential padding/stride
            bytes_per_line = mask_image.bytesPerLine()
            height = mask_image.height()
            width = mask_image.width() # Should match img_shape[0]

            # Create numpy array from the memory view, considering stride
            # Use np.frombuffer for direct view without copying if possible
            # Ensure the buffer size matches expected size
            expected_size = height * bytes_per_line
            buffer = ptr.tobytes() # Get bytes from memory view
            if len(buffer) < expected_size:
                 logging.error(f"get_selection_mask: Buffer size mismatch. Expected {expected_size}, got {len(buffer)}")
                 del mask_image
                 return np.zeros((img_shape[1], img_shape[0]), dtype=bool)

            # Create array from buffer
            arr = np.frombuffer(buffer, dtype=np.uint8).reshape((height, bytes_per_line))

            # If stride equals width, we can use the array directly (or slice)
            if bytes_per_line == width:
                arr_cropped = arr
            else:
                # Slice the array to remove padding bytes at the end of each line
                arr_cropped = arr[:, :width].copy() # Copy needed after slicing complex view

            # Mask is where the array is white (255)
            bool_mask = (arr_cropped == 255)
            logging.debug(f"get_selection_mask: Mask created with {np.sum(bool_mask)} selected pixels.")

            # Clean up the QImage explicitly (though Python's GC should handle it)
            del mask_image
            del arr
            del arr_cropped

            return bool_mask

        except Exception as e:
            logging.error(f"Seçim maskesi oluşturulurken hata: {e}", exc_info=True)
            # Return an empty boolean mask on error
            return np.zeros((img_shape[1], img_shape[0]), dtype=bool)


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
