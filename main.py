import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QPushButton, QFileDialog, QTabWidget,
                             QSpinBox, QDoubleSpinBox, QScrollArea, QFrame, QGroupBox,
                             QComboBox, QMessageBox, QProgressDialog)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QColor
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from image_processor import ImageProcessor
from undo_redo import UndoRedoManager

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.undo_redo = UndoRedoManager()
        self.init_ui()
        self.apply_dark_theme()
        self.setAcceptDrops(True)
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Image Editor - Professional Edition")
        self.setGeometry(50, 50, 1600, 950)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel - Image display with controls
        left_layout = QVBoxLayout()
        
        # Image info label
        self.info_label = QLabel("No image loaded")
        self.info_label.setStyleSheet("color: #888; font-size: 10px;")
        left_layout.addWidget(self.info_label)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setMinimumSize(650, 650)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #2a2a2a; background: #0a0a0a;")
        left_layout.addWidget(self.image_label)
        
        # Before/After toggle
        compare_layout = QHBoxLayout()
        self.compare_btn = QPushButton("👁️ Compare Before/After")
        self.compare_btn.setCheckable(True)
        self.compare_btn.setEnabled(False)
        self.compare_btn.clicked.connect(self.toggle_compare)
        compare_layout.addWidget(self.compare_btn)
        left_layout.addLayout(compare_layout)
        
        # Load/Save buttons
        button_layout = QHBoxLayout()
        load_btn = QPushButton("📁 Open Image")
        load_btn.clicked.connect(self.load_image)
        load_btn.setFixedHeight(40)
        load_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        
        save_btn = QPushButton("💾 Save Image")
        save_btn.clicked.connect(self.save_image)
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet(self.get_button_style("#3f5a6a"))
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.reset_image)
        reset_btn.setFixedHeight(40)
        reset_btn.setStyleSheet(self.get_button_style("#6a3f3f"))
        
        button_layout.addWidget(load_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        left_layout.addLayout(button_layout)
        
        # Right panel - Controls
        right_layout = QVBoxLayout()
        
        # Undo/Redo buttons
        undo_redo_layout = QHBoxLayout()
        self.undo_btn = QPushButton("↶ Undo")
        self.redo_btn = QPushButton("↷ Redo")
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn.clicked.connect(self.redo)
        self.undo_btn.setEnabled(False)
        self.redo_btn.setEnabled(False)
        undo_redo_layout.addWidget(self.undo_btn)
        undo_redo_layout.addWidget(self.redo_btn)
        right_layout.addLayout(undo_redo_layout)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(self.get_tab_style())
        
        # Adjustments tab
        adjustments_widget = self.create_adjustments_tab()
        tabs.addTab(adjustments_widget, "⚙️ Adjustments")
        
        # Filters tab
        filters_widget = self.create_filters_tab()
        tabs.addTab(filters_widget, "✨ Filters")
        
        # Transform tab
        transform_widget = self.create_transform_tab()
        tabs.addTab(transform_widget, "🔄 Transform")
        
        # Effects tab
        effects_widget = self.create_effects_tab()
        tabs.addTab(effects_widget, "🎆 Effects")
        
        right_layout.addWidget(tabs)
        
        # Add layouts to main
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        self.original_image_for_compare = None
    
    def create_adjustments_tab(self):
        """Create adjustments tab with value display"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Brightness
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Brightness"))
        self.bright_value = QLabel("0")
        self.bright_value.setFixedWidth(40)
        self.bright_value.setAlignment(Qt.AlignRight)
        bright_layout.addWidget(self.bright_value)
        layout.addLayout(bright_layout)
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.sliderMoved.connect(self.on_brightness_changed)
        self.brightness_slider.sliderMoved.connect(lambda: self.bright_value.setText(str(self.brightness_slider.value())))
        layout.addWidget(self.brightness_slider)
        
        # Contrast
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast"))
        self.contrast_value = QLabel("0")
        self.contrast_value.setFixedWidth(40)
        self.contrast_value.setAlignment(Qt.AlignRight)
        contrast_layout.addWidget(self.contrast_value)
        layout.addLayout(contrast_layout)
        
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.sliderMoved.connect(self.on_contrast_changed)
        self.contrast_slider.sliderMoved.connect(lambda: self.contrast_value.setText(str(self.contrast_slider.value())))
        layout.addWidget(self.contrast_slider)
        
        # Saturation
        sat_layout = QHBoxLayout()
        sat_layout.addWidget(QLabel("Saturation"))
        self.sat_value = QLabel("0")
        self.sat_value.setFixedWidth(40)
        self.sat_value.setAlignment(Qt.AlignRight)
        sat_layout.addWidget(self.sat_value)
        layout.addLayout(sat_layout)
        
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.sliderMoved.connect(self.on_saturation_changed)
        self.saturation_slider.sliderMoved.connect(lambda: self.sat_value.setText(str(self.saturation_slider.value())))
        layout.addWidget(self.saturation_slider)
        
        # Sharpness
        sharp_layout = QHBoxLayout()
        sharp_layout.addWidget(QLabel("Sharpness"))
        self.sharp_value = QLabel("0")
        self.sharp_value.setFixedWidth(40)
        self.sharp_value.setAlignment(Qt.AlignRight)
        sharp_layout.addWidget(self.sharp_value)
        layout.addLayout(sharp_layout)
        
        self.sharpness_slider = QSlider(Qt.Horizontal)
        self.sharpness_slider.setRange(0, 100)
        self.sharpness_slider.setValue(0)
        self.sharpness_slider.sliderMoved.connect(self.on_sharpness_changed)
        self.sharpness_slider.sliderMoved.connect(lambda: self.sharp_value.setText(str(self.sharpness_slider.value())))
        layout.addWidget(self.sharpness_slider)
        
        # Hue rotation
        hue_layout = QHBoxLayout()
        hue_layout.addWidget(QLabel("Hue Rotation"))
        self.hue_value = QLabel("0")
        self.hue_value.setFixedWidth(40)
        self.hue_value.setAlignment(Qt.AlignRight)
        hue_layout.addWidget(self.hue_value)
        layout.addLayout(hue_layout)
        
        self.hue_slider = QSlider(Qt.Horizontal)
        self.hue_slider.setRange(-180, 180)
        self.hue_slider.setValue(0)
        self.hue_slider.sliderMoved.connect(self.on_hue_changed)
        self.hue_slider.sliderMoved.connect(lambda: self.hue_value.setText(str(self.hue_slider.value())))
        layout.addWidget(self.hue_slider)
        
        # Apply Adjustments button
        apply_adj_btn = QPushButton("✓ Confirm Adjustments")
        apply_adj_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        apply_adj_btn.clicked.connect(self.confirm_adjustments)
        layout.addWidget(apply_adj_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_filters_tab(self):
        """Create filters tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Blur
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(QLabel("Blur"))
        self.blur_value = QLabel("1")
        self.blur_value.setFixedWidth(40)
        self.blur_value.setAlignment(Qt.AlignRight)
        blur_layout.addWidget(self.blur_value)
        layout.addLayout(blur_layout)
        
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(1, 50)
        self.blur_slider.setValue(1)
        self.blur_slider.sliderMoved.connect(self.apply_blur)
        self.blur_slider.sliderMoved.connect(lambda: self.blur_value.setText(str(self.blur_slider.value())))
        layout.addWidget(self.blur_slider)
        
        # Noise
        noise_layout = QHBoxLayout()
        noise_layout.addWidget(QLabel("Add Noise"))
        self.noise_value = QLabel("0")
        self.noise_value.setFixedWidth(40)
        self.noise_value.setAlignment(Qt.AlignRight)
        noise_layout.addWidget(self.noise_value)
        layout.addLayout(noise_layout)
        
        self.noise_slider = QSlider(Qt.Horizontal)
        self.noise_slider.setRange(0, 50)
        self.noise_slider.setValue(0)
        self.noise_slider.sliderMoved.connect(self.apply_noise)
        self.noise_slider.sliderMoved.connect(lambda: self.noise_value.setText(str(self.noise_slider.value())))
        layout.addWidget(self.noise_slider)
        
        # Preset filters
        layout.addWidget(QLabel("Quick Filters"))
        
        filters_grid = QVBoxLayout()
        
        gray_btn = QPushButton("⚪ Grayscale")
        gray_btn.clicked.connect(self.apply_grayscale)
        gray_btn.setStyleSheet(self.get_button_style("#4a5a6a"))
        
        sepia_btn = QPushButton("🟤 Sepia")
        sepia_btn.clicked.connect(self.apply_sepia)
        sepia_btn.setStyleSheet(self.get_button_style("#4a5a6a"))
        
        edge_btn = QPushButton("⚡ Edge Detection")
        edge_btn.clicked.connect(self.apply_edge_detection)
        edge_btn.setStyleSheet(self.get_button_style("#4a5a6a"))
        
        filters_grid.addWidget(gray_btn)
        filters_grid.addWidget(sepia_btn)
        filters_grid.addWidget(edge_btn)
        
        layout.addLayout(filters_grid)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_transform_tab(self):
        """Create transform tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Resize
        layout.addWidget(QLabel("Resize Image"))
        
        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel("Width:"))
        self.resize_width = QSpinBox()
        self.resize_width.setRange(10, 5000)
        self.resize_width.setValue(800)
        resize_layout.addWidget(self.resize_width)
        layout.addLayout(resize_layout)
        
        resize_layout2 = QHBoxLayout()
        resize_layout2.addWidget(QLabel("Height:"))
        self.resize_height = QSpinBox()
        self.resize_height.setRange(10, 5000)
        self.resize_height.setValue(600)
        resize_layout2.addWidget(self.resize_height)
        layout.addLayout(resize_layout2)
        
        resize_btn = QPushButton("✓ Apply Resize")
        resize_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        resize_btn.clicked.connect(self.apply_resize)
        layout.addWidget(resize_btn)
        
        # Rotate
        layout.addWidget(QLabel("Rotate"))
        rotate_layout = QHBoxLayout()
        rotate_layout.addWidget(QLabel("Angle:"))
        self.rotate_value = QLabel("0°")
        self.rotate_value.setFixedWidth(50)
        self.rotate_value.setAlignment(Qt.AlignRight)
        rotate_layout.addWidget(self.rotate_value)
        layout.addLayout(rotate_layout)
        
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setRange(-180, 180)
        self.rotate_slider.setValue(0)
        self.rotate_slider.sliderMoved.connect(self.apply_rotate)
        self.rotate_slider.sliderMoved.connect(lambda: self.rotate_value.setText(str(self.rotate_slider.value()) + "°"))
        layout.addWidget(self.rotate_slider)
        
        # Flip
        layout.addWidget(QLabel("Flip"))
        flip_layout = QHBoxLayout()
        flip_h_btn = QPushButton("↔️ Horizontal")
        flip_h_btn.clicked.connect(self.apply_flip_horizontal)
        flip_v_btn = QPushButton("↕️ Vertical")
        flip_v_btn.clicked.connect(self.apply_flip_vertical)
        flip_layout.addWidget(flip_h_btn)
        flip_layout.addWidget(flip_v_btn)
        layout.addLayout(flip_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_effects_tab(self):
        """Create effects tab with advanced filters"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Advanced Effects"))
        
        # Vignette
        vig_layout = QHBoxLayout()
        vig_layout.addWidget(QLabel("Vignette"))
        self.vig_value = QLabel("0")
        self.vig_value.setFixedWidth(40)
        vig_layout.addWidget(self.vig_value)
        layout.addLayout(vig_layout)
        
        self.vignette_slider = QSlider(Qt.Horizontal)
        self.vignette_slider.setRange(0, 100)
        self.vignette_slider.setValue(0)
        self.vignette_slider.sliderMoved.connect(self.apply_vignette)
        self.vignette_slider.sliderMoved.connect(lambda: self.vig_value.setText(str(self.vignette_slider.value())))
        layout.addWidget(self.vignette_slider)
        
        # Posterize
        post_layout = QHBoxLayout()
        post_layout.addWidget(QLabel("Posterize"))
        self.post_value = QLabel("256")
        self.post_value.setFixedWidth(40)
        post_layout.addWidget(self.post_value)
        layout.addLayout(post_layout)
        
        self.posterize_slider = QSlider(Qt.Horizontal)
        self.posterize_slider.setRange(2, 256)
        self.posterize_slider.setValue(256)
        self.posterize_slider.sliderMoved.connect(self.apply_posterize)
        self.posterize_slider.sliderMoved.connect(lambda: self.post_value.setText(str(self.posterize_slider.value())))
        layout.addWidget(self.posterize_slider)
        
        layout.addWidget(QLabel("One-Click Effects"))
        
        # Effect buttons
        effects = [
            ("🌅 Warm", self.apply_warm),
            ("❄️ Cool", self.apply_cool),
            ("🌙 Dark Mode", self.apply_dark),
            ("☀️ Bright", self.apply_bright),
        ]
        
        for effect_name, effect_func in effects:
            btn = QPushButton(effect_name)
            btn.setStyleSheet(self.get_button_style("#4a5a6a"))
            btn.clicked.connect(effect_func)
            layout.addWidget(btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def apply_dark_theme(self):
        """Apply Ampcode dark theme"""
        dark_stylesheet = """
        QMainWindow, QWidget {
            background-color: #0d0d0d;
            color: #e0e0e0;
        }
        
        QLabel {
            color: #e0e0e0;
            font-size: 11px;
        }
        
        QPushButton {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
            transition: all 0.2s;
        }
        
        QPushButton:hover {
            background-color: #252525;
            border: 1px solid #444444;
        }
        
        QPushButton:pressed {
            background-color: #1a1a1a;
        }
        
        QPushButton:disabled {
            color: #666666;
            background-color: #0d0d0d;
            border: 1px solid #222222;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #333333;
            height: 6px;
            background: #1a1a1a;
            margin: 2px 0;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background: #4a9eff;
            border: 1px solid #3a7eff;
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }
        
        QSlider::handle:horizontal:hover {
            background: #5aaeef;
            border: 1px solid #4a9eff;
        }
        
        QTabWidget::pane {
            border: 1px solid #333333;
            background-color: #0d0d0d;
        }
        
        QTabBar::tab {
            background-color: #1a1a1a;
            color: #e0e0e0;
            padding: 8px 20px;
            border: 1px solid #333333;
        }
        
        QTabBar::tab:selected {
            background-color: #252525;
            border: 1px solid #4a9eff;
            border-bottom: 2px solid #4a9eff;
        }
        
        QSpinBox, QDoubleSpinBox {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
            border-radius: 4px;
            padding: 5px;
        }
        
        QScrollArea {
            background-color: #0d0d0d;
            border: none;
        }
        
        QScrollBar:vertical {
            background: #1a1a1a;
            width: 12px;
            border: 1px solid #333333;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background: #4a9eff;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #5aaeef;
        }
        """
        
        self.setStyleSheet(dark_stylesheet)
    
    def get_button_style(self, color):
        """Get custom button style with specific color"""
        return f"""
        QPushButton {{
            background-color: {color}22;
            color: #e0e0e0;
            border: 1px solid {color}66;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {color}44;
            border: 1px solid {color};
        }}
        
        QPushButton:pressed {{
            background-color: {color}22;
        }}
        """
    
    def get_tab_style(self):
        """Get custom tab style"""
        return """
        QTabWidget::pane {
            border: 1px solid #333333;
        }
        
        QTabBar::tab {
            background-color: #1a1a1a;
            color: #888888;
            padding: 10px 20px;
            border: 1px solid #333333;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #252525;
            color: #4a9eff;
            border: 1px solid #4a9eff;
            border-bottom: 3px solid #4a9eff;
        }
        """
    
    def load_image(self):
        """Load image from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )
        
        if file_path:
            try:
                self.image_processor.load_image(file_path)
                self.original_image_for_compare = self.image_processor.original_image.copy()
                self.undo_redo.clear()
                self.undo_redo.add_state(self.image_processor.get_current_image())
                self.display_image()
                
                # Update image info
                h, w = self.image_processor.current_image.shape[:2]
                self.info_label.setText(f"Loaded: {file_path.split('/')[-1]} | {w}x{h}px")
                
                self.resize_width.setValue(w)
                self.resize_height.setValue(h)
                self.compare_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load image: {e}")
    
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_image_from_path(files[0])
    
    def load_image_from_path(self, file_path):
        """Load image from specific path"""
        try:
            self.image_processor.load_image(file_path)
            self.original_image_for_compare = self.image_processor.original_image.copy()
            self.undo_redo.clear()
            self.undo_redo.add_state(self.image_processor.get_current_image())
            self.display_image()
            h, w = self.image_processor.current_image.shape[:2]
            self.info_label.setText(f"Loaded: {file_path.split('/')[-1]} | {w}x{h}px")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load image: {e}")
    
    def display_image(self):
        """Display current image on label"""
        if self.image_processor.current_image is None:
            return
        
        image = self.image_processor.current_image
        h, w, ch = image.shape
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create QImage
        bytes_per_line = 3 * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to fit label
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaledToWidth(600, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
    
    def apply_all_adjustments(self):
        """Apply all adjustment sliders together"""
        if self.image_processor.original_image is None:
            return
        
        self.image_processor.current_image = self.image_processor.original_image.copy()
        
        brightness = self.brightness_slider.value()
        if brightness != 0:
            self.image_processor.brightness(brightness)
        
        contrast = self.contrast_slider.value()
        if contrast != 0:
            self.image_processor.contrast(contrast)
        
        saturation = self.saturation_slider.value()
        if saturation != 0:
            self.image_processor.saturation(saturation)
        
        sharpness = self.sharpness_slider.value()
        if sharpness != 0:
            self.image_processor.sharpen(sharpness)
        
        hue = self.hue_slider.value()
        if hue != 0:
            self.image_processor.rotate_hue(hue)
        
        self.display_image()
    
    def on_brightness_changed(self):
        self.apply_all_adjustments()
    
    def on_contrast_changed(self):
        self.apply_all_adjustments()
    
    def on_saturation_changed(self):
        self.apply_all_adjustments()
    
    def on_sharpness_changed(self):
        self.apply_all_adjustments()
    
    def on_hue_changed(self):
        self.apply_all_adjustments()
    
    def confirm_adjustments(self):
        """Confirm adjustments and save to undo history"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.update_undo_redo_buttons()
        QMessageBox.information(self, "Success", "Adjustments confirmed!")
    
    def apply_blur(self, value):
        """Apply blur filter"""
        if self.image_processor.current_image is None:
            return
        img_copy = self.image_processor.current_image.copy()
        if value < 1:
            value = 1
        if value % 2 == 0:
            value += 1
        self.image_processor.current_image = cv2.GaussianBlur(img_copy, (value, value), 0)
        self.display_image()
    
    def apply_noise(self, value):
        """Apply noise filter"""
        if self.image_processor.current_image is None:
            return
        img_copy = self.image_processor.current_image.copy()
        noise = np.random.normal(0, value, img_copy.shape)
        self.image_processor.current_image = np.clip(img_copy + noise, 0, 255).astype(np.uint8)
        self.display_image()
    
    def apply_grayscale(self):
        """Apply grayscale filter"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.grayscale()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_sepia(self):
        """Apply sepia filter"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.sepia()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_edge_detection(self):
        """Apply edge detection filter"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.edge_detection()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_vignette(self, value):
        """Apply vignette effect"""
        if self.image_processor.current_image is None:
            return
        
        rows, cols = self.image_processor.current_image.shape[:2]
        X_resultant_kernel = cv2.getGaussianKernel(cols, cols/2)
        Y_resultant_kernel = cv2.getGaussianKernel(rows, rows/2)
        kernel = Y_resultant_kernel * X_resultant_kernel.T
        mask = kernel / kernel.max()
        mask = mask ** (1 - value / 100)
        
        output = self.image_processor.current_image.copy().astype(np.float32)
        for i in range(3):
            output[:, :, i] = output[:, :, i] * mask
        
        self.image_processor.current_image = np.clip(output, 0, 255).astype(np.uint8)
        self.display_image()
    
    def apply_posterize(self, value):
        """Apply posterize effect"""
        if self.image_processor.current_image is None:
            return
        
        levels = value
        self.image_processor.current_image = (self.image_processor.current_image // (256 // levels)) * (256 // levels)
        self.display_image()
    
    def apply_warm(self):
        """Apply warm tone effect"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        img = self.image_processor.current_image.astype(np.float32)
        img[:, :, 0] = np.clip(img[:, :, 0] * 0.8, 0, 255)  # Blue down
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.0, 0, 255)  # Green normal
        img[:, :, 2] = np.clip(img[:, :, 2] * 1.2, 0, 255)  # Red up
        self.image_processor.current_image = np.clip(img, 0, 255).astype(np.uint8)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_cool(self):
        """Apply cool tone effect"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        img = self.image_processor.current_image.astype(np.float32)
        img[:, :, 0] = np.clip(img[:, :, 0] * 1.2, 0, 255)  # Blue up
        img[:, :, 1] = np.clip(img[:, :, 1] * 1.0, 0, 255)  # Green normal
        img[:, :, 2] = np.clip(img[:, :, 2] * 0.8, 0, 255)  # Red down
        self.image_processor.current_image = np.clip(img, 0, 255).astype(np.uint8)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_dark(self):
        """Apply dark mode effect"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.current_image = (self.image_processor.current_image * 0.7).astype(np.uint8)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_bright(self):
        """Apply bright effect"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        img = self.image_processor.current_image.astype(np.float32)
        img = np.clip(img * 1.3, 0, 255)
        self.image_processor.current_image = img.astype(np.uint8)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_resize(self):
        """Apply resize"""
        if self.image_processor.current_image is None:
            return
        width = self.resize_width.value()
        height = self.resize_height.value()
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.resize(width, height)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_rotate(self, value):
        """Apply rotation"""
        if self.image_processor.current_image is None:
            return
        # Use original image for rotation to avoid artifacts
        img = self.image_processor.original_image.copy()
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, value, 1.0)
        rotated = cv2.warpAffine(img, matrix, (w, h))
        self.image_processor.current_image = rotated
        self.display_image()
    
    def apply_flip_horizontal(self):
        """Flip image horizontally"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.flip_horizontal()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_flip_vertical(self):
        """Flip image vertically"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.flip_vertical()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def toggle_compare(self):
        """Toggle before/after comparison"""
        if not self.compare_btn.isChecked():
            self.display_image()
        else:
            if self.original_image_for_compare is not None:
                self.image_processor.current_image = self.original_image_for_compare.copy()
                self.display_image()
    
    def undo(self):
        """Undo last action"""
        state = self.undo_redo.undo()
        if state is not None:
            self.image_processor.current_image = state
            self.display_image()
            self.update_undo_redo_buttons()
    
    def redo(self):
        """Redo last action"""
        state = self.undo_redo.redo()
        if state is not None:
            self.image_processor.current_image = state
            self.display_image()
            self.update_undo_redo_buttons()
    
    def reset_image(self):
        """Reset to original image"""
        if self.image_processor.original_image is None:
            return
        
        reply = QMessageBox.question(
            self, "Reset",
            "Reset all changes to original image?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.image_processor.reset()
            self.undo_redo.clear()
            self.undo_redo.add_state(self.image_processor.get_current_image())
            self.brightness_slider.setValue(0)
            self.contrast_slider.setValue(0)
            self.saturation_slider.setValue(0)
            self.sharpness_slider.setValue(0)
            self.hue_slider.setValue(0)
            self.blur_slider.setValue(1)
            self.noise_slider.setValue(0)
            self.rotate_slider.setValue(0)
            self.vignette_slider.setValue(0)
            self.posterize_slider.setValue(256)
            self.display_image()
            self.update_undo_redo_buttons()
            self.compare_btn.setChecked(False)
    
    def save_image(self):
        """Save current image"""
        if self.image_processor.current_image is None:
            QMessageBox.warning(self, "Warning", "No image to save!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;BMP Image (*.bmp);;All Files (*)"
        )
        
        if file_path:
            try:
                self.image_processor.save_image(file_path)
                QMessageBox.information(self, "Success", f"Image saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save image: {e}")
    
    def update_undo_redo_buttons(self):
        """Update undo/redo button states"""
        self.undo_btn.setEnabled(self.undo_redo.can_undo())
        self.redo_btn.setEnabled(self.undo_redo.can_redo())

def main():
    app = QApplication(sys.argv)
    editor = ImageEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
