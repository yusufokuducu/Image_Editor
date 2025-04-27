from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

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

    def _create_file_menu(self):
        """Creates the File menu."""
        file_menu = self.main_window.menu_bar.addMenu('Dosya')
        
        open_action = QAction('Aç', self.main_window)
        open_action.triggered.connect(self.main_window.open_image)
        file_menu.addAction(open_action)
        
        save_action = QAction('Kaydet', self.main_window)
        save_action.triggered.connect(self.main_window.save_image)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Farklı Kaydet', self.main_window)
        save_as_action.triggered.connect(self.main_window.save_image_as)
        file_menu.addAction(save_as_action)
        
        close_action = QAction('Kapat', self.main_window)
        close_action.triggered.connect(self.main_window.close_image)
        file_menu.addAction(close_action)

    def _create_edit_menu(self):
        """Creates the Edit menu."""
        edit_menu = self.main_window.menu_bar.addMenu('Düzen')
        
        undo_action = QAction('Geri Al', self.main_window)
        undo_action.triggered.connect(self.main_window.undo)
        undo_action.setShortcut('Ctrl+Z')
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('Yinele', self.main_window)
        redo_action.triggered.connect(self.main_window.redo)
        redo_action.setShortcut('Ctrl+Y')
        edit_menu.addAction(redo_action)

    def _create_filters_menu(self):
        """Creates the Filters menu."""
        filters_menu = self.main_window.menu_bar.addMenu('Filtreler')
        
        blur_action = QAction('Bulanıklaştır', self.main_window)
        blur_action.triggered.connect(self.main_window.blur_dialog)
        filters_menu.addAction(blur_action)
        
        sharpen_action = QAction('Keskinleştir', self.main_window)
        sharpen_action.triggered.connect(self.main_window.sharpen_dialog)
        filters_menu.addAction(sharpen_action)
        
        edge_action = QAction('Kenarları Vurgula', self.main_window)
        edge_action.triggered.connect(lambda: self.main_window.apply_filter('edge_enhance'))
        filters_menu.addAction(edge_action)
        
        gray_action = QAction('Gri Ton', self.main_window)
        gray_action.triggered.connect(self.main_window.grayscale_dialog)
        filters_menu.addAction(gray_action)
        
        noise_action = QAction('Gelişmiş Noise Ekle', self.main_window)
        noise_action.triggered.connect(self.main_window.noise_dialog)
        filters_menu.addAction(noise_action)

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
        transform_menu = self.main_window.menu_bar.addMenu('Dönüşümler')
        
        rotate90_action = QAction('90° Döndür', self.main_window)
        rotate90_action.triggered.connect(lambda: self.main_window.apply_transform('rotate90'))
        transform_menu.addAction(rotate90_action)
        
        rotate180_action = QAction('180° Döndür', self.main_window)
        rotate180_action.triggered.connect(lambda: self.main_window.apply_transform('rotate180'))
        transform_menu.addAction(rotate180_action)
        
        rotate270_action = QAction('270° Döndür', self.main_window)
        rotate270_action.triggered.connect(lambda: self.main_window.apply_transform('rotate270'))
        transform_menu.addAction(rotate270_action)
        
        flip_h_action = QAction('Yatay Çevir', self.main_window)
        flip_h_action.triggered.connect(lambda: self.main_window.apply_transform('flip_h'))
        transform_menu.addAction(flip_h_action)
        
        flip_v_action = QAction('Dikey Çevir', self.main_window)
        flip_v_action.triggered.connect(lambda: self.main_window.apply_transform('flip_v'))
        transform_menu.addAction(flip_v_action)
        
        resize_action = QAction('Yeniden Boyutlandır', self.main_window)
        resize_action.triggered.connect(self.main_window.resize_dialog)
        transform_menu.addAction(resize_action)
        
        crop_action = QAction('Kırp (Seçili Alan)', self.main_window)
        crop_action.triggered.connect(self.main_window.crop_selected)
        transform_menu.addAction(crop_action)

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
        layers_menu = self.main_window.menu_bar.addMenu('Katmanlar')
        
        add_layer_action = QAction('Yeni Katman', self.main_window)
        add_layer_action.triggered.connect(self.main_window.add_layer)
        add_layer_action.setShortcut('Ctrl+Shift+N')
        layers_menu.addAction(add_layer_action)
        
        del_layer_action = QAction('Katmanı Sil', self.main_window)
        del_layer_action.triggered.connect(self.main_window.delete_layer)
        del_layer_action.setShortcut('Del')
        layers_menu.addAction(del_layer_action)
        
        merge_action = QAction('Görünür Katmanları Birleştir', self.main_window)
        merge_action.triggered.connect(self.main_window.merge_layers)
        merge_action.setShortcut('Ctrl+M')
        layers_menu.addAction(merge_action)
        
        vis_toggle_action = QAction('Katman Görünürlüğünü Değiştir', self.main_window)
        vis_toggle_action.triggered.connect(self.main_window.toggle_layer_visibility)
        vis_toggle_action.setShortcut('Ctrl+H')
        layers_menu.addAction(vis_toggle_action)
        
        move_up_action = QAction('Katmanı Yukarı Taşı', self.main_window)
        move_up_action.triggered.connect(self.main_window.move_layer_up)
        move_up_action.setShortcut('Ctrl+Up')
        layers_menu.addAction(move_up_action)
        
        move_down_action = QAction('Katmanı Aşağı Taşı', self.main_window)
        move_down_action.triggered.connect(self.main_window.move_layer_down)
        move_down_action.setShortcut('Ctrl+Down')
        layers_menu.addAction(move_down_action)

    def _create_tools_menu(self):
        """Creates the Tools menu."""
        tools_menu = self.main_window.menu_bar.addMenu('Araçlar')
        
        text_tool_action = QAction('Metin Aracı', self.main_window)
        text_tool_action.setCheckable(True)
        text_tool_action.triggered.connect(lambda: self.main_window.set_tool('text'))
        tools_menu.addAction(text_tool_action)
        
        select_tool_action = QAction('Seçim Aracı', self.main_window)
        select_tool_action.setCheckable(True)
        select_tool_action.setChecked(True)
        select_tool_action.triggered.connect(lambda: self.main_window.set_tool('select'))
        tools_menu.addAction(select_tool_action)

        # Store actions for tool management
        self.tool_actions = {
            'select': select_tool_action,
            'text': text_tool_action
        }
