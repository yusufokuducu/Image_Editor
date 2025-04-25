import sys
import os
import traceback
import gc
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QMenuBar, QFileDialog, QMessageBox, QInputDialog, QDockWidget
from PyQt6.QtGui import QAction, QPainter, QPixmap
from PyQt6.QtCore import Qt, QTimer
import logging
from image_io import load_image, image_to_qpixmap
from image_view import ImageView
from filters import apply_blur, apply_sharpen, apply_edge_enhance, apply_grayscale, apply_noise
from transform import rotate_image, flip_image, resize_image, crop_image
from history import History, Command
from layers import LayerManager
import numpy as np
from PIL import Image
from layer_panel import LayerPanel

# Ana logging yapılandırması main() fonksiyonuna taşındı

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
        self.image_view = ImageView()
        self.setCentralWidget(self.image_view)

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
        val, ok = QInputDialog.getInt(self, 'Bulanıklık Yarıçapı', 'Yarıçap (1-20):', value=2, min=1, max=20)
        if ok:
            self.apply_filter('blur', val)

    def noise_dialog(self):
        val, ok = QInputDialog.getDouble(self, 'Noise Seviyesi', 'Noise (0.0-1.0):', value=0.1, min=0.01, max=1.0, decimals=2)
        if ok:
            self.apply_filter('noise', val)

    def apply_filter(self, filter_type, param=None):
        """
        Seçili katmana filtre uygular.

        Args:
            filter_type (str): Uygulanacak filtre tipi ('blur', 'sharpen', 'edge', 'grayscale', 'noise')
            param: Filtre parametresi (blur için radius, noise için amount)
        """
        logging.info(f"Filtre uygulanıyor: {filter_type}, param: {param}")

        # Aktif katmanı kontrol et
        if not hasattr(self, 'layers'):
            QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
            return

        layer = self.layers.get_active_layer()
        if layer is None:
            QMessageBox.warning(self, 'Uyarı', 'Uygulanacak katman yok!')
            return

        # Orijinal görüntüyü sakla (geri alma için)
        old_img = None
        try:
            old_img = layer.image.copy()  # Orijinal görüntünün kopyasını al
        except Exception as e:
            logging.error(f"Orijinal görüntü kopyalanamadı: {e}")
            QMessageBox.critical(self, 'Hata', f'Görüntü kopyalanamadı: {e}')
            return

        # Filtre uygulama işlemi
        try:
            # Görüntüyü kontrol et
            if not hasattr(layer, 'image') or layer.image is None:
                raise ValueError("Geçerli bir görüntü yok")

            # Görüntünün kopyasını al
            img = layer.image.copy()

            # Filtre tipine göre işlem yap
            if filter_type == 'blur':
                radius = param if param is not None else 2
                new_img = apply_blur(img, radius)
            elif filter_type == 'sharpen':
                new_img = apply_sharpen(img)
            elif filter_type == 'edge':
                new_img = apply_edge_enhance(img)
            elif filter_type == 'grayscale':
                new_img = apply_grayscale(img)
            elif filter_type == 'noise':
                amount = param if param is not None else 0.1
                new_img = apply_noise(img, amount)
            else:
                logging.warning(f"Bilinmeyen filtre tipi: {filter_type}")
                return

            # Sonuç görüntüsünü kontrol et
            if new_img is None:
                raise ValueError(f"Filtre sonucu geçersiz: {filter_type}")

            # RGBA moduna dönüştür
            if not hasattr(new_img, 'mode') or new_img.mode != 'RGBA':
                new_img = new_img.convert('RGBA')

            # Geri alma/yineleme için komut oluştur (Lambda ile yakalama)
            current_layer_ref = layer # Avoid closure issues
            new_img_copy = new_img.copy()
            old_img_copy = old_img.copy()

            def do():
                try:
                    current_layer_ref.image = new_img_copy.copy()
                    self.refresh_layers()
                except Exception as e:
                    logging.error(f"Filtre uygulama (do) hatası: {e}")

            def undo():
                try:
                    current_layer_ref.image = old_img_copy.copy()
                    self.refresh_layers()
                except Exception as e:
                    logging.error(f"Filtre geri alma (undo) hatası: {e}")

            # Komutu oluştur ve uygula
            cmd = Command(do, undo, f'Filtre: {filter_type}')
            cmd.do()
            self.history.push(cmd)

            # Durum çubuğunu güncelle
            self.status_bar.showMessage(f'{filter_type} filtresi uygulandı.')

        except Exception as e:
            logging.error(f'apply_filter error: {e}')
            QMessageBox.critical(self, 'Hata', f'Filtre uygulanırken hata oluştu: {e}')
            # Hata durumunda orijinal görüntüyü geri yükle
            if old_img is not None:
                try:
                    layer.image = old_img.copy()
                    self.refresh_layers()
                except Exception as restore_error:
                    logging.error(f"Orijinal görüntü geri yüklenirken hata: {restore_error}")

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
            self.layer_panel.refresh()
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
