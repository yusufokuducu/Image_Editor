from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QSlider
from PySide6.QtCore import Qt

class Controls(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Brightness
        self.brightness_label = QLabel("Parlaklık: 0")
        self.layout.addWidget(self.brightness_label)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.layout.addWidget(self.brightness_slider)

        # Contrast
        self.contrast_label = QLabel("Kontrast: 1.0")
        self.layout.addWidget(self.contrast_label)
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(1, 200) # Representing 0.1 to 2.0
        self.contrast_slider.setValue(100)
        self.layout.addWidget(self.contrast_slider)

        # Saturation
        self.saturation_label = QLabel("Doygunluk: 1.0")
        self.layout.addWidget(self.saturation_label)
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(0, 200) # Representing 0.0 to 2.0
        self.saturation_slider.setValue(100)
        self.layout.addWidget(self.saturation_slider)

        # Noise
        self.noise_label = QLabel("Parazit: 0")
        self.layout.addWidget(self.noise_label)
        self.noise_slider = QSlider(Qt.Orientation.Horizontal)
        self.noise_slider.setRange(0, 100)
        self.noise_slider.setValue(0)
        self.layout.addWidget(self.noise_slider)
