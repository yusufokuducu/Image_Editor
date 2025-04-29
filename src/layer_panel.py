from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout,
                             QLabel, QMessageBox, QComboBox, QListWidgetItem, QSlider) # Added QSlider
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QDropEvent, QDragEnterEvent, QMouseEvent
import logging
from .layers import BLEND_MODES # Import blend modes

# Tıklanabilir etiket sınıfı
class ClickableLabel(QLabel):
    clicked = pyqtSignal(int)  # Tıklama sinyali

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

        # Sürükle-bırak ayarları
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection) # Zaten varsayılan ama açıkça belirtmek iyi olabilir
        self.list_widget.model().rowsMoved.connect(self.handle_rows_moved)


        btn_layout = QHBoxLayout()
        self.btn_up = QPushButton('↑')
        self.btn_down = QPushButton('↓')
        self.btn_copy = QPushButton('Kopyala')
        self.btn_paste = QPushButton('Yapıştır')
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_paste)
        self.layout.addLayout(btn_layout)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_copy.clicked.connect(self.copy_layer)
        self.btn_paste.clicked.connect(self.paste_layer)
        self.list_widget.currentRowChanged.connect(self.set_active_layer)
        # self.list_widget.itemClicked.connect(self.toggle_layer_visibility) # Removed: Handled by label click now

        # Trash Can Area
        self.trash_layout = QHBoxLayout()
        self.trash_layout.addStretch() # Push trash can to the right
        self.trash_label = QLabel('🗑️')
        self.trash_label.setToolTip("Katmanı silmek için buraya sürükleyin")
        self.trash_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.trash_layout.addWidget(self.trash_label)
        self.layout.addLayout(self.trash_layout)

        self.copied_layer = None
        self.setAcceptDrops(True) # Enable drops on the panel itself for the trash can
        self.refresh()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """ Accept drags only if they come from the internal list widget. """
        if event.source() == self.list_widget:
            event.acceptProposedAction()
            logging.debug("Drag entered LayerPanel from list_widget")
        else:
            event.ignore()
            logging.debug("Drag entered LayerPanel from external source, ignored")

    def dropEvent(self, event: QDropEvent):
        """ Handle drops onto the trash can icon. """
        if event.source() != self.list_widget:
            event.ignore()
            logging.debug("Drop ignored: Source is not list_widget")
            return

        # Check if the drop occurred over the trash label
        trash_rect = self.trash_label.geometry()
        # Map the drop position relative to the LayerPanel widget
        drop_pos_in_panel = event.position().toPoint()

        logging.debug(f"Drop position in panel: {drop_pos_in_panel}, Trash rect: {trash_rect}")

        if trash_rect.contains(drop_pos_in_panel):
            logging.debug("Drop detected over trash icon")
            item = self.list_widget.currentItem() # Get the item being dragged
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
                    self.main_window.layers.delete_layer(idx)
                    self.main_window.refresh_layers() # Refresh main view first
                    self.refresh() # Then refresh the panel
                    logging.info(f"Katman silindi (sürükle-bırak): {layer_to_delete.name} (indeks {idx})")
                    event.acceptProposedAction() # Consume the event
                except Exception as e:
                    logging.error(f"Katman silinirken hata (sürükle-bırak): {e}")
                    QMessageBox.critical(self, 'Hata', f'Katman silinirken bir hata oluştu: {e}')
                    event.ignore()
            else:
                logging.debug("Katman silme iptal edildi.")
                event.ignore() # Drop was cancelled
        else:
            logging.debug("Drop not on trash icon, ignoring (let list widget handle internal move)")
            event.ignore() # Let the list widget handle the internal move if applicable

    def refresh(self):
        try:
            self.list_widget.clear()

            # Katman listesi boşsa uyarı göster
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                self.list_widget.addItem("Katman yok - Önce bir resim açın")
                return

            # Katmanları listele (özel widget'lar kullanarak)
            for idx, layer in enumerate(self.main_window.layers.layers):
                item = QListWidgetItem(self.list_widget) # Create item but don't set text
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 2, 5, 2) # Adjust margins

                # Visibility Label (clickable) - Özel tıklanabilir etiket kullan
                visibility_label = ClickableLabel('☑' if layer.visible else '☐', idx)
                visibility_label.setToolTip("Görünürlüğü değiştirmek için tıklayın")
                visibility_label.clicked.connect(self.toggle_layer_visibility)

                # Layer Name Label
                name_label = QLabel(layer.name)
                name_label.setToolTip(layer.name) # Show full name on hover

                # Opacity indicator text
                opacity_text = QLabel(f"{layer.opacity}%")
                opacity_text.setFixedWidth(30)

                # Blend Mode ComboBox
                blend_combo = QComboBox()
                blend_combo.setProperty("layer_index", idx) # Store index
                for mode_key, mode_name in BLEND_MODES.items():
                    blend_combo.addItem(mode_name, userData=mode_key) # Store key in userData
                current_blend_key = layer.blend_mode
                # Find the index corresponding to the layer's current blend mode key
                combo_index = blend_combo.findData(current_blend_key)
                if combo_index != -1:
                    blend_combo.setCurrentIndex(combo_index)
                blend_combo.currentTextChanged.connect(self._on_blend_mode_changed) # Connect signal

                # Opacity Slider
                opacity_slider = QSlider(Qt.Orientation.Horizontal)
                opacity_slider.setMinimum(0)
                opacity_slider.setMaximum(100)
                opacity_slider.setValue(layer.opacity)
                opacity_slider.setFixedWidth(60)  # Make it compact
                opacity_slider.setProperty("layer_index", idx)
                opacity_slider.valueChanged.connect(self._on_opacity_changed)
                opacity_slider.setToolTip(f"Opaklık: {layer.opacity}%")

                layout.addWidget(visibility_label)
                layout.addWidget(name_label, 1) # Give name label stretch factor
                layout.addWidget(opacity_text)
                layout.addWidget(opacity_slider)
                layout.addWidget(blend_combo)
                widget.setLayout(layout)

                # Set the custom widget for the list item
                item.setSizeHint(widget.sizeHint()) # Important for proper sizing
                self.list_widget.addItem(item) # Add the item itself
                self.list_widget.setItemWidget(item, widget) # Set the widget for the item

            # Aktif katmanı seç
            active_idx = self.main_window.layers.active_index
            if 0 <= active_idx < len(self.main_window.layers.layers):
                # Programatik olarak satır değiştirirken sinyalleri engelle
                self.list_widget.blockSignals(True)
                self.list_widget.setCurrentRow(active_idx)
                self.list_widget.blockSignals(False)
        except Exception as e:
            logging.error(f"Katman paneli güncellenirken hata: {e}")

    def set_active_layer(self, idx):
        """Aktif katmanı değiştirir. Özyinelemeli referans sorunlarını önlemek için optimize edilmiştir."""
        try:
            # Geçersiz indeks kontrolü
            if idx < 0:
                return

            # Katman listesi kontrolü
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                return

            # İndeks sınırları kontrolü
            if idx >= len(self.main_window.layers.layers):
                return

            # Aktif katmanı MainWindow üzerinden değiştir
            # Bu, hem LayerManager'daki indeksi günceller hem de
            # MainWindow.refresh_layers() çağrısını tetikler (gerekirse).
            self.main_window.set_active_layer(idx)
            # Panel refresh'i MainWindow.set_active_layer tarafından tetiklenmeli
            # (çünkü o da LayerPanel.refresh çağırıyor).
            # Bu yüzden buradaki self.refresh() çağrısı kaldırılabilir veya
            # MainWindow.set_active_layer'ın bunu yapması sağlanabilir.
            # Şimdilik bırakalım, en kötü ihtimalle çift refresh olur.
            # self.refresh() # Bu satır gereksiz, MainWindow.set_active_layer zaten refresh tetikliyor.
            logging.debug(f"Aktif katman değiştirme isteği gönderildi: {idx}")

        except Exception as e:
            logging.error(f"set_active_layer (LayerPanel) hatası: {e}")
            # Hata durumunda logla

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

    # Removed toggle_layer_visibility(self, item) as it's handled by _on_visibility_clicked

    def _on_visibility_clicked(self, event):
        """ Handles clicks on the visibility label. """
        sender_label = self.sender() # Get the label that was clicked
        if not sender_label: return

        idx = sender_label.property("layer_index")
        if idx is None or not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
            return

        if 0 <= idx < len(self.main_window.layers.layers):
            try:
                layer = self.main_window.layers.layers[idx]
                # Toggle visibility
                layer.visible = not layer.visible
                logging.info(f"Katman görünürlüğü değiştirildi: {layer.name} -> {'Görünür' if layer.visible else 'Gizli'}")
                
                # Update the specific item's widget appearance
                item = self.list_widget.item(idx)
                if item:
                    widget = self.list_widget.itemWidget(item)
                    if widget:
                        # Find the visibility label within the widget
                        for child in widget.findChildren(QLabel):
                            # Check if this label has our layer_index property
                            if child.property("layer_index") == idx:
                                child.setText('☑' if layer.visible else '☐')
                                break
                
                # Refresh the main canvas
                self.main_window.refresh_layers()
            except Exception as e:
                 logging.error(f"_on_visibility_clicked hatası: {e}")
                 QMessageBox.warning(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')
        else:
            logging.warning(f"_on_visibility_clicked: Geçersiz indeks {idx}")


    def _on_blend_mode_changed(self, text):
        """ Handles changes in the blend mode combo box. """
        sender_combo = self.sender() # Get the combo box that emitted the signal
        if not sender_combo: return

        idx = sender_combo.property("layer_index")
        if idx is None or not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
            return

        if 0 <= idx < len(self.main_window.layers.layers):
            try:
                layer = self.main_window.layers.layers[idx]
                selected_mode_key = sender_combo.currentData() # Get the key stored in userData

                if layer.blend_mode != selected_mode_key:
                    layer.blend_mode = selected_mode_key
                    logging.info(f"Katman {idx} blend modu değiştirildi: {selected_mode_key}")
                    # Refresh the main canvas to show the blend mode change
                    self.main_window.refresh_layers()
            except Exception as e:
                logging.error(f"_on_blend_mode_changed hatası: {e}")
                QMessageBox.warning(self, 'Hata', f'Blend modu değiştirilirken hata: {e}')
        else:
             logging.warning(f"_on_blend_mode_changed: Geçersiz indeks {idx}")


    def _on_opacity_changed(self, value):
        """ Handles changes in the opacity slider. """
        sender_slider = self.sender()  # Get the slider that emitted the signal
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
                    
                    # Update the opacity text label 
                    item = self.list_widget.item(idx)
                    if item:
                        widget = self.list_widget.itemWidget(item)
                        if widget:
                            # Find the opacity text label (should be the third QLabel)
                            labels = widget.findChildren(QLabel)
                            if len(labels) >= 3:
                                opacity_label = labels[2]  # Third label should be the opacity text
                                opacity_label.setText(f"{value}%")

                    logging.info(f"Katman {idx} opaklığı değiştirildi: {value}%")
                    # Refresh the main canvas to show the opacity change
                    self.main_window.refresh_layers()
            except Exception as e:
                logging.error(f"_on_opacity_changed hatası: {e}")
                QMessageBox.warning(self, 'Hata', f'Opaklık değiştirilirken hata: {e}')
        else:
            logging.warning(f"_on_opacity_changed: Geçersiz indeks {idx}")

    def handle_rows_moved(self, parent: QModelIndex, start: int, end: int, destination: QModelIndex, row: int):
        """ QListWidget içinde bir öğe taşındığında çağrılır. """
        try:
            # Sadece tek bir öğe taşındığını varsayıyoruz (end == start)
            if start == end:
                source_index = start
                # `row` hedef indeksi belirtir (taşınan öğenin önüne ekleneceği sıra)
                # Eğer öğe aşağı taşınıyorsa, efektif hedef indeks `row - 1` olur.
                # Eğer öğe yukarı taşınıyorsa, efektif hedef indeks `row` olur.
                dest_index = row
                if dest_index > source_index:
                    final_dest_index = dest_index - 1
                else:
                    # Eğer aynı yere bırakılırsa (dest_index == source_index), işlem yapma
                    if dest_index == source_index:
                        return
                    final_dest_index = dest_index

                logging.debug(f"Katman sürükle-bırak: Kaynak={source_index}, Hedef Sıra={row}, Son Hedef İndeks={final_dest_index}")

                # Ana penceredeki katman yöneticisini güncelle
                if hasattr(self.main_window, 'layers') and self.main_window.layers:
                    self.main_window.layers.move_layer(source_index, final_dest_index)
                    # Ana pencereyi yenile (bu LayerPanel'i de yenilemeli)
                    self.main_window.refresh_layers()
                    logging.info(f"Katman sürükle-bırak ile taşındı: {source_index} -> {final_dest_index}")
                else:
                     logging.warning("handle_rows_moved: Katman yöneticisi bulunamadı.")

            else:
                logging.warning(f"Beklenmeyen çoklu satır taşıma: start={start}, end={end}")

        except Exception as e:
            logging.error(f"handle_rows_moved hatası: {e}")
            QMessageBox.warning(self, 'Hata', f'Katman taşınırken bir hata oluştu: {e}')

    # Yeni metod: Katman görünürlüğünü değiştir
    def toggle_layer_visibility(self, idx):
        """Katman görünürlüğünü değiştirir."""
        try:
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                return

            if 0 <= idx < len(self.main_window.layers.layers):
                layer = self.main_window.layers.layers[idx]
                # Görünürlüğü değiştir
                layer.visible = not layer.visible
                logging.info(f"Katman görünürlüğü değiştirildi: {layer.name} -> {'Görünür' if layer.visible else 'Gizli'}")
                
                # GUI'yi güncelle
                self.refresh()
                
                # Ana kanvası yenile
                self.main_window.refresh_layers()
            else:
                logging.warning(f"toggle_layer_visibility: Geçersiz indeks {idx}")
        except Exception as e:
            logging.error(f"toggle_layer_visibility hatası: {e}")
            QMessageBox.warning(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')
