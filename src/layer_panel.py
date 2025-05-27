from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout,
                             QLabel, QMessageBox, QComboBox, QListWidgetItem, QSlider, QInputDialog, QCheckBox,
                             QDialog) 
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QDropEvent, QDragEnterEvent, QMouseEvent
import logging
from PIL import Image 
from .layers import BLEND_MODES, Layer 
from .resize_dialog import ResizeDialog  
class ClickableLabel(QLabel):
    clicked = pyqtSignal(int)  
    def __init__(self, text, layer_index, parent=None):
        super().__init__(text, parent)
        self.layer_index = layer_index
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, event):
        self.clicked.emit(self.layer_index)
        super().mousePressEvent(event)
class LayerPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel('Katmanlar')
        self.layout.addWidget(self.label)
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection) 
        self.list_widget.model().rowsMoved.connect(self.handle_rows_moved)
        btn_layout = QHBoxLayout()
        self.btn_up = QPushButton('↑')
        self.btn_down = QPushButton('↓')
        self.btn_copy = QPushButton('Kopyala')
        self.btn_paste = QPushButton('Yapıştır')
        self.btn_add_empty = QPushButton('Boş Katman')  
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_paste)
        btn_layout.addWidget(self.btn_add_empty)  
        self.layout.addLayout(btn_layout)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_copy.clicked.connect(self.copy_layer)
        self.btn_paste.clicked.connect(self.paste_layer)
        self.btn_add_empty.clicked.connect(self.add_empty_layer)  
        self.list_widget.currentRowChanged.connect(self.set_active_layer)
        self.trash_layout = QHBoxLayout()
        self.trash_layout.addStretch() 
        self.trash_label = QLabel('🗑️')
        self.trash_label.setToolTip("Katmanı silmek için buraya sürükleyin")
        self.trash_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.trash_layout.addWidget(self.trash_label)
        self.layout.addLayout(self.trash_layout)
        self.copied_layer = None
        self.setAcceptDrops(True) 
        self.refresh()
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.source() == self.list_widget:
            event.acceptProposedAction()
            logging.debug("Drag entered LayerPanel from list_widget")
        else:
            event.ignore()
            logging.debug("Drag entered LayerPanel from external source, ignored")
    def dropEvent(self, event: QDropEvent):
        if event.source() != self.list_widget:
            event.ignore()
            logging.debug("Drop ignored: Source is not list_widget")
            return
        trash_rect = self.trash_label.geometry()
        drop_pos_in_panel = event.position().toPoint()
        logging.debug(f"Drop position in panel: {drop_pos_in_panel}, Trash rect: {trash_rect}")
        if trash_rect.contains(drop_pos_in_panel):
            logging.debug("Drop detected over trash icon")
            item = self.list_widget.currentItem() 
            if not item:
                logging.warning("Drop on trash: No current item found.")
                event.ignore()
                return
            idx = self.list_widget.row(item)
            if idx < 0:
                logging.warning(f"Drop on trash: Invalid index {idx} for item.")
                event.ignore()
                return
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                 logging.warning("Drop on trash: No layers found.")
                 event.ignore()
                 return
            if idx >= len(self.main_window.layers.layers):
                logging.warning(f"Drop on trash: Index {idx} out of bounds.")
                event.ignore()
                return
            layer_to_delete = self.main_window.layers.layers[idx]
            reply = QMessageBox.question(self, 'Katmanı Sil',
                                         f"'{layer_to_delete.name}' katmanını silmek istediğinizden emin misiniz?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.main_window.layers.remove_layer(idx)
                    self.main_window.refresh_layers() 
                    self.refresh() 
                    logging.info(f"Katman silindi (sürükle-bırak): {layer_to_delete.name} (indeks {idx})")
                    event.acceptProposedAction() 
                except Exception as e:
                    logging.error(f"Katman silinirken hata (sürükle-bırak): {e}")
                    QMessageBox.critical(self, 'Hata', f'Katman silinirken bir hata oluştu: {e}')
                    event.ignore()
            else:
                logging.debug("Katman silme iptal edildi.")
                event.ignore() 
        else:
            logging.debug("Drop not on trash icon, ignoring (let list widget handle internal move)")
            event.ignore() 
    def refresh(self):
        try:
            self.list_widget.clear()
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                self.list_widget.addItem("Katman yok - Önce bir resim açın")
                return
            for idx, layer in enumerate(self.main_window.layers.layers):
                item = QListWidgetItem(self.list_widget) 
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 2, 5, 2) 
                visibility_label = ClickableLabel('☑' if layer.visible else '☐', idx)
                visibility_label.setToolTip("Görünürlüğü değiştirmek için tıklayın")
                visibility_label.clicked.connect(self.toggle_layer_visibility)
                name_label = QLabel(layer.name)
                name_label.setToolTip(layer.name) 
                opacity_text = QLabel(f"{layer.opacity}%")
                opacity_text.setFixedWidth(30)
                blend_combo = QComboBox()
                blend_combo.setProperty("layer_index", idx) 
                for mode_key, mode_name in BLEND_MODES.items():
                    blend_combo.addItem(mode_name, userData=mode_key) 
                current_blend_key = layer.blend_mode
                combo_index = blend_combo.findData(current_blend_key)
                if combo_index != -1:
                    blend_combo.setCurrentIndex(combo_index)
                blend_combo.currentTextChanged.connect(self._on_blend_mode_changed) 
                opacity_slider = QSlider(Qt.Orientation.Horizontal)
                opacity_slider.setMinimum(0)
                opacity_slider.setMaximum(100)
                opacity_slider.setValue(layer.opacity)
                opacity_slider.setFixedWidth(60)  
                opacity_slider.setProperty("layer_index", idx)
                opacity_slider.valueChanged.connect(self._on_opacity_changed)
                opacity_slider.setToolTip(f"Opaklık: {layer.opacity}%")
                resolution_btn = QPushButton("📐")  
                resolution_btn.setFixedWidth(25)
                resolution_btn.setToolTip("Katman çözünürlüğünü değiştir")
                resolution_btn.setProperty("layer_index", idx)
                resolution_btn.clicked.connect(self.change_layer_resolution)
                layout.addWidget(visibility_label)
                layout.addWidget(name_label, 1) 
                layout.addWidget(opacity_text)
                layout.addWidget(opacity_slider)
                layout.addWidget(blend_combo)
                layout.addWidget(resolution_btn)
                widget.setLayout(layout)
                item.setSizeHint(widget.sizeHint()) 
                self.list_widget.addItem(item) 
                self.list_widget.setItemWidget(item, widget) 
            active_idx = self.main_window.layers.active_index
            if 0 <= active_idx < len(self.main_window.layers.layers):
                self.list_widget.blockSignals(True)
                self.list_widget.setCurrentRow(active_idx)
                self.list_widget.blockSignals(False)
        except Exception as e:
            logging.error(f"Katman paneli güncellenirken hata: {e}")
    def set_active_layer(self, idx):
        try:
            if idx < 0:
                return
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                return
            if idx >= len(self.main_window.layers.layers):
                return
            self.main_window.set_active_layer(idx)
            logging.debug(f"Aktif katman değiştirme isteği gönderildi: {idx}")
        except Exception as e:
            logging.error(f"set_active_layer (LayerPanel) hatası: {e}")
    def move_up(self):
        try:
            idx = self.list_widget.currentRow()
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Taşınacak katman yok!')
                return
            if idx > 0:
                self.main_window.layers.move_layer(idx, idx-1)
                self.refresh()
                self.main_window.refresh_layers()
                logging.info(f"Katman yukarı taşındı: {idx} -> {idx-1}")
        except Exception as e:
            logging.error(f"move_up error: {e}")
            QMessageBox.warning(self, 'Uyarı', f'Katman taşınırken hata: {e}')
    def move_down(self):
        try:
            idx = self.list_widget.currentRow()
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Taşınacak katman yok!')
                return
            if idx < len(self.main_window.layers.layers)-1:
                self.main_window.layers.move_layer(idx, idx+1)
                self.refresh()
                self.main_window.refresh_layers()
                logging.info(f"Katman aşağı taşındı: {idx} -> {idx+1}")
        except Exception as e:
            logging.error(f"move_down error: {e}")
            QMessageBox.warning(self, 'Uyarı', f'Katman taşınırken hata: {e}')
    def copy_layer(self):
        try:
            idx = self.list_widget.currentRow()
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Kopyalanacak katman yok!')
                return
            if 0 <= idx < len(self.main_window.layers.layers):
                import copy
                try:
                    self.copied_layer = copy.deepcopy(self.main_window.layers.layers[idx])
                    logging.info(f"Katman kopyalandı: {self.copied_layer.name}")
                except Exception as e:
                    logging.error(f"Katman kopyalanırken hata: {e}")
                    QMessageBox.warning(self, 'Uyarı', f'Katman kopyalanırken hata: {e}')
        except Exception as e:
            logging.error(f"copy_layer error: {e}")
    def paste_layer(self):
        try:
            if not self.copied_layer:
                QMessageBox.warning(self, 'Uyarı', 'Yapıştırılacak katman yok! Önce bir katman kopyalayın.')
                return
            if not hasattr(self.main_window, 'layers'):
                QMessageBox.warning(self, 'Uyarı', 'Önce bir resim açmalısınız!')
                return
            import copy
            try:
                new_layer = copy.deepcopy(self.copied_layer)
                self.main_window.layers.add_layer(new_layer.image, new_layer.name + ' (Kopya)')
                self.refresh()
                self.main_window.refresh_layers()
                logging.info(f"Katman yapıştırıldı: {new_layer.name} (Kopya)")
            except Exception as e:
                logging.error(f"Katman yapıştırılırken hata: {e}")
                QMessageBox.warning(self, 'Uyarı', f'Katman yapıştırılırken hata: {e}')
        except Exception as e:
            logging.error(f"paste_layer error: {e}")
    def _on_visibility_clicked(self, event):
        sender_label = self.sender() 
        if not sender_label: return
        idx = sender_label.property("layer_index")
        if idx is None or not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
            return
        if 0 <= idx < len(self.main_window.layers.layers):
            try:
                layer = self.main_window.layers.layers[idx]
                layer.visible = not layer.visible
                logging.info(f"Katman görünürlüğü değiştirildi: {layer.name} -> {'Görünür' if layer.visible else 'Gizli'}")
                item = self.list_widget.item(idx)
                if item:
                    widget = self.list_widget.itemWidget(item)
                    if widget:
                        for child in widget.findChildren(QLabel):
                            if child.property("layer_index") == idx:
                                child.setText('☑' if layer.visible else '☐')
                                break
                self.main_window.refresh_layers()
            except Exception as e:
                 logging.error(f"_on_visibility_clicked hatası: {e}")
                 QMessageBox.warning(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')
        else:
            logging.warning(f"_on_visibility_clicked: Geçersiz indeks {idx}")
    def _on_blend_mode_changed(self, text):
        sender_combo = self.sender() 
        if not sender_combo: return
        idx = sender_combo.property("layer_index")
        if idx is None or not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
            return
        if 0 <= idx < len(self.main_window.layers.layers):
            try:
                layer = self.main_window.layers.layers[idx]
                selected_mode_key = sender_combo.currentData() 
                if layer.blend_mode != selected_mode_key:
                    layer.blend_mode = selected_mode_key
                    logging.info(f"Katman {idx} blend modu değiştirildi: {selected_mode_key}")
                    self.main_window.refresh_layers()
            except Exception as e:
                logging.error(f"_on_blend_mode_changed hatası: {e}")
                QMessageBox.warning(self, 'Hata', f'Blend modu değiştirilirken hata: {e}')
        else:
             logging.warning(f"_on_blend_mode_changed: Geçersiz indeks {idx}")
    def _on_opacity_changed(self, value):
        sender_slider = self.sender()  
        if not sender_slider: return
        idx = sender_slider.property("layer_index")
        if idx is None or not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
            return
        if 0 <= idx < len(self.main_window.layers.layers):
            try:
                layer = self.main_window.layers.layers[idx]
                if layer.opacity != value:
                    layer.opacity = value
                    sender_slider.setToolTip(f"Opaklık: {value}%")
                    item = self.list_widget.item(idx)
                    if item:
                        widget = self.list_widget.itemWidget(item)
                        if widget:
                            labels = widget.findChildren(QLabel)
                            if len(labels) >= 3:
                                opacity_label = labels[2]  
                                opacity_label.setText(f"{value}%")
                    logging.info(f"Katman {idx} opaklığı değiştirildi: {value}%")
                    self.main_window.refresh_layers()
            except Exception as e:
                logging.error(f"_on_opacity_changed hatası: {e}")
                QMessageBox.warning(self, 'Hata', f'Opaklık değiştirilirken hata: {e}')
        else:
            logging.warning(f"_on_opacity_changed: Geçersiz indeks {idx}")
    def handle_rows_moved(self, parent: QModelIndex, start: int, end: int, destination: QModelIndex, row: int):
        try:
            if start == end:
                source_index = start
                dest_index = row
                if dest_index > source_index:
                    final_dest_index = dest_index - 1
                else:
                    if dest_index == source_index:
                        return
                    final_dest_index = dest_index
                logging.debug(f"Katman sürükle-bırak: Kaynak={source_index}, Hedef Sıra={row}, Son Hedef İndeks={final_dest_index}")
                if hasattr(self.main_window, 'layers') and self.main_window.layers:
                    self.main_window.layers.move_layer(source_index, final_dest_index)
                    self.main_window.refresh_layers()
                    logging.info(f"Katman sürükle-bırak ile taşındı: {source_index} -> {final_dest_index}")
                else:
                     logging.warning("handle_rows_moved: Katman yöneticisi bulunamadı.")
            else:
                logging.warning(f"Beklenmeyen çoklu satır taşıma: start={start}, end={end}")
        except Exception as e:
            logging.error(f"handle_rows_moved hatası: {e}")
            QMessageBox.warning(self, 'Hata', f'Katman taşınırken bir hata oluştu: {e}')
    def toggle_layer_visibility(self, idx):
        try:
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                return
            if 0 <= idx < len(self.main_window.layers.layers):
                layer = self.main_window.layers.layers[idx]
                layer.visible = not layer.visible
                logging.info(f"Katman görünürlüğü değiştirildi: {layer.name} -> {'Görünür' if layer.visible else 'Gizli'}")
                self.refresh()
                self.main_window.refresh_layers()
            else:
                logging.warning(f"toggle_layer_visibility: Geçersiz indeks {idx}")
        except Exception as e:
            logging.error(f"toggle_layer_visibility hatası: {e}")
            QMessageBox.warning(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')
    def change_layer_resolution(self):
        try:
            sender_btn = self.sender()
            if not sender_btn:
                return
            idx = sender_btn.property("layer_index")
            if idx is None or not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                return
            if 0 <= idx < len(self.main_window.layers.layers):
                layer = self.main_window.layers.layers[idx]
                resize_dialog = ResizeDialog(layer, self)
                result = resize_dialog.exec()
                if result == QDialog.DialogCode.Accepted:
                    new_width, new_height, keep_aspect, resample_method = resize_dialog.get_resize_parameters()
                    current_width, current_height = layer.image.size
                    if new_width != current_width or new_height != current_height:
                        if layer.resize(new_width, new_height, resample=resample_method, keep_aspect_ratio=keep_aspect):
                            logging.info(f"Katman {idx} ({layer.name}) çözünürlüğü değiştirildi: {current_width}x{current_height} -> {new_width}x{new_height}, Oran Koru: {keep_aspect}, Metod: {resample_method}")
                            self.main_window.refresh_layers()
                        else:
                            QMessageBox.warning(self, 'Hata', 'Katman çözünürlüğü değiştirilirken bir hata oluştu!')
                else:
                    logging.debug(f"Katman {idx} çözünürlük değiştirme iptal edildi.")
            else:
                logging.warning(f"change_layer_resolution: Geçersiz indeks {idx}")
        except Exception as e:
            logging.error(f"change_layer_resolution hatası: {e}")
            QMessageBox.warning(self, 'Hata', f'Katman çözünürlüğü değiştirilirken hata: {e}')
    def add_empty_layer(self):
        try:
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                QMessageBox.warning(self, 'Uyarı', 'Boş katman eklemek için önce bir proje açmalısınız.')
                return
            base_size = self.main_window.layers.layers[0].image.size
            empty_image = Image.new('RGBA', base_size, (0, 0, 0, 0))
            default_name = f"Boş Katman {len(self.main_window.layers.layers) + 1}"
            name, ok = QInputDialog.getText(self, 'Katman Adı', 
                                           'Yeni katman adını girin:', 
                                           text=default_name)
            if not ok:  
                return
            layer_name = name if name.strip() else default_name
            new_layer = Layer(empty_image, name=layer_name)
            self.main_window.layers.layers.append(new_layer)
            self.main_window.layers.active_index = len(self.main_window.layers.layers) - 1
            self.main_window.refresh_layers()
            self.refresh()
            logging.info(f"Boş katman eklendi: {layer_name}")
        except Exception as e:
            logging.error(f"Boş katman eklenirken hata: {e}")
            QMessageBox.critical(self, 'Hata', f'Boş katman eklenirken bir hata oluştu: {e}')