from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFontComboBox,
                             QSpinBox, QPushButton, QFrame, QColorDialog)
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import logging
class TextOptionsWidget(QWidget):
    optionsChanged = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(Qt.GlobalColor.black) 
        self._init_ui()
        self._connect_signals()
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(8)
        font_layout = QHBoxLayout()
        font_label = QLabel("Font:")
        self.font_combo = QFontComboBox()
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        main_layout.addLayout(font_layout)
        size_style_layout = QHBoxLayout()
        size_label = QLabel("Size:")
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(6, 128)
        self.size_spinbox.setValue(12)
        self.size_spinbox.setSuffix(" pt")
        self.bold_button = QPushButton("B")
        self.bold_button.setCheckable(True)
        self.bold_button.setFixedWidth(30)
        font = self.bold_button.font()
        font.setBold(True)
        self.bold_button.setFont(font)
        self.italic_button = QPushButton("I")
        self.italic_button.setCheckable(True)
        self.italic_button.setFixedWidth(30)
        font = self.italic_button.font()
        font.setItalic(True)
        self.italic_button.setFont(font)
        size_style_layout.addWidget(size_label)
        size_style_layout.addWidget(self.size_spinbox)
        size_style_layout.addStretch()
        size_style_layout.addWidget(self.bold_button)
        size_style_layout.addWidget(self.italic_button)
        main_layout.addLayout(size_style_layout)
        color_layout = QHBoxLayout()
        color_label = QLabel("Color:")
        self.color_button = QPushButton()
        self.color_button.setFixedWidth(80)
        self._update_color_button(self.current_color) 
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        main_layout.addLayout(color_layout)
        main_layout.addStretch() 
    def _connect_signals(self):
        self.font_combo.currentFontChanged.connect(self.optionsChanged.emit)
        self.size_spinbox.valueChanged.connect(self.optionsChanged.emit)
        self.bold_button.toggled.connect(self.optionsChanged.emit)
        self.italic_button.toggled.connect(self.optionsChanged.emit)
        self.color_button.clicked.connect(self._show_color_dialog)
    def _show_color_dialog(self):
        color = QColorDialog.getColor(self.current_color, self, "Select Text Color")
        if color.isValid():
            self.current_color = color
            self._update_color_button(color)
            self.optionsChanged.emit() 
    def _update_color_button(self, color: QColor):
        pixmap = QPixmap(60, 20)
        pixmap.fill(color)
        self.color_button.setIcon(QIcon(pixmap))
        self.color_button.setToolTip(f"Color: {color.name()}")
    def get_font(self) -> QFont:
        font = self.font_combo.currentFont()
        font.setPointSize(self.size_spinbox.value())
        font.setBold(self.bold_button.isChecked())
        font.setItalic(self.italic_button.isChecked())
        return font
    def get_color(self) -> QColor:
        return self.current_color
    def get_options(self) -> dict:
        font = self.get_font()
        color = self.get_color()
        return {
            "font": font,
            "color": color,
            "family": font.family(),
            "size": font.pointSize(),
            "bold": font.bold(),
            "italic": font.italic(),
            "color_rgba": (color.red(), color.green(), color.blue(), color.alpha())
        }
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication(sys.argv)
    window = QMainWindow()
    text_options = TextOptionsWidget()
    window.setCentralWidget(text_options)
    def on_options_changed():
        opts = text_options.get_options()
        print("Options changed:", opts)
    text_options.optionsChanged.connect(on_options_changed)
    window.show()
    sys.exit(app.exec())