import gc
import logging
from PIL import Image
from PyQt6.QtWidgets import (QMainWindow, QStatusBar, QMenuBar,
                             QFileDialog, QMessageBox, QInputDialog, QDockWidget,
                             QDialog, QColorDialog, QFontDialog, QWidget, QVBoxLayout,
                             QLabel, QSlider, QPushButton, QHBoxLayout, QScrollArea,
                             QGraphicsView, QToolBar, QComboBox, QSpinBox)
from PyQt6.QtGui import (QFont, QColor, QPixmap, QPainter, QPen, QCursor, QAction,
                         QGuiApplication, QClipboard, QIcon, QDoubleValidator,
                         QShortcut, QKeySequence)
from PyQt6.QtCore import Qt, QTimer, QPointF, QSize, QPoint, QRectF, QSettings
import os
import torch
from .image_io import load_image, image_to_qpixmap
from .image_view import ImageView
from .transform import rotate_image, flip_image, resize_image, crop_image
from .history import History, Command
from .layers import LayerManager
from .layer_panel import LayerPanel
from .effects_panel import EffectsPanel
from .dialogs import FilterSliderDialog
from .resize_dialog import ResizeDialog
from .image_processing import get_filtered_image
from .menu import MenuManager
from .text_utils import get_pil_font, draw_text_on_image
from .utils import (compose_layers_pixmap, validate_layer_operation,
                   create_command, ensure_rgba, create_transparent_image)
