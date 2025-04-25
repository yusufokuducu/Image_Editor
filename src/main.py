import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStatusBar, QMenuBar, QFileDialog, QMessageBox, QInputDialog, QDockWidget
from PyQt6.QtGui import QAction, QPainter, QPixmap
from PyQt6.QtCore import Qt
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyxelEdit')
        self.setGeometry(100, 100, 1024, 768)
        self.history = History()
        self.layers = LayerManager()
        self._init_ui()

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
                self.current_image = merged
                self.current_image_path = file_path
            else:
                QMessageBox.critical(self, 'Hata', 'Resim yüklenemedi!')

    def save_image(self):
        if not hasattr(self, 'current_image') or self.current_image is None or not hasattr(self, 'current_image_path'):
            QMessageBox.warning(self, 'Uyarı', 'Kaydedilecek bir resim yok!')
            return
        try:
            self.current_image.save(self.current_image_path)
            self.status_bar.showMessage(f'Resim kaydedildi: {self.current_image_path}')
        except Exception as e:
            QMessageBox.critical(self, 'Hata', f'Resim kaydedilemedi!\n{e}')

    def save_image_as(self):
        if not hasattr(self, 'current_image') or self.current_image is None:
            QMessageBox.warning(self, 'Uyarı', 'Kaydedilecek bir resim yok!')
            return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Farklı Kaydet', '', 'Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif)')
        if file_path:
            try:
                self.current_image.save(file_path)
                self.current_image_path = file_path
                self.status_bar.showMessage(f'Resim farklı kaydedildi: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Hata', f'Resim kaydedilemedi!\n{e}')

    def close_image(self):
        self.image_view.scene.clear()
        self.current_image = None
        self.current_image_path = None
        self.status_bar.clearMessage()

    def blur_dialog(self):
        val, ok = QInputDialog.getInt(self, 'Bulanıklık Yarıçapı', 'Yarıçap (1-20):', value=2, min=1, max=20)
        if ok:
            self.apply_filter('blur', val)

    def noise_dialog(self):
        val, ok = QInputDialog.getDouble(self, 'Noise Seviyesi', 'Noise (0.0-1.0):', value=0.1, min=0.01, max=1.0, decimals=2)
        if ok:
            self.apply_filter('noise', val)

    def apply_filter(self, filter_type, param=None):
        # Aktif katmana uygula
        layer = self.layers.get_active_layer()
        if layer is None:
            QMessageBox.warning(self, 'Uyarı', 'Uygulanacak katman yok!')
            return
        img = layer.image.copy()  # DAİMA kopya ile çalış
        try:
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
                return
            if not hasattr(new_img, 'mode') or new_img.mode != 'RGBA':
                new_img = new_img.convert('RGBA')
            # Kendi kendini referans eden bir yapı olup olmadığını kontrol et
            if hasattr(new_img, '__dict__') and any(id(new_img) == id(v) for v in new_img.__dict__.values()):
                raise ValueError('Efekt sonrası oluşan görselde recursive referans tespit edildi!')
            layer.image = new_img.copy()  # Katmana daima kopya ata
            self.refresh_layers()
            self.status_bar.showMessage(f'{filter_type} filtresi uygulandı.')
        except Exception as e:
            import logging
            logging.error(f'apply_filter error: {e}')
            QMessageBox.critical(self, 'Hata', f'Filtre uygulanırken hata oluştu: {e}')

    def apply_transform(self, ttype):
        if not hasattr(self, 'current_image') or self.current_image is None:
            QMessageBox.warning(self, 'Uyarı', 'Dönüştürülecek bir resim yok!')
            return
        old_img = self.current_image.copy()
        img = self.current_image
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
        else:
            return
        def do():
            self.current_image = img
            pixmap = image_to_qpixmap(img)
            self.image_view.set_image(pixmap)
        def undo():
            self.current_image = old_img
            pixmap = image_to_qpixmap(old_img)
            self.image_view.set_image(pixmap)
        cmd = Command(do, undo, f'Dönüşüm: {ttype}')
        cmd.do()
        self.history.push(cmd)
        self.status_bar.showMessage('Dönüşüm uygulandı: ' + ttype)

    def resize_dialog(self):
        if not hasattr(self, 'current_image') or self.current_image is None:
            QMessageBox.warning(self, 'Uyarı', 'Boyutlandırılacak bir resim yok!')
            return
        w, h = self.current_image.width, self.current_image.height
        width, ok1 = QInputDialog.getInt(self, 'Yeniden Boyutlandır', 'Yeni genişlik:', w, 1, 10000)
        if not ok1:
            return
        height, ok2 = QInputDialog.getInt(self, 'Yeniden Boyutlandır', 'Yeni yükseklik:', h, 1, 10000)
        if not ok2:
            return
        keep_aspect, _ = QInputDialog.getItem(self, 'Oran Koru', 'Oran korunsun mu?', ['Evet', 'Hayır'], 0, False)
        old_img = self.current_image.copy()
        img = resize_image(self.current_image, width, height, keep_aspect == 'Evet')
        def do():
            self.current_image = img
            pixmap = image_to_qpixmap(img)
            self.image_view.set_image(pixmap)
        def undo():
            self.current_image = old_img
            pixmap = image_to_qpixmap(old_img)
            self.image_view.set_image(pixmap)
        cmd = Command(do, undo, 'Yeniden Boyutlandır')
        cmd.do()
        self.history.push(cmd)
        self.status_bar.showMessage(f'Yeniden boyutlandırıldı: {width}x{height} (Oran Koru: {keep_aspect})')

    def crop_selected(self):
        if not hasattr(self, 'current_image') or self.current_image is None:
            QMessageBox.warning(self, 'Uyarı', 'Kırpılacak bir resim yok!')
            return
        box = self.image_view.get_selected_box()
        if not box:
            QMessageBox.warning(self, 'Uyarı', 'Kırpma için bir alan seçmelisiniz!')
            return
        old_img = self.current_image.copy()
        img = crop_image(self.current_image, box)
        def do():
            self.current_image = img
            pixmap = image_to_qpixmap(img)
            self.image_view.set_image(pixmap)
        def undo():
            self.current_image = old_img
            pixmap = image_to_qpixmap(old_img)
            self.image_view.set_image(pixmap)
        cmd = Command(do, undo, 'Kırp')
        cmd.do()
        self.history.push(cmd)
        self.status_bar.showMessage('Seçili alan kırpıldı.')
        self.image_view.clear_selection()

    def undo(self):
        self.history.undo()
        self.status_bar.showMessage('Geri alındı.')

    def redo(self):
        self.history.redo()
        self.status_bar.showMessage('Yinele uygulandı.')

    def add_layer(self):
        if not hasattr(self, 'current_image') or self.current_image is None:
            QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
            return
        img = self.current_image.copy()
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
        merged = self.layers.merge_visible()
        if merged:
            self.current_image = merged
            pixmap = image_to_qpixmap(merged)
            self.image_view.set_image(pixmap)
            self.status_bar.showMessage('Katmanlar birleştirildi.')

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
        # Preview için Qt üzerinden katmanları birleştir
        pixmap = self._compose_layers_pixmap()
        if pixmap:
            self.image_view.set_image(pixmap)
        # Katman panelini de güncelle
        self.layer_panel.refresh()

    def _compose_layers_pixmap(self):
        from PyQt6.QtGui import QPainter, QPixmap
        from PyQt6.QtCore import Qt
        # Katmanları al
        layers = self.layers.layers
        if not layers:
            return None
        pixmaps = []
        for layer in layers:
            if not layer.visible:
                continue
            pm = image_to_qpixmap(layer.image)
            if pm:
                pixmaps.append(pm)
        if not pixmaps:
            return None
        # Boyutları sabit kabul et
        width = pixmaps[0].width()
        height = pixmaps[0].height()
        result = QPixmap(width, height)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        for pm in pixmaps:
            painter.drawPixmap(0, 0, pm)
        painter.end()
        return result

    # Katman değiştirme fonksiyonu (örnek, daha gelişmiş UI için geliştirilebilir)
    def set_active_layer(self, idx):
        self.layers.set_active_layer(idx)
        self.refresh_layers()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
