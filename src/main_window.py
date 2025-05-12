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

# Import custom modules
from .image_io import load_image, image_to_qpixmap
from .image_view import ImageView
from .transform import rotate_image, flip_image, resize_image, crop_image
from .history import History, Command
from .layers import LayerManager
from .layer_panel import LayerPanel
from .effects_panel import EffectsPanel
from .dialogs import FilterSliderDialog
from .resize_dialog import ResizeDialog # Import ResizeDialog
from .image_processing import get_filtered_image
from .menu import MenuManager
from .text_utils import get_pil_font, draw_text_on_image
from .utils import (compose_layers_pixmap, validate_layer_operation,
                   create_command, ensure_rgba, create_transparent_image)
from .drawing_tools import Brush, Pencil, Eraser, FillBucket  # Çizim araçlarını içe aktar
from .shape_tools import ShapeTool, LineTool, RectangleTool, EllipseTool  # Şekil araçlarını içe aktar
from .gpu_utils import configure_gpu, check_gpu_memory, use_cpu_fallback

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyxelEdit')
        self.setGeometry(100, 100, 1024, 768)

        # Program ayarlarını yükle
        self.settings = QSettings("PyxelEdit", "ImageEditor")
        
        # GPU ayarlarını başlat
        self.use_gpu = self.settings.value("use_gpu", True, type=bool)
        self.gpu_id = self.settings.value("gpu_id", 0, type=int)
        self.check_gpu_status()
        
        # Core components
        self.history = History()
        self.layers = LayerManager()
        self.menu_manager = MenuManager(self)

        # Memory cleanup timer
        self.gc_timer = QTimer(self)
        self.gc_timer.timeout.connect(lambda: gc.collect())
        self.gc_timer.start(30000)  # Cleanup every 30 seconds

        # Preview state
        self.original_preview_image = None
        self.preview_active = False
        self.current_preview_filter_type = None
        self.current_tool = 'select'
        
        # Çizim araçları
        self.current_brush_size = 15
        self.current_pencil_size = 2
        self.current_eraser_size = 20
        self.current_color = QColor(0, 0, 0, 255)  # Varsayılan siyah renk
        self.current_fill_tolerance = 32  # Varsayılan doldurma toleransı
        
        # Araç nesnelerini oluştur
        self._create_drawing_tools()

        # Preview Throttling Timer
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(150)
        self.preview_timer.timeout.connect(self._perform_preview_update)
        self.last_preview_value = None

        # Initialize UI
        self._init_ui()

        # Enable Drag and Drop
        self.setAcceptDrops(True)

        logging.info("PyxelEdit başlatıldı")
        
        # Temel pencere yapılandırması
        self.setWindowTitle("PyxelEdit - Image Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Program ayarlarını yükle
        self.settings = QSettings("PyxelEdit", "ImageEditor")
        
        # GPU ayarları
        self.use_gpu = self.settings.value("use_gpu", True, type=bool)
        self.gpu_id = self.settings.value("gpu_id", 0, type=int)
        self.check_gpu_status()
        
    def handle_text_tool_click(self, position):
        """Metin aracı tıklandığında çağrılır, metni aktif katmana ekler."""
        try:
            if not hasattr(self, 'layers') or not self.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Resim veya katman yok!')
                return
                
            active_layer = self.layers.get_active_layer()
            if not active_layer:
                QMessageBox.warning(self, 'Uyarı', 'Metin eklenecek bir katman yok!')
                return
                
            # Metin girişi için diyalog göster
            text, ok = QInputDialog.getText(self, 'Metin Ekle', 'Metni girin:')
            if not ok or not text:
                return  # Kullanıcı iptal etti
                
            # Font ayarları için diyalog göster
            font, ok = QFontDialog.getFont(QFont("Arial", 12), self, "Font Seç")
            if not ok:
                return
                
            # Renk ayarları için diyalog göster
            color = QColorDialog.getColor(QColor(0, 0, 0), self, "Metin Rengi Seç")
            if not color.isValid():
                return
                
            # Metni ekleme işlemini yap
            old_img = active_layer.image.copy()
            
            def do_add_text():
                # Metni katmana ekle
                draw_text_on_image(active_layer.image, text, position, font, color)
                self.refresh_layers()
                
            def undo_add_text():
                # Orijinal görüntüyü geri yükle
                active_layer.image = old_img
                self.refresh_layers()
                
            # Command oluştur ve geçmişe ekle
            active_layer_idx = self.layers.active_index
            command = create_command(
                do_func=do_add_text,
                undo_func=undo_add_text,
                description=f"Metin eklendi (Katman {active_layer_idx+1})"
            )
            # Önce değişikliği uygula
            do_add_text()
            # Geçmişe ekle
            self.history.push(command)
            
            # Metin eklendi mesajını göster
            self.status_bar.showMessage(f"Metin eklendi: '{text}'", 5000)
            
        except Exception as e:
            logging.error(f"Metin ekleme hatası: {e}")
            QMessageBox.critical(self, 'Hata', f'Metin eklenirken hata oluştu: {e}')
            # Hata durumunda orijinal görüntüyü geri yükle
            if 'old_img' in locals() and active_layer:
                active_layer.image = old_img
                self.refresh_layers()

    def _init_ui(self):
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Menu bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        # Image view (Initialize before menus that might access it)
        self.image_view = ImageView(self)
        self.setCentralWidget(self.image_view)

        # Menu bar (Create after image view)
        self.menu_manager.create_menus()
        self.image_view.textToolClicked.connect(self.handle_text_tool_click)
        
        # Çizim araçları için sinyal-yuva bağlantısı kur
        self.image_view.drawingComplete.connect(self.handle_drawing_complete)
        self.image_view.textToolClicked.connect(self.handle_text_tool_click)

        # Layer panel
        self.layer_panel = LayerPanel(self)
        self.dock = QDockWidget('Katman Paneli', self)
        self.dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

        # Effects panel
        self.effects_panel = EffectsPanel(self)
        self.effects_dock = QDockWidget('Efektler ve Ayarlamalar', self)
        self.effects_dock.setWidget(self.effects_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.effects_dock)
        self.tabifyDockWidget(self.dock, self.effects_dock)
        
        # Drawing Tools panel - Çizim Araçları Paneli
        self.drawing_tools_panel = self.create_drawing_tools_panel()
        self.drawing_tools_dock = QDockWidget('Çizim Araçları', self)
        self.drawing_tools_dock.setWidget(self.drawing_tools_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.drawing_tools_dock)
        
        self.dock.raise_()

    def _create_drawing_tools(self):
        """Çizim ve şekil araçlarını oluşturur."""
        self.brush_tool = Brush(self.current_color, self.current_brush_size)
        self.pencil_tool = Pencil(self.current_color, self.current_pencil_size)
        self.eraser_tool = Eraser(self.current_eraser_size)
        self.fill_tool = FillBucket(self.current_color, self.current_fill_tolerance)
        self.shape_tool = ShapeTool(self.current_color, self.current_brush_size)
        self.line_tool = LineTool(self.current_color, self.current_brush_size)
        self.rectangle_tool = RectangleTool(self.current_color, self.current_brush_size)
        self.ellipse_tool = EllipseTool(self.current_color, self.current_brush_size)
        
    def _create_brush_cursor(self, size):
        """Fırça/kalem boyutuna göre daire şeklinde imleç oluşturur."""
        # İmleç boyutu (görünür çemberin biraz daha büyük olması için)
        cursor_size = max(20, size + 4)  # Minimum 20 piksel, çizgi kalem için
        
        # Transparent pixmap oluştur
        pixmap = QPixmap(cursor_size, cursor_size)
        pixmap.fill(QColor(0, 0, 0, 0))  # Tamamen şeffaf
        
        # Çizim yap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dış çizgi (beyaz)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawEllipse(2, 2, size, size)
        
        # İç çizgi (siyah)
        painter.setPen(QPen(QColor(0, 0, 0), 0.5))
        painter.drawEllipse(2, 2, size, size)
        
        # Merkez noktası (hedef imleci)
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawPoint(cursor_size // 2, cursor_size // 2)
        
        painter.end()
        
        # İmleç oluşturma (sıcak nokta = merkez)
        return QCursor(pixmap, cursor_size // 2, cursor_size // 2)
        
    def set_drawing_color(self, color=None):
        """Çizim rengini ayarlar."""
        if color is None:
            # Renk seçim diyalogu göster
            color = QColorDialog.getColor(
                self.current_color, 
                self, 
                "Çizim Rengi Seç",
                QColorDialog.ColorDialogOption.ShowAlphaChannel
            )
            
            if not color.isValid():
                return  # Kullanıcı diyalogu iptal etti
                
        self.current_color = color
        
        # Araçların renklerini güncelle
        self.brush_tool.set_color(color)
        self.pencil_tool.set_color(color)
        self.fill_tool.set_color(color)
        
        # Durum çubuğunu güncelle
        self.status_bar.showMessage(f"Renk: RGB({color.red()}, {color.green()}, {color.blue()}, A:{color.alpha()})")
        
    def set_brush_size(self, size=None):
        """Fırça boyutunu ayarlar."""
        if size is None:
            # Boyut girmesi için diyalog göster
            size, ok = QInputDialog.getInt(
                self, 
                "Fırça Boyutu", 
                "Boyut (1-100):", 
                self.current_brush_size, 
                1, 100
            )
            
            if not ok:
                return  # Kullanıcı diyalogu iptal etti
                
        self.current_brush_size = size
        # Fırça aracını güncelle
        self.brush_tool.set_size(size)
        
        # Aktif araç fırça ise imleci güncelle
        if self.current_tool == 'brush':
            self.image_view.setCursor(self._create_brush_cursor(size))
            
        # Durum çubuğunu güncelle
        self.status_bar.showMessage(f"Fırça Boyutu: {size}px")
        
    def set_pencil_size(self, size=None):
        """Kalem boyutunu ayarlar."""
        if size is None:
            # Boyut girmesi için diyalog göster
            size, ok = QInputDialog.getInt(
                self, 
                "Kalem Boyutu", 
                "Boyut (1-20):", 
                self.current_pencil_size, 
                1, 20
            )
            
            if not ok:
                return  # Kullanıcı diyalogu iptal etti
                
        self.current_pencil_size = size
        # Kalem aracını güncelle
        self.pencil_tool.set_size(size)
        
        # Aktif araç kalem ise imleci güncelle
        if self.current_tool == 'pencil':
            self.image_view.setCursor(self._create_brush_cursor(size))
            
        # Durum çubuğunu güncelle
        self.status_bar.showMessage(f"Kalem Boyutu: {size}px")
        
    def set_eraser_size(self, size=None):
        """Silgi boyutunu ayarlar."""
        if size is None:
            # Boyut girmesi için diyalog göster
            size, ok = QInputDialog.getInt(
                self, 
                "Silgi Boyutu", 
                "Boyut (1-100):", 
                self.current_eraser_size, 
                1, 100
            )
            
            if not ok:
                return  # Kullanıcı diyalogu iptal etti
                
        self.current_eraser_size = size
        # Silgi aracını güncelle
        self.eraser_tool.set_size(size)
        
        # Aktif araç silgi ise imleci güncelle
        if self.current_tool == 'eraser':
            self.image_view.setCursor(self._create_brush_cursor(size))
            
        # Durum çubuğunu güncelle
        self.status_bar.showMessage(f"Silgi Boyutu: {size}px")
        
    def set_fill_tolerance(self, tolerance=None):
        """Doldurma toleransını ayarlar."""
        if tolerance is None:
            # Tolerans girmesi için diyalog göster
            tolerance, ok = QInputDialog.getInt(
                self, 
                "Doldurma Toleransı", 
                "Tolerans (0-255):", 
                self.current_fill_tolerance, 
                0, 255
            )
            
            if not ok:
                return  # Kullanıcı diyalogu iptal etti
                
        self.current_fill_tolerance = tolerance
        self.fill_tool.tolerance = tolerance
        
        # Durum çubuğunu güncelle
        self.status_bar.showMessage(f"Doldurma Toleransı: {tolerance}")
        
    def handle_drawing_complete(self, tool, paths):
        """Çizim tamamlandığında çağrılır, çizimi aktif katmana uygular."""
        # Katman kontrolü yap
        active_layer = self.layers.get_active_layer()
        if not active_layer:
            QMessageBox.warning(self, "Uyarı", "Çizim yapılacak bir katman yok. Lütfen önce bir katman ekleyin.")
            return
            
        # Çizimi uygulamak için Command oluştur
        def do_draw():
            # Orijinal görüntünün kopyasını al
            original_image = active_layer.image.copy()
            
            # Çizimi uygula
            if isinstance(tool, FillBucket):
                # Kova aracı paths yerine point kullanır
                # paths[0] bir QLineF olabilir, p1() metodu ile ilk noktayı alıyoruz
                if paths and len(paths) > 0:
                    if hasattr(paths[0], 'p1'):
                        point = paths[0].p1()  # QLineF için
                        success = tool.apply_to_layer(active_layer, point)
                    else:
                        # Diğer olası durumlar
                        success = tool.apply_to_layer(active_layer, paths[0])
                else:
                    # Paths boşsa bir şey yapmayalım
                    logging.warning("Doldurma için geçerli bir nokta bulunamadı")
                    success = False
            else:
                # Fırça, kalem, silgi çizgileri
                success = tool.apply_to_layer(active_layer, paths)
                
            # Değişikliği göster
            self.refresh_layers()
            
            return original_image
            
        def undo_draw(original_image):
            # Orijinal görüntüyü geri yükle
            active_layer.image = original_image
            self.refresh_layers()
            
        # Command oluştur ve geçmişe ekle
        active_layer_idx = self.layers.active_index
        command = Command(
            do_func=do_draw,
            undo_func=lambda img=None: undo_draw(img),
            description=f"{type(tool).__name__} çizim işlemi (Katman {active_layer_idx+1})"
        )
        # Önce değişikliği uygula
        result = do_draw()
        # Sonra undo fonksiyonunu güncelle
        command.undo_func = lambda: undo_draw(result)
        # Geçmişe ekle
        self.history.push(command)

    def set_tool(self, tool_name):
        """Sets the active tool and updates menu checks."""
        if tool_name in self.menu_manager.tool_actions or tool_name in ['shape', 'line', 'rectangle', 'ellipse']:
            self.current_tool = tool_name
            logging.info(f"Araç değiştirildi: {tool_name}")
            for name, action in self.menu_manager.tool_actions.items():
                action.setChecked(name == tool_name)
            # Update status bar or cursor if needed
            self.status_bar.showMessage(f"Aktif Araç: {tool_name.capitalize()}")
            
            # Çizim ve şekil araçları için NoDrag modunu, diğer araçlar için ScrollHandDrag modunu ayarla
            is_drawing_tool = tool_name in ['brush', 'pencil', 'eraser', 'fill', 'shape', 'line', 'rectangle', 'ellipse']
            if is_drawing_tool:
                self.image_view.setDragMode(QGraphicsView.DragMode.NoDrag)
            else:
                self.image_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            
            # Seçilen araca göre ImageView'daki aracı ayarla
            if tool_name == 'select':
                # Set the default selection shape (e.g., rectangle) when selection tool is active
                self.image_view.set_selection_mode('rectangle')
                # Normal imleç
                self.image_view.setCursor(Qt.CursorShape.ArrowCursor)
            elif tool_name == 'brush':
                self.image_view.drawing_tool = self.brush_tool
                # Fırça aracı seçildiğinde fırça boyutunda imleç oluştur
                self.image_view.setCursor(self._create_brush_cursor(self.current_brush_size))
            elif tool_name == 'pencil':
                self.image_view.drawing_tool = self.pencil_tool
                # Kalem aracı seçildiğinde kalem boyutunda imleç oluştur
                self.image_view.setCursor(self._create_brush_cursor(self.current_pencil_size))
            elif tool_name == 'eraser':
                self.image_view.drawing_tool = self.eraser_tool
                # Silgi aracı seçildiğinde silgi boyutunda imleç oluştur
                self.image_view.setCursor(self._create_brush_cursor(self.current_eraser_size))
            elif tool_name == 'fill':
                self.image_view.drawing_tool = self.fill_tool
                # Kova aracı seçildiğinde kova imleci göster
                self.image_view.setCursor(Qt.CursorShape.PointingHandCursor)
            elif tool_name == 'text':
                # Metin aracı seçildiğinde metin imleci göster
                self.image_view.setCursor(Qt.CursorShape.IBeamCursor)
            else:
                # Başka araçlar seçildiğinde normal imleç
                self.image_view.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            logging.warning(f"Bilinmeyen araç adı: {tool_name}")

    def _load_image_from_path(self, file_path):
        """Loads an image from the given file path and updates the UI."""
        try:
            img = load_image(file_path)
            if img is not None:
                # Eğer hiç katman yoksa, yeni bir LayerManager oluştur
                if not hasattr(self, 'layers') or not self.layers or not self.layers.layers:
                    self.layers = LayerManager() # Reset layers for new image
                    self.history = History() # Reset history for new image
                    self.layers.add_layer(img, 'Arka Plan')
                    self.current_image_path = file_path
                else:
                    # Mevcut bir resim varsa, yeni görüntüyü katman olarak ekle
                    # Dosya adını katman adı olarak kullan (dosya yolu yerine sadece dosya adı)
                    file_name = os.path.basename(file_path)
                    layer_name = os.path.splitext(file_name)[0]  # Uzantıyı kaldır
                    self.layers.add_layer(img, layer_name)
                
                merged = self.layers.merge_visible() # Get merged view
                if merged:
                    pixmap = image_to_qpixmap(merged)
                    self.image_view.set_image(pixmap)
                    self.status_bar.showMessage(f'{file_path} | {img.width}x{img.height}')
                    self.refresh_layers() # Update display and layer panel
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
        # No critical message here, _load_image_from_path handles errors

    def save_image(self):
        # Save the merged image from layers
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
        # Save the merged image from layers to a new path
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
                self.current_image_path = file_path # Update path if saved successfully
                self.status_bar.showMessage(f'Resim farklı kaydedildi: {file_path}')
            except Exception as e:
                logging.error(f"Save As error: {e}")
                QMessageBox.critical(self, 'Hata', f'Resim kaydedilemedi!\n{e}')

    def close_image(self):
        self.image_view.scene.clear()
        self.layers = LayerManager() # Reset layers
        self.history = History() # Reset history
        self.current_image_path = None
        self.status_bar.clearMessage()
        self.layer_panel.refresh() # Clear layer panel

    def blur_dialog(self):
        dialog = FilterSliderDialog(
            title='Bulanıklık Ayarı',
            label_text='Yarıçap',
            min_val=1,
            max_val=20,
            initial_val=2,
            step=1,
            decimals=0, # Integer value
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
            decimals=2, # Float value with 2 decimals
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
        """Connects signals for a preview dialog and shows it."""
        if not hasattr(self, 'layers') or not self.layers.get_active_layer():
            QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açın ve bir katman seçin!')
            return

        layer = self.layers.get_active_layer()
        if layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Aktif katmanda görüntü yok!')
            return

        # Store original image and set preview state
        self.original_preview_image = layer.image.copy()
        self.preview_active = True
        self.current_preview_filter_type = filter_type
        self.last_preview_value = dialog.get_value() # Store initial value

        # Connect signals
        # Connect slider change to request an update (throttled)
        dialog.valueChangedPreview.connect(self._request_preview_update)
        # Use finished signal which provides the result code
        dialog.finished.connect(lambda result: self._finalize_preview(result, filter_type, dialog))

        # Apply initial preview immediately
        self._perform_preview_update()

        # Show the dialog (non-modal might be better for true live preview, but modal is simpler for now)
        dialog.exec() # exec() is blocking, finalize will be called after it closes

    def _request_preview_update(self, value):
        """Stores the latest value and starts the preview timer."""
        self.last_preview_value = value
        if self.preview_active:
            self.preview_timer.start() # Restarts the timer if already running

    def _perform_preview_update(self): # Renamed from _apply_preview_filter
        """Applies the filter temporarily for preview using the last stored value."""
        if not self.preview_active or self.original_preview_image is None or self.last_preview_value is None:
            return

        # Stop the timer to prevent it firing again if it was somehow pending
        self.preview_timer.stop()

        layer = self.layers.get_active_layer()
        if layer is None:
            return # Should not happen if preview_active is true

        try:
            # Apply filter to the *original* image copy using the stored value
            img_copy = self.original_preview_image.copy()
            # Use the imported function with the stored value
            preview_img = get_filtered_image(img_copy, self.current_preview_filter_type, self.last_preview_value)

            if preview_img:
                # Temporarily update the layer's image *without* history
                layer.image = preview_img
                # Refresh display only (don't update layer panel unnecessarily during preview)
                pixmap = self._compose_layers_pixmap()
                if pixmap and not pixmap.isNull():
                    self.image_view.set_image(pixmap)
                # self.refresh_layers() # Avoid full refresh for performance
        except Exception as e:
            logging.error(f"Preview filter error ({self.current_preview_filter_type}): {e}")
            # Optionally revert to original here if preview fails badly

    def _finalize_preview(self, result, filter_type, dialog):
        """Finalizes the filter operation after the dialog closes."""
        if not self.preview_active:
            return

        # Stop any pending preview timer
        self.preview_timer.stop()

        layer = self.layers.get_active_layer()
        original_image_to_restore = self.original_preview_image.copy() # Keep a copy before clearing

        # Clean up preview state immediately
        self.preview_active = False
        self.original_preview_image = None
        self.current_preview_filter_type = None
        self.last_preview_value = None # Reset last value

        if layer is None: # Should not happen
             logging.warning("Finalize preview called with no active layer.")
             return

        if result == QDialog.DialogCode.Accepted:
            # Apply the final filter value permanently and add to history
            final_value = dialog.get_value()
            logging.info(f"Applying final filter: {filter_type} with value: {final_value}")
            # Use the stored original image as the base for the final application
            self.apply_filter(filter_type, final_value, base_image=original_image_to_restore)
        else:
            # Rejected: Restore the original image
            logging.info(f"Filter preview cancelled: {filter_type}. Restoring original.")
            layer.image = original_image_to_restore
            self.refresh_layers() # Refresh to show the restored image

        # Disconnect signals to avoid issues if dialog object persists
        try:
            dialog.valueChangedPreview.disconnect()
            dialog.finished.disconnect()
        except TypeError: # Signal already disconnected
            pass
        except Exception as e:
            logging.warning(f"Error disconnecting dialog signals: {e}")

    def sharpen_dialog(self):
        """Opens a dialog to adjust sharpen amount."""
        dialog = FilterSliderDialog(
            title='Keskinlik Ayarı',
            label_text='Miktar',
            min_val=0.0,
            max_val=1.0, # Blend amount
            initial_val=1.0, # Default to full effect
            step=0.05,
            decimals=2,
            parent=self
        )
        self._setup_preview_dialog(dialog, 'sharpen')

    def grayscale_dialog(self):
        """Opens a dialog to adjust grayscale amount."""
        dialog = FilterSliderDialog(
            title='Gri Ton Ayarı',
            label_text='Miktar',
            min_val=0.0,
            max_val=1.0, # Blend amount
            initial_val=1.0, # Default to full effect
            step=0.05,
            decimals=2,
            parent=self
        )
        self._setup_preview_dialog(dialog, 'grayscale')

    # _get_filtered_image method removed, functionality moved to image_processing.py

    def apply_filter(self, filter_type, param=None, base_image=None):
        """
        Seçili katmana filtre veya ayarlama uygular.

        Args:
            filter_type (str): Type of operation ('blur', 'sharpen', etc.)
            param: Parameter for the operation (factor, radius, amount, shift, etc.)
            base_image (Image.Image, optional): The image to apply the filter to.
                                                If None, uses the active layer's current image.
                                                Used by preview finalization.
        """
        logging.info(f"Applying filter/adjustment: {filter_type}, param: {param}")

        # Check active layer
        if not hasattr(self, 'layers'):
            QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
            return

        layer = self.layers.get_active_layer()
        if layer is None:
            QMessageBox.warning(self, 'Uyarı', 'Uygulanacak katman yok!')
            return

        # Determine the starting image for the operation
        if base_image is None:
            # No base image provided (standard filter application), use current layer image
            if layer.image is None:
                 QMessageBox.warning(self, 'Uyarı', 'Aktif katmanda görüntü yok!')
                 return
            start_img = layer.image.copy()
        else:
            # Base image provided (likely from preview finalization)
            start_img = base_image.copy() # Use the provided base image

        # Store the state *before* applying the filter for undo
        # This should be the image state *before* this specific filter application
        # If base_image was provided, layer.image might already hold a preview state.
        # We need the state *before* the preview started, which is base_image.
        old_img_for_undo = start_img.copy()


        # Apply the filter using the imported function
        try:
            new_img = get_filtered_image(start_img, filter_type, param)

            if new_img is None:
                raise ValueError(f"Filter application returned None for {filter_type}")

            # --- History Command Setup ---
            # Capture the necessary state for do/undo
            current_layer_ref = layer
            final_new_img = new_img.copy() # Image after filter is applied
            # old_img_for_undo is already captured above


            def do_action():
                try:
                    # Set the layer's image to the final filtered result
                    current_layer_ref.image = final_new_img.copy()
                    self.refresh_layers() # Update display and layer panel
                except Exception as e:
                    logging.error(f"Filter/Adjustment 'do' action error ({filter_type}): {e}")

            def undo_action():
                try:
                    # Restore the layer's image to the state before the filter
                    current_layer_ref.image = old_img_for_undo.copy()
                    self.refresh_layers() # Update display and layer panel
                except Exception as e:
                    logging.error(f"Filter/Adjustment 'undo' action error ({filter_type}): {e}")

            # Create and execute the command
            cmd = create_command(do_action, undo_action, f'İşlem: {filter_type}')
            cmd.do() # Apply the change
            self.history.push(cmd) # Add to history

            # Update status bar
            self.status_bar.showMessage(f'{filter_type} işlemi uygulandı.')

        except Exception as e:
            logging.error(f'apply_filter error ({filter_type}): {e}')
            QMessageBox.critical(self, 'Hata', f'İşlem uygulanırken hata oluştu ({filter_type}): {e}')
            # If the operation failed, ensure the layer image is restored to the pre-operation state
            # (which is old_img_for_undo, equivalent to start_img here)
            try:
                layer.image = old_img_for_undo.copy()
                self.refresh_layers()
            except Exception as restore_error:
                 logging.error(f"Error restoring image after filter failure: {restore_error}")

    def apply_transform(self, ttype):
        # Apply transform to the active layer
        if not hasattr(self, 'layers'):
             QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
             return
        layer = self.layers.get_active_layer()
        if layer is None or layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Dönüştürülecek aktif katman yok!')
            return

        old_img = layer.image.copy()
        img = layer.image # Operate on the layer's image
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
            return # Unknown transform type

        if img is None:
             QMessageBox.critical(self, 'Hata', 'Dönüşüm başarısız oldu!')
             return

        # Ensure RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Create command for undo/redo (capture copies)
        current_layer_ref = layer
        new_img_copy = img.copy()
        old_img_copy = old_img.copy()

        def do():
            try:
                current_layer_ref.image = new_img_copy.copy()
                self.refresh_layers() # Update display
            except Exception as e:
                logging.error(f"Dönüşüm uygulama (do) hatası: {e}")
        def undo():
            try:
                current_layer_ref.image = old_img_copy.copy()
                self.refresh_layers() # Update display
            except Exception as e:
                logging.error(f"Dönüşüm geri alma (undo) hatası: {e}")

        cmd = create_command(do, undo, f'Dönüşüm: {ttype}')
        cmd.do() # Apply the change
        self.history.push(cmd)
        self.status_bar.showMessage('Dönüşüm uygulandı: ' + ttype)

    def resize_dialog(self):
        # Resize the active layer
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
            # Ensure RGBA
            if img.mode != 'RGBA': img = img.convert('RGBA')
        except Exception as e:
            logging.error(f"Resize error: {e}")
            QMessageBox.critical(self, 'Hata', f'Yeniden boyutlandırma başarısız: {e}')
            return

        # Create command for undo/redo (capture copies)
        current_layer_ref = layer
        new_img_copy = img.copy()
        old_img_copy = old_img.copy()

        def do():
            try:
                current_layer_ref.image = new_img_copy.copy()
                self.refresh_layers() # Update display
            except Exception as e:
                logging.error(f"Resize uygulama (do) hatası: {e}")
        def undo():
            try:
                current_layer_ref.image = old_img_copy.copy()
                self.refresh_layers() # Update display
            except Exception as e:
                logging.error(f"Resize geri alma (undo) hatası: {e}")

        cmd = create_command(do, undo, 'Yeniden Boyutlandır')
        cmd.do() # Apply the change
        self.history.push(cmd)
        self.status_bar.showMessage(f'Aktif katman yeniden boyutlandırıldı: {width}x{height} (Oran Koru: {keep_aspect})')

    def crop_selected(self):
        # Crop the active layer based on selection
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
             # Ensure RGBA
            if img.mode != 'RGBA': img = img.convert('RGBA')
        except Exception as e:
            logging.error(f"Crop error: {e}")
            QMessageBox.critical(self, 'Hata', f'Kırpma başarısız: {e}')
            return

        # Create command for undo/redo (capture copies)
        current_layer_ref = layer
        new_img_copy = img.copy()
        old_img_copy = old_img.copy()

        def do():
            try:
                current_layer_ref.image = new_img_copy.copy()
                # After cropping, the layer size changes, potentially affecting other layers.
                # Option 1: Resize other layers (complex)
                # Option 2: Keep original canvas size, fill outside crop with transparent (simpler)
                # Implementing Option 2 for now: Create a new transparent image of the original size
                # and paste the cropped image onto it.
                new_canvas = Image.new('RGBA', old_img_copy.size, (0,0,0,0))
                paste_x = box[0] # Use the top-left corner of the crop box
                paste_y = box[1]
                new_canvas.paste(current_layer_ref.image, (paste_x, paste_y))
                current_layer_ref.image = new_canvas # Update layer with the new canvas

                self.refresh_layers() # Update display
                self.image_view.clear_selection() # Clear selection after crop
            except Exception as e:
                logging.error(f"Kırpma uygulama (do) hatası: {e}")
        def undo():
            try:
                current_layer_ref.image = old_img_copy.copy()
                self.refresh_layers() # Update display
            except Exception as e:
                logging.error(f"Kırpma geri alma (undo) hatası: {e}")

        cmd = Command(do, undo, 'Kırp')
        cmd.do() # Apply the change
        self.history.push(cmd)
        self.status_bar.showMessage('Aktif katman kırpıldı.')
        # Selection is cleared within the 'do' function now

    def undo(self):
        if self.history.undo():
            self.status_bar.showMessage('Geri alındı.')
            self.refresh_layers() # Ensure display updates after undo
        else:
            self.status_bar.showMessage('Geri alınacak işlem yok.')

    def redo(self):
        if self.history.redo():
            self.status_bar.showMessage('Yinele uygulandı.')
            self.refresh_layers() # Ensure display updates after redo
        else:
            self.status_bar.showMessage('Yinelenecek işlem yok.')

    def add_layer(self):
        logging.debug("add_layer called") # Added logging
        # Add a new layer based on the size of the first layer, filled with transparency
        if not hasattr(self, 'layers') or not self.layers.layers:
             QMessageBox.warning(self, 'Uyarı', 'Yeni katman eklemek için önce bir resim açın veya mevcut bir katman olmalı!')
             logging.warning("add_layer aborted: No layers exist.") # Added logging
             return
        try: # Added try-except
            base_size = self.layers.layers[0].image.size
            img = Image.new('RGBA', base_size, (0,0,0,0)) # Create transparent layer
            self.layers.add_layer(img, f'Katman {len(self.layers.layers)+1}')
            self.refresh_layers()
            self.status_bar.showMessage('Yeni katman eklendi.')
            logging.info("add_layer completed successfully.") # Added logging
        except Exception as e:
            logging.error(f"add_layer error: {e}")
            QMessageBox.critical(self, 'Hata', f'Yeni katman eklenirken hata: {e}')

    def delete_layer(self):
        logging.debug("delete_layer called") # Added logging
        idx = self.layers.active_index
        if idx == -1:
            QMessageBox.warning(self, 'Uyarı', 'Silinecek katman yok! Lütfen bir katman seçin.') # Modified message
            logging.warning("delete_layer aborted: No active layer selected.") # Added logging
            return
        try: # Added try-except
            layer_name = self.layers.layers[idx].name # Get name before deleting
            self.layers.remove_layer(idx)
            self.refresh_layers()
            self.status_bar.showMessage(f"'{layer_name}' katmanı silindi.") # Show name
            logging.info(f"delete_layer completed successfully for index {idx}.") # Added logging
        except Exception as e:
            logging.error(f"delete_layer error: {e}")
            QMessageBox.critical(self, 'Hata', f'Katman silinirken hata: {e}')


    def merge_layers(self):
        logging.debug("merge_layers called") # Added logging
        # Merge visible layers into a single new layer
        if not hasattr(self, 'layers') or len(self.layers.layers) < 2:
            QMessageBox.warning(self, 'Uyarı', 'Birleştirmek için en az 2 katman olmalı.')
            logging.warning("merge_layers aborted: Less than 2 layers exist.") # Added logging
            return

        try: # Added try-except for the whole operation
            merged_img = self.layers.merge_visible()
            if merged_img:
                # Keep track of old layers and indices for undo
                old_layers_list = list(self.layers.layers) # Shallow copy is enough
                old_active_index = self.layers.active_index

                def do():
                    logging.debug("merge_layers 'do' action executing.") # Added logging
                    # Remove all existing layers
                    self.layers.layers.clear()
                    # Add the merged layer
                    self.layers.add_layer(merged_img.copy(), 'Birleştirilmiş Katman')
                    self.refresh_layers()
                    self.status_bar.showMessage('Görünür katmanlar birleştirildi.')
                    logging.info("merge_layers 'do' action completed.") # Added logging

                def undo():
                    logging.debug("merge_layers 'undo' action executing.") # Added logging
                    # Restore old layers
                    self.layers.layers = list(old_layers_list) # Restore from copy
                    self.layers.active_index = old_active_index
                    self.refresh_layers()
                    self.status_bar.showMessage('Katman birleştirme geri alındı.')
                    logging.info("merge_layers 'undo' action completed.") # Added logging

                cmd = Command(do, undo, 'Katmanları Birleştir')
                cmd.do()
                self.history.push(cmd)
                logging.info("merge_layers completed successfully and added to history.") # Added logging
            else:
                QMessageBox.warning(self, 'Uyarı', 'Birleştirilecek görünür katman bulunamadı.')
                logging.warning("merge_layers aborted: merge_visible returned None.") # Added logging
        except Exception as e:
             logging.error(f"merge_layers error: {e}")
             QMessageBox.critical(self, 'Hata', f'Katmanlar birleştirilirken hata: {e}')


    def toggle_layer_visibility(self):
        logging.debug("toggle_layer_visibility called") # Added logging
        idx = self.layers.active_index
        if idx == -1:
            QMessageBox.warning(self, 'Uyarı', 'Görünürlüğü değiştirilecek katman yok! Lütfen bir katman seçin.') # Modified message
            logging.warning("toggle_layer_visibility aborted: No active layer selected.") # Added logging
            return
        try: # Added try-except
            self.layers.toggle_visibility(idx)
            layer_name = self.layers.layers[idx].name
            visibility_status = 'görünür' if self.layers.layers[idx].visible else 'gizli'
            self.refresh_layers()
            self.status_bar.showMessage(f"'{layer_name}' katmanı {visibility_status} yapıldı.") # Show status
            logging.info(f"toggle_layer_visibility completed successfully for index {idx}.") # Added logging
        except Exception as e:
            logging.error(f"toggle_layer_visibility error: {e}")
            QMessageBox.critical(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')


    def move_layer_up(self):
        logging.debug("move_layer_up called") # Added logging
        idx = self.layers.active_index
        if idx == -1:
             QMessageBox.warning(self, 'Uyarı', 'Taşınacak katman seçili değil.')
             logging.warning("move_layer_up aborted: No active layer.")
             return
        if idx > 0:
            try: # Added try-except
                self.layers.move_layer(idx, idx - 1)
                self.refresh_layers()
                self.status_bar.showMessage('Katman yukarı taşındı.')
                logging.info(f"move_layer_up completed successfully for index {idx}.") # Added logging
            except Exception as e:
                logging.error(f"move_layer_up error: {e}")
                QMessageBox.critical(self, 'Hata', f'Katman yukarı taşınırken hata: {e}')
        else:
            logging.info("move_layer_up: Layer already at top.") # Added logging

    def move_layer_down(self):
        logging.debug("move_layer_down called") # Added logging
        idx = self.layers.active_index
        if idx == -1:
             QMessageBox.warning(self, 'Uyarı', 'Taşınacak katman seçili değil.')
             logging.warning("move_layer_down aborted: No active layer.")
             return
        if idx < len(self.layers.layers) - 1:
            try: # Added try-except
                self.layers.move_layer(idx, idx + 1)
                self.refresh_layers()
                self.status_bar.showMessage('Katman aşağı taşındı.')
                logging.info(f"move_layer_down completed successfully for index {idx}.") # Added logging
            except Exception as e:
                logging.error(f"move_layer_down error: {e}")
                QMessageBox.critical(self, 'Hata', f'Katman aşağı taşınırken hata: {e}')
        else:
             logging.info("move_layer_down: Layer already at bottom.") # Added logging

    def refresh_layers(self):
        """Katmanları birleştirip görüntüyü günceller ve katman panelini yeniler."""
        logging.debug("refresh_layers called") # Added logging
        try:
            # Katmanlar var mı kontrol et
            if not hasattr(self, 'layers') or not self.layers.layers:
                logging.warning("refresh_layers: No layers object or layers list is empty.") # Modified log
                # Clear the view if no layers exist
                self.image_view.scene.clear()
                # Also refresh the panel to show "No layers" message
                if hasattr(self, 'layer_panel'):
                    self.layer_panel.refresh()
                return

            logging.debug("refresh_layers: Composing layers...") # Added logging
            # Katmanları birleştirip pixmap oluştur (display için)
            pixmap = self._compose_layers_pixmap()
            logging.debug(f"refresh_layers: Composition complete. Pixmap is null: {pixmap is None or pixmap.isNull()}") # Added logging

            if pixmap and not pixmap.isNull():
                logging.debug("refresh_layers: Setting image view...") # Added logging
                self.image_view.set_image(pixmap)
                logging.debug("refresh_layers: Image view set.") # Added logging
            elif not self.layers.layers: # Handle case where all layers are deleted
                 logging.debug("refresh_layers: Clearing image view scene (no layers).") # Added logging
                 self.image_view.scene.clear()
            else: # Handle case where there are layers but none are visible or valid
                 logging.warning("refresh_layers: Composition resulted in null pixmap, clearing scene.") # Added logging
                 self.image_view.scene.clear() # Clear scene if composition fails

            # Katman panelini güncelle
            if hasattr(self, 'layer_panel'):
                logging.debug("refresh_layers: Refreshing layer panel...") # Added logging
                self.layer_panel.refresh()
                logging.debug("refresh_layers: Layer panel refreshed.") # Added logging
            # Efekt panelini güncelle (gerekirse)
            # if hasattr(self, 'effects_panel'):
            #     self.effects_panel.refresh() # Şimdilik efekt paneli statik, refresh gerekmeyebilir
            logging.debug("refresh_layers finished successfully.") # Added logging
        except Exception as e:
            logging.error(f"refresh_layers error: {e}", exc_info=True) # Added exc_info for traceback
            QMessageBox.critical(self, 'Hata', f'Katmanlar güncellenirken hata oluştu: {e}')

    def _compose_layers_pixmap(self):
        """Görünür katmanları birleştirerek bir QPixmap oluşturur."""
        return compose_layers_pixmap(self.layers, image_to_qpixmap)

    def set_active_layer(self, idx):
        """Aktif katmanı değiştirir. Özyinelemeli referans sorunlarını önlemek için optimize edilmiştir."""
        try:
            # Katman kontrolü
            if not hasattr(self, 'layers'):
                logging.warning("set_active_layer: Katman yok")
                return

            # İndeks kontrolü
            if not (0 <= idx < len(self.layers.layers)):
                logging.warning(f"set_active_layer: Geçersiz indeks: {idx}")
                return

            # Aktif katmanı LayerManager üzerinden değiştir
            self.layers.set_active_layer(idx) # Use LayerManager's method

            # Katman panelini güncelle (LayerManager değişikliği tetiklemeli veya burada yapılmalı)
            # LayerPanel'in refresh'i zaten set_active_layer içinde çağrılıyor olmalı
            # Eğer LayerPanel refresh'i MainWindow'dan bağımsız değilse, burada çağır:
            self.layer_panel.refresh()

            logging.info(f"Aktif katman değiştirildi: {idx}")

        except Exception as e:
            logging.error(f"set_active_layer (MainWindow) hatası: {e}")
            # Hata durumunda sessizce devam etme, logla

    def handle_text_tool_click(self, scene_pos: QPointF):
        """Handles clicks when the text tool is active."""
        logging.info(f"Handling text tool click at {scene_pos.x()}, {scene_pos.y()}")
        if not hasattr(self, 'layers'):
            QMessageBox.warning(self, 'Uyarı', 'Metin eklemek için önce bir resim açın!')
            return

        layer = self.layers.get_active_layer()
        if layer is None or layer.image is None:
            QMessageBox.warning(self, 'Uyarı', 'Metin eklemek için aktif bir katman seçin!')
            return

        # --- Get Text Properties ---
        text, ok1 = QInputDialog.getText(self, 'Metin Ekle', 'Metni girin:')
        if not ok1 or not text:
            return # User cancelled or entered empty text

        # Font Selection (Basic for now, using QFontDialog)
        font, ok2 = QFontDialog.getFont(self)
        if not ok2:
            return # User cancelled font selection

        # Color Selection
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Metin Rengi Seç")
        if not color.isValid():
            return # User cancelled color selection

        # Convert QColor to RGBA tuple for PIL
        text_color = (color.red(), color.green(), color.blue(), color.alpha())

        # Convert scene coordinates to image coordinates (integer)
        img_x = int(scene_pos.x())
        img_y = int(scene_pos.y())

        # --- Apply Text ---
        old_img = layer.image.copy()
        try:
            # Use the selected QFont properties with PIL ImageFont
            # Need to find a suitable font file (.ttf, .otf)
            font_size = font.pointSize()
            if font_size <= 0: font_size = 12 # Default size if pointSize is invalid
            pil_font = get_pil_font(font.family(), font_size, font.styleName())

            new_img = draw_text_on_image(layer.image, text, (img_x, img_y), pil_font, text_color)
            if new_img is None:
                raise ValueError("Metin çizimi başarısız oldu.")

            # --- History Command ---
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
            # Restore original image on error
            layer.image = old_img
            self.refresh_layers()

    def restore_layer_original_size(self):
        """Aktif katmanı orijinal çözünürlüğüne döndürür."""
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

    # --- Drag and Drop Events ---
    def dragEnterEvent(self, event):
        """Handles drag enter events to accept image files."""
        mime_data = event.mimeData()
        # Check if the dragged data contains URLs and if they are local files
        if mime_data.hasUrls() and all(url.isLocalFile() for url in mime_data.urls()):
            # Check if any file has a supported image extension
            supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            if any(url.toLocalFile().lower().endswith(tuple(supported_extensions)) for url in mime_data.urls()):
                event.acceptProposedAction() # Accept the drop
                logging.debug("Drag enter accepted for image file(s).")
            else:
                logging.debug("Drag enter rejected: Unsupported file type.")
                event.ignore()
        else:
            logging.debug("Drag enter rejected: Not a local file URL.")
            event.ignore()

    def dropEvent(self, event):
        """Handles drop events to load the dropped image file."""
        logging.debug("Drop event received.") # Added logging
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            logging.debug(f"Dropped URLs: {[url.toString() for url in mime_data.urls()]}") # Added logging
            # Process only the first valid image file found
            supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            loaded_successfully = False # Added flag
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    logging.debug(f"Processing local file URL: {file_path}") # Added logging
                    if file_path.lower().endswith(tuple(supported_extensions)):
                        logging.info(f"Attempting to load supported dropped file: {file_path}") # Modified logging
                        if self._load_image_from_path(file_path):
                            logging.info(f"Successfully loaded dropped file: {file_path}") # Added logging
                            event.acceptProposedAction()
                            loaded_successfully = True # Set flag
                        else:
                            logging.warning(f"Failed to load dropped file via _load_image_from_path: {file_path}") # Added logging
                            event.ignore() # Loading failed
                        return # Stop after processing the first valid image (success or failure)
                    else:
                        logging.debug(f"Skipping unsupported file type: {file_path}") # Added logging
                else:
                    logging.debug(f"Skipping non-local URL: {url.toString()}") # Added logging

            # This part is reached only if the loop completes without finding a supported local file
            if not loaded_successfully:
                logging.warning("Drop event ignored: No supported image files found or loaded from dropped items.")
                event.ignore()
        else:
            logging.debug("Drop event ignored: No URLs found.")
            event.ignore()

    # --- Helper Methods ---
    def _compose_layers_pixmap(self):
        """Composes visible layers into a single QPixmap."""
        if not hasattr(self, 'layers') or not self.layers.layers:
            return None
        merged_image = self.layers.merge_visible()
        if merged_image:
            return image_to_qpixmap(merged_image)
        return None

    def toggle_resize_mode(self):
        """Yeniden boyutlandırma modunu açıp kapatır."""
        # This function should now open the ResizeDialog
        try:
            layer = self.layers.get_active_layer()
            if layer is None or layer.image is None:
                QMessageBox.warning(self, 'Uyarı', 'Resize işlemi için aktif bir katman gerekli!')
                return

            original_size = layer.image.size # Store original size for undo

            dialog = ResizeDialog(layer, self) # Pass layer and parent window
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Call the correct method and unpack needed values
                # The resample method is also returned but handled by layer.resize
                new_width, new_height, _, _ = dialog.get_resize_parameters() 

                # Check if size actually changed
                if (new_width, new_height) == original_size:
                    self.status_bar.showMessage("Boyut değiştirilmedi.")
                    return

                logging.info(f"Resizing layer '{layer.name}' from {original_size} to ({new_width}, {new_height})")

                # --- Create command for history ---
                def redo_func():
                    # The actual resize happens here, using the layer's method
                    success = layer.resize(new_width, new_height)
                    if success:
                        self.refresh_layers() # Update display after resize
                        self.status_bar.showMessage(f"Katman '{layer.name}' yeniden boyutlandırıldı: {new_width}x{new_height}")
                    else:
                         # layer.resize might log errors, but show a message too
                         QMessageBox.critical(self, 'Hata', 'Katman yeniden boyutlandırılamadı.')
                    return success # Indicate success/failure for history

                def undo_func():
                    # Resize back to original size
                    success = layer.resize(original_size[0], original_size[1])
                    if success:
                        self.refresh_layers()
                        self.status_bar.showMessage(f"Yeniden boyutlandırma geri alındı: {original_size[0]}x{original_size[1]}")
                    else:
                         QMessageBox.critical(self, 'Hata', 'Yeniden boyutlandırma geri alınamadı.')
                    return success
                # --- End command definition ---

                command = Command(redo_func, undo_func, f"Resize Layer '{layer.name}'")
                # Execute the command and add to history
                command.do() 
                self.history.push(command)

            else:
                # Dialog was cancelled
                self.status_bar.showMessage("Yeniden boyutlandırma iptal edildi.")

        except Exception as e:
            logging.error(f"Resize action failed: {e}", exc_info=True)
            QMessageBox.critical(self, 'Hata', f'Yeniden boyutlandırma sırasında bir hata oluştu: {e}')

    def create_drawing_tools_panel(self):
        """Çizim ve şekil araçları ayarları için panel oluşturur."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Renk seçim düğmesi
        color_button = QPushButton("Renk Seç")
        color_button.setStyleSheet(f"background-color: rgb({self.current_color.red()}, {self.current_color.green()}, {self.current_color.blue()}); color: white;")
        color_button.clicked.connect(self.select_color_from_panel)
        layout.addWidget(color_button)
        self.color_button = color_button  # Daha sonra güncellemek için referans saklayalım
        
        # Şekil araçları butonları
        shape_button_layout = QHBoxLayout()
        
        shape_button = QPushButton("Şekil")
        shape_button.setCheckable(True)
        shape_button.clicked.connect(lambda: self.set_tool('shape'))
        shape_button_layout.addWidget(shape_button)
        self.shape_button = shape_button
        
        line_button = QPushButton("Çizgi")
        line_button.setCheckable(True)
        line_button.clicked.connect(lambda: self.set_tool('line'))
        shape_button_layout.addWidget(line_button)
        self.line_button = line_button
        
        rect_button = QPushButton("Dikdörtgen")
        rect_button.setCheckable(True)
        rect_button.clicked.connect(lambda: self.set_tool('rectangle'))
        shape_button_layout.addWidget(rect_button)
        self.rect_button = rect_button
        
        ellipse_button = QPushButton("Elips")
        ellipse_button.setCheckable(True)
        ellipse_button.clicked.connect(lambda: self.set_tool('ellipse'))
        shape_button_layout.addWidget(ellipse_button)
        self.ellipse_button = ellipse_button
        
        layout.addLayout(shape_button_layout)
        
        # Fırça boyutu slider
        brush_layout = QHBoxLayout()
        brush_label = QLabel("Fırça Boyutu:")
        brush_layout.addWidget(brush_label)
        
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setMinimum(1)
        self.brush_size_slider.setMaximum(100)
        self.brush_size_slider.setValue(self.current_brush_size)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        brush_layout.addWidget(self.brush_size_slider)
        
        self.brush_size_value_label = QLabel(f"{self.current_brush_size}")
        brush_layout.addWidget(self.brush_size_value_label)
        layout.addLayout(brush_layout)
        
        # Kalem boyutu slider
        pencil_layout = QHBoxLayout()
        pencil_label = QLabel("Kalem Boyutu:")
        pencil_layout.addWidget(pencil_label)
        
        self.pencil_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.pencil_size_slider.setMinimum(1)
        self.pencil_size_slider.setMaximum(20)
        self.pencil_size_slider.setValue(self.current_pencil_size)
        self.pencil_size_slider.valueChanged.connect(self._on_pencil_size_changed)
        pencil_layout.addWidget(self.pencil_size_slider)
        
        self.pencil_size_value_label = QLabel(f"{self.current_pencil_size}")
        pencil_layout.addWidget(self.pencil_size_value_label)
        layout.addLayout(pencil_layout)
        
        # Silgi boyutu slider
        eraser_layout = QHBoxLayout()
        eraser_label = QLabel("Silgi Boyutu:")
        eraser_layout.addWidget(eraser_label)
        
        self.eraser_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.eraser_size_slider.setMinimum(1)
        self.eraser_size_slider.setMaximum(100)
        self.eraser_size_slider.setValue(self.current_eraser_size)
        self.eraser_size_slider.valueChanged.connect(self._on_eraser_size_changed)
        eraser_layout.addWidget(self.eraser_size_slider)
        
        self.eraser_size_value_label = QLabel(f"{self.current_eraser_size}")
        eraser_layout.addWidget(self.eraser_size_value_label)
        layout.addLayout(eraser_layout)
        
        # Doldurma toleransı slider
        fill_layout = QHBoxLayout()
        fill_label = QLabel("Doldurma Toleransı:")
        fill_layout.addWidget(fill_label)
        
        self.fill_tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self.fill_tolerance_slider.setMinimum(0)
        self.fill_tolerance_slider.setMaximum(255)
        self.fill_tolerance_slider.setValue(self.current_fill_tolerance)
        self.fill_tolerance_slider.valueChanged.connect(self._on_fill_tolerance_changed)
        fill_layout.addWidget(self.fill_tolerance_slider)
        
        self.fill_tolerance_value_label = QLabel(f"{self.current_fill_tolerance}")
        fill_layout.addWidget(self.fill_tolerance_value_label)
        layout.addLayout(fill_layout)
        
        # Boşluk ekle
        layout.addStretch()
        
        # Panel için stil
        panel.setStyleSheet("""
            QLabel { font-size: 12px; }
            QPushButton { font-size: 14px; padding: 8px; }
            QSlider { height: 20px; }
        """)
        
        return panel
        
    def select_color_from_panel(self):
        """Panel üzerindeki renk düğmesinden renk seçimi yapar."""
        color = QColorDialog.getColor(
            self.current_color, 
            self, 
            "Çizim Rengi Seç",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        
        if color.isValid():
            self.set_drawing_color(color)
            # Renk düğmesinin arkaplan rengini güncelle
            self.color_button.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); color: white;")
            
    def _on_brush_size_changed(self, value):
        """Slider ile fırça boyutu değiştiğinde."""
        self.current_brush_size = value
        self.brush_size_value_label.setText(f"{value}")
        self.brush_tool.set_size(value)
        
        # Aktif araç fırça ise imleci güncelle
        if self.current_tool == 'brush':
            self.image_view.setCursor(self._create_brush_cursor(value))
            
    def _on_pencil_size_changed(self, value):
        """Slider ile kalem boyutu değiştiğinde."""
        self.current_pencil_size = value
        self.pencil_size_value_label.setText(f"{value}")
        self.pencil_tool.set_size(value)
        
        # Aktif araç kalem ise imleci güncelle
        if self.current_tool == 'pencil':
            self.image_view.setCursor(self._create_brush_cursor(value))
            
    def _on_eraser_size_changed(self, value):
        """Slider ile silgi boyutu değiştiğinde."""
        self.current_eraser_size = value
        self.eraser_size_value_label.setText(f"{value}")
        self.eraser_tool.set_size(value)
        
        # Aktif araç silgi ise imleci güncelle
        if self.current_tool == 'eraser':
            self.image_view.setCursor(self._create_brush_cursor(value))
            
    def _on_fill_tolerance_changed(self, value):
        """Slider ile doldurma toleransı değiştiğinde."""
        self.current_fill_tolerance = value
        self.fill_tolerance_value_label.setText(f"{value}")
        self.fill_tool.tolerance = value

    def check_gpu_status(self):
        """Check GPU availability and set internal state"""
        self.has_gpu = torch.cuda.is_available()
        if self.has_gpu:
            self.gpu_count = torch.cuda.device_count()
            self.gpu_info = []
            for i in range(self.gpu_count):
                self.gpu_info.append({
                    "id": i,
                    "name": torch.cuda.get_device_name(i)
                })
            # Durum çubuğunu güncelle
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
            # Durum çubuğunu güncelle
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("GPU bulunamadı, CPU modu kullanılıyor", 5000)
    
    def toggle_gpu_usage(self, checked):
        """Toggle GPU usage on/off"""
        self.use_gpu = checked
        self.settings.setValue("use_gpu", checked)
        
        if checked and not self.has_gpu:
            QMessageBox.warning(self, "GPU Not Available", 
                               "GPU acceleration is not available on this system. "
                               "The software will continue to run in CPU mode.")
            self.use_gpu = False
            self.use_gpu_action.setChecked(False)
            return
        
        # Apply the change immediately
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
        """Select a specific GPU device"""
        if gpu_id >= self.gpu_count:
            QMessageBox.warning(self, "Invalid GPU", f"GPU {gpu_id} is not available")
            return
            
        self.gpu_id = gpu_id
        self.settings.setValue("gpu_id", gpu_id)
        
        # Apply the change if GPU is enabled
        if self.use_gpu:
            configure_gpu(self.gpu_id)
            QMessageBox.information(self, "GPU Changed", 
                                   f"Now using GPU {gpu_id}: {torch.cuda.get_device_name(gpu_id)}")
    
    def show_gpu_info(self):
        """Show detailed GPU information"""
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
                
            # Get memory info
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