from .drawing_tools import Brush, Pencil, Eraser, FillBucket
from .shape_tools import ShapeTool, LineTool, RectangleTool, EllipseTool
from .gpu_utils import configure_gpu, check_gpu_memory, use_cpu_fallback
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyxelEdit')
        self.setGeometry(100, 100, 1024, 768)
        self.settings = QSettings("PyxelEdit", "ImageEditor")
        self.use_gpu = self.settings.value("use_gpu", True, type=bool)
        self.gpu_id = self.settings.value("gpu_id", 0, type=int)
        self.check_gpu_status()
        self.history = History()
        self.layers = LayerManager()
        self.menu_manager = MenuManager(self)
        self.gc_timer = QTimer(self)
        self.gc_timer.timeout.connect(lambda: gc.collect())
        self.gc_timer.start(30000)
        self.original_preview_image = None
        self.preview_active = False
        self.current_preview_filter_type = None
        self.current_tool = 'select'
        self.current_brush_size = 15
        self.current_pencil_size = 2
        self.current_eraser_size = 20
        self.current_color = QColor(0, 0, 0, 255)
        self.current_fill_tolerance = 32
        self._create_drawing_tools()
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(150)
        self.preview_timer.timeout.connect(self._perform_preview_update)
        self.last_preview_value = None
        self._init_ui()
        self.setAcceptDrops(True)
        logging.info("PyxelEdit başlatıldı")
        self.setWindowTitle("PyxelEdit - Image Editor")
        self.setGeometry(100, 100, 1200, 800)
        self.settings = QSettings("PyxelEdit", "ImageEditor")
        self.use_gpu = self.settings.value("use_gpu", True, type=bool)
        self.gpu_id = self.settings.value("gpu_id", 0, type=int)
        self.check_gpu_status()
    def handle_text_tool_click(self, position):
        try:
            if not hasattr(self, 'layers') or not self.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Resim veya katman yok!')
                return
            active_layer = self.layers.get_active_layer()
            if not active_layer:
                QMessageBox.warning(self, 'Uyarı', 'Metin eklenecek bir katman yok!')
                return
            text, ok = QInputDialog.getText(self, 'Metin Ekle', 'Metni girin:')
            if not ok or not text:
                return
            font, ok = QFontDialog.getFont(QFont("Arial", 12), self, "Font Seç")
            if not ok:
                return
            color = QColorDialog.getColor(QColor(0, 0, 0), self, "Metin Rengi Seç")
            if not color.isValid():
                return
            old_img = active_layer.image.copy()
            def do_add_text():
                draw_text_on_image(active_layer.image, text, position, font, color)
                self.refresh_layers()
            def undo_add_text():
                active_layer.image = old_img
                self.refresh_layers()
            active_layer_idx = self.layers.active_index
            command = create_command(
                do_func=do_add_text,
                undo_func=undo_add_text,
                description=f"Metin eklendi (Katman {active_layer_idx+1})"
            )
            do_add_text()
            self.history.push(command)
            self.status_bar.showMessage(f"Metin eklendi: '{text}'", 5000)
        except Exception as e:
            logging.error(f"Metin ekleme hatası: {e}")
            QMessageBox.critical(self, 'Hata', f'Metin eklenirken hata oluştu: {e}')
            if 'old_img' in locals() and active_layer:
                active_layer.image = old_img
                self.refresh_layers()
    def _init_ui(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.image_view = ImageView(self)
        self.setCentralWidget(self.image_view)
        self.menu_manager.create_menus()
        self.image_view.textToolClicked.connect(self.handle_text_tool_click)
        self.image_view.drawingComplete.connect(self.handle_drawing_complete)
        self.image_view.textToolClicked.connect(self.handle_text_tool_click)
        self.layer_panel = LayerPanel(self)
        self.dock = QDockWidget('Katman Paneli', self)
        self.dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.effects_panel = EffectsPanel(self)
        self.effects_dock = QDockWidget('Efektler ve Ayarlamalar', self)
        self.effects_dock.setWidget(self.effects_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.effects_dock)
        self.tabifyDockWidget(self.dock, self.effects_dock)
        self.drawing_tools_panel = self.create_drawing_tools_panel()
        self.drawing_tools_dock = QDockWidget('Çizim Araçları', self)
        self.drawing_tools_dock.setWidget(self.drawing_tools_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.drawing_tools_dock)
        self.dock.raise_()
        self.setup_initial_state()

        # Ana pencere temasını ayarla
        self.setup_main_theme()
    def _create_drawing_tools(self):
        self.brush_tool = Brush(self.current_color, self.current_brush_size)
        self.pencil_tool = Pencil(self.current_color, self.current_pencil_size)
        self.eraser_tool = Eraser(self.current_eraser_size)
        self.fill_tool = FillBucket(self.current_color, self.current_fill_tolerance)
        self.shape_tool = ShapeTool(self.current_color, self.current_brush_size)
        self.line_tool = LineTool(self.current_color, self.current_brush_size)
        self.rectangle_tool = RectangleTool(self.current_color, self.current_brush_size)
        self.ellipse_tool = EllipseTool(self.current_color, self.current_brush_size)
    def _create_brush_cursor(self, size):
        cursor_size = max(20, size + 4)
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawEllipse(2, 2, size, size)
        painter.setPen(QPen(QColor(0, 0, 0), 0.5))
        painter.drawEllipse(2, 2, size, size)
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawPoint(cursor_size // 2, cursor_size // 2)
        painter.end()
        return QCursor(pixmap, cursor_size // 2, cursor_size // 2)
    def set_drawing_color(self, color=None):
        if color is None:
            color = QColorDialog.getColor(
                self.current_color,
                self,
                "Çizim Rengi Seç",
                QColorDialog.ColorDialogOption.ShowAlphaChannel
            )
            if not color.isValid():
                return
        self.current_color = color
        self.brush_tool.set_color(color)
        self.pencil_tool.set_color(color)
        self.fill_tool.set_color(color)
        self.status_bar.showMessage(f"Renk: RGB({color.red()}, {color.green()}, {color.blue()}, A:{color.alpha()})")
    def set_brush_size(self, size=None):
        if size is None:
            size, ok = QInputDialog.getInt(
                self,
                "Fırça Boyutu",
                "Boyut (1-100):",
                self.current_brush_size,
                1, 100
            )
            if not ok:
                return
        self.current_brush_size = size
        self.brush_tool.set_size(size)
        if self.current_tool == 'brush':
            self.image_view.setCursor(self._create_brush_cursor(size))
        self.status_bar.showMessage(f"Fırça Boyutu: {size}px")
    def set_pencil_size(self, size=None):
        if size is None:
            size, ok = QInputDialog.getInt(
                self,
                "Kalem Boyutu",
                "Boyut (1-20):",
                self.current_pencil_size,
                1, 20
            )
            if not ok:
                return
        self.current_pencil_size = size
        self.pencil_tool.set_size(size)
        if self.current_tool == 'pencil':
            self.image_view.setCursor(self._create_brush_cursor(size))
        self.status_bar.showMessage(f"Kalem Boyutu: {size}px")
    def set_eraser_size(self, size=None):
        if size is None:
            size, ok = QInputDialog.getInt(
                self,
                "Silgi Boyutu",
                "Boyut (1-100):",
                self.current_eraser_size,
                1, 100
            )
            if not ok:
                return
        self.current_eraser_size = size
        self.eraser_tool.set_size(size)
        if self.current_tool == 'eraser':
            self.image_view.setCursor(self._create_brush_cursor(size))
        self.status_bar.showMessage(f"Silgi Boyutu: {size}px")
    def set_fill_tolerance(self, tolerance=None):
        if tolerance is None:
            tolerance, ok = QInputDialog.getInt(
                self,
                "Doldurma Toleransı",
                "Tolerans (0-255):",
                self.current_fill_tolerance,
                0, 255
            )
            if not ok:
                return
        self.current_fill_tolerance = tolerance
        self.fill_tool.tolerance = tolerance
        self.status_bar.showMessage(f"Doldurma Toleransı: {tolerance}")
    def handle_drawing_complete(self, tool, paths):
        active_layer = self.layers.get_active_layer()
        if not active_layer:
            QMessageBox.warning(self, "Uyarı", "Çizim yapılacak bir katman yok. Lütfen önce bir katman ekleyin.")
            return
        def do_draw():
            original_image = active_layer.image.copy()
            if isinstance(tool, FillBucket):
                if paths and len(paths) > 0:
                    if hasattr(paths[0], 'p1'):
                        point = paths[0].p1()
                        success = tool.apply_to_layer(active_layer, point)
                    else:
                        success = tool.apply_to_layer(active_layer, paths[0])
                else:
                    logging.warning("Doldurma için geçerli bir nokta bulunamadı")
                    success = False
            else:
                success = tool.apply_to_layer(active_layer, paths)
            self.refresh_layers()
            return original_image
        def undo_draw(original_image):
            active_layer.image = original_image
            self.refresh_layers()
        active_layer_idx = self.layers.active_index
        command = Command(
            do_func=do_draw,
            undo_func=lambda img=None: undo_draw(img),
            description=f"{type(tool).__name__} çizim işlemi (Katman {active_layer_idx+1})"
        )
        result = do_draw()
        command.undo_func = lambda: undo_draw(result)
        self.history.push(command)
    def set_tool(self, tool_name):
        if tool_name in self.menu_manager.tool_actions or tool_name in ['shape', 'line', 'rectangle', 'ellipse']:
            self.current_tool = tool_name
            logging.info(f"Araç değiştirildi: {tool_name}")
            for name, action in self.menu_manager.tool_actions.items():
                action.setChecked(name == tool_name)
            if tool_name == 'select':
                self.status_bar.showMessage("Seçim Aracı: Sürükleyerek gezinin, Alt+Sürükle ile seçim yapın")
            else:
                self.status_bar.showMessage(f"Aktif Araç: {tool_name.capitalize()}")
            is_drawing_tool = tool_name in ['brush', 'pencil', 'eraser', 'fill', 'shape', 'line', 'rectangle', 'ellipse']
            if is_drawing_tool:
                self.image_view.setDragMode(QGraphicsView.DragMode.NoDrag)
            else:
                self.image_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            if tool_name == 'select':
                self.image_view.set_selection_mode('rectangle')
                self.image_view.setCursor(Qt.CursorShape.ArrowCursor)
            elif tool_name == 'brush':
                self.image_view.drawing_tool = self.brush_tool
                self.image_view.setCursor(self._create_brush_cursor(self.current_brush_size))
            elif tool_name == 'pencil':
                self.image_view.drawing_tool = self.pencil_tool
                self.image_view.setCursor(self._create_brush_cursor(self.current_pencil_size))
            elif tool_name == 'eraser':
                self.image_view.drawing_tool = self.eraser_tool
                self.image_view.setCursor(self._create_brush_cursor(self.current_eraser_size))
            elif tool_name == 'fill':
                self.image_view.drawing_tool = self.fill_tool
                self.image_view.setCursor(Qt.CursorShape.PointingHandCursor)
            elif tool_name == 'text':
                self.image_view.setCursor(Qt.CursorShape.IBeamCursor)
            else:
                self.image_view.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            logging.warning(f"Bilinmeyen araç adı: {tool_name}")
    def _load_image_from_path(self, file_path):
        try:
            img = load_image(file_path)
            if img is not None:
                if not hasattr(self, 'layers') or not self.layers or not self.layers.layers:
                    self.layers = LayerManager()
                    self.history = History()
                    self.layers.add_layer(img, 'Arka Plan')
                    self.current_image_path = file_path
                else:
                    file_name = os.path.basename(file_path)
                    layer_name = os.path.splitext(file_name)[0]
                    self.layers.add_layer(img, layer_name)
                merged = self.layers.merge_visible()
                if merged:
                    pixmap = image_to_qpixmap(merged)
                    self.image_view.set_image(pixmap)
                    self.status_bar.showMessage(f'{file_path} | {img.width}x{img.height}')
                    self.refresh_layers()
                    logging.info(f"Resim yüklendi: {file_path}")
                    return True
                else:
                    QMessageBox.warning(self, 'Uyarı', 'Resim katmanı oluşturulamadı.')
                    return False
            else:
                QMessageBox.critical(self, 'Hata', f'Resim yüklenemedi: {file_path}')
                return False
        except Exception as e:
            logging.error(f"Error loading image from path {file_path}: {e}")
            QMessageBox.critical(self, 'Hata', f'Resim yüklenirken hata oluştu:\n{e}')
            return False
    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Resim Aç', '', 'Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif)')
        if file_path:
            self._load_image_from_path(file_path)
    def save_image(self):
        if not hasattr(self, 'layers') or not self.layers.layers or not hasattr(self, 'current_image_path'):
            QMessageBox.warning(self, 'Uyarı', 'Kaydedilecek bir resim veya yol yok!')
            return
        merged_image = self.layers.merge_visible()
        if merged_image is None:
             QMessageBox.warning(self, 'Uyarı', 'Görünür katman bulunamadı!')
             return
        try:
            merged_image.save(self.current_image_path)
            self.status_bar.showMessage(f'Resim kaydedildi: {self.current_image_path}')
        except Exception as e:
            logging.error(f"Save error: {e}")
            QMessageBox.critical(self, 'Hata', f'Resim kaydedilemedi!\n{e}')
    def save_image_as(self):
        if not hasattr(self, 'layers') or not self.layers.layers:
            QMessageBox.warning(self, 'Uyarı', 'Kaydedilecek bir resim yok!')
            return
        merged_image = self.layers.merge_visible()
        if merged_image is None:
             QMessageBox.warning(self, 'Uyarı', 'Görünür katman bulunamadı!')
             return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Farklı Kaydet', '', 'Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif)')
        if file_path:
            try:
                merged_image.save(file_path)
                self.current_image_path = file_path
                self.status_bar.showMessage(f'Resim farklı kaydedildi: {file_path}')
            except Exception as e:
                logging.error(f"Save As error: {e}")
                QMessageBox.critical(self, 'Hata', f'Resim kaydedilemedi!\n{e}')
    def close_image(self):
        self.image_view.scene.clear()
        self.layers = LayerManager()
        self.history = History()
        self.current_image_path = None
        self.status_bar.clearMessage()
        self.layer_panel.refresh()
    def blur_dialog(self):
        dialog = FilterSliderDialog(
            title='Bulanıklık Ayarı',
            label_text='Yarıçap',
            min_val=1,
            max_val=20,
            initial_val=2,
            step=1,
            decimals=0,
            parent=self
        )
        self._setup_preview_dialog(dialog, 'blur')
    def noise_dialog(self):
        dialog = FilterSliderDialog(
            title='Noise Ayarı',
            label_text='Miktar',
            min_val=0.01,
            max_val=1.0,
            initial_val=0.1,
            step=0.01,
            decimals=2,
            parent=self
        )
        self._setup_preview_dialog(dialog, 'noise')
    def brightness_dialog(self):
        dialog = FilterSliderDialog(
            title='Parlaklık Ayarı', label_text='Faktör',
            min_val=0.1, max_val=3.0, initial_val=1.0, step=0.05, decimals=2, parent=self
        )
        self._setup_preview_dialog(dialog, 'brightness')
    def contrast_dialog(self):
        dialog = FilterSliderDialog(
            title='Kontrast Ayarı', label_text='Faktör',
            min_val=0.1, max_val=3.0, initial_val=1.0, step=0.05, decimals=2, parent=self
        )
        self._setup_preview_dialog(dialog, 'contrast')
    def saturation_dialog(self):
        dialog = FilterSliderDialog(
            title='Doygunluk Ayarı', label_text='Faktör',
            min_val=0.0, max_val=3.0, initial_val=1.0, step=0.05, decimals=2, parent=self
        )
        self._setup_preview_dialog(dialog, 'saturation')
    def hue_dialog(self):
        dialog = FilterSliderDialog(
            title='Ton Ayarı', label_text='Kaydırma (-180° ile +180°)',
            min_val=-1.0, max_val=1.0, initial_val=0.0, step=0.01, decimals=2, parent=self
        )
        self._setup_preview_dialog(dialog, 'hue')
    def _setup_preview_dialog(self, dialog, filter_type):
        if not hasattr(self, 'layers') or not self.layers.get_active_layer():
            QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açın ve bir katman seçin!')
            return
        layer = self.layers.get_active_layer()
        if layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Aktif katmanda görüntü yok!')
            return
        self.original_preview_image = layer.image.copy()
        self.preview_active = True
        self.current_preview_filter_type = filter_type
        self.last_preview_value = dialog.get_value()
        dialog.valueChangedPreview.connect(self._request_preview_update)
        dialog.finished.connect(lambda result: self._finalize_preview(result, filter_type, dialog))
        self._perform_preview_update()
        dialog.exec()
    def _request_preview_update(self, value):
        self.last_preview_value = value
        if self.preview_active:
            self.preview_timer.start()
    def _perform_preview_update(self):
        if not self.preview_active or self.original_preview_image is None or self.last_preview_value is None:
            return
        self.preview_timer.stop()
        layer = self.layers.get_active_layer()
        if layer is None:
            return
        try:
            img_copy = self.original_preview_image.copy()
            preview_img = get_filtered_image(img_copy, self.current_preview_filter_type, self.last_preview_value)
            if preview_img:
                layer.image = preview_img
                pixmap = self._compose_layers_pixmap()
                if pixmap and not pixmap.isNull():
                    self.image_view.update_image(pixmap)
        except Exception as e:
            logging.error(f"Preview filter error ({self.current_preview_filter_type}): {e}")
    def _finalize_preview(self, result, filter_type, dialog):
        if not self.preview_active:
            return
        self.preview_timer.stop()
        layer = self.layers.get_active_layer()
        original_image_to_restore = self.original_preview_image.copy()
        self.preview_active = False
        self.original_preview_image = None
        self.current_preview_filter_type = None
        self.last_preview_value = None
        if layer is None:
             logging.warning("Finalize preview called with no active layer.")
             return
        if result == QDialog.DialogCode.Accepted:
            final_value = dialog.get_value()
            logging.info(f"Applying final filter: {filter_type} with value: {final_value}")
            self.apply_filter(filter_type, final_value, base_image=original_image_to_restore)
        else:
            logging.info(f"Filter preview cancelled: {filter_type}. Restoring original.")
            layer.image = original_image_to_restore
            self.refresh_layers()
        try:
            dialog.valueChangedPreview.disconnect()
            dialog.finished.disconnect()
        except TypeError:
            pass
        except Exception as e:
            logging.warning(f"Error disconnecting dialog signals: {e}")
    def sharpen_dialog(self):
        dialog = FilterSliderDialog(
            title='Keskinlik Ayarı',
            label_text='Miktar',
            min_val=0.0,
            max_val=1.0,
            initial_val=1.0,
            step=0.05,
            decimals=2,
            parent=self
        )
        self._setup_preview_dialog(dialog, 'sharpen')
    def grayscale_dialog(self):
        dialog = FilterSliderDialog(
            title='Gri Ton Ayarı',
            label_text='Miktar',
            min_val=0.0,
            max_val=1.0,
            initial_val=1.0,
            step=0.05,
            decimals=2,
            parent=self
        )
        self._setup_preview_dialog(dialog, 'grayscale')
    def apply_filter(self, filter_type, param=None, base_image=None):
        logging.info(f"Applying filter/adjustment: {filter_type}, param: {param}")
        if not hasattr(self, 'layers'):
            QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
            return
        layer = self.layers.get_active_layer()
        if layer is None:
            QMessageBox.warning(self, 'Uyarı', 'Uygulanacak katman yok!')
            return
        if base_image is None:
            if layer.image is None:
                 QMessageBox.warning(self, 'Uyarı', 'Aktif katmanda görüntü yok!')
                 return
            start_img = layer.image.copy()
        else:
            start_img = base_image.copy()
        old_img_for_undo = start_img.copy()
        try:
            new_img = get_filtered_image(start_img, filter_type, param)
            if new_img is None:
                raise ValueError(f"Filter application returned None for {filter_type}")
            current_layer_ref = layer
            final_new_img = new_img.copy()
            def do_action():
                try:
                    current_layer_ref.image = final_new_img.copy()
                    self.refresh_layers()
                except Exception as e:
                    logging.error(f"Filter/Adjustment 'do' action error ({filter_type}): {e}")
            def undo_action():
                try:
                    current_layer_ref.image = old_img_for_undo.copy()
                    self.refresh_layers()
                except Exception as e:
                    logging.error(f"Filter/Adjustment 'undo' action error ({filter_type}): {e}")
            cmd = create_command(do_action, undo_action, f'İşlem: {filter_type}')
            cmd.do()
            self.history.push(cmd)
            self.status_bar.showMessage(f'{filter_type} işlemi uygulandı.')
        except Exception as e:
            logging.error(f'apply_filter error ({filter_type}): {e}')
            QMessageBox.critical(self, 'Hata', f'İşlem uygulanırken hata oluştu ({filter_type}): {e}')
            try:
                layer.image = old_img_for_undo.copy()
                self.refresh_layers()
            except Exception as restore_error:
                 logging.error(f"Error restoring image after filter failure: {restore_error}")
    def apply_transform(self, ttype):
        if not hasattr(self, 'layers'):
             QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
             return
        layer = self.layers.get_active_layer()
        if layer is None or layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Dönüştürülecek aktif katman yok!')
            return
        old_img = layer.image.copy()
        img = layer.image
        if ttype == 'rotate90':
            img = rotate_image(img, 90)
        elif ttype == 'rotate180':
            img = rotate_image(img, 180)
        elif ttype == 'rotate270':
            img = rotate_image(img, 270)
        elif ttype == 'flip_h':
            img = flip_image(img, 'horizontal')
        elif ttype == 'flip_v':
            img = flip_image(img, 'vertical')
            return
        if img is None:
             QMessageBox.critical(self, 'Hata', 'Dönüşüm başarısız oldu!')
             return
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        current_layer_ref = layer
        new_img_copy = img.copy()
        old_img_copy = old_img.copy()
        def do():
            try:
                current_layer_ref.image = new_img_copy.copy()
                self.refresh_layers()
            except Exception as e:
                logging.error(f"Dönüşüm uygulama (do) hatası: {e}")
        def undo():
            try:
                current_layer_ref.image = old_img_copy.copy()
                self.refresh_layers()
            except Exception as e:
                logging.error(f"Dönüşüm geri alma (undo) hatası: {e}")
        cmd = create_command(do, undo, f'Dönüşüm: {ttype}')
        cmd.do()
        self.history.push(cmd)
        self.status_bar.showMessage('Dönüşüm uygulandı: ' + ttype)
    def resize_dialog(self):
        if not hasattr(self, 'layers'):
             QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
             return
        layer = self.layers.get_active_layer()
        if layer is None or layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Boyutlandırılacak aktif katman yok!')
            return
        w, h = layer.image.width, layer.image.height
        width, ok1 = QInputDialog.getInt(self, 'Yeniden Boyutlandır', 'Yeni genişlik:', w, 1, 10000)
        if not ok1: return
        height, ok2 = QInputDialog.getInt(self, 'Yeniden Boyutlandır', 'Yeni yükseklik:', h, 1, 10000)
        if not ok2: return
        keep_aspect, _ = QInputDialog.getItem(self, 'Oran Koru', 'Oran korunsun mu?', ['Evet', 'Hayır'], 0, False)
        old_img = layer.image.copy()
        try:
            img = resize_image(layer.image, width, height, keep_aspect == 'Evet')
            if img is None: raise ValueError("Resize returned None")
            if img.mode != 'RGBA': img = img.convert('RGBA')
        except Exception as e:
            logging.error(f"Resize error: {e}")
            QMessageBox.critical(self, 'Hata', f'Yeniden boyutlandırma başarısız: {e}')
            return
        current_layer_ref = layer
        new_img_copy = img.copy()
        old_img_copy = old_img.copy()
        def do():
            try:
                current_layer_ref.image = new_img_copy.copy()
                self.refresh_layers()
            except Exception as e:
                logging.error(f"Resize uygulama (do) hatası: {e}")
        def undo():
            try:
                current_layer_ref.image = old_img_copy.copy()
                self.refresh_layers()
            except Exception as e:
                logging.error(f"Resize geri alma (undo) hatası: {e}")
        cmd = create_command(do, undo, 'Yeniden Boyutlandır')
        cmd.do()
        self.history.push(cmd)
        self.status_bar.showMessage(f'Aktif katman yeniden boyutlandırıldı: {width}x{height} (Oran Koru: {keep_aspect})')
    def crop_selected(self):
        if not hasattr(self, 'layers'):
             QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
             return
        layer = self.layers.get_active_layer()
        if layer is None or layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Kırpılacak aktif katman yok!')
            return
        box = self.image_view.get_selected_box()
        if not box:
            QMessageBox.warning(self, 'Uyarı', 'Kırpma için bir alan seçmelisiniz!')
            return
        old_img = layer.image.copy()
        try:
            img = crop_image(layer.image, box)
            if img is None: raise ValueError("Crop returned None")
            if img.mode != 'RGBA': img = img.convert('RGBA')
        except Exception as e:
            logging.error(f"Crop error: {e}")
            QMessageBox.critical(self, 'Hata', f'Kırpma başarısız: {e}')
            return
        current_layer_ref = layer
        new_img_copy = img.copy()
        old_img_copy = old_img.copy()
        def do():
            try:
                current_layer_ref.image = new_img_copy.copy()
                new_canvas = Image.new('RGBA', old_img_copy.size, (0,0,0,0))
                paste_x = box[0]
                paste_y = box[1]
                new_canvas.paste(current_layer_ref.image, (paste_x, paste_y))
                current_layer_ref.image = new_canvas
                self.refresh_layers()
                self.image_view.clear_selection()
            except Exception as e:
                logging.error(f"Kırpma uygulama (do) hatası: {e}")
        def undo():
            try:
                current_layer_ref.image = old_img_copy.copy()
                self.refresh_layers()
            except Exception as e:
                logging.error(f"Kırpma geri alma (undo) hatası: {e}")
        cmd = Command(do, undo, 'Kırp')
        cmd.do()
        self.history.push(cmd)
        self.status_bar.showMessage('Aktif katman kırpıldı.')
    def undo(self):
        if self.history.undo():
            self.status_bar.showMessage('Geri alındı.')
            self.refresh_layers()
        else:
            self.status_bar.showMessage('Geri alınacak işlem yok.')
    def redo(self):
        if self.history.redo():
            self.status_bar.showMessage('Yinele uygulandı.')
            self.refresh_layers()
        else:
            self.status_bar.showMessage('Yinelenecek işlem yok.')
    def add_layer(self):
        logging.debug("add_layer called")
        if not hasattr(self, 'layers') or not self.layers.layers:
             QMessageBox.warning(self, 'Uyarı', 'Yeni katman eklemek için önce bir resim açın veya mevcut bir katman olmalı!')
             logging.warning("add_layer aborted: No layers exist.")
             return
        try:
            base_size = self.layers.layers[0].image.size
            img = Image.new('RGBA', base_size, (0,0,0,0))
            self.layers.add_layer(img, f'Katman {len(self.layers.layers)+1}')
            self.refresh_layers()
            self.status_bar.showMessage('Yeni katman eklendi.')
            logging.info("add_layer completed successfully.")
        except Exception as e:
            logging.error(f"add_layer error: {e}")
            QMessageBox.critical(self, 'Hata', f'Yeni katman eklenirken hata: {e}')
    def delete_layer(self):
        logging.debug("delete_layer called")
        idx = self.layers.active_index
        if idx == -1:
            QMessageBox.warning(self, 'Uyarı', 'Silinecek katman yok! Lütfen bir katman seçin.')
            logging.warning("delete_layer aborted: No active layer selected.")
            return
        try:
            layer_name = self.layers.layers[idx].name
            self.layers.remove_layer(idx)
            self.refresh_layers()
            self.status_bar.showMessage(f"'{layer_name}' katmanı silindi.")
            logging.info(f"delete_layer completed successfully for index {idx}.")
        except Exception as e:
            logging.error(f"delete_layer error: {e}")
            QMessageBox.critical(self, 'Hata', f'Katman silinirken hata: {e}')
    def merge_layers(self):
        logging.debug("merge_layers called")
        if not hasattr(self, 'layers') or len(self.layers.layers) < 2:
            QMessageBox.warning(self, 'Uyarı', 'Birleştirmek için en az 2 katman olmalı.')
            logging.warning("merge_layers aborted: Less than 2 layers exist.")
            return
        try:
            merged_img = self.layers.merge_visible()
            if merged_img:
                old_layers_list = list(self.layers.layers)
                old_active_index = self.layers.active_index
                def do():
                    logging.debug("merge_layers 'do' action executing.")
                    self.layers.layers.clear()
                    self.layers.add_layer(merged_img.copy(), 'Birleştirilmiş Katman')
                    self.refresh_layers()
                    self.status_bar.showMessage('Görünür katmanlar birleştirildi.')
                    logging.info("merge_layers 'do' action completed.")
                def undo():
                    logging.debug("merge_layers 'undo' action executing.")
                    self.layers.layers = list(old_layers_list)
                    self.layers.active_index = old_active_index
                    self.refresh_layers()
                    self.status_bar.showMessage('Katman birleştirme geri alındı.')
                    logging.info("merge_layers 'undo' action completed.")
                cmd = Command(do, undo, 'Katmanları Birleştir')
                cmd.do()
                self.history.push(cmd)
                logging.info("merge_layers completed successfully and added to history.")
            else:
                QMessageBox.warning(self, 'Uyarı', 'Birleştirilecek görünür katman bulunamadı.')
                logging.warning("merge_layers aborted: merge_visible returned None.")
        except Exception as e:
             logging.error(f"merge_layers error: {e}")
             QMessageBox.critical(self, 'Hata', f'Katmanlar birleştirilirken hata: {e}')
    def toggle_layer_visibility(self):
        logging.debug("toggle_layer_visibility called")
        idx = self.layers.active_index
        if idx == -1:
            QMessageBox.warning(self, 'Uyarı', 'Görünürlüğü değiştirilecek katman yok! Lütfen bir katman seçin.')
            logging.warning("toggle_layer_visibility aborted: No active layer selected.")
            return
        try:
            self.layers.toggle_visibility(idx)
            layer_name = self.layers.layers[idx].name
            visibility_status = 'görünür' if self.layers.layers[idx].visible else 'gizli'
            self.refresh_layers()
            self.status_bar.showMessage(f"'{layer_name}' katmanı {visibility_status} yapıldı.")
            logging.info(f"toggle_layer_visibility completed successfully for index {idx}.")
        except Exception as e:
            logging.error(f"toggle_layer_visibility error: {e}")
            QMessageBox.critical(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')
    def move_layer_up(self):
        logging.debug("move_layer_up called")
        idx = self.layers.active_index
        if idx == -1:
             QMessageBox.warning(self, 'Uyarı', 'Taşınacak katman seçili değil.')
             logging.warning("move_layer_up aborted: No active layer.")
             return
        if idx > 0:
            try:
                self.layers.move_layer(idx, idx - 1)
                self.refresh_layers()
                self.status_bar.showMessage('Katman yukarı taşındı.')
                logging.info(f"move_layer_up completed successfully for index {idx}.")
            except Exception as e:
                logging.error(f"move_layer_up error: {e}")
                QMessageBox.critical(self, 'Hata', f'Katman yukarı taşınırken hata: {e}')
        else:
            logging.info("move_layer_up: Layer already at top.")
    def move_layer_down(self):
        logging.debug("move_layer_down called")
        idx = self.layers.active_index
        if idx == -1:
             QMessageBox.warning(self, 'Uyarı', 'Taşınacak katman seçili değil.')
             logging.warning("move_layer_down aborted: No active layer.")
             return
        if idx < len(self.layers.layers) - 1:
            try:
                self.layers.move_layer(idx, idx + 1)
                self.refresh_layers()
                self.status_bar.showMessage('Katman aşağı taşındı.')
                logging.info(f"move_layer_down completed successfully for index {idx}.")
            except Exception as e:
                logging.error(f"move_layer_down error: {e}")
                QMessageBox.critical(self, 'Hata', f'Katman aşağı taşınırken hata: {e}')
        else:
             logging.info("move_layer_down: Layer already at bottom.")
    def refresh_layers(self):
        logging.debug("refresh_layers called")
        try:
            if not hasattr(self, 'layers') or not self.layers.layers:
                logging.warning("refresh_layers: No layers object or layers list is empty.")
                self.image_view.scene.clear()
                if hasattr(self, 'layer_panel'):
                    self.layer_panel.refresh()
                return
            logging.debug("refresh_layers: Composing layers...")
            pixmap = self._compose_layers_pixmap()
            logging.debug(f"refresh_layers: Composition complete. Pixmap is null: {pixmap is None or pixmap.isNull()}")
            if pixmap and not pixmap.isNull():
                logging.debug("refresh_layers: Updating image view (preserving zoom)...")
                self.image_view.update_image(pixmap)
                logging.debug("refresh_layers: Image view updated.")
            elif not self.layers.layers:
                 logging.debug("refresh_layers: Clearing image view scene (no layers).")
                 self.image_view.scene.clear()
            else:
                 logging.warning("refresh_layers: Composition resulted in null pixmap, clearing scene.")
                 self.image_view.scene.clear()
            if hasattr(self, 'layer_panel'):
                logging.debug("refresh_layers: Refreshing layer panel...")
                self.layer_panel.refresh()
                logging.debug("refresh_layers: Layer panel refreshed.")
            logging.debug("refresh_layers finished successfully.")
        except Exception as e:
            logging.error(f"refresh_layers error: {e}", exc_info=True)
            QMessageBox.critical(self, 'Hata', f'Katmanlar güncellenirken hata oluştu: {e}')
    def _compose_layers_pixmap(self):
        return compose_layers_pixmap(self.layers, image_to_qpixmap)
    def set_active_layer(self, idx):
        try:
            if not hasattr(self, 'layers'):
                logging.warning("set_active_layer: Katman yok")
                return
            if not (0 <= idx < len(self.layers.layers)):
                logging.warning(f"set_active_layer: Geçersiz indeks: {idx}")
                return
            self.layers.set_active_layer(idx)
            self.layer_panel.refresh()
            logging.info(f"Aktif katman değiştirildi: {idx}")
        except Exception as e:
            logging.error(f"set_active_layer (MainWindow) hatası: {e}")
    def handle_text_tool_click(self, scene_pos: QPointF):
        logging.info(f"Handling text tool click at {scene_pos.x()}, {scene_pos.y()}")
        if not hasattr(self, 'layers'):
            QMessageBox.warning(self, 'Uyarı', 'Metin eklemek için önce bir resim açın!')
            return
        layer = self.layers.get_active_layer()
        if layer is None or layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Metin eklemek için aktif bir katman seçin!')
            return
        text, ok1 = QInputDialog.getText(self, 'Metin Ekle', 'Metni girin:')
        if not ok1 or not text:
            return
        font, ok2 = QFontDialog.getFont(self)
        if not ok2:
            return
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Metin Rengi Seç")
        if not color.isValid():
            return
        text_color = (color.red(), color.green(), color.blue(), color.alpha())
        img_x = int(scene_pos.x())
        img_y = int(scene_pos.y())
        old_img = layer.image.copy()
        try:
            font_size = font.pointSize()
            if font_size <= 0: font_size = 12
            pil_font = get_pil_font(font.family(), font_size, font.styleName())
            new_img = draw_text_on_image(layer.image, text, (img_x, img_y), pil_font, text_color)
            if new_img is None:
                raise ValueError("Metin çizimi başarısız oldu.")
            current_layer_ref = layer
            final_new_img = new_img.copy()
            old_img_copy = old_img.copy()
            def do_action():
                try:
                    current_layer_ref.image = final_new_img.copy()
                    self.refresh_layers()
                except Exception as e:
                    logging.error(f"Metin ekleme (do) hatası: {e}")
            def undo_action():
                try:
                    current_layer_ref.image = old_img_copy.copy()
                    self.refresh_layers()
                except Exception as e:
                    logging.error(f"Metin ekleme (undo) hatası: {e}")
            cmd = Command(do_action, undo_action, f'Metin Ekle: "{text[:20]}..."')
            cmd.do()
            self.history.push(cmd)
            self.status_bar.showMessage('Metin eklendi.')
        except Exception as e:
            logging.error(f"Metin ekleme hatası: {e}")
            QMessageBox.critical(self, 'Hata', f'Metin eklenirken hata oluştu: {e}')
            layer.image = old_img
            self.refresh_layers()
    def restore_layer_original_size(self):
        try:
            if not hasattr(self, 'layers') or not self.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Resim veya katman yok!')
                return
            layer = self.layers.get_active_layer()
            if layer is None:
                QMessageBox.warning(self, 'Uyarı', 'Aktif katman yok!')
                return
            if layer.restore_original_size():
                logging.info(f"Katman {self.layers.active_index} ({layer.name}) orijinal çözünürlüğe döndürüldü: {layer.image.size}.")
                self.refresh_layers()
                self.status_bar.showMessage(f"'{layer.name}' katmanı orijinal çözünürlüğe döndürüldü: {layer.image.width}x{layer.image.height}")
            else:
                self.status_bar.showMessage(f"'{layer.name}' katmanı zaten orijinal çözünürlükte ({layer.image.width}x{layer.image.height})")
        except Exception as e:
            logging.error(f"restore_layer_original_size hatası: {e}")
            QMessageBox.critical(self, 'Hata', f'Katman orijinal çözünürlüğe döndürülürken hata oluştu: {e}')
    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() and all(url.isLocalFile() for url in mime_data.urls()):
            supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            if any(url.toLocalFile().lower().endswith(tuple(supported_extensions)) for url in mime_data.urls()):
                event.acceptProposedAction()
                logging.debug("Drag enter accepted for image file(s).")
            else:
                logging.debug("Drag enter rejected: Unsupported file type.")
                event.ignore()
        else:
            logging.debug("Drag enter rejected: Not a local file URL.")
            event.ignore()
    def dropEvent(self, event):
        logging.debug("Drop event received.")
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            logging.debug(f"Dropped URLs: {[url.toString() for url in mime_data.urls()]}")
            supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            loaded_successfully = False
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    logging.debug(f"Processing local file URL: {file_path}")
                    if file_path.lower().endswith(tuple(supported_extensions)):
                        logging.info(f"Attempting to load supported dropped file: {file_path}")
                        if self._load_image_from_path(file_path):
                            logging.info(f"Successfully loaded dropped file: {file_path}")
                            event.acceptProposedAction()
                            loaded_successfully = True
                        else:
                            logging.warning(f"Failed to load dropped file via _load_image_from_path: {file_path}")
                            event.ignore()
                        return
                    else:
                        logging.debug(f"Skipping unsupported file type: {file_path}")
                else:
                    logging.debug(f"Skipping non-local URL: {url.toString()}")
            if not loaded_successfully:
                logging.warning("Drop event ignored: No supported image files found or loaded from dropped items.")
                event.ignore()
        else:
            logging.debug("Drop event ignored: No URLs found.")
            event.ignore()
    def _compose_layers_pixmap(self):
        if not hasattr(self, 'layers') or not self.layers.layers:
            return None
        merged_image = self.layers.merge_visible()
        if merged_image:
            return image_to_qpixmap(merged_image)
        return None
    def toggle_resize_mode(self):
        try:
            layer = self.layers.get_active_layer()
            if layer is None or layer.image is None:
                QMessageBox.warning(self, 'Uyarı', 'Resize işlemi için aktif bir katman gerekli!')
                return
            original_size = layer.image.size
            dialog = ResizeDialog(layer, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_width, new_height, _, _ = dialog.get_resize_parameters()
                if (new_width, new_height) == original_size:
                    self.status_bar.showMessage("Boyut değiştirilmedi.")
                    return
                logging.info(f"Resizing layer '{layer.name}' from {original_size} to ({new_width}, {new_height})")
                def redo_func():
                    success = layer.resize(new_width, new_height)
                    if success:
                        self.refresh_layers()
                        self.status_bar.showMessage(f"Katman '{layer.name}' yeniden boyutlandırıldı: {new_width}x{new_height}")
                    else:
                         QMessageBox.critical(self, 'Hata', 'Katman yeniden boyutlandırılamadı.')
                    return success
                def undo_func():
                    success = layer.resize(original_size[0], original_size[1])
                    if success:
                        self.refresh_layers()
                        self.status_bar.showMessage(f"Yeniden boyutlandırma geri alındı: {original_size[0]}x{original_size[1]}")
                    else:
                         QMessageBox.critical(self, 'Hata', 'Yeniden boyutlandırma geri alınamadı.')
                    return success
                command = Command(redo_func, undo_func, f"Resize Layer '{layer.name}'")
                command.do()
                self.history.push(command)
            else:
                self.status_bar.showMessage("Yeniden boyutlandırma iptal edildi.")
        except Exception as e:
            logging.error(f"Resize action failed: {e}", exc_info=True)
            QMessageBox.critical(self, 'Hata', f'Yeniden boyutlandırma sırasında bir hata oluştu: {e}')
    def create_drawing_tools_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Renk seçici bölümü
        color_group = QWidget()
        color_layout = QVBoxLayout(color_group)
        color_layout.setContentsMargins(0, 0, 0, 0)

        color_label = QLabel("Renk:")
        color_label.setStyleSheet("font-weight: bold; color: #333;")
        color_layout.addWidget(color_label)

        color_button = QPushButton()
        color_button.setFixedHeight(40)
        color_button.setText("Renk Seç")
        self._update_color_button_style(color_button, self.current_color)
        color_button.clicked.connect(self.select_color_from_panel)
        color_layout.addWidget(color_button)

        layout.addWidget(color_group)
        self.color_button = color_button
        # Şekil araçları bölümü
        shape_group = QWidget()
        shape_group_layout = QVBoxLayout(shape_group)
        shape_group_layout.setContentsMargins(0, 0, 0, 0)

        shape_label = QLabel("Şekil Araçları:")
        shape_label.setStyleSheet("font-weight: bold; color: #333;")
        shape_group_layout.addWidget(shape_label)

        # İlk satır: Şekil ve Çizgi
        shape_row1 = QHBoxLayout()
        shape_button = QPushButton("Şekil")
        shape_button.setCheckable(True)
        shape_button.setFixedHeight(35)
        shape_button.clicked.connect(lambda: self.set_tool('shape'))
        shape_row1.addWidget(shape_button)
        self.shape_button = shape_button

        line_button = QPushButton("Çizgi")
        line_button.setCheckable(True)
        line_button.setFixedHeight(35)
        line_button.clicked.connect(lambda: self.set_tool('line'))
        shape_row1.addWidget(line_button)
        self.line_button = line_button

        shape_group_layout.addLayout(shape_row1)

        # İkinci satır: Dikdörtgen ve Elips
        shape_row2 = QHBoxLayout()
        rect_button = QPushButton("Dikdörtgen")
        rect_button.setCheckable(True)
        rect_button.setFixedHeight(35)
        rect_button.clicked.connect(lambda: self.set_tool('rectangle'))
        shape_row2.addWidget(rect_button)
        self.rect_button = rect_button

        ellipse_button = QPushButton("Elips")
        ellipse_button.setCheckable(True)
        ellipse_button.setFixedHeight(35)
        ellipse_button.clicked.connect(lambda: self.set_tool('ellipse'))
        shape_row2.addWidget(ellipse_button)
        self.ellipse_button = ellipse_button

        shape_group_layout.addLayout(shape_row2)
        layout.addWidget(shape_group)
        # Boyut ayarları bölümü
        size_group = QWidget()
        size_group_layout = QVBoxLayout(size_group)
        size_group_layout.setContentsMargins(0, 0, 0, 0)

        size_label = QLabel("Boyut Ayarları:")
        size_label.setStyleSheet("font-weight: bold; color: #333;")
        size_group_layout.addWidget(size_label)

        # Fırça boyutu
        brush_layout = QVBoxLayout()
        brush_label = QLabel("Fırça Boyutu:")
        brush_label.setStyleSheet("color: #555; font-size: 11px;")
        brush_layout.addWidget(brush_label)

        brush_control = QHBoxLayout()
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setMinimum(1)
        self.brush_size_slider.setMaximum(100)
        self.brush_size_slider.setValue(self.current_brush_size)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        brush_control.addWidget(self.brush_size_slider)

        self.brush_size_value_label = QLabel(f"{self.current_brush_size}")
        self.brush_size_value_label.setStyleSheet("color: #333; font-weight: bold; min-width: 30px;")
        self.brush_size_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brush_control.addWidget(self.brush_size_value_label)

        brush_layout.addLayout(brush_control)
        size_group_layout.addLayout(brush_layout)
        # Kalem boyutu
        pencil_layout = QVBoxLayout()
        pencil_label = QLabel("Kalem Boyutu:")
        pencil_label.setStyleSheet("color: #555; font-size: 11px;")
        pencil_layout.addWidget(pencil_label)

        pencil_control = QHBoxLayout()
        self.pencil_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.pencil_size_slider.setMinimum(1)
        self.pencil_size_slider.setMaximum(20)
        self.pencil_size_slider.setValue(self.current_pencil_size)
        self.pencil_size_slider.valueChanged.connect(self._on_pencil_size_changed)
        pencil_control.addWidget(self.pencil_size_slider)

        self.pencil_size_value_label = QLabel(f"{self.current_pencil_size}")
        self.pencil_size_value_label.setStyleSheet("color: #333; font-weight: bold; min-width: 30px;")
        self.pencil_size_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pencil_control.addWidget(self.pencil_size_value_label)

        pencil_layout.addLayout(pencil_control)
        size_group_layout.addLayout(pencil_layout)

        # Silgi boyutu
        eraser_layout = QVBoxLayout()
        eraser_label = QLabel("Silgi Boyutu:")
        eraser_label.setStyleSheet("color: #555; font-size: 11px;")
        eraser_layout.addWidget(eraser_label)

        eraser_control = QHBoxLayout()
        self.eraser_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.eraser_size_slider.setMinimum(1)
        self.eraser_size_slider.setMaximum(100)
        self.eraser_size_slider.setValue(self.current_eraser_size)
        self.eraser_size_slider.valueChanged.connect(self._on_eraser_size_changed)
        eraser_control.addWidget(self.eraser_size_slider)

        self.eraser_size_value_label = QLabel(f"{self.current_eraser_size}")
        self.eraser_size_value_label.setStyleSheet("color: #333; font-weight: bold; min-width: 30px;")
        self.eraser_size_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eraser_control.addWidget(self.eraser_size_value_label)

        eraser_layout.addLayout(eraser_control)
        size_group_layout.addLayout(eraser_layout)

        # Doldurma toleransı
        fill_layout = QVBoxLayout()
        fill_label = QLabel("Doldurma Toleransı:")
        fill_label.setStyleSheet("color: #555; font-size: 11px;")
        fill_layout.addWidget(fill_label)

        fill_control = QHBoxLayout()
        self.fill_tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self.fill_tolerance_slider.setMinimum(0)
        self.fill_tolerance_slider.setMaximum(255)
        self.fill_tolerance_slider.setValue(self.current_fill_tolerance)
        self.fill_tolerance_slider.valueChanged.connect(self._on_fill_tolerance_changed)
        fill_control.addWidget(self.fill_tolerance_slider)

        self.fill_tolerance_value_label = QLabel(f"{self.current_fill_tolerance}")
        self.fill_tolerance_value_label.setStyleSheet("color: #333; font-weight: bold; min-width: 30px;")
        self.fill_tolerance_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fill_control.addWidget(self.fill_tolerance_value_label)

        fill_layout.addLayout(fill_control)
        size_group_layout.addLayout(fill_layout)

        layout.addWidget(size_group)
        layout.addStretch()

        # Modern ve tutarlı tema
        panel.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: none;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }

            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: #ffffff;
                font-weight: 500;
                min-height: 25px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #666666;
            }

            QPushButton:pressed {
                background-color: #353535;
                border-color: #777777;
            }

            QPushButton:checked {
                background-color: #0078d4;
                border-color: #106ebe;
                color: #ffffff;
            }

            QPushButton:checked:hover {
                background-color: #106ebe;
                border-color: #005a9e;
            }

            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 6px;
                background: #404040;
                margin: 2px 0;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #106ebe;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #106ebe;
                border-color: #005a9e;
            }

            QSlider::handle:horizontal:pressed {
                background: #005a9e;
            }
        """)
        return panel
    def _update_color_button_style(self, button, color):
        """Renk butonunun stilini günceller."""
        # Rengin parlaklığına göre metin rengini belirle
        brightness = (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114)
        text_color = "#000000" if brightness > 128 else "#ffffff"

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                border: 2px solid #555555;
                border-radius: 6px;
                color: {text_color};
                font-weight: bold;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: #0078d4;
            }}
            QPushButton:pressed {{
                border-color: #106ebe;
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 0.8);
            }}
        """)

    def select_color_from_panel(self):
        color = QColorDialog.getColor(
            self.current_color,
            self,
            "Çizim Rengi Seç",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        if color.isValid():
            self.set_drawing_color(color)
            self._update_color_button_style(self.color_button, color)
    def _on_brush_size_changed(self, value):
        self.current_brush_size = value
        self.brush_size_value_label.setText(f"{value}")
        self.brush_tool.set_size(value)
        if self.current_tool == 'brush':
            self.image_view.setCursor(self._create_brush_cursor(value))
    def _on_pencil_size_changed(self, value):
        self.current_pencil_size = value
        self.pencil_size_value_label.setText(f"{value}")
        self.pencil_tool.set_size(value)
        if self.current_tool == 'pencil':
            self.image_view.setCursor(self._create_brush_cursor(value))
    def _on_eraser_size_changed(self, value):
        self.current_eraser_size = value
        self.eraser_size_value_label.setText(f"{value}")
        self.eraser_tool.set_size(value)
        if self.current_tool == 'eraser':
            self.image_view.setCursor(self._create_brush_cursor(value))
    def _on_fill_tolerance_changed(self, value):
        self.current_fill_tolerance = value
        self.fill_tolerance_value_label.setText(f"{value}")
        self.fill_tool.tolerance = value
    def check_gpu_status(self):
        self.has_gpu = torch.cuda.is_available()
        if self.has_gpu:
            self.gpu_count = torch.cuda.device_count()
            self.gpu_info = []
            for i in range(self.gpu_count):
                self.gpu_info.append({
                    "id": i,
                    "name": torch.cuda.get_device_name(i)
                })
            if hasattr(self, 'status_bar'):
                current_gpu = self.gpu_info[self.gpu_id]["name"] if self.gpu_id < self.gpu_count else self.gpu_info[0]["name"]
                if self.use_gpu:
                    self.status_bar.showMessage(f"GPU aktif: {current_gpu}", 5000)
                else:
                    self.status_bar.showMessage(f"GPU devre dışı (kullanılabilir: {current_gpu})", 5000)
        else:
            self.gpu_count = 0
            self.gpu_info = []
            self.use_gpu = False
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("GPU bulunamadı, CPU modu kullanılıyor", 5000)
    def toggle_gpu_usage(self, checked):
        self.use_gpu = checked
        self.settings.setValue("use_gpu", checked)
        if checked and not self.has_gpu:
            QMessageBox.warning(self, "GPU Not Available",
                               "GPU acceleration is not available on this system. "
                               "The software will continue to run in CPU mode.")
            self.use_gpu = False
            self.use_gpu_action.setChecked(False)
            return
        if self.use_gpu:
            gpu_available = configure_gpu(self.gpu_id)
            if not gpu_available:
                QMessageBox.warning(self, "GPU Configuration Failed",
                                   "Failed to configure GPU. Falling back to CPU mode.")
                self.use_gpu = False
                self.use_gpu_action.setChecked(False)
        else:
            use_cpu_fallback()
        QMessageBox.information(self, "Settings Changed",
                               f"GPU acceleration is now {'enabled' if self.use_gpu else 'disabled'}.\n"
                               "This will affect newly applied filters and operations.")
    def select_gpu_device(self, gpu_id):
        if gpu_id >= self.gpu_count:
            QMessageBox.warning(self, "Invalid GPU", f"GPU {gpu_id} is not available")
            return
        self.gpu_id = gpu_id
        self.settings.setValue("gpu_id", gpu_id)
        if self.use_gpu:
            configure_gpu(self.gpu_id)
            QMessageBox.information(self, "GPU Changed",
                                   f"Now using GPU {gpu_id}: {torch.cuda.get_device_name(gpu_id)}")
    def show_gpu_info(self):
        if not self.has_gpu:
            QMessageBox.information(self, "GPU Status", "No GPU detected. Running in CPU mode.")
            return
        info_text = "GPU Information:\n\n"
        info_text += f"CUDA Available: {torch.cuda.is_available()}\n"
        info_text += f"Number of GPUs: {self.gpu_count}\n\n"
        for i in range(self.gpu_count):
            info_text += f"GPU {i}: {torch.cuda.get_device_name(i)}\n"
            if i == self.gpu_id:
                info_text += "  ✓ Currently selected\n"
            try:
                total_mem = torch.cuda.get_device_properties(i).total_memory / (1024 * 1024)
                free_mem = torch.cuda.mem_get_info(i)[0] / (1024 * 1024)
                used_mem = total_mem - free_mem
                info_text += f"  Total Memory: {total_mem:.0f} MB\n"
                info_text += f"  Used Memory: {used_mem:.0f} MB\n"
                info_text += f"  Free Memory: {free_mem:.0f} MB\n"
            except Exception as e:
                info_text += f"  Memory info unavailable: {e}\n"
            info_text += "\n"
        QMessageBox.information(self, "GPU Status", info_text)
    def select_all(self):
        if not hasattr(self, 'layers') or not self.layers.get_active_layer():
            QMessageBox.warning(self, 'Uyarı', 'Seçim yapılacak bir resim yok!')
            return
        layer = self.layers.get_active_layer()
        if layer.image is None:
            return
        width, height = layer.image.size
        from PyQt6.QtGui import QPainterPath
        from PyQt6.QtCore import QRectF
        path = QPainterPath()
        path.addRect(QRectF(0, 0, width, height))
        self.image_view.current_selection_path = path
        self.image_view.selection_operation = 'new'
        if self.image_view.final_selection_item:
            self.image_view.scene.removeItem(self.image_view.final_selection_item)
        from PyQt6.QtGui import QPen, QColor
        from PyQt6.QtCore import Qt
        pen = QPen(QColor(0, 0, 255, 180), 1, Qt.PenStyle.DashLine)
        self.image_view.final_selection_item = self.image_view.scene.addPath(path, pen)
        if self.image_view.final_selection_item:
            self.image_view.final_selection_item.setZValue(10)
        self.status_bar.showMessage("Tüm görüntü seçildi.")
    def setup_initial_state(self):
        self.set_tool('select')
        self.image_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.status_bar.showMessage("PyxelEdit'e hoş geldiniz! Resim açın (Ctrl+O), sürükleyerek gezinin, Alt+Sürükle ile seçim yapın.")
        logging.info("Initial state configured: Selection tool active, drag mode enabled")

    def setup_main_theme(self):
        """Ana pencere için modern tema ayarlar."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            QMenuBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-bottom: 1px solid #555555;
                padding: 4px;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QMenuBar::item:selected {
                background-color: #0078d4;
            }

            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 4px;
            }

            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background-color: #0078d4;
            }

            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 4px 0;
            }

            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #555555;
                padding: 4px;
            }

            QDockWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }

            QDockWidget::title {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px;
                border-bottom: 1px solid #555555;
                font-weight: bold;
            }

            QScrollArea {
                background-color: #2b2b2b;
                border: none;
            }

            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #606060;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #0078d4;
            }

            QScrollBar:horizontal {
                background-color: #404040;
                height: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:horizontal {
                background-color: #606060;
                border-radius: 6px;
                min-width: 20px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #0078d4;
            }
        """)

        logging.info("Main theme applied")