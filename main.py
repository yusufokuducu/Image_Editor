import sys
import cv2
import numpy as np
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QPushButton, QFileDialog, QTabWidget,
                             QSpinBox, QDoubleSpinBox, QScrollArea, QFrame, QGroupBox,
                             QComboBox, QMessageBox, QProgressDialog, QMenuBar, QMenu,
                             QStatusBar, QDialog, QCheckBox)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QColor
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QSettings
from image_processor import ImageProcessor
from undo_redo import UndoRedoManager
from crop_tool import CropTool

class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.undo_redo = UndoRedoManager()
        self.settings = QSettings('ImageEditor', 'Settings')
        self.zoom_level = 1.0
        self.recent_files = self.load_recent_files()
        self.init_ui()
        self.apply_dark_theme()
        self.setAcceptDrops(True)
        self.restore_window_geometry()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Professional Image Editor")
        self.setGeometry(50, 50, 1700, 1000)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label = QLabel("Ready")
        self.statusBar.addWidget(self.status_label)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel - Image display
        left_layout = QVBoxLayout()
        
        # Image info
        self.info_label = QLabel("No image loaded")
        self.info_label.setStyleSheet("color: #888; font-size: 10px;")
        left_layout.addWidget(self.info_label)
        
        # Image label with crop tool
        self.image_label = CropTool()
        self.image_label.setMinimumSize(700, 700)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #2a2a2a; background: #0a0a0a;")
        self.image_label.crop_finished.connect(self.finalize_crop)
        left_layout.addWidget(self.image_label)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setMaximumWidth(150)
        self.zoom_slider.sliderMoved.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        zoom_layout.addWidget(self.zoom_label)
        left_layout.addLayout(zoom_layout)
        
        # Compare button
        self.compare_btn = QPushButton("👁️ Before/After")
        self.compare_btn.setCheckable(True)
        self.compare_btn.setEnabled(False)
        self.compare_btn.clicked.connect(self.toggle_compare)
        left_layout.addWidget(self.compare_btn)
        
        # Right panel - Controls
        right_layout = QVBoxLayout()
        
        # Undo/Redo
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
        
        # Basic adjustments
        tabs.addTab(self.create_adjustments_tab(), "⚙️ Adjustments")
        
        # Color correction
        tabs.addTab(self.create_color_tab(), "🎨 Colors")
        
        # Filters
        tabs.addTab(self.create_filters_tab(), "✨ Filters")
        
        # Transform
        tabs.addTab(self.create_transform_tab(), "🔄 Transform")
        
        # Effects
        tabs.addTab(self.create_effects_tab(), "🎆 Effects")
        
        # Analysis
        tabs.addTab(self.create_analysis_tab(), "📊 Analysis")
        
        right_layout.addWidget(tabs)
        
        # Save/Reset buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_image)
        save_btn.setStyleSheet(self.get_button_style("#3f5a6a"))
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.reset_image)
        reset_btn.setStyleSheet(self.get_button_style("#6a3f3f"))
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        right_layout.addLayout(button_layout)
        
        # Add layouts
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        
        self.original_image_for_compare = None
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Image", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_image)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_image_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Recent files
        self.recent_menu = file_menu.addMenu("Recent Files")
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        reset_action = QAction("Reset Image", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.reset_image)
        edit_menu.addAction(reset_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        crop_action = QAction("Crop Tool", self)
        crop_action.setShortcut("C")
        crop_action.triggered.connect(self.start_crop)
        tools_menu.addAction(crop_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        zoom_fit = QAction("Fit to Window", self)
        zoom_fit.setShortcut("Ctrl+0")
        zoom_fit.triggered.connect(lambda: self.zoom_slider.setValue(100))
        view_menu.addAction(zoom_fit)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        shortcuts_action = QAction("Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_adjustments_tab(self):
        """Create basic adjustments tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        adjustments = [
            ("Brightness", -100, 100, 0, self.on_brightness_changed),
            ("Contrast", -100, 100, 0, self.on_contrast_changed),
            ("Saturation", -100, 100, 0, self.on_saturation_changed),
            ("Sharpness", 0, 100, 0, self.on_sharpness_changed),
            ("Hue Rotation", -180, 180, 0, self.on_hue_changed),
        ]
        
        self.adjustment_sliders = {}
        self.adjustment_labels = {}
        
        for name, min_val, max_val, default, callback in adjustments:
            label_layout = QHBoxLayout()
            label = QLabel(name)
            value_label = QLabel(str(default))
            value_label.setFixedWidth(40)
            value_label.setAlignment(Qt.AlignRight)
            label_layout.addWidget(label)
            label_layout.addWidget(value_label)
            layout.addLayout(label_layout)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.sliderMoved.connect(callback)
            layout.addWidget(slider)
            
            self.adjustment_sliders[name] = slider
            self.adjustment_labels[name] = value_label
        
        apply_btn = QPushButton("✓ Confirm Adjustments")
        apply_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        apply_btn.clicked.connect(self.confirm_adjustments)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_color_tab(self):
        """Create color correction tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Levels
        layout.addWidget(QLabel("Levels"))
        levels_layout = QHBoxLayout()
        layout.addWidget(QLabel("Black Point:"))
        self.levels_black = QSpinBox()
        self.levels_black.setRange(0, 255)
        self.levels_black.setValue(0)
        levels_layout.addWidget(self.levels_black)
        layout.addLayout(levels_layout)
        
        layout.addWidget(QLabel("White Point:"))
        self.levels_white = QSpinBox()
        self.levels_white.setRange(0, 255)
        self.levels_white.setValue(255)
        layout.addWidget(self.levels_white)
        
        apply_levels_btn = QPushButton("Apply Levels")
        apply_levels_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        apply_levels_btn.clicked.connect(self.apply_levels)
        layout.addWidget(apply_levels_btn)
        
        layout.addSpacing(20)
        
        # Color temperature
        layout.addWidget(QLabel("Color Temperature"))
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Warm/Cool:"))
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(-50, 50)
        self.temp_slider.setValue(0)
        temp_layout.addWidget(self.temp_slider)
        layout.addLayout(temp_layout)
        
        layout.addSpacing(20)
        
        # Preset color grades
        layout.addWidget(QLabel("Color Presets"))
        presets = [
            ("🌅 Warm", self.apply_warm),
            ("❄️ Cool", self.apply_cool),
            ("🌙 Dark", self.apply_dark),
            ("☀️ Bright", self.apply_bright),
        ]
        
        for preset_name, preset_func in presets:
            btn = QPushButton(preset_name)
            btn.setStyleSheet(self.get_button_style("#4a5a6a"))
            btn.clicked.connect(preset_func)
            layout.addWidget(btn)
        
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
        
        filters = [
            ("Blur", 1, 50, 1, self.apply_blur),
            ("Noise", 0, 50, 0, self.apply_noise),
        ]
        
        self.filter_sliders = {}
        self.filter_labels = {}
        
        for name, min_val, max_val, default, callback in filters:
            label_layout = QHBoxLayout()
            label = QLabel(name)
            value_label = QLabel(str(default))
            value_label.setFixedWidth(40)
            label_layout.addWidget(label)
            label_layout.addWidget(value_label)
            layout.addLayout(label_layout)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.sliderMoved.connect(callback)
            layout.addWidget(slider)
            
            self.filter_sliders[name] = slider
            self.filter_labels[name] = value_label
        
        layout.addWidget(QLabel("Quick Filters"))
        
        quick_filters = [
            ("⚪ Grayscale", self.apply_grayscale),
            ("🟤 Sepia", self.apply_sepia),
            ("⚡ Edge Detection", self.apply_edge_detection),
        ]
        
        for filter_name, filter_func in quick_filters:
            btn = QPushButton(filter_name)
            btn.setStyleSheet(self.get_button_style("#4a5a6a"))
            btn.clicked.connect(filter_func)
            layout.addWidget(btn)
        
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
        
        # Crop button
        crop_btn = QPushButton("✂️ Crop Image")
        crop_btn.setStyleSheet(self.get_button_style("#4a6a3f"))
        crop_btn.clicked.connect(self.start_crop)
        layout.addWidget(crop_btn)
        
        # Resize
        layout.addWidget(QLabel("Resize"))
        layout.addWidget(QLabel("Width:"))
        self.resize_width = QSpinBox()
        self.resize_width.setRange(10, 10000)
        self.resize_width.setValue(800)
        layout.addWidget(self.resize_width)
        
        layout.addWidget(QLabel("Height:"))
        self.resize_height = QSpinBox()
        self.resize_height.setRange(10, 10000)
        self.resize_height.setValue(600)
        layout.addWidget(self.resize_height)
        
        resize_btn = QPushButton("Apply Resize")
        resize_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        resize_btn.clicked.connect(self.apply_resize)
        layout.addWidget(resize_btn)
        
        # Rotate
        layout.addWidget(QLabel("Rotate"))
        rotate_layout = QHBoxLayout()
        rotate_layout.addWidget(QLabel("Angle:"))
        self.rotate_value = QLabel("0°")
        self.rotate_value.setFixedWidth(50)
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
        flip_h = QPushButton("↔️ Horizontal")
        flip_h.clicked.connect(self.apply_flip_horizontal)
        flip_v = QPushButton("↕️ Vertical")
        flip_v.clicked.connect(self.apply_flip_vertical)
        flip_layout.addWidget(flip_h)
        flip_layout.addWidget(flip_v)
        layout.addLayout(flip_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_effects_tab(self):
        """Create effects tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        effects = [
            ("Vignette", 0, 100, 0, self.apply_vignette),
            ("Posterize", 2, 256, 256, self.apply_posterize),
        ]
        
        for name, min_val, max_val, default, callback in effects:
            label_layout = QHBoxLayout()
            label = QLabel(name)
            value_label = QLabel(str(default))
            value_label.setFixedWidth(40)
            label_layout.addWidget(label)
            label_layout.addWidget(value_label)
            layout.addLayout(label_layout)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.sliderMoved.connect(callback)
            slider.sliderMoved.connect(lambda v, vl=value_label: vl.setText(str(v)))
            layout.addWidget(slider)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def create_analysis_tab(self):
        """Create analysis tab with histogram"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Image Analysis"))
        
        # Image stats
        self.stats_label = QLabel("Load image to see statistics")
        self.stats_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.stats_label)
        
        # Histogram display
        layout.addWidget(QLabel("Histogram"))
        self.histogram_label = QLabel()
        self.histogram_label.setMinimumHeight(150)
        self.histogram_label.setStyleSheet("border: 1px solid #333; background: #1a1a1a;")
        layout.addWidget(self.histogram_label)
        
        refresh_btn = QPushButton("Refresh Analysis")
        refresh_btn.setStyleSheet(self.get_button_style("#2a6a3f"))
        refresh_btn.clicked.connect(self.update_analysis)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def apply_dark_theme(self):
        """Apply dark theme"""
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
        }
        
        QPushButton:hover {
            background-color: #252525;
            border: 1px solid #444444;
        }
        
        QPushButton:disabled {
            color: #666666;
        }
        
        QSlider::groove:horizontal {
            border: 1px solid #333333;
            height: 6px;
            background: #1a1a1a;
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
        }
        
        QTabWidget::pane {
            border: 1px solid #333333;
        }
        
        QTabBar::tab {
            background-color: #1a1a1a;
            color: #888888;
            padding: 10px 20px;
            border: 1px solid #333333;
        }
        
        QTabBar::tab:selected {
            background-color: #252525;
            color: #4a9eff;
            border: 1px solid #4a9eff;
            border-bottom: 3px solid #4a9eff;
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
        }
        
        QScrollBar::handle:vertical {
            background: #4a9eff;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QMenuBar {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border-bottom: 1px solid #333333;
        }
        
        QMenuBar::item:selected {
            background-color: #252525;
        }
        
        QMenu {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border: 1px solid #333333;
        }
        
        QMenu::item:selected {
            background-color: #252525;
        }
        
        QStatusBar {
            background-color: #1a1a1a;
            color: #888888;
            border-top: 1px solid #333333;
        }
        """
        self.setStyleSheet(dark_stylesheet)
    
    def get_button_style(self, color):
        """Get custom button style"""
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
        """
    
    def get_tab_style(self):
        """Get tab style"""
        return """
        QTabBar::tab {
            padding: 10px 20px;
            margin-right: 2px;
        }
        """
    
    def load_image(self):
        """Load image from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )
        
        if file_path:
            self.load_image_from_path(file_path)
            self.add_recent_file(file_path)
    
    def load_image_from_path(self, file_path):
        """Load image from path"""
        try:
            self.image_processor.load_image(file_path)
            self.original_image_for_compare = self.image_processor.original_image.copy()
            self.undo_redo.clear()
            self.undo_redo.add_state(self.image_processor.get_current_image())
            self.display_image()
            
            h, w = self.image_processor.current_image.shape[:2]
            filename = os.path.basename(file_path)
            self.info_label.setText(f"{filename} | {w}×{h} px")
            self.resize_width.setValue(w)
            self.resize_height.setValue(h)
            self.compare_btn.setEnabled(True)
            
            self.status_label.setText(f"Loaded: {filename}")
            self.update_analysis()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load image: {e}")
    
    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        """Handle drop"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_image_from_path(files[0])
    
    def display_image(self):
        """Display image on label"""
        if self.image_processor.current_image is None:
            return
        
        image = self.image_processor.current_image
        h, w, ch = image.shape
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(q_image)
        
        # Apply zoom
        zoom_percent = self.zoom_slider.value()
        scaled_size = int(pixmap.width() * zoom_percent / 100)
        scaled_pixmap = pixmap.scaledToWidth(scaled_size, Qt.SmoothTransformation)
        
        self.image_label.set_pixmap(scaled_pixmap)
    
    def on_zoom_changed(self):
        """Handle zoom change"""
        zoom = self.zoom_slider.value()
        self.zoom_label.setText(f"{zoom}%")
        self.display_image()
    
    def apply_all_adjustments(self):
        """Apply all adjustments together"""
        if self.image_processor.original_image is None:
            return
        
        self.image_processor.current_image = self.image_processor.original_image.copy()
        
        for name, slider in self.adjustment_sliders.items():
            value = slider.value()
            if value != 0:
                if name == "Brightness":
                    self.image_processor.brightness(value)
                elif name == "Contrast":
                    self.image_processor.contrast(value)
                elif name == "Saturation":
                    self.image_processor.saturation(value)
                elif name == "Sharpness":
                    self.image_processor.sharpen(value)
                elif name == "Hue Rotation":
                    self.image_processor.rotate_hue(value)
            
            self.adjustment_labels[name].setText(str(value))
        
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
        """Confirm adjustments"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.update_undo_redo_buttons()
        self.status_label.setText("Adjustments confirmed")
    
    def apply_levels(self):
        """Apply levels"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        black = self.levels_black.value()
        white = self.levels_white.value()
        self.image_processor.apply_levels(black, white, 0, 255)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_blur(self, value):
        """Apply blur"""
        if self.image_processor.current_image is None:
            return
        img = self.image_processor.current_image.copy()
        if value < 1:
            value = 1
        if value % 2 == 0:
            value += 1
        self.image_processor.current_image = cv2.GaussianBlur(img, (value, value), 0)
        self.display_image()
    
    def apply_noise(self, value):
        """Apply noise"""
        if self.image_processor.current_image is None:
            return
        img = self.image_processor.current_image.copy()
        noise = np.random.normal(0, value, img.shape)
        self.image_processor.current_image = np.clip(img + noise, 0, 255).astype(np.uint8)
        self.display_image()
    
    def apply_grayscale(self):
        """Apply grayscale"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.grayscale()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_sepia(self):
        """Apply sepia"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.sepia()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_edge_detection(self):
        """Apply edge detection"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.edge_detection()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_vignette(self, value):
        """Apply vignette"""
        if self.image_processor.current_image is None:
            return
        
        rows, cols = self.image_processor.current_image.shape[:2]
        X_kernel = cv2.getGaussianKernel(cols, cols/2)
        Y_kernel = cv2.getGaussianKernel(rows, rows/2)
        kernel = Y_kernel * X_kernel.T
        mask = kernel / kernel.max()
        mask = mask ** (1 - value / 100)
        
        output = self.image_processor.current_image.copy().astype(np.float32)
        for i in range(3):
            output[:, :, i] = output[:, :, i] * mask
        
        self.image_processor.current_image = np.clip(output, 0, 255).astype(np.uint8)
        self.display_image()
    
    def apply_posterize(self, value):
        """Apply posterize"""
        if self.image_processor.current_image is None:
            return
        
        levels = value
        self.image_processor.current_image = (self.image_processor.current_image // (256 // levels)) * (256 // levels)
        self.display_image()
    
    def apply_warm(self):
        """Apply warm tone"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        img = self.image_processor.current_image.astype(np.float32)
        img[:, :, 0] *= 0.8
        img[:, :, 2] *= 1.2
        self.image_processor.current_image = np.clip(img, 0, 255).astype(np.uint8)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_cool(self):
        """Apply cool tone"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        img = self.image_processor.current_image.astype(np.float32)
        img[:, :, 0] *= 1.2
        img[:, :, 2] *= 0.8
        self.image_processor.current_image = np.clip(img, 0, 255).astype(np.uint8)
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_dark(self):
        """Apply dark effect"""
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
    
    def start_crop(self):
        """Start crop mode"""
        if self.image_processor.current_image is None:
            QMessageBox.warning(self, "Warning", "Load image first")
            return
        
        self.image_label.set_crop_mode(True)
        self.status_label.setText("Crop mode: Click and drag to select area")
    
    def finalize_crop(self, x1, y1, x2, y2):
        """Finalize crop"""
        if self.image_processor.current_image is None:
            return
        
        # Convert from display coordinates to image coordinates
        pixmap = self.image_label.pixmap()
        if pixmap:
            scale = self.image_processor.current_image.shape[1] / pixmap.width()
            x1, y1, x2, y2 = int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale)
        
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.crop(x1, y1, x2, y2)
        self.display_image()
        self.update_undo_redo_buttons()
        self.status_label.setText("Image cropped")
    
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
        """Apply rotate"""
        if self.image_processor.current_image is None:
            return
        img = self.image_processor.original_image.copy()
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, value, 1.0)
        rotated = cv2.warpAffine(img, matrix, (w, h))
        self.image_processor.current_image = rotated
        self.display_image()
    
    def apply_flip_horizontal(self):
        """Flip horizontal"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.flip_horizontal()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def apply_flip_vertical(self):
        """Flip vertical"""
        if self.image_processor.current_image is None:
            return
        self.undo_redo.add_state(self.image_processor.current_image)
        self.image_processor.flip_vertical()
        self.display_image()
        self.update_undo_redo_buttons()
    
    def toggle_compare(self):
        """Toggle before/after"""
        if not self.compare_btn.isChecked():
            self.display_image()
        else:
            if self.original_image_for_compare is not None:
                self.image_processor.current_image = self.original_image_for_compare.copy()
                self.display_image()
    
    def update_analysis(self):
        """Update image analysis"""
        if self.image_processor.current_image is None:
            return
        
        img = self.image_processor.current_image
        h, w = img.shape[:2]
        
        # Calculate statistics
        mean_val = cv2.mean(img)[:3]
        std_val = cv2.calcHist([img], [0], None, [256], [0, 256]).std()
        
        stats_text = f"""Image: {w}×{h} px
Mean RGB: ({mean_val[2]:.1f}, {mean_val[1]:.1f}, {mean_val[0]:.1f})
Std Dev: {std_val:.1f}
Size: {w*h/1e6:.2f} MP"""
        
        self.stats_label.setText(stats_text)
        self.draw_histogram()
    
    def draw_histogram(self):
        """Draw histogram"""
        if self.image_processor.current_image is None:
            return
        
        hist_data = self.image_processor.get_histogram()
        if not hist_data:
            return
        
        # Create histogram image
        hist_img = np.ones((150, 256, 3), dtype=np.uint8) * 13
        
        # Draw channels
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for hist, color in zip([hist_data.blue_hist, hist_data.green_hist, hist_data.red_hist], colors):
            hist_norm = hist / hist.max() * 140
            for i in range(256):
                cv2.line(hist_img, (i, 150), (i, int(150 - hist_norm[i])), color, 1)
        
        # Convert to QImage
        rgb_hist = cv2.cvtColor(hist_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_hist.shape
        q_img = QImage(rgb_hist.data, w, h, 3*w, QImage.Format_RGB888)
        
        pixmap = QPixmap.fromImage(q_img)
        self.histogram_label.setPixmap(pixmap)
    
    def undo(self):
        """Undo"""
        state = self.undo_redo.undo()
        if state is not None:
            self.image_processor.current_image = state
            self.display_image()
            self.update_undo_redo_buttons()
            self.status_label.setText("Undo")
    
    def redo(self):
        """Redo"""
        state = self.undo_redo.redo()
        if state is not None:
            self.image_processor.current_image = state
            self.display_image()
            self.update_undo_redo_buttons()
            self.status_label.setText("Redo")
    
    def reset_image(self):
        """Reset image"""
        if self.image_processor.original_image is None:
            return
        
        reply = QMessageBox.question(
            self, "Reset",
            "Reset all changes?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.image_processor.reset()
            self.undo_redo.clear()
            self.undo_redo.add_state(self.image_processor.get_current_image())
            self.display_image()
            self.update_undo_redo_buttons()
            self.compare_btn.setChecked(False)
            self.status_label.setText("Image reset")
    
    def save_image(self):
        """Save image"""
        if self.image_processor.current_image is None:
            QMessageBox.warning(self, "Warning", "No image to save")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        
        if file_path:
            try:
                self.image_processor.save_image(file_path)
                self.status_label.setText(f"Saved: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Success", f"Saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Save failed: {e}")
    
    def save_image_as(self):
        """Save as"""
        self.save_image()
    
    def update_undo_redo_buttons(self):
        """Update button states"""
        self.undo_btn.setEnabled(self.undo_redo.can_undo())
        self.redo_btn.setEnabled(self.undo_redo.can_redo())
    
    def add_recent_file(self, file_path):
        """Add to recent files"""
        files = self.load_recent_files()
        if file_path in files:
            files.remove(file_path)
        files.insert(0, file_path)
        files = files[:10]  # Keep last 10
        
        with open('recent_files.json', 'w') as f:
            json.dump(files, f)
        
        self.recent_files = files
        self.update_recent_menu()
    
    def load_recent_files(self):
        """Load recent files"""
        try:
            with open('recent_files.json', 'r') as f:
                return json.load(f)
        except:
            return []
    
    def update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.clear()
        for file_path in self.recent_files:
            if os.path.exists(file_path):
                action = QAction(os.path.basename(file_path), self)
                action.triggered.connect(lambda checked, p=file_path: self.load_image_from_path(p))
                self.recent_menu.addAction(action)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """
        Ctrl+O - Open Image
        Ctrl+S - Save
        Ctrl+Shift+S - Save As
        Ctrl+Z - Undo
        Ctrl+Y - Redo
        Ctrl+R - Reset
        C - Crop Tool
        Ctrl+Q - Exit
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Professional Image Editor
        v1.0
        
        A powerful, feature-rich image editor with support for:
        - Advanced color correction
        - Batch processing
        - Professional filters
        - Histogram analysis
        """
        QMessageBox.information(self, "About", about_text)
    
    def save_window_geometry(self):
        """Save window geometry"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def restore_window_geometry(self):
        """Restore window geometry"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
    
    def closeEvent(self, event):
        """Handle close event"""
        self.save_window_geometry()
        event.accept()

def main():
    app = QApplication(sys.argv)
    editor = ImageEditor()
    editor.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
