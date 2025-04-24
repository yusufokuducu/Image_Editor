from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

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
        self.copied_layer = None
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        for idx, layer in enumerate(self.main_window.layers.layers):
            text = f"{'👁️' if layer.visible else '❌'} {layer.name}"
            self.list_widget.addItem(text)
        self.list_widget.setCurrentRow(self.main_window.layers.active_index)

    def set_active_layer(self, idx):
        self.main_window.set_active_layer(idx)

    def move_up(self):
        idx = self.list_widget.currentRow()
        if idx > 0:
            self.main_window.layers.move_layer(idx, idx-1)
            self.refresh()
            self.main_window.refresh_layers()

    def move_down(self):
        idx = self.list_widget.currentRow()
        if idx < len(self.main_window.layers.layers)-1:
            self.main_window.layers.move_layer(idx, idx+1)
            self.refresh()
            self.main_window.refresh_layers()

    def copy_layer(self):
        idx = self.list_widget.currentRow()
        if 0 <= idx < len(self.main_window.layers.layers):
            import copy
            self.copied_layer = copy.deepcopy(self.main_window.layers.layers[idx])

    def paste_layer(self):
        if self.copied_layer:
            import copy
            new_layer = copy.deepcopy(self.copied_layer)
            self.main_window.layers.add_layer(new_layer.image, new_layer.name + ' (Kopya)')
            self.refresh()
            self.main_window.refresh_layers()
