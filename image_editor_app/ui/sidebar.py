"""
Sidebar UI components and related methods
"""
import customtkinter as ctk
from image_editor_app.utils.constants import *
from image_editor_app.widgets.tooltip import ToolTip
from image_editor_app.widgets.toggle_button import ToggleButton
from image_editor_app.widgets.effect_intensity import EffectIntensityFrame

def create_sidebar(self):
    """Create the sidebar with control panels"""
    # Sidebar container
    self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
    self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    self.sidebar.grid_propagate(False)  # Sabit genişliği koru
    
    # Configure sidebar
    self.sidebar.grid_columnconfigure(0, weight=1)  # Content expands horizontally
    
    # Create scrollable frame for sidebar content
    self.scrollable_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
    self.scrollable_container.grid(row=0, column=0, sticky="nsew")
    self.sidebar.grid_rowconfigure(0, weight=1)
    
    # Add canvas and scrollbar for scrolling
    self.sidebar_canvas = ctk.CTkCanvas(
        self.scrollable_container,
        bg="#242424",
        highlightthickness=0
    )
    self.sidebar_canvas.pack(side="left", fill="both", expand=True)
    
    # Add scrollbar
    self.sidebar_scrollbar = ctk.CTkScrollbar(
        self.scrollable_container, 
        command=self.sidebar_canvas.yview
    )
    self.sidebar_scrollbar.pack(side="right", fill="y")
    
    # Configure canvas
    self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
    self.sidebar_canvas.bind('<Configure>', lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all")))
    
    # Create frame for scrollable content
    self.scrollable_frame = ctk.CTkFrame(self.sidebar_canvas, fg_color="transparent")
    self.sidebar_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=260)
    
    # HEADER SECTION
    header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
    
    app_name = ctk.CTkLabel(
        header_frame, 
        text="Pro Image Editor", 
        font=TITLE_FONT,
        text_color=ACCENT_COLOR
    )
    app_name.pack(anchor="w")
    
    # FILE OPERATIONS SECTION
    self.file_section = self.create_section(self.scrollable_frame, "Dosya İşlemleri", row=5)
    
    # Open Image Button
    open_btn = ctk.CTkButton(
        self.file_section, 
        text="Dosya Aç", 
        command=self.open_image,
        font=BUTTON_FONT
    )
    open_btn.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    ToolTip(open_btn, "Düzenlemek için bir görüntü dosyası açın")
    
    # Save Image Button
    save_btn = ctk.CTkButton(
        self.file_section, 
        text="Kaydet", 
        command=self.save_image,
        font=BUTTON_FONT
    )
    save_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    ToolTip(save_btn, "Düzenlenen görüntüyü kaydedin")
    
    # Reset Image Button
    reset_btn = ctk.CTkButton(
        self.file_section, 
        text="Sıfırla", 
        command=self.reset_image,
        font=BUTTON_FONT,
        fg_color=WARNING_COLOR,
        hover_color="#aa7930"
    )
    reset_btn.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    ToolTip(reset_btn, "Orijinal görüntüye geri dönün")
    
    # BASIC TOOLS SECTION
    self.basic_section = self.create_section(self.scrollable_frame, "Temel Araçlar", row=10)
    
    # Brightness control
    self.brightness_frame = EffectIntensityFrame(
        self.basic_section,
        "Parlaklık",
        min_val=0.0,
        max_val=2.0,
        default_val=1.0,
        callback=self.update_brightness
    )
    self.brightness_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    
    # Contrast control
    self.contrast_frame = EffectIntensityFrame(
        self.basic_section,
        "Kontrast",
        min_val=0.0,
        max_val=2.0,
        default_val=1.0,
        callback=self.update_contrast
    )
    self.contrast_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    
    # Saturation control
    self.saturation_frame = EffectIntensityFrame(
        self.basic_section,
        "Doygunluk",
        min_val=0.0,
        max_val=2.0,
        default_val=1.0,
        callback=self.update_saturation
    )
    self.saturation_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
    
    # Rotation and flipping buttons
    rotation_frame = ctk.CTkFrame(self.basic_section)
    rotation_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
    
    # Row title
    rotation_label = ctk.CTkLabel(rotation_frame, text="Döndürme ve Çevirme", font=LABEL_FONT)
    rotation_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
    
    # Rotate buttons
    rotate_left_btn = ctk.CTkButton(
        rotation_frame, 
        text="↺ Sol", 
        width=70,
        command=lambda: self.rotate_image("left")
    )
    rotate_left_btn.grid(row=1, column=0, padx=5, pady=5)
    ToolTip(rotate_left_btn, "Görüntüyü sola 90° döndür")
    
    rotate_right_btn = ctk.CTkButton(
        rotation_frame, 
        text="↻ Sağ", 
        width=70,
        command=lambda: self.rotate_image("right")
    )
    rotate_right_btn.grid(row=1, column=1, padx=5, pady=5)
    ToolTip(rotate_right_btn, "Görüntüyü sağa 90° döndür")
    
    # Flip buttons
    flip_h_btn = ctk.CTkButton(
        rotation_frame, 
        text="↔ Yatay", 
        width=70,
        command=lambda: self.flip_image("horizontal")
    )
    flip_h_btn.grid(row=2, column=0, padx=5, pady=5)
    ToolTip(flip_h_btn, "Görüntüyü yatay olarak çevir")
    
    flip_v_btn = ctk.CTkButton(
        rotation_frame, 
        text="↕ Dikey", 
        width=70,
        command=lambda: self.flip_image("vertical")
    )
    flip_v_btn.grid(row=2, column=1, padx=5, pady=5)
    ToolTip(flip_v_btn, "Görüntüyü dikey olarak çevir")
    
    # FILTERS SECTION
    self.filter_section = self.create_section(self.scrollable_frame, "Filtreler", row=15)
    
    # Simple Filter Buttons
    simple_filter_frame = ctk.CTkFrame(self.filter_section, fg_color="transparent")
    simple_filter_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    simple_filter_frame.grid_columnconfigure((0, 1), weight=1)
    
    # Create filter buttons dynamically with icons
    filter_configs = [
        {"name": "blur", "text": "Bulanıklaştır", "row": 0, "col": 0},
        {"name": "sharpen", "text": "Keskinleştir", "row": 0, "col": 1},
        {"name": "contour", "text": "Kontur", "row": 1, "col": 0},
        {"name": "emboss", "text": "Kabartma", "row": 1, "col": 1},
        {"name": "bw", "text": "Siyah-Beyaz", "row": 2, "col": 0},
        {"name": "invert", "text": "Negatif", "row": 2, "col": 1},
    ]
    
    for filter_cfg in filter_configs:
        filter_btn = ctk.CTkButton(
            simple_filter_frame, 
            text=filter_cfg["text"],
            width=100,
            height=30,
            command=lambda f=filter_cfg["name"]: self.apply_filter(f)
        )
        filter_btn.grid(
            row=filter_cfg["row"], 
            column=filter_cfg["col"], 
            padx=5, pady=5, 
            sticky="ew"
        )
        ToolTip(filter_btn, f"{filter_cfg['text']} filtresi uygula")
    
    # ADVANCED FILTERS SECTION
    self.advanced_section = self.create_section(self.scrollable_frame, "Gelişmiş Efektler", row=20)
    
    # Advanced Filter buttons
    advanced_filter_frame = ctk.CTkFrame(self.advanced_section, fg_color="transparent")
    advanced_filter_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    advanced_filter_frame.grid_columnconfigure((0, 1), weight=1)
    
    # Create filter buttons dynamically with icons
    advanced_configs = [
        {"name": "sepia", "text": "Sepya", "row": 0, "col": 0},
        {"name": "cartoon", "text": "Çizgi Film", "row": 0, "col": 1},
        {"name": "vignette", "text": "Vinyet", "row": 1, "col": 0},
        {"name": "pixelate", "text": "Pikselleştir", "row": 1, "col": 1},
        {"name": "red_splash", "text": "Renk Sıçratma", "row": 2, "col": 0},
        {"name": "oil", "text": "Yağlı Boya", "row": 2, "col": 1},
        {"name": "noise", "text": "Gürültü", "row": 3, "col": 0},
    ]
    
    for filter_cfg in advanced_configs:
        filter_btn = ctk.CTkButton(
            advanced_filter_frame, 
            text=filter_cfg["text"],
            width=100,
            height=30,
            command=lambda f=filter_cfg["name"]: self.apply_advanced_filter(f)
        )
        filter_btn.grid(
            row=filter_cfg["row"], 
            column=filter_cfg["col"], 
            padx=5, pady=5, 
            sticky="ew"
        )
        ToolTip(filter_btn, f"{filter_cfg['text']} filtresi uygula")
    
    # INFO SECTION
    info_section = self.create_section(self.scrollable_frame, "Bilgi", row=30)
    
    info_text = ctk.CTkLabel(
        info_section,
        text="Pro Image Editor v1.0\n© 2023 All Rights Reserved",
        font=SMALL_FONT,
        justify="center"
    )
    info_text.grid(row=0, column=0, padx=10, pady=10)
    
    # Yardım ve destek butonu
    help_btn = ctk.CTkButton(
        info_section,
        text="Yardım ve Destek",
        command=lambda: self.show_status("Yardım ve destek alanı geliştiriliyor"),
        font=SMALL_FONT,
        height=25
    )
    help_btn.grid(row=1, column=0, padx=10, pady=(5, 15), sticky="ew")
    ToolTip(help_btn, "Yardım ve destek bilgileri")

def create_section(self, parent, title, row):
    """Create a collapsible section with title"""
    section_frame = ctk.CTkFrame(parent)
    section_frame.grid(row=row, column=0, padx=15, pady=(15, 5), sticky="ew")
    
    # Section title
    section_title = ctk.CTkLabel(
        section_frame, 
        text=title, 
        font=SUBTITLE_FONT,
        text_color=ACCENT_COLOR
    )
    section_title.grid(row=0, column=0, padx=10, pady=8, sticky="w")
    
    # Divider
    divider = ctk.CTkFrame(section_frame, height=1, fg_color=ACCENT_COLOR)
    divider.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
    
    # Content frame
    content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
    content_frame.grid(row=2, column=0, sticky="ew")
    section_frame.grid_columnconfigure(0, weight=1)
    
    return content_frame 