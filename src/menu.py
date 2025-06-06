from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import torch
class MenuManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tool_actions = {}
    def create_menus(self):
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
        self.file_menu = self.main_window.menu_bar.addMenu('Dosya')
        open_action = QAction('Aç...', self.main_window)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.main_window.open_image)
        self.file_menu.addAction(open_action)
        save_action = QAction('Kaydet', self.main_window)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.main_window.save_image)
        self.file_menu.addAction(save_action)
        save_as_action = QAction('Farklı Kaydet...', self.main_window)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.main_window.save_image_as)
        self.file_menu.addAction(save_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction('Kapat', self.main_window.close_image)
        self.file_menu.addSeparator()
        exit_action = QAction('Çıkış', self.main_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.main_window.close)
        self.file_menu.addAction(exit_action)
    def _create_edit_menu(self):
        self.edit_menu = self.main_window.menu_bar.addMenu('Düzenle')
        undo_action = QAction('Geri Al', self.main_window)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.main_window.undo)
        self.edit_menu.addAction(undo_action)
        redo_action = QAction('İleri Al', self.main_window)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(self.main_window.redo)
        self.edit_menu.addAction(redo_action)
    def _create_filters_menu(self):
        self.filter_menu = self.main_window.menu_bar.addMenu('Filtreler')
        self.filter_menu.addAction('Bulanıklaştır...', self.main_window.blur_dialog)
        self.filter_menu.addAction('Keskinleştir...', self.main_window.sharpen_dialog)
        self.filter_menu.addAction('Gürültü Ekle...', self.main_window.noise_dialog)
        self.filter_menu.addAction('Gri Tonlama...', self.main_window.grayscale_dialog)
        self.filter_menu.addSeparator()
        self.filter_menu.addAction('Parlaklık...', self.main_window.brightness_dialog)
        self.filter_menu.addAction('Kontrast...', self.main_window.contrast_dialog)
        self.filter_menu.addAction('Doygunluk...', self.main_window.saturation_dialog)
        self.filter_menu.addAction('Ton...', self.main_window.hue_dialog)
    def _create_adjustments_menu(self):
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
        select_menu = self.main_window.menu_bar.addMenu('Seçim')
        select_all_action = QAction('Tümünü Seç', self.main_window)
        select_all_action.setShortcut('Ctrl+A')
        select_all_action.triggered.connect(self.main_window.select_all)
        select_menu.addAction(select_all_action)
        clear_sel_action = QAction('Seçimi Temizle', self.main_window)
        clear_sel_action.setShortcut('Ctrl+D')
        clear_sel_action.triggered.connect(self.main_window.image_view.clear_selection)
        select_menu.addAction(clear_sel_action)
        select_menu.addSeparator()
        rect_action = QAction('Dikdörtgen Seç', self.main_window)
        rect_action.triggered.connect(lambda: self.main_window.image_view.set_selection_mode('rectangle'))
        select_menu.addAction(rect_action)
        ellipse_action = QAction('Elips Seç', self.main_window)
        ellipse_action.triggered.connect(lambda: self.main_window.image_view.set_selection_mode('ellipse'))
        select_menu.addAction(ellipse_action)
        lasso_action = QAction('Serbest Seç (Lasso)', self.main_window)
        lasso_action.triggered.connect(lambda: self.main_window.image_view.set_selection_mode('lasso'))
        select_menu.addAction(lasso_action)
    def _create_layers_menu(self):
        self.layer_menu = self.main_window.menu_bar.addMenu('Katman')
        add_layer_action = QAction('Katman Ekle', self.main_window)
        add_layer_action.setShortcut('Ctrl+Shift+N')
        add_layer_action.triggered.connect(self.main_window.add_layer)
        self.layer_menu.addAction(add_layer_action)
        delete_layer_action = QAction('Katman Sil', self.main_window)
        delete_layer_action.setShortcut('Del')
        delete_layer_action.triggered.connect(self.main_window.delete_layer)
        self.layer_menu.addAction(delete_layer_action)
        self.layer_menu.addSeparator()
        merge_layers_action = QAction('Katmanları Birleştir', self.main_window)
        merge_layers_action.setShortcut('Ctrl+M')
        merge_layers_action.triggered.connect(self.main_window.merge_layers)
        self.layer_menu.addAction(merge_layers_action)
        toggle_visibility_action = QAction('Katman Görünürlüğünü Değiştir', self.main_window)
        toggle_visibility_action.setShortcut('Ctrl+H')
        toggle_visibility_action.triggered.connect(self.main_window.toggle_layer_visibility)
        self.layer_menu.addAction(toggle_visibility_action)
        self.layer_menu.addSeparator()
        move_up_action = QAction('Katmanı Yukarı Taşı', self.main_window)
        move_up_action.setShortcut('Ctrl+Up')
        move_up_action.triggered.connect(self.main_window.move_layer_up)
        self.layer_menu.addAction(move_up_action)
        move_down_action = QAction('Katmanı Aşağı Taşı', self.main_window)
        move_down_action.setShortcut('Ctrl+Down')
        move_down_action.triggered.connect(self.main_window.move_layer_down)
        self.layer_menu.addAction(move_down_action)
        self.layer_menu.addSeparator()
        self.layer_menu.addAction('Orijinal Çözünürlüğe Döndür', self.main_window.restore_layer_original_size)
    def _create_tools_menu(self):
        self.tools_menu = self.main_window.menu_bar.addMenu('Araçlar')
        select_action = QAction('Seçim Aracı', self.main_window)
        select_action.setCheckable(True)
        select_action.setChecked(True)  
        select_action.setShortcut('V')
        select_action.triggered.connect(lambda: self.main_window.set_tool('select'))
        self.tools_menu.addAction(select_action)
        self.tool_actions['select'] = select_action
        text_action = QAction('Metin Aracı', self.main_window)
        text_action.setCheckable(True)
        text_action.setShortcut('T')
        text_action.triggered.connect(lambda: self.main_window.set_tool('text'))
        self.tools_menu.addAction(text_action)
        self.tool_actions['text'] = text_action
        self.tools_menu.addSeparator()
        brush_action = QAction('Fırça', self.main_window)
        brush_action.setCheckable(True)
        brush_action.setShortcut('B')
        brush_action.setStatusTip('Yumuşak fırça ile çizim yapın')
        brush_action.triggered.connect(lambda: self.main_window.set_tool('brush'))
        self.tools_menu.addAction(brush_action)
        self.tool_actions['brush'] = brush_action
        pencil_action = QAction('Kalem', self.main_window)
        pencil_action.setCheckable(True)
        pencil_action.setShortcut('P')
        pencil_action.setStatusTip('Keskin kenarlı kalem ile çizim yapın')
        pencil_action.triggered.connect(lambda: self.main_window.set_tool('pencil'))
        self.tools_menu.addAction(pencil_action)
        self.tool_actions['pencil'] = pencil_action
        eraser_action = QAction('Silgi', self.main_window)
        eraser_action.setCheckable(True)
        eraser_action.setShortcut('E')
        eraser_action.setStatusTip('Silgi ile pikselleri şeffaflaştırın')
        eraser_action.triggered.connect(lambda: self.main_window.set_tool('eraser'))
        self.tools_menu.addAction(eraser_action)
        self.tool_actions['eraser'] = eraser_action
        fill_action = QAction('Doldurma Kovası', self.main_window)
        fill_action.setCheckable(True)
        fill_action.setShortcut('G')
        fill_action.setStatusTip('Benzer renkli alanları doldurun')
        fill_action.triggered.connect(lambda: self.main_window.set_tool('fill'))
        self.tools_menu.addAction(fill_action)
        self.tool_actions['fill'] = fill_action
        self.tools_menu.addSeparator()
        resize_action = self.tools_menu.addAction('Yeniden Boyutlandır')
        resize_action.setCheckable(True)
        resize_action.setStatusTip('Katmanı kenarlarından sürükleyerek yeniden boyutlandır')
        resize_action.triggered.connect(self.main_window.toggle_resize_mode)
        self.resize_action = resize_action  
        self.tool_actions['resize'] = resize_action
    def _create_drawing_options_menu(self):
        draw_options_menu = self.main_window.menu_bar.addMenu('Çizim Seçenekleri')
        color_action = QAction('Çizim Rengi Seç...', self.main_window)
        color_action.triggered.connect(self.main_window.set_drawing_color)
        draw_options_menu.addAction(color_action)
        draw_options_menu.addSeparator()
        brush_size_action = QAction('Fırça Boyutu...', self.main_window)
        brush_size_action.triggered.connect(self.main_window.set_brush_size)
        draw_options_menu.addAction(brush_size_action)
        pencil_size_action = QAction('Kalem Boyutu...', self.main_window)
        pencil_size_action.triggered.connect(self.main_window.set_pencil_size)
        draw_options_menu.addAction(pencil_size_action)
        eraser_size_action = QAction('Silgi Boyutu...', self.main_window)
        eraser_size_action.triggered.connect(self.main_window.set_eraser_size)
        draw_options_menu.addAction(eraser_size_action)
        draw_options_menu.addSeparator()
        fill_tolerance_action = QAction('Doldurma Toleransı...', self.main_window)
        fill_tolerance_action.triggered.connect(self.main_window.set_fill_tolerance)
        draw_options_menu.addAction(fill_tolerance_action)
    def _create_settings_menu(self):
        settings_menu = self.main_window.menu_bar.addMenu('Ayarlar')
        gpu_menu = settings_menu.addMenu('GPU Ayarları')
        self.use_gpu_action = QAction("GPU Kullan", self.main_window)
        self.use_gpu_action.setCheckable(True)
        self.use_gpu_action.setChecked(self.main_window.use_gpu)
        self.use_gpu_action.triggered.connect(self.main_window.toggle_gpu_usage)
        gpu_menu.addAction(self.use_gpu_action)
        if torch.cuda.is_available():
            gpu_device_menu = gpu_menu.addMenu("GPU Cihazı Seç")
            device_count = torch.cuda.device_count()
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                device_action = QAction(f"GPU {i}: {device_name}", self.main_window)
                device_action.setCheckable(True)
                device_action.setChecked(self.main_window.gpu_id == i)
                device_action.triggered.connect(lambda checked, gpu_id=i: self.main_window.select_gpu_device(gpu_id))
                gpu_device_menu.addAction(device_action)
        gpu_info_action = QAction("GPU Bilgisini Göster", self.main_window)
        gpu_info_action.triggered.connect(self.main_window.show_gpu_info)
        gpu_menu.addAction(gpu_info_action)