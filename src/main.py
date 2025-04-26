import sys
import os
import traceback
import gc
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStatusBar, QMenuBar,
                             QFileDialog, QMessageBox, QInputDialog, QDockWidget,
                             QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
                             QPushButton, QColorDialog, QFontDialog) # Added QColorDialog, QFontDialog
from PyQt6.QtGui import QAction, QPainter, QPixmap, QFont, QColor # Added QFont, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPointF # Added QObject for signals, QPointF
import logging
from .image_io import load_image, image_to_qpixmap
from .image_view import ImageView
from .filters import (apply_blur, apply_sharpen, apply_edge_enhance, apply_grayscale,
                      apply_noise, apply_brightness, apply_contrast, apply_saturation,
                      apply_hue)
from .transform import rotate_image, flip_image, resize_image, crop_image
from .history import History, Command
from .layers import LayerManager
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .layer_panel import LayerPanel
from .effects_panel import EffectsPanel # Yeni paneli import et
import platform

# --- Filter Slider Dialog ---
class FilterSliderDialog(QDialog):
    """A dialog with a slider to get a filter parameter, with preview signal."""
    # Signal emitted when the slider value changes, sending the correctly scaled value
    valueChangedPreview = pyqtSignal(float)
    # Signal emitted when the dialog is closed (accepted or rejected)
    previewFinished = pyqtSignal()

    def __init__(self, title, label_text, min_val, max_val, initial_val, step=1, decimals=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.decimals = decimals
        self.step = step # Store step for potential float conversion

        # Determine slider range based on decimals
        self.slider_min = int(min_val * (10**decimals))
        self.slider_max = int(max_val * (10**decimals))
        self.slider_initial = int(initial_val * (10**decimals))
        self.slider_step = int(step * (10**decimals)) # Slider step is always integer

        layout = QVBoxLayout(self)

        self.label = QLabel(f"{label_text}: {self._format_value(self.slider_initial)}")
        layout.addWidget(self.label)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(self.slider_min, self.slider_max)
        self.slider.setValue(self.slider_initial)
        self.slider.setSingleStep(self.slider_step)
        self.slider.setTickInterval(self.slider_step * 10) # Example tick interval
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.valueChanged.connect(self._update_label_and_emit) # Connect to new method
        layout.addWidget(self.slider)

        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Tamam")
        self.cancel_button = QPushButton("İptal")
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Emit previewFinished when the dialog closes
        self.finished.connect(self.previewFinished.emit) # Connect built-in finished signal

    def _update_label_and_emit(self, value):
        """Updates the label and emits the valueChangedPreview signal."""
        formatted_value = self._format_value(value)
        self.label.setText(f"{self.label.text().split(':')[0]}: {formatted_value}")
        # Emit the correctly scaled value
        if self.decimals == 0:
            self.valueChangedPreview.emit(float(value))
        else:
            self.valueChangedPreview.emit(value / (10**self.decimals))

    def _format_value(self, value):
        """Formats the integer slider value back to the original scale."""
        float_value = value / (10**self.decimals)
        return f"{float_value:.{self.decimals}f}"

    def get_value(self):
        """Returns the selected value in the original scale (float or int)."""
        slider_value = self.slider.value()
        if self.decimals == 0:
            return slider_value # Return as integer
        else:
            return slider_value / (10**self.decimals) # Return as float

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyxelEdit')
        self.setGeometry(100, 100, 1024, 768)

        # Temel bileşenleri oluştur
        self.history = History()
        self.layers = LayerManager()

        # Bellek temizleme zamanlayıcısı
        self.gc_timer = QTimer(self)
        self.gc_timer.timeout.connect(lambda: gc.collect())
        self.gc_timer.start(30000)  # 30 saniyede bir bellek temizliği

        # Preview state
        self.original_preview_image = None
        self.preview_active = False
        self.current_preview_filter_type = None # To know which filter is being previewed
        self.current_tool = 'select' # Default tool ('select', 'text', etc.)

        # UI bileşenlerini oluştur
        self._init_ui()

        logging.info("PyxelEdit başlatıldı")

    def _init_ui(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        # Menü ve diğer UI öğeleri burada eklenecek

        # Dosya menüsü
        file_menu = self.menu_bar.addMenu('Dosya')
        open_action = QAction('Aç', self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        save_action = QAction('Kaydet', self)
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)
        save_as_action = QAction('Farklı Kaydet', self)
        save_as_action.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_action)
        close_action = QAction('Kapat', self)
        close_action.triggered.connect(self.close_image)
        file_menu.addAction(close_action)

        # Düzen menüsü: Undo/Redo
        edit_menu = self.menu_bar.addMenu('Düzen')
        undo_action = QAction('Geri Al', self)
        undo_action.triggered.connect(self.undo)
        undo_action.setShortcut('Ctrl+Z')
        edit_menu.addAction(undo_action)
        redo_action = QAction('Yinele', self)
        redo_action.triggered.connect(self.redo)
        redo_action.setShortcut('Ctrl+Y')
        edit_menu.addAction(redo_action)

        # Filtreler menüsü
        filters_menu = self.menu_bar.addMenu('Filtreler')
        blur_action = QAction('Bulanıklaştır', self)
        blur_action.triggered.connect(self.blur_dialog)
        filters_menu.addAction(blur_action)
        sharpen_action = QAction('Keskinleştir', self)
        sharpen_action.triggered.connect(lambda: self.apply_filter('sharpen'))
        filters_menu.addAction(sharpen_action)
        edge_action = QAction('Kenarları Vurgula', self)
        edge_action.triggered.connect(lambda: self.apply_filter('edge'))
        filters_menu.addAction(edge_action)
        gray_action = QAction('Gri Ton', self)
        gray_action.triggered.connect(lambda: self.apply_filter('grayscale'))
        filters_menu.addAction(gray_action)
        noise_action = QAction('Gelişmiş Noise Ekle', self)
        noise_action.triggered.connect(self.noise_dialog)
        filters_menu.addAction(noise_action)

        # Ayarlamalar menüsü
        adjust_menu = self.menu_bar.addMenu('Ayarlamalar')
        bright_action = QAction('Parlaklık', self)
        bright_action.triggered.connect(self.brightness_dialog)
        adjust_menu.addAction(bright_action)
        contrast_action = QAction('Kontrast', self)
        contrast_action.triggered.connect(self.contrast_dialog)
        adjust_menu.addAction(contrast_action)
        sat_action = QAction('Doygunluk', self)
        sat_action.triggered.connect(self.saturation_dialog)
        adjust_menu.addAction(sat_action)
        hue_action = QAction('Ton', self)
        hue_action.triggered.connect(self.hue_dialog)
        adjust_menu.addAction(hue_action)


        # Dönüşümler menüsü
        transform_menu = self.menu_bar.addMenu('Dönüşümler')
        rotate90_action = QAction('90° Döndür', self)
        rotate90_action.triggered.connect(lambda: self.apply_transform('rotate90'))
        transform_menu.addAction(rotate90_action)
        rotate180_action = QAction('180° Döndür', self)
        rotate180_action.triggered.connect(lambda: self.apply_transform('rotate180'))
        transform_menu.addAction(rotate180_action)
        rotate270_action = QAction('270° Döndür', self)
        rotate270_action.triggered.connect(lambda: self.apply_transform('rotate270'))
        transform_menu.addAction(rotate270_action)
        flip_h_action = QAction('Yatay Çevir', self)
        flip_h_action.triggered.connect(lambda: self.apply_transform('flip_h'))
        transform_menu.addAction(flip_h_action)
        flip_v_action = QAction('Dikey Çevir', self)
        flip_v_action.triggered.connect(lambda: self.apply_transform('flip_v'))
        transform_menu.addAction(flip_v_action)
        resize_action = QAction('Yeniden Boyutlandır', self)
        resize_action.triggered.connect(self.resize_dialog)
        transform_menu.addAction(resize_action)
        # Dönüşümler menüsüne kırpma ekle
        crop_action = QAction('Kırp (Seçili Alan)', self)
        crop_action.triggered.connect(self.crop_selected)
        transform_menu.addAction(crop_action)

        # Görüntü alanı (QGraphicsView tabanlı ImageView)
        self.image_view = ImageView(self) # Pass main window reference
        self.setCentralWidget(self.image_view)
        self.image_view.textToolClicked.connect(self.handle_text_tool_click) # Connect the signal

        # Katman panelini dock olarak ekle
        self.layer_panel = LayerPanel(self)
        self.dock = QDockWidget('Katman Paneli', self)
        self.dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

        # Seçim araçları menüsü
        select_menu = self.menu_bar.addMenu('Seçim')
        rect_action = QAction('Dikdörtgen Seç', self)
        rect_action.triggered.connect(lambda: self.image_view.set_selection_mode('rectangle'))
        select_menu.addAction(rect_action)
        ellipse_action = QAction('Elips Seç', self)
        ellipse_action.triggered.connect(lambda: self.image_view.set_selection_mode('ellipse'))
        select_menu.addAction(ellipse_action)
        lasso_action = QAction('Serbest Seç (Lasso)', self)
        lasso_action.triggered.connect(lambda: self.image_view.set_selection_mode('lasso'))
        select_menu.addAction(lasso_action)
        clear_sel_action = QAction('Seçimi Temizle', self)
        clear_sel_action.triggered.connect(self.image_view.clear_selection)
        select_menu.addAction(clear_sel_action)

        # Katmanlar menüsü
        layers_menu = self.menu_bar.addMenu('Katmanlar')
        add_layer_action = QAction('Yeni Katman', self)
        add_layer_action.triggered.connect(self.add_layer)
        add_layer_action.setShortcut('Ctrl+Shift+N')
        layers_menu.addAction(add_layer_action)
        del_layer_action = QAction('Katmanı Sil', self)
        del_layer_action.triggered.connect(self.delete_layer)
        del_layer_action.setShortcut('Del')
        layers_menu.addAction(del_layer_action)
        merge_action = QAction('Görünür Katmanları Birleştir', self)
        merge_action.triggered.connect(self.merge_layers)
        merge_action.setShortcut('Ctrl+M')
        layers_menu.addAction(merge_action)
        vis_toggle_action = QAction('Katman Görünürlüğünü Değiştir', self)
        vis_toggle_action.triggered.connect(self.toggle_layer_visibility)
        vis_toggle_action.setShortcut('Ctrl+H')
        layers_menu.addAction(vis_toggle_action)
        # Katmanlar menüsüne yukarı/aşağı taşıma ekle
        move_up_action = QAction('Katmanı Yukarı Taşı', self)
        move_up_action.triggered.connect(self.move_layer_up)
        move_up_action.setShortcut('Ctrl+Up')
        layers_menu.addAction(move_up_action)
        move_down_action = QAction('Katmanı Aşağı Taşı', self)
        move_down_action.triggered.connect(self.move_layer_down)
        move_down_action.setShortcut('Ctrl+Down')
        layers_menu.addAction(move_down_action)

        # Araçlar menüsü
        tools_menu = self.menu_bar.addMenu('Araçlar')
        text_tool_action = QAction('Metin Aracı', self)
        text_tool_action.setCheckable(True) # Make it checkable to show active tool
        text_tool_action.triggered.connect(lambda: self.set_tool('text'))
        tools_menu.addAction(text_tool_action)
        # Add selection tool action to allow switching back
        select_tool_action = QAction('Seçim Aracı', self)
        select_tool_action.setCheckable(True)
        select_tool_action.setChecked(True) # Default tool
        select_tool_action.triggered.connect(lambda: self.set_tool('select'))
        tools_menu.addAction(select_tool_action)

        # Group actions for exclusive checking (optional but good UI)
        self.tool_actions = {
            'select': select_tool_action,
            'text': text_tool_action
        }

        # Efekt panelini dock olarak ekle
        self.effects_panel = EffectsPanel(self)
        self.effects_dock = QDockWidget('Efektler ve Ayarlamalar', self)
        self.effects_dock.setWidget(self.effects_panel)
        # Katman panelinin altına ekleyelim
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.effects_dock)
        # İki dock widget'ı yan yana değil de alt alta göstermek için (isteğe bağlı)
        self.tabifyDockWidget(self.dock, self.effects_dock) # Katman ve Efekt panellerini sekmeli yap
        self.dock.raise_() # Başlangıçta Katman paneli görünsün


    def set_tool(self, tool_name):
        """Sets the active tool and updates menu checks."""
        if tool_name in self.tool_actions:
            self.current_tool = tool_name
            logging.info(f"Araç değiştirildi: {tool_name}")
            for name, action in self.tool_actions.items():
                action.setChecked(name == tool_name)
            # Update status bar or cursor if needed
            self.status_bar.showMessage(f"Aktif Araç: {tool_name.capitalize()}")
            # Explicitly set ImageView mode when 'select' tool is chosen
            if tool_name == 'select':
                # Set the default selection shape (e.g., rectangle) when selection tool is active
                self.image_view.set_selection_mode('rectangle')
            # Optional: Clear selection when switching *away* from selection tool
            # else:
            #     self.image_view.clear_selection()
        else:
            logging.warning(f"Bilinmeyen araç adı: {tool_name}")


    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Resim Aç', '', 'Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif)')
        if file_path:
            img = load_image(file_path)
            if img is not None:
                self.layers = LayerManager()
                self.layers.add_layer(img, 'Arka Plan')
                merged = self.layers.merge_visible()
                pixmap = image_to_qpixmap(merged)
                self.image_view.set_image(pixmap)
            self.status_bar.showMessage(f'{file_path} | {img.width}x{img.height}')
            # self.current_image = merged # Removed: Rely on layers as source of truth
            self.current_image_path = file_path
            self.refresh_layers() # Update display and layer panel
        else:
            QMessageBox.critical(self, 'Hata', 'Resim yüklenemedi!')

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

        # Connect signals
        dialog.valueChangedPreview.connect(self._apply_preview_filter)
        # Use finished signal which provides the result code
        dialog.finished.connect(lambda result: self._finalize_preview(result, filter_type, dialog))

        # Show the dialog (non-modal might be better for true live preview, but modal is simpler for now)
        dialog.exec() # exec() is blocking, finalize will be called after it closes

    def _apply_preview_filter(self, value):
        """Applies the filter temporarily for preview."""
        if not self.preview_active or self.original_preview_image is None:
            return

        layer = self.layers.get_active_layer()
        if layer is None:
            return # Should not happen if preview_active is true

        try:
            # Apply filter to the *original* image copy
            img_copy = self.original_preview_image.copy()
            preview_img = self._get_filtered_image(img_copy, self.current_preview_filter_type, value)

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

        layer = self.layers.get_active_layer()
        original_image_to_restore = self.original_preview_image.copy() # Keep a copy before clearing

        # Clean up preview state immediately
        self.preview_active = False
        self.original_preview_image = None
        self.current_preview_filter_type = None

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


    def _get_filtered_image(self, img, filter_type, param):
        """Helper function to apply a filter and return the result."""
        # Ensure we have a valid image to work with
        if img is None or not isinstance(img, Image.Image):
             logging.error(f"_get_filtered_image: Invalid input image for {filter_type}")
             return None

        # Make a copy to avoid modifying the input directly during filtering
        img_copy = img.copy()

        try:
            if filter_type == 'blur':
                radius = param if param is not None else 2
                new_img = apply_blur(img_copy, radius)
            elif filter_type == 'sharpen':
                new_img = apply_sharpen(img_copy)
            elif filter_type == 'edge':
                new_img = apply_edge_enhance(img_copy)
            elif filter_type == 'grayscale':
                new_img = apply_grayscale(img_copy)
            elif filter_type == 'noise':
                amount = param if param is not None else 0.1
                new_img = apply_noise(img_copy, amount)
            elif filter_type == 'brightness':
                factor = param if param is not None else 1.0
                new_img = apply_brightness(img_copy, factor)
            elif filter_type == 'contrast':
                factor = param if param is not None else 1.0
                new_img = apply_contrast(img_copy, factor)
            elif filter_type == 'saturation':
                factor = param if param is not None else 1.0
                new_img = apply_saturation(img_copy, factor)
            elif filter_type == 'hue':
                shift = param if param is not None else 0.0
                new_img = apply_hue(img_copy, shift)
            else:
                logging.warning(f"Bilinmeyen filtre/ayarlama tipi: {filter_type}")
                return None # Return None for unknown types

            # Ensure RGBA output
            if new_img and (not hasattr(new_img, 'mode') or new_img.mode != 'RGBA'):
                new_img = new_img.convert('RGBA')

            return new_img
        except Exception as e:
            logging.error(f"Error applying filter {filter_type} in _get_filtered_image: {e}")
            return None # Return None on error


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


        # Apply the filter using the helper function
        try:
            new_img = self._get_filtered_image(start_img, filter_type, param)

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
            cmd = Command(do_action, undo_action, f'İşlem: {filter_type}')
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

        cmd = Command(do, undo, f'Dönüşüm: {ttype}')
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

        cmd = Command(do, undo, 'Yeniden Boyutlandır')
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
        # Add a new layer based on the size of the first layer, filled with transparency
        if not hasattr(self, 'layers') or not self.layers.layers:
             QMessageBox.warning(self, 'Uyarı', 'Yeni katman eklemek için önce bir resim açın veya mevcut bir katman olmalı!')
             return
        base_size = self.layers.layers[0].image.size
        img = Image.new('RGBA', base_size, (0,0,0,0)) # Create transparent layer
        self.layers.add_layer(img, f'Katman {len(self.layers.layers)+1}')
        self.refresh_layers()
        self.status_bar.showMessage('Yeni katman eklendi.')

    def delete_layer(self):
        idx = self.layers.active_index
        if idx == -1:
            QMessageBox.warning(self, 'Uyarı', 'Silinecek katman yok!')
            return
        self.layers.remove_layer(idx)
        self.refresh_layers()
        self.status_bar.showMessage('Katman silindi.')

    def merge_layers(self):
        # Merge visible layers into a single new layer
        if not hasattr(self, 'layers') or len(self.layers.layers) < 2:
            QMessageBox.warning(self, 'Uyarı', 'Birleştirmek için en az 2 katman olmalı.')
            return

        merged_img = self.layers.merge_visible()
        if merged_img:
            # Keep track of old layers and indices for undo
            old_layers_list = list(self.layers.layers) # Shallow copy is enough
            old_active_index = self.layers.active_index

            def do():
                # Remove all existing layers
                self.layers.layers.clear()
                # Add the merged layer
                self.layers.add_layer(merged_img.copy(), 'Birleştirilmiş Katman')
                self.refresh_layers()
                self.status_bar.showMessage('Görünür katmanlar birleştirildi.')

            def undo():
                # Restore old layers
                self.layers.layers = list(old_layers_list) # Restore from copy
                self.layers.active_index = old_active_index
                self.refresh_layers()
                self.status_bar.showMessage('Katman birleştirme geri alındı.')

            cmd = Command(do, undo, 'Katmanları Birleştir')
            cmd.do()
            self.history.push(cmd)
        else:
            QMessageBox.warning(self, 'Uyarı', 'Birleştirilecek görünür katman bulunamadı.')

    def toggle_layer_visibility(self):
        idx = self.layers.active_index
        if idx == -1:
            QMessageBox.warning(self, 'Uyarı', 'Görünürlüğü değiştirilecek katman yok!')
            return
        self.layers.toggle_visibility(idx)
        self.refresh_layers()
        self.status_bar.showMessage('Katman görünürlüğü değiştirildi.')

    def move_layer_up(self):
        idx = self.layers.active_index
        if idx > 0:
            self.layers.move_layer(idx, idx - 1)
            self.refresh_layers()
            self.status_bar.showMessage('Katman yukarı taşındı.')

    def move_layer_down(self):
        idx = self.layers.active_index
        if idx < len(self.layers.layers) - 1:
            self.layers.move_layer(idx, idx + 1)
            self.refresh_layers()
            self.status_bar.showMessage('Katman aşağı taşındı.')

    def refresh_layers(self):
        """Katmanları birleştirip görüntüyü günceller ve katman panelini yeniler."""
        try:
            # Katmanlar var mı kontrol et
            if not hasattr(self, 'layers') or not self.layers.layers:
                logging.warning("refresh_layers: Katman yok")
                return

            # Katmanları birleştirip pixmap oluştur (display için)
            pixmap = self._compose_layers_pixmap()
            if pixmap and not pixmap.isNull():
                self.image_view.set_image(pixmap)
            elif not self.layers.layers: # Handle case where all layers are deleted
                 self.image_view.scene.clear()
            # else: # Handle case where there are layers but none are visible or valid
            #     # Optionally display a blank canvas or message
            #     # For now, do nothing, leaving the view as is or empty
            #     pass

            # Katman panelini güncelle
            if hasattr(self, 'layer_panel'):
                self.layer_panel.refresh()
            # Efekt panelini güncelle (gerekirse)
            # if hasattr(self, 'effects_panel'):
            #     self.effects_panel.refresh() # Şimdilik efekt paneli statik, refresh gerekmeyebilir
        except Exception as e:
            logging.error(f"refresh_layers error: {e}")
            QMessageBox.critical(self, 'Hata', f'Katmanlar güncellenirken hata oluştu: {e}')

    def _compose_layers_pixmap(self):
        """Görünür katmanları birleştirerek bir QPixmap oluşturur."""
        try:
            from PyQt6.QtGui import QPainter, QPixmap
            from PyQt6.QtCore import Qt

            # Katmanları kontrol et
            if not hasattr(self, 'layers') or not self.layers.layers:
                return None

            # Görünür katmanları al
            visible_layers = [layer for layer in self.layers.layers if layer.visible]
            if not visible_layers:
                logging.warning("_compose_layers_pixmap: Görünür katman yok")
                return None

            # Katmanları pixmap'e dönüştür
            pixmaps = []
            for layer in visible_layers:
                try:
                    if not hasattr(layer, 'image') or layer.image is None:
                        continue

                    pm = image_to_qpixmap(layer.image)
                    if pm and not pm.isNull():
                        pixmaps.append(pm)
                except Exception as e:
                    logging.error(f"Katman pixmap'e dönüştürülürken hata: {e}")
                    continue

            if not pixmaps:
                return None

            # Boyutları al
            width = pixmaps[0].width()
            height = pixmaps[0].height()

            # Sonuç pixmap'i oluştur
            result = QPixmap(width, height)
            result.fill(Qt.GlobalColor.transparent)

            # Katmanları çiz
            painter = QPainter(result)
            for pm in pixmaps:
                if not pm.isNull():
                    painter.drawPixmap(0, 0, pm)
            painter.end()

            return result
        except Exception as e:
            logging.error(f"_compose_layers_pixmap error: {e}")
            return None

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
            pil_font = self._get_pil_font(font.family(), font_size, font.styleName()) # Helper to find font file

            new_img = self.draw_text_on_image(layer.image, text, (img_x, img_y), pil_font, text_color)
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

    def _get_pil_font(self, family, size, style="Regular"):
        """Attempts to load a PIL ImageFont based on QFont properties."""
        # This is a simplified and potentially fragile way to find fonts.
        # A more robust solution would involve fontconfig (Linux), CoreText (macOS),
        # or the Windows font directory, and better matching logic.
        font_file = None
        try:
            # Try common system font locations
            if platform.system() == "Windows":
                font_dir = "C:/Windows/Fonts"
                # Basic matching - improve this with style checks (Bold, Italic etc.)
                potential_files = [f for f in os.listdir(font_dir) if f.lower().endswith(('.ttf', '.otf')) and family.lower() in f.lower()]
                if potential_files:
                    # Prioritize files matching style if possible
                    style_matches = [f for f in potential_files if style.lower() in f.lower()]
                    if style_matches:
                        font_file = os.path.join(font_dir, style_matches[0])
                    else:
                        font_file = os.path.join(font_dir, potential_files[0]) # Fallback
                else: # Fallback to Arial if family not found
                     font_file = os.path.join(font_dir, "arial.ttf")
            elif platform.system() == "Darwin": # macOS
                font_dir = "/Library/Fonts" # System fonts
                user_font_dir = os.path.expanduser("~/Library/Fonts")
                # Simplified search - needs improvement
                found = False
                for d in [font_dir, user_font_dir]:
                     if os.path.exists(d):
                        potential_files = [f for f in os.listdir(d) if f.lower().endswith(('.ttf', '.otf', '.ttc')) and family.lower() in f.lower()]
                        if potential_files:
                            style_matches = [f for f in potential_files if style.lower() in f.lower()]
                            if style_matches:
                                font_file = os.path.join(d, style_matches[0])
                            else:
                                font_file = os.path.join(d, potential_files[0])
                            found = True
                            break
                if not found: # Fallback
                    font_file = "/System/Library/Fonts/Helvetica.ttc" # Common fallback
            else: # Linux (basic guess)
                font_dirs = ["/usr/share/fonts/truetype", "/usr/share/fonts/opentype", os.path.expanduser("~/.fonts")]
                found = False
                for d in font_dirs:
                    if os.path.exists(d):
                        for root, _, files in os.walk(d):
                            potential_files = [f for f in files if f.lower().endswith(('.ttf', '.otf')) and family.lower() in f.lower()]
                            if potential_files:
                                style_matches = [f for f in potential_files if style.lower() in f.lower()]
                                if style_matches:
                                    font_file = os.path.join(root, style_matches[0])
                                else:
                                    font_file = os.path.join(root, potential_files[0])
                                found = True
                                break
                    if found: break
                if not found: # Fallback
                    # Try finding DejaVu Sans, a common default
                    dejavu_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                    if os.path.exists(dejavu_path):
                        font_file = dejavu_path
                    else: # Absolute fallback
                        font_file = "arial.ttf" # Hope it's findable somehow

            if font_file and os.path.exists(font_file):
                 logging.info(f"Using font file: {font_file} for family {family}, size {size}")
                 return ImageFont.truetype(font_file, size)
            else:
                 logging.warning(f"Font file for '{family}' not found or path invalid: {font_file}. Falling back to default.")
                 # Load PIL default font if specific one not found
                 return ImageFont.load_default()

        except ImportError:
            logging.error("PIL/Pillow ImageFont not found. Please install Pillow.")
            return None
        except Exception as e:
            logging.error(f"Error loading font '{family}' size {size}: {e}. Falling back to default.")
            try:
                return ImageFont.load_default() # Fallback to PIL default
            except:
                 return None # Total failure

    def draw_text_on_image(self, img: Image.Image, text: str, position: tuple, font: ImageFont.FreeTypeFont, color: tuple):
        """Draws text onto a PIL image."""
        if img is None or font is None:
            logging.error("draw_text_on_image: Görüntü veya font geçersiz.")
            return None

        try:
            # Ensure image is RGBA for drawing with alpha
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Create a drawing context
            draw = ImageDraw.Draw(img)

            # Draw the text
            # position is the top-left corner of the text bounding box
            draw.text(position, text, fill=color, font=font)

            return img
        except Exception as e:
            logging.error(f"Metin çizilirken hata: {e}")
            return None


def main():
    try:
        # Hata ayıklama seviyesini ayarla
        logging.basicConfig(level=logging.INFO,
                           format='%(asctime)s [%(levelname)s] %(message)s',
                           handlers=[
                               logging.FileHandler("pyxeledit.log"),
                               logging.StreamHandler()
                           ])

        # Uygulama başlatma
        app = QApplication(sys.argv)

        # Ana pencereyi oluştur
        window = MainWindow()
        window.show()

        # Uygulama döngüsünü başlat
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Uygulama başlatılırken kritik hata: {e}")
        # Hata mesajını göster
        if 'app' in locals():
            QMessageBox.critical(None, 'Kritik Hata',
                               f'Uygulama başlatılırken beklenmeyen bir hata oluştu:\n{e}\n\n'
                               f'Lütfen pyxeledit.log dosyasını kontrol edin.')



if __name__ == '__main__':
    main()
