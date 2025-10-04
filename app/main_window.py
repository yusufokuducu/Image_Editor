import cv2
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QHBoxLayout, QGraphicsScene, 
    QGraphicsView, QGraphicsPixmapItem
)
from PySide6.QtGui import QPixmap, QIcon, QAction, QImage, QPainter
from PySide6.QtCore import Qt

# Import the refactored components
from .controls_widget import Controls
from . import image_processor

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pycture Perfect")
        # The icon path needs to be relative to where the app is run from, or absolute
        self.setWindowIcon(QIcon("C:\\Users\\kyusu\\Desktop\\gitypity\\image_Editor\\imageEditor\\icon.png"))
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        # Use QGraphicsView for robust image display
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setStyleSheet("border: none;")
        self.layout.addWidget(self.view, 7)

        self.controls = Controls()
        self.layout.addWidget(self.controls, 3)

        self._create_menu_bar()

        self.original_image = None
        self.processed_image = None
        self.pixmap_item = None

        # Connect signals
        self.controls.brightness_slider.valueChanged.connect(self.update_image_effects)
        self.controls.contrast_slider.valueChanged.connect(self.update_image_effects)
        self.controls.saturation_slider.valueChanged.connect(self.update_image_effects)
        self.controls.noise_slider.valueChanged.connect(self.update_image_effects)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Dosya")

        open_action = file_menu.addAction("Aç")
        open_action.triggered.connect(self.open_image)

        save_action = file_menu.addAction("Kaydet")
        save_action.triggered.connect(self.save_image)

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Görsel Aç", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                self.processed_image = self.original_image.copy()
                self.display_image(self.processed_image)
                # Reset sliders
                self.controls.brightness_slider.setValue(0)
                self.controls.contrast_slider.setValue(100)
                self.controls.saturation_slider.setValue(100)
                self.controls.noise_slider.setValue(0)

    def save_image(self):
        if self.processed_image is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Görseli Kaydet", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;All Files (*)")
        if file_path:
            cv2.imwrite(file_path, self.processed_image)

    def update_image_effects(self):
        if self.original_image is None:
            return

        brightness = self.controls.brightness_slider.value()
        contrast = self.controls.contrast_slider.value() / 100.0
        saturation = self.controls.saturation_slider.value() / 100.0
        noise = self.controls.noise_slider.value()

        self.controls.brightness_label.setText(f"Parlaklık: {brightness}")
        self.controls.contrast_label.setText(f"Kontrast: {contrast:.1f}")
        self.controls.saturation_label.setText(f"Doygunluk: {saturation:.1f}")
        self.controls.noise_label.setText(f"Parazit: {noise}")

        self.processed_image = self.original_image.copy()

        # Apply effects using the image_processor module
        self.processed_image = image_processor.apply_brightness_contrast(self.processed_image, brightness, contrast)
        self.processed_image = image_processor.apply_saturation(self.processed_image, saturation)
        self.processed_image = image_processor.apply_noise(self.processed_image, noise)

        self.display_image(self.processed_image)

    def display_image(self, image_data):
        height, width, channel = image_data.shape
        bytes_per_line = 3 * width
        q_image = QImage(image_data.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(q_image)

        if self.pixmap_item is None:
            self.pixmap_item = self.scene.addPixmap(pixmap)
        else:
            self.pixmap_item.setPixmap(pixmap)
        
        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self.fit_view()

    def resizeEvent(self, event):
        self.fit_view()
        super().resizeEvent(event)

    def fit_view(self):
        if self.pixmap_item:
            self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
