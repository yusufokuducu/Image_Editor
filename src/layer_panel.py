from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import QDropEvent
import logging

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
        self.list_widget.itemClicked.connect(self.toggle_layer_visibility) # Katman görünürlüğünü değiştirmek için eklendi
        self.copied_layer = None
        self.refresh()

    def refresh(self):
        try:
            self.list_widget.clear()

            # Katman listesi boşsa uyarı göster
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                self.list_widget.addItem("Katman yok - Önce bir resim açın")
                return

            # Katmanları listele
            for idx, layer in enumerate(self.main_window.layers.layers):
                text = f"{'👁️' if layer.visible else '❌'} {layer.name}"
                self.list_widget.addItem(text)

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

    def toggle_layer_visibility(self, item):
        """ Katmanın görünürlüğünü değiştirir. """
        try:
            idx = self.list_widget.row(item)
            if not hasattr(self.main_window, 'layers') or not self.main_window.layers.layers:
                return # Katman yoksa işlem yapma

            if 0 <= idx < len(self.main_window.layers.layers):
                layer = self.main_window.layers.layers[idx]
                layer.visible = not layer.visible
                logging.info(f"Katman görünürlüğü değiştirildi: {layer.name} -> {'Görünür' if layer.visible else 'Gizli'}")
                self.refresh() # Paneldeki ikonu güncelle
                self.main_window.refresh_layers() # Ana görünümü güncelle
            else:
                logging.warning(f"toggle_layer_visibility: Geçersiz indeks {idx}")
        except Exception as e:
            logging.error(f"toggle_layer_visibility hatası: {e}")
            QMessageBox.warning(self, 'Hata', f'Katman görünürlüğü değiştirilirken hata: {e}')

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
