from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import torch

class MenuManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tool_actions = {}

    def create_menus(self):
        """Creates and returns all menus for the main window."""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_filters_menu()
        self._create_adjustments_menu()
        self._create_transform_menu()
        self._create_selection_menu()
        self._create_layers_menu()
        self._create_tools_menu()
        self._create_drawing_options_menu()
        self._create_settings_menu()

    def _create_file_menu(self):
        """Creates the File menu."""
        self.file_menu = self.main_window.menu_bar.addMenu('Dosya')
        self.file_menu.addAction('Aç...', self.main_window.open_image)
        self.file_menu.addAction('Kaydet', self.main_window.save_image)
        self.file_menu.addAction('Farklı Kaydet...', self.main_window.save_image_as)
        self.file_menu.addSeparator()
        self.file_menu.addAction('Kapat', self.main_window.close_image)
        self.file_menu.addSeparator()
        self.file_menu.addAction('Çıkış', self.main_window.close)

    def _create_edit_menu(self):
        """Creates the Edit menu."""
        self.edit_menu = self.main_window.menu_bar.addMenu('Düzenle')
        self.edit_menu.addAction('Geri Al', self.main_window.undo)
        self.edit_menu.addAction('İleri Al', self.main_window.redo)

    def _create_filters_menu(self):
        """Creates the Filters menu."""
        self.filter_menu = self.main_window.menu_bar.addMenu('Filtreler')
        
        # Basic filters
        self.filter_menu.addAction('Bulanıklaştır...', self.main_window.blur_dialog)
        self.filter_menu.addAction('Keskinleştir...', self.main_window.sharpen_dialog)
        self.filter_menu.addAction('Gürültü Ekle...', self.main_window.noise_dialog)
        self.filter_menu.addAction('Gri Tonlama...', self.main_window.grayscale_dialog)
        
        # Separating color adjustments
        self.filter_menu.addSeparator()
        
        # Color adjustments
        self.filter_menu.addAction('Parlaklık...', self.main_window.brightness_dialog)
        self.filter_menu.addAction('Kontrast...', self.main_window.contrast_dialog)
        self.filter_menu.addAction('Doygunluk...', self.main_window.saturation_dialog)
        self.filter_menu.addAction('Ton...', self.main_window.hue_dialog)

    def _create_adjustments_menu(self):
        """Creates the Adjustments menu."""
        adjust_menu = self.main_window.menu_bar.addMenu('Ayarlamalar')
        
        bright_action = QAction('Parlaklık', self.main_window)
        bright_action.triggered.connect(self.main_window.brightness_dialog)
        adjust_menu.addAction(bright_action)
        
        contrast_action = QAction('Kontrast', self.main_window)
        contrast_action.triggered.connect(self.main_window.contrast_dialog)
        adjust_menu.addAction(contrast_action)
        
        sat_action = QAction('Doygunluk', self.main_window)
        sat_action.triggered.connect(self.main_window.saturation_dialog)
        adjust_menu.addAction(sat_action)
        
        hue_action = QAction('Ton', self.main_window)
        hue_action.triggered.connect(self.main_window.hue_dialog)
        adjust_menu.addAction(hue_action)

    def _create_transform_menu(self):
        """Creates the Transform menu."""
        self.transform_menu = self.main_window.menu_bar.addMenu('Dönüştür')
        self.transform_menu.addAction('90° Sağa Döndür', lambda: self.main_window.apply_transform('rotate_90'))
        self.transform_menu.addAction('90° Sola Döndür', lambda: self.main_window.apply_transform('rotate_270'))
        self.transform_menu.addAction('180° Döndür', lambda: self.main_window.apply_transform('rotate_180'))
        self.transform_menu.addSeparator()
        self.transform_menu.addAction('Yatay Çevir', lambda: self.main_window.apply_transform('flip_h'))
        self.transform_menu.addAction('Dikey Çevir', lambda: self.main_window.apply_transform('flip_v'))
        self.transform_menu.addSeparator()
        self.transform_menu.addAction('Yeniden Boyutlandır...', self.main_window.resize_dialog)
        self.transform_menu.addAction('Seçimi Kırp', self.main_window.crop_selected)

    def _create_selection_menu(self):
        """Creates the Selection menu."""
        select_menu = self.main_window.menu_bar.addMenu('Seçim')
        
        rect_action = QAction('Dikdörtgen Seç', self.main_window)
        rect_action.triggered.connect(lambda: self.main_window.image_view.set_selection_mode('rectangle'))
        select_menu.addAction(rect_action)
        
        ellipse_action = QAction('Elips Seç', self.main_window)
        ellipse_action.triggered.connect(lambda: self.main_window.image_view.set_selection_mode('ellipse'))
        select_menu.addAction(ellipse_action)
        
        lasso_action = QAction('Serbest Seç (Lasso)', self.main_window)
        lasso_action.triggered.connect(lambda: self.main_window.image_view.set_selection_mode('lasso'))
        select_menu.addAction(lasso_action)
        
        clear_sel_action = QAction('Seçimi Temizle', self.main_window)
        clear_sel_action.triggered.connect(self.main_window.image_view.clear_selection)
        select_menu.addAction(clear_sel_action)

    def _create_layers_menu(self):
        """Creates the Layers menu."""
        self.layer_menu = self.main_window.menu_bar.addMenu('Katman')
        self.layer_menu.addAction('Katman Ekle', self.main_window.add_layer)
        self.layer_menu.addAction('Katman Sil', self.main_window.delete_layer)
        self.layer_menu.addSeparator()
        self.layer_menu.addAction('Katmanları Birleştir', self.main_window.merge_layers)
        self.layer_menu.addAction('Katman Görünürlüğünü Değiştir', self.main_window.toggle_layer_visibility)
        self.layer_menu.addSeparator()
        self.layer_menu.addAction('Katmanı Yukarı Taşı', self.main_window.move_layer_up)
        self.layer_menu.addAction('Katmanı Aşağı Taşı', self.main_window.move_layer_down)
        self.layer_menu.addSeparator()
        self.layer_menu.addAction('Orijinal Çözünürlüğe Döndür', self.main_window.restore_layer_original_size)

    def _create_tools_menu(self):
        """Creates the Tools menu."""
        self.tools_menu = self.main_window.menu_bar.addMenu('Araçlar')
        
        # Add selection tool action
        select_action = self.tools_menu.addAction('Seçim Aracı')
        select_action.setCheckable(True)
        select_action.setChecked(True)  # Default tool selected
        select_action.triggered.connect(lambda: self.main_window.set_tool('select'))
        self.tool_actions['select'] = select_action
        
        # Add text tool action
        text_action = self.tools_menu.addAction('Metin Aracı')
        text_action.setCheckable(True)
        text_action.triggered.connect(lambda: self.main_window.set_tool('text'))
        self.tool_actions['text'] = text_action
        
        # Çizim araçları için menü ayırıcı
        self.tools_menu.addSeparator()
        
        # Fırça aracı
        brush_action = self.tools_menu.addAction('Fırça')
        brush_action.setCheckable(True)
        brush_action.setStatusTip('Yumuşak fırça ile çizim yapın')
        brush_action.triggered.connect(lambda: self.main_window.set_tool('brush'))
        self.tool_actions['brush'] = brush_action
        
        # Kalem aracı
        pencil_action = self.tools_menu.addAction('Kalem')
        pencil_action.setCheckable(True)
        pencil_action.setStatusTip('Keskin kenarlı kalem ile çizim yapın')
        pencil_action.triggered.connect(lambda: self.main_window.set_tool('pencil'))
        self.tool_actions['pencil'] = pencil_action
        
        # Silgi aracı
        eraser_action = self.tools_menu.addAction('Silgi')
        eraser_action.setCheckable(True)
        eraser_action.setStatusTip('Silgi ile pikselleri şeffaflaştırın')
        eraser_action.triggered.connect(lambda: self.main_window.set_tool('eraser'))
        self.tool_actions['eraser'] = eraser_action
        
        # Kova aracı
        fill_action = self.tools_menu.addAction('Doldurma Kovası')
        fill_action.setCheckable(True)
        fill_action.setStatusTip('Benzer renkli alanları doldurun')
        fill_action.triggered.connect(lambda: self.main_window.set_tool('fill'))
        self.tool_actions['fill'] = fill_action
        
        # Yeniden boyutlandırma aracı bölümü
        self.tools_menu.addSeparator()
        resize_action = self.tools_menu.addAction('Yeniden Boyutlandır')
        resize_action.setCheckable(True)
        resize_action.setStatusTip('Katmanı kenarlarından sürükleyerek yeniden boyutlandır')
        resize_action.triggered.connect(self.main_window.toggle_resize_mode)
        self.resize_action = resize_action  # Bunu MainWindow'dan erişilebilir yap
        
        # Resize aracını da tool_actions listesine ekle
        self.tool_actions['resize'] = resize_action

    def _create_drawing_options_menu(self):
        """Çizim seçenekleri menüsünü oluşturur."""
        draw_options_menu = self.main_window.menu_bar.addMenu('Çizim Seçenekleri')
        
        # Renk seçimi
        color_action = QAction('Çizim Rengi Seç...', self.main_window)
        color_action.triggered.connect(self.main_window.set_drawing_color)
        draw_options_menu.addAction(color_action)
        
        # Ayırıcı
        draw_options_menu.addSeparator()
        
        # Fırça boyutu
        brush_size_action = QAction('Fırça Boyutu...', self.main_window)
        brush_size_action.triggered.connect(self.main_window.set_brush_size)
        draw_options_menu.addAction(brush_size_action)
        
        # Kalem boyutu
        pencil_size_action = QAction('Kalem Boyutu...', self.main_window)
        pencil_size_action.triggered.connect(self.main_window.set_pencil_size)
        draw_options_menu.addAction(pencil_size_action)
        
        # Silgi boyutu
        eraser_size_action = QAction('Silgi Boyutu...', self.main_window)
        eraser_size_action.triggered.connect(self.main_window.set_eraser_size)
        draw_options_menu.addAction(eraser_size_action)
        
        # Ayırıcı
        draw_options_menu.addSeparator()
        
        # Doldurma toleransı
        fill_tolerance_action = QAction('Doldurma Toleransı...', self.main_window)
        fill_tolerance_action.triggered.connect(self.main_window.set_fill_tolerance)
        draw_options_menu.addAction(fill_tolerance_action)

    def _create_settings_menu(self):
        """Creates the Settings menu with GPU options."""
        settings_menu = self.main_window.menu_bar.addMenu('Ayarlar')
        
        # GPU Settings Submenu
        gpu_menu = settings_menu.addMenu('GPU Ayarları')
        
        # Toggle GPU usage
        self.use_gpu_action = QAction("GPU Kullan", self.main_window)
        self.use_gpu_action.setCheckable(True)
        self.use_gpu_action.setChecked(self.main_window.use_gpu)
        self.use_gpu_action.triggered.connect(self.main_window.toggle_gpu_usage)
        gpu_menu.addAction(self.use_gpu_action)
        
        # GPU Device Selection submenu (only shown if CUDA is available)
        if torch.cuda.is_available():
            gpu_device_menu = gpu_menu.addMenu("GPU Cihazı Seç")
            device_count = torch.cuda.device_count()
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                device_action = QAction(f"GPU {i}: {device_name}", self.main_window)
                device_action.setCheckable(True)
                device_action.setChecked(self.main_window.gpu_id == i)
                # Use a lambda with default argument to capture the current value of i
                device_action.triggered.connect(lambda checked, gpu_id=i: self.main_window.select_gpu_device(gpu_id))
                gpu_device_menu.addAction(device_action)
        
        # Show GPU Info
        gpu_info_action = QAction("GPU Bilgisini Göster", self.main_window)
        gpu_info_action.triggered.connect(self.main_window.show_gpu_info)
        gpu_menu.addAction(gpu_info_action)
