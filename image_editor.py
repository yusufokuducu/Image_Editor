import os
import customtkinter as ctk
from customtkinter import filedialog
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
import numpy as np
import advanced_filters
import app_icon
import threading
import time

# Debug çıktısı
print("Uygulama başlatılıyor...")

# Set appearance mode and color theme
ctk.set_appearance_mode("system")  # "system", "dark" veya "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# UI Teması
ACCENT_COLOR = "#3a7ebf"
SECONDARY_COLOR = "#2a5d8f"
SUCCESS_COLOR = "#2d9657"
WARNING_COLOR = "#d19a41"
ERROR_COLOR = "#b33f3f"

# UI Yazı Tipleri
FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Helvetica"
TITLE_FONT = (FONT_FAMILY, 20, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 16, "bold")
BUTTON_FONT = (FONT_FAMILY, 12)
LABEL_FONT = (FONT_FAMILY, 12)
SMALL_FONT = (FONT_FAMILY, 10)

# Maksimum önizleme boyutu - daha büyük görüntüler önizleme için bu boyuta küçültülecek
MAX_PREVIEW_WIDTH = 1200
MAX_PREVIEW_HEIGHT = 800

class ToolTip:
    """Arayüz elemanları için ipucu balonu sınıfı"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.timer_id = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        # Eğer widget tıklanırsa tooltip kaybolsun
        self.widget.bind("<Button-1>", self.hide_tooltip)
    
    def on_enter(self, event=None):
        """Fare widget üzerine geldiğinde tooltip'i göster"""
        # Önceki zamanlayıcıyı iptal et
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
        
        # Tooltip zaten görünür değilse göster
        if not self.tooltip:
            # Küçük bir gecikme ekle ki kazara aktivasyonlar olmasın
            self.timer_id = self.widget.after(400, self.show_tooltip)
    
    def on_leave(self, event=None):
        """Fare widget üzerinden ayrıldığında tooltip'i gizle"""
        # Zamanlayıcıyı iptal et
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
        
        # Tooltip'i gizle
        self.hide_tooltip()
    
    def show_tooltip(self, event=None):
        """İpucu balonunu göster"""
        # Önceden var olan tooltip'i temizle
        self.hide_tooltip()
        
        # Konum hesaplama
        x, y = 0, 0
        
        try:
            x, y, _, _ = self.widget.bbox("insert")
            # Insert konumu bulunamadıysa, widget'ın merkez konumunu kullan
        except:
            x = self.widget.winfo_width() // 2
            y = self.widget.winfo_height() // 2
        
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # İpucu penceresi oluştur
        self.tooltip = ctk.CTkToplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # Pencere dekorasyonlarını kaldır
        
        # Tooltip her zaman üstte olsun
        self.tooltip.attributes('-topmost', True)
        
        # Windows'ta tooltip pencerelerini taskbar'da gösterme
        if os.name == "nt":
            self.tooltip.attributes("-toolwindow", True)
        
        # İpucu içeriğini oluştur - tema rengi yerine sabit renkler kullan
        bg_color = "#333333"  # Koyu tema için varsayılan renk
        border_color = "#555555"  # Koyu tema için kenarlık rengi
        text_color = "white"  # Koyu tema için metin rengi
        
        # Aydınlık tema için farklı renkler kullan
        if ctk.get_appearance_mode() == "light":
            bg_color = "#f0f0f0"
            border_color = "#cccccc"
            text_color = "black"
        
        frame = ctk.CTkFrame(
            self.tooltip,
            corner_radius=6,
            border_width=1,
            fg_color=bg_color,
            border_color=border_color
        )
        frame.pack(padx=2, pady=2)
        
        label = ctk.CTkLabel(
            frame,
            text=self.text,
            font=SMALL_FONT,
            text_color=text_color
        )
        label.pack(padx=6, pady=3)
        
        # Tooltip boyutlarını al ve ekrana sığdır
        self.tooltip.update_idletasks()
        tooltip_width = self.tooltip.winfo_width()
        tooltip_height = self.tooltip.winfo_height()
        
        # Ekran boyutlarını al
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        # Tooltip konumunu ekran sınırları içinde tut
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 10
        if y + tooltip_height > screen_height:
            y = screen_height - tooltip_height - 10
        
        # Tooltip'i konumlandır
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Güvenlik için otomatik kapanma zamanlayıcısı
        self.timer_id = self.widget.after(5000, self.hide_tooltip)
    
    def hide_tooltip(self, event=None):
        """İpucu balonunu gizle"""
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except:
                pass  # Pencere zaten kapatılmış olabilir
            self.tooltip = None
        
        # Zamanlayıcıyı temizle
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None

# Yeni modern stil ToggleButton sınıfı
class ToggleButton(ctk.CTkButton):
    """Açılıp kapanabilen buton sınıfı"""
    def __init__(self, master, text="", command=None, **kwargs):
        super().__init__(master, text=text, command=self._toggle, **kwargs)
        self.command = command
        self.active = False
        self.configure(fg_color=ACCENT_COLOR)
    
    def _toggle(self):
        """Butonun durumunu değiştir"""
        self.active = not self.active
        if self.active:
            self.configure(fg_color=SUCCESS_COLOR)
        else:
            self.configure(fg_color=ACCENT_COLOR)
        
        if self.command:
            self.command(self.active)
    
    def set_state(self, state):
        """Butonun durumunu dışarıdan ayarla"""
        if state != self.active:
            self._toggle()

class EffectIntensityFrame(ctk.CTkFrame):
    """Modern slider kontrol paneli"""
    def __init__(self, parent, title, min_val, max_val, default_val, callback, step_size=None, integer=False, **kwargs):
        kwargs["fg_color"] = kwargs.get("fg_color", "transparent")
        kwargs["corner_radius"] = kwargs.get("corner_radius", 8)
        super().__init__(parent, **kwargs)
        
        # Store parameters
        self.callback = callback
        self.default_val = default_val
        self.min_val = min_val
        self.max_val = max_val
        self.integer = integer
        
        # Calculate number of steps
        if step_size:
            self.number_of_steps = int((max_val - min_val) / step_size)
        else:
            self.number_of_steps = 100
        
        # Create title label with icon
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=(8, 0), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            title_frame, 
            text=title,
            font=LABEL_FONT,
            anchor="w"
        )
        self.title_label.pack(side="left", padx=5)
        
        # Value display
        self.value_str = self._format_value(default_val)
        self.value_label = ctk.CTkLabel(
            title_frame, 
            text=self.value_str, 
            width=50,
            font=SMALL_FONT
        )
        self.value_label.pack(side="right", padx=5)
        
        # Create slider with progress bar appearance
        slider_frame = ctk.CTkFrame(self, fg_color="transparent")
        slider_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        
        self.slider = ctk.CTkSlider(
            slider_frame, 
            from_=min_val, 
            to=max_val, 
            number_of_steps=self.number_of_steps, 
            command=self.on_change,
            button_color=ACCENT_COLOR,
            button_hover_color=SECONDARY_COLOR,
            progress_color=ACCENT_COLOR
        )
        self.slider.pack(fill="x", padx=5, pady=5)
        self.slider.set(default_val)
        
        # Create controls frame with modern styling
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        
        # Add preset buttons with icons
        button_style = {
            "corner_radius": 6,
            "border_width": 0,
            "text_color": "white",
            "hover": True,
            "font": SMALL_FONT
        }
        
        self.min_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Min", 
            width=40, 
            command=lambda: self.set_value(min_val),
            fg_color=SECONDARY_COLOR,
            **button_style
        )
        self.min_btn.grid(row=0, column=0, padx=2, pady=2, sticky="w")
        
        self.max_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Max", 
            width=40, 
            command=lambda: self.set_value(max_val),
            fg_color=SECONDARY_COLOR,
            **button_style
        )
        self.max_btn.grid(row=0, column=1, padx=2, pady=2, sticky="w")
        
        self.default_btn = ctk.CTkButton(
            self.controls_frame, 
            text="Varsayılan", 
            width=70, 
            command=self.reset,
            fg_color=SECONDARY_COLOR,
            **button_style
        )
        self.default_btn.grid(row=0, column=2, padx=2, pady=2, sticky="e")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Tooltips for buttons
        ToolTip(self.min_btn, f"Minimum değere ayarla: {min_val}")
        ToolTip(self.max_btn, f"Maksimum değere ayarla: {max_val}")
        ToolTip(self.default_btn, f"Varsayılan değere sıfırla: {default_val}")
    
    def _format_value(self, value):
        """Format value for display"""
        if self.integer:
            return f"{int(value)}"
        else:
            return f"{value:.2f}"
    
    def on_change(self, value):
        """Handle slider value change"""
        # Format for display
        if self.integer:
            value = int(value)
            
        self.value_str = self._format_value(value)
        self.value_label.configure(text=self.value_str)
        
        if self.callback:
            self.callback(value)
    
    def get_value(self):
        """Get current slider value"""
        value = self.slider.get()
        if self.integer:
            return int(value)
        return value
    
    def set_value(self, value):
        """Set slider to specific value"""
        self.slider.set(value)
        self.value_str = self._format_value(value)
        self.value_label.configure(text=self.value_str)
        if self.callback:
            self.callback(value)
    
    def reset(self):
        """Reset slider to default value"""
        self.slider.set(self.default_val)
        self.value_str = self._format_value(self.default_val)
        self.value_label.configure(text=self.value_str)
        if self.callback:
            self.callback(self.default_val)

class ImageEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Pro Image Editor")
        self.geometry("1300x800")
        self.minsize(1000, 700)
        
        # Set icon
        self.set_app_icon()
        
        # Variables
        self.current_image = None
        self.original_image = None
        self.working_image = None
        self.image_path = None
        self.filename = None
        self.current_effect = None
        self.last_edited_time = None  # Son düzenleme zamanı
        self.effect_params = {
            # Gelişmiş filtreler
            "sepia": {"intensity": 1.0},
            "cartoon": {"edge_intensity": 3, "simplify": 5},
            "vignette": {"amount": 0.5},
            "pixelate": {"pixel_size": 10},
            "red_splash": {"intensity": 1.0, "color": "red"},
            "oil": {"brush_size": 3, "levels": 8},
            "noise": {"amount": 0.5},
            # Temel filtreler
            "blur": {"radius": 2.0},
            "sharpen": {"intensity": 1.0},
            "contour": {"intensity": 1.0},
            "emboss": {"intensity": 1.0},
            "bw": {"threshold": 128},
            "invert": {"intensity": 1.0}
        }
        
        # Create UI
        self.create_ui()
        
        # Effect intensity controls (created hidden initially)
        self.create_effect_controls()
        
        # Effect control frame'ini gizle, ancak henüz hide_effect_controls() metodu tanımlanmadı
        if hasattr(self, 'effect_control_frame'):
            self.effect_control_frame.grid_forget() 
            self.current_effect = None
            
        # Uygulamanın hazır olduğunu göster
        self.after(500, lambda: self.show_status("Uygulama hazır. Görüntü açmak için 'Dosya Aç' düğmesine tıklayın."))
        
    def set_app_icon(self):
        """Set the application icon"""
        icon_path = os.path.join('resources', 'app_icon.png')
        # Check if icon exists, create if it doesn't
        if not os.path.exists(icon_path):
            icon_path = app_icon.create_app_icon()
        
        # Load the icon
        icon_image = Image.open(icon_path)
        # Convert to PhotoImage
        self.icon_photo = ImageTk.PhotoImage(icon_image)
        # Set the window icon
        self.iconphoto(True, self.icon_photo)
        
    def create_ui(self):
        # Ana çerçeve düzeni - düzgün ölçekleme için ağırlık kullan
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)
        self.grid_rowconfigure(0, weight=1)
        
        # Sol panel (Sidebar) oluştur
        self.create_sidebar()
        
        # Ana içerik alanı (resim tuvali) oluştur
        self.create_main_view()
        
        # Durum çubuğu oluştur
        self.create_status_bar()
    
    def create_sidebar(self):
        """Sol kenar çubuğunu oluştur"""
        # Kenar çubuğu ana çerçevesi
        # Tema rengini sabit değerle değiştir
        sidebar_color = "#2b2b2b"  # Koyu tema için varsayılan renk
        if ctk.get_appearance_mode() == "light":
            sidebar_color = "#ebebeb"  # Açık tema için varsayılan renk
            
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=sidebar_color)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Kaydırılabilir içerik için çerçeve oluştur
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.sidebar_frame, 
            width=280,
            fg_color="transparent",
            scrollbar_button_color=ACCENT_COLOR,
            scrollbar_button_hover_color=SECONDARY_COLOR
        )
        self.scrollable_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # App logosu ve başlığı
        logo_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.logo_label = ctk.CTkLabel(
            logo_frame, 
            text="Pro Image Editor",
            font=TITLE_FONT,
            text_color=ACCENT_COLOR
        )
        self.logo_label.pack(pady=(5, 0))
        
        version_label = ctk.CTkLabel(
            logo_frame, 
            text="Sürüm 2.0", 
            font=SMALL_FONT,
            text_color="gray"
        )
        version_label.pack(pady=(0, 5))
        
        # Dosya işlemleri bölümü
        file_section = self.create_section(self.scrollable_frame, "Dosya İşlemleri", 1)
        
        self.file_frame = ctk.CTkFrame(file_section, fg_color="transparent")
        self.file_frame.pack(fill="x", padx=5, pady=5)
        
        # Grid yapılandırması
        self.file_frame.grid_columnconfigure(0, weight=1)
        self.file_frame.grid_columnconfigure(1, weight=1)
        
        # Dosya açma butonu
        self.open_button = ctk.CTkButton(
            self.file_frame, 
            text="Dosya Aç",
            command=self.open_image,
            font=BUTTON_FONT,
            fg_color=ACCENT_COLOR,
            hover_color=SECONDARY_COLOR,
            height=36,
            corner_radius=8
        )
        self.open_button.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        ToolTip(self.open_button, "Düzenlemek için bir görüntü dosyası açın")
        
        # Kaydetme butonu
        self.save_button = ctk.CTkButton(
            self.file_frame, 
            text="Kaydet",
            command=self.save_image,
            font=BUTTON_FONT,
            fg_color=ACCENT_COLOR,
            hover_color=SECONDARY_COLOR,
            height=36,
            corner_radius=8
        )
        self.save_button.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        ToolTip(self.save_button, "Düzenlenmiş görüntüyü kaydedin")
        
        # Sıfırlama butonu
        self.reset_button = ctk.CTkButton(
            file_section, 
            text="Görüntüyü Sıfırla",
            command=self.reset_image,
            font=BUTTON_FONT,
            fg_color=WARNING_COLOR,
            hover_color="#b88733",
            height=36,
            corner_radius=8
        )
        self.reset_button.pack(fill="x", padx=8, pady=(0, 5))
        ToolTip(self.reset_button, "Görüntüyü orijinal haline sıfırlayın")
        
        # Temel filtreler bölümü
        filter_section = self.create_section(self.scrollable_frame, "Temel Filtreler", 2)
        
        # Filtre butonları için çerçeve
        self.basic_filter_frame = ctk.CTkFrame(filter_section, fg_color="transparent")
        self.basic_filter_frame.pack(fill="x", padx=5, pady=5)
        
        # Daha iyi dağılım için sütunları yapılandır
        for i in range(3):
            self.basic_filter_frame.grid_columnconfigure(i, weight=1)
        
        # Temel filtre butonları (2x3 ızgara)
        filters = [
            ("Bulanık", lambda: self.apply_filter("blur"), "Görüntü üzerine bulanıklık efekti uygular"),
            ("Keskin", lambda: self.apply_filter("sharpen"), "Görüntüyü keskinleştirir"),
            ("Kontur", lambda: self.apply_filter("contour"), "Nesnelerin kenarlarını belirginleştirir"),
            ("Kabartma", lambda: self.apply_filter("emboss"), "Kabartma efekti uygular"),
            ("S/B", lambda: self.apply_filter("bw"), "Siyah-beyaz dönüşüm yapar"),
            ("Negatif", lambda: self.apply_filter("invert"), "Görüntünün renklerini tersine çevirir")
        ]
        
        for i, (name, command, tooltip) in enumerate(filters):
            btn = ctk.CTkButton(
                self.basic_filter_frame, 
                text=name, 
                command=command, 
                width=70, 
                height=32,
                fg_color=ACCENT_COLOR,
                hover_color=SECONDARY_COLOR,
                font=BUTTON_FONT,
                corner_radius=6
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
            ToolTip(btn, tooltip)
        
        # Gelişmiş filtreler bölümü
        adv_filter_section = self.create_section(self.scrollable_frame, "Gelişmiş Filtreler", 3)
        
        # Gelişmiş filtre butonları için çerçeve
        self.adv_filter_frame = ctk.CTkFrame(adv_filter_section, fg_color="transparent")
        self.adv_filter_frame.pack(fill="x", padx=5, pady=5)
        
        # Daha iyi dağılım için sütunları yapılandır
        for i in range(3):
            self.adv_filter_frame.grid_columnconfigure(i, weight=1)
        
        # Gelişmiş filtre butonları (3x3 ızgara, duyarlı düzen ile)
        adv_filters = [
            ("Sepya", lambda: self.apply_advanced_filter("sepia"), "Nostaljik sepya efekti uygular"),
            ("Çizgi Film", lambda: self.apply_advanced_filter("cartoon"), "Görüntüyü çizgi film stiline dönüştürür"),
            ("Vinyet", lambda: self.apply_advanced_filter("vignette"), "Köşeleri karartan vinyet efekti ekler"),
            ("Piksel", lambda: self.apply_advanced_filter("pixelate"), "Piksel efekti uygular"),
            ("Renk Sıçrama", lambda: self.apply_advanced_filter("red_splash"), "Sadece seçilen rengi korur"),
            ("Yağlı Boya", lambda: self.apply_advanced_filter("oil"), "Yağlı boya resim efekti uygular"),
            ("Gürültü", lambda: self.apply_advanced_filter("noise"), "Görüntüye rastgele gürültü ekler")
        ]
        
        for i, (name, command, tooltip) in enumerate(adv_filters):
            btn = ctk.CTkButton(
                self.adv_filter_frame, 
                text=name, 
                command=command, 
                width=70, 
                height=32,
                fg_color=ACCENT_COLOR,
                hover_color=SECONDARY_COLOR,
                font=BUTTON_FONT,
                corner_radius=6
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
            ToolTip(btn, tooltip)
        
        # Ayarlamalar bölümü
        adjustments_section = self.create_section(self.scrollable_frame, "Temel Ayarlar", 4)
        
        # Parlaklık ayarı
        self.brightness_frame = EffectIntensityFrame(
            adjustments_section, 
            "Parlaklık", 
            0.1, 2.0, 1.0, 
            self.update_brightness
        )
        self.brightness_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # Kontrast ayarı
        self.contrast_frame = EffectIntensityFrame(
            adjustments_section, 
            "Kontrast", 
            0.1, 2.0, 1.0, 
            self.update_contrast
        )
        self.contrast_frame.pack(fill="x", padx=5, pady=(10, 0))
        
        # Doygunluk ayarı
        self.saturation_frame = EffectIntensityFrame(
            adjustments_section, 
            "Doygunluk", 
            0.0, 2.0, 1.0, 
            self.update_saturation
        )
        self.saturation_frame.pack(fill="x", padx=5, pady=(10, 5))
        
        # Döndürme bölümü
        rotation_section = self.create_section(self.scrollable_frame, "Döndürme ve Çevirme", 5)
        
        # Döndürme butonları çerçevesi
        self.rotate_frame = ctk.CTkFrame(rotation_section, fg_color="transparent")
        self.rotate_frame.pack(fill="x", padx=5, pady=5)
        
        # Eşit dağılım için sütunları yapılandır
        for i in range(4):
            self.rotate_frame.grid_columnconfigure(i, weight=1)
        
        # Döndürme butonları
        rotate_style = {
            "width": 40,
            "height": 40,
            "corner_radius": 8,
            "fg_color": ACCENT_COLOR,
            "hover_color": SECONDARY_COLOR,
            "text_color": "white",
            "font": ctk.CTkFont(size=18)
        }
        
        self.rotate_left = ctk.CTkButton(
            self.rotate_frame, 
            text="↺", 
            command=lambda: self.rotate_image("left"),
            **rotate_style
        )
        self.rotate_left.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ToolTip(self.rotate_left, "90° sola döndür")
        
        self.rotate_right = ctk.CTkButton(
            self.rotate_frame, 
            text="↻", 
            command=lambda: self.rotate_image("right"),
            **rotate_style
        )
        self.rotate_right.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ToolTip(self.rotate_right, "90° sağa döndür")
        
        self.flip_h = ctk.CTkButton(
            self.rotate_frame, 
            text="↔", 
            command=lambda: self.flip_image("horizontal"),
            **rotate_style
        )
        self.flip_h.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        ToolTip(self.flip_h, "Yatay çevir")
        
        self.flip_v = ctk.CTkButton(
            self.rotate_frame, 
            text="↕", 
            command=lambda: self.flip_image("vertical"),
            **rotate_style
        )
        self.flip_v.grid(row=0, column=3, padx=2, pady=2, sticky="ew")
        ToolTip(self.flip_v, "Dikey çevir")
    
    def create_section(self, parent, title, row):
        """UI için bölüm oluştur"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.grid(row=row, column=0, padx=5, pady=(15, 5), sticky="ew")
        
        section_title = ctk.CTkLabel(
            section_frame, 
            text=title, 
            font=SUBTITLE_FONT,
            anchor="w"
        )
        section_title.pack(fill="x", padx=10, pady=(5, 10))
        
        # Her bölüm için iç içe içerik çerçevesi
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=5)
        
        return content_frame
        
    def create_main_view(self):
        """Ana görüntüleme alanını oluştur"""
        # Ana içerik alanı (görüntü tuvali)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Görüntü çerçevesi - sabit renk değeri kullan
        frame_color = "#2b2b2b"  # Koyu tema için varsayılan renk
        if ctk.get_appearance_mode() == "light":
            frame_color = "#ebebeb"  # Açık tema için varsayılan renk
            
        self.image_frame = ctk.CTkFrame(
            self.main_frame, 
            fg_color=frame_color
        )
        self.image_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Görüntü tuvalini oluştur - CTkCanvas değil, normal Canvas kullan
        # Tema renginden tek bir değer kullan, muhtemelen gece/gündüz moduna göre farklı
        bg_color = "#2b2b2b"  # Koyu tema için varsayılan renk
        if ctk.get_appearance_mode() == "light":
            bg_color = "#ebebeb"  # Açık tema için varsayılan renk
            
        self.canvas = ctk.CTkCanvas(
            self.main_frame, 
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Karşılama mesajı göster
        self.canvas.create_text(
            self.winfo_width() // 2, self.winfo_height() // 2,
            text="Düzenlemeye başlamak için bir görüntü açın",
            fill="white", font=SUBTITLE_FONT
        )
    
    def create_status_bar(self):
        """Durum çubuğunu oluştur"""
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar, 
            text="Hazır", 
            font=SMALL_FONT,
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, fill="y")
    
    def open_image(self):
        """Open an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # İlerleme durumunu göster
                self.show_status("Görüntü yükleniyor...")
                self.update()  # UI güncellemelerini zorla
                
                # Open and process the image
                self.image_path = file_path
                self.filename = os.path.basename(file_path)
                
                # Yüksek çözünürlüklü orijinal görüntü
                self.original_image = Image.open(file_path)
                
                # Convert to RGB if not already
                if self.original_image.mode != 'RGB':
                    self.original_image = self.original_image.convert('RGB')
                
                # Görüntünün boyutunu al
                img_width, img_height = self.original_image.size
                
                # Görüntü boyutları hakkında bilgi
                print(f"Orijinal görüntü boyutu: {img_width}x{img_height}")
                
                # Eğer görüntü çok büyükse, çalışma versiyonu için ölçeklendir
                # Bu, hızlı önizleme ve işleme için kullanılacak
                if img_width > MAX_PREVIEW_WIDTH or img_height > MAX_PREVIEW_HEIGHT:
                    ratio = min(MAX_PREVIEW_WIDTH / img_width, MAX_PREVIEW_HEIGHT / img_height)
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    
                    # Ölçeklendirilmiş çalışma kopyası
                    self.working_image = self.original_image.resize(
                        (new_width, new_height), 
                        Image.Resampling.LANCZOS
                    )
                    print(f"Ölçeklendirilmiş çalışma kopyası: {new_width}x{new_height}")
                else:
                    # Boyut küçükse, doğrudan kopyala
                    self.working_image = self.original_image.copy()
                
                # Mevcut görüntüyü çalışma görüntüsü olarak ayarla
                self.current_image = self.working_image.copy()
                
                # Gösterme
                self.display_image()
                
                # Reset sliders
                self.brightness_frame.reset()
                self.contrast_frame.reset()
                self.saturation_frame.reset()
                
                # Update window title
                self.title(f"Advanced Image Editor - {self.filename}")
                
                # Update status
                self.status_label.configure(text=f"Yüklendi: {self.filename}")
                
            except Exception as e:
                print(f"Error opening image: {e}")
                self.status_label.configure(text=f"Hata: Görüntü açılamadı")
    
    def save_image(self):
        """Save the edited image"""
        if self.current_image:
            save_path = filedialog.asksaveasfilename(
                title="Save Image",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg *.jpeg"),
                    ("BMP files", "*.bmp"),
                    ("GIF files", "*.gif"),
                    ("TIFF files", "*.tiff"),
                ]
            )
            
            if save_path:
                try:
                    # Durumu göster
                    self.show_status("Görüntü kaydediliyor...")
                    self.update()  # UI güncellemelerini zorla
                    
                    # Kayıt öncesi onay penceresi
                    if hasattr(self, 'original_image') and id(self.original_image) != id(self.current_image):
                        # Kullanıcıya kayıt tercihi için bir dialog göster
                        save_dialog = ctk.CTkToplevel(self)
                        save_dialog.title("Kaydetme Seçenekleri")
                        save_dialog.geometry("400x200")
                        save_dialog.resizable(False, False)
                        save_dialog.transient(self)  # Ana pencereye bağlı
                        save_dialog.grab_set()  # Modal pencere
                        
                        # Bu değişken, kullanıcının seçimini tutacak
                        save_option = ctk.StringVar(value="current")
                        
                        # Etiket
                        ctk.CTkLabel(
                            save_dialog, 
                            text="Görüntüyü nasıl kaydetmek istersiniz?",
                            font=ctk.CTkFont(size=16, weight="bold")
                        ).pack(pady=(20, 10))
                        
                        # Mevcut çözünürlük seçeneği
                        ctk.CTkRadioButton(
                            save_dialog, 
                            text=f"Mevcut çözünürlükte kaydet ({self.current_image.width}x{self.current_image.height})",
                            variable=save_option, 
                            value="current"
                        ).pack(anchor="w", padx=20, pady=5)
                        
                        # Orijinal çözünürlük seçeneği
                        ctk.CTkRadioButton(
                            save_dialog, 
                            text=f"Orijinal çözünürlükte kaydet ({self.original_image.width}x{self.original_image.height})",
                            variable=save_option, 
                            value="original"
                        ).pack(anchor="w", padx=20, pady=5)
                        
                        # İşlev
                        def on_save():
                            nonlocal save_path
                            selection = save_option.get()
                            save_dialog.destroy()
                            
                            if selection == "original":
                                # Son efektleri orijinal boyutlu görüntüye uygula
                                self.show_status("Yüksek çözünürlüklü görüntü hazırlanıyor...")
                                self.update()
                                
                                # Threading kullanarak ana UI'ı bloke etmeden işlemi yap
                                def process_and_save():
                                    # Burada her efekti orijinal görüntüye uygulayabilirsiniz
                                    # Bu basit bir örnek
                                    final_image = self.apply_current_effects_to_original()
                                    final_image.save(save_path)
                                    
                                    # UI thread'inde güncelleme yapmak için after kullan
                                    self.after(100, lambda: self.show_status(f"Yüksek çözünürlüklü görüntü kaydedildi: {os.path.basename(save_path)}"))
                                
                                # Arka planda işlem yap
                                threading.Thread(target=process_and_save, daemon=True).start()
                            else:
                                # Mevcut görüntüyü direk kaydet
                                self.current_image.save(save_path)
                                self.show_status(f"Görüntü kaydedildi: {os.path.basename(save_path)}")
                        
                        # Kaydetme butonları
                        button_frame = ctk.CTkFrame(save_dialog)
                        button_frame.pack(fill="x", padx=20, pady=20)
                        
                        ctk.CTkButton(
                            button_frame, 
                            text="Kaydet",
                            command=on_save
                        ).pack(side="left", padx=10)
                        
                        ctk.CTkButton(
                            button_frame, 
                            text="İptal",
                            command=save_dialog.destroy
                        ).pack(side="right", padx=10)
                        
                        # Dialog kapanana kadar bekle
                        self.wait_window(save_dialog)
                    else:
                        # Orijinal görüntü yoksa veya aynıysa, direkt kaydet
                        self.current_image.save(save_path)
                        save_filename = os.path.basename(save_path)
                        self.show_status(f"Kaydedildi: {save_filename}")
                    
                except Exception as e:
                    print(f"Error saving image: {e}")
                    self.status_label.configure(text=f"Hata: Görüntü kaydedilemedi")
    
    def apply_current_effects_to_original(self):
        """Mevcut efektleri orijinal görüntüye uygula"""
        if not hasattr(self, 'original_image'):
            return self.current_image.copy()
            
        # Bu fonksiyon, tüm mevcut efektleri orijinal görüntüye uygular
        # Bu yalnızca basit bir örnek
        result = self.original_image.copy()
        
        # Temel ayarlamaları uygula
        if hasattr(self, 'brightness_frame'):
            value = self.brightness_frame.get_value()
            if value != 1.0:
                enhancer = ImageEnhance.Brightness(result)
                result = enhancer.enhance(value)
        
        if hasattr(self, 'contrast_frame'):
            value = self.contrast_frame.get_value()
            if value != 1.0:
                enhancer = ImageEnhance.Contrast(result)
                result = enhancer.enhance(value)
        
        if hasattr(self, 'saturation_frame'):
            value = self.saturation_frame.get_value()
            if value != 1.0:
                enhancer = ImageEnhance.Color(result)
                result = enhancer.enhance(value)
        
        # Mevcut efekti uygula
        if self.current_effect and hasattr(self, 'preview_image'):
            # Burada mevcut efekt için tüm parametreleri kullanarak
            # orijinal görüntüye uygulama kodu olmalı
            # Gerçek uygulamada bu daha karmaşık olabilir
            
            # Basit bir örnek - burada gerçek kodunuza göre değişecektir
            if self.current_effect == "sepia":
                intensity = self.effect_params["sepia"]["intensity"]
                if intensity > 0:
                    result = advanced_filters.apply_sepia(result, intensity=intensity)
            # Diğer efektler için de benzer kontroller eklenmelidir
        
        return result
    
    def reset_image(self):
        """Reset to original image"""
        if hasattr(self, 'working_image'):
            # Çalışma görüntüsünü baştan oluştur
            self.current_image = self.working_image.copy()
            self.display_image()
            # Reset sliders
            self.brightness_frame.reset()
            self.contrast_frame.reset()
            self.saturation_frame.reset()
            # Update status
            self.status_label.configure(text="Görüntü orijinaline sıfırlandı")
            
            # Efekt panellerini kapat
            if self.current_effect:
                self.hide_all_effect_controls()
    
    def display_image(self, image=None):
        """Display the current image on the canvas"""
        if image:
            self.current_image = image
        
        if self.current_image:
            # Önceki görüntüyü temizle
            self.canvas.delete("all")
            
            start_time = time.time()
            
            # Görüntüleme için görüntüyü hazırla - performans için
            # Get canvas dimensions
            canvas_width = self.main_frame.winfo_width()
            canvas_height = self.main_frame.winfo_height()
            
            # Eğer görüntü 800x600'den büyükse ve çok fazla ölçekleme gerekiyorsa,
            # görüntüyü işlemeden önce kabaca yeniden boyutlandır, ardından ince ayar yap
            img_width, img_height = self.current_image.size
            
            # Ölçekleme oranını hesapla
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            display_image = None
            
            # Yalnızca gerekirse küçült
            if ratio < 1 or (img_width > 1000 and img_height > 1000):
                # İlk ölçeklendirme adımını çok büyük görüntüler için optimize et
                if img_width > 2000 or img_height > 2000:
                    # İki adımda ölçeklendirme - ilk adımda hızlı bir yöntem kullan
                    intermediate_ratio = min(1000 / img_width, 1000 / img_height)
                    intermediate_width = int(img_width * intermediate_ratio)
                    intermediate_height = int(img_height * intermediate_ratio)
                    
                    # İlk adım için hızlı yeniden boyutlandırma
                    intermediate_image = self.current_image.resize(
                        (intermediate_width, intermediate_height), 
                        Image.Resampling.BILINEAR  # Hızlı, düşük kalite
                    )
                    
                    # İkinci adım için daha kaliteli yeniden boyutlandırma
                    if ratio < intermediate_ratio:
                        display_image = intermediate_image.resize(
                            (new_width, new_height), 
                            Image.Resampling.LANCZOS  # Yüksek kalite
                        )
                    else:
                        display_image = intermediate_image
                else:
                    # Küçük görüntüler için doğrudan kaliteli yeniden boyutlandırma
                    display_image = self.current_image.resize(
                        (new_width, new_height), 
                        Image.Resampling.LANCZOS
                    )
            else:
                # Ölçeklendirme gerekmiyorsa orijinali kullan
                display_image = self.current_image.copy()
            
            # Convert to PhotoImage and keep a reference
            self.photo_image = ImageTk.PhotoImage(display_image)
            
            # Calculate center position
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            # Add image to canvas
            self.canvas.create_image(x, y, anchor="nw", image=self.photo_image)
            
            # Performans ölçümü
            end_time = time.time()
            print(f"Görüntüleme işlemi: {end_time - start_time:.3f} saniye")
    
    def apply_filter(self, filter_name):
        """Temel filtre uygula"""
        if not self.current_image:
            self.show_status("Önce bir resim yükleyin.")
            return
            
        # Mevcut çalışma modunu güncelle
        self.current_effect = filter_name
        
        # Önceki tüm kontrolleri gizle
        self.hide_all_effect_controls()
        
        # Filtre için gerekli kontrolleri göster
        if filter_name == "blur":
            if not hasattr(self, 'blur_controls'):
                self.blur_controls = EffectIntensityFrame(
                    self.effect_control_frame,
                    "Bulanıklık Seviyesi",
                    0, 10, 2.0,
                    lambda v: self.update_effect_param("blur", "radius", v)
                )
            self.blur_controls.grid(row=0, column=0, padx=10, pady=10)
        
        elif filter_name == "sharpen":
            if not hasattr(self, 'sharpen_controls'):
                self.sharpen_controls = EffectIntensityFrame(
                    self.effect_control_frame,
                    "Keskinlik Seviyesi",
                    1, 5, 1.0,
                    lambda v: self.update_effect_param("sharpen", "intensity", v)
                )
            self.sharpen_controls.grid(row=0, column=0, padx=10, pady=10)
        
        elif filter_name == "contour":
            if not hasattr(self, 'contour_controls'):
                self.contour_controls = EffectIntensityFrame(
                    self.effect_control_frame,
                    "Kontur Seviyesi",
                    1, 5, 1.0,
                    lambda v: self.update_effect_param("contour", "intensity", v)
                )
            self.contour_controls.grid(row=0, column=0, padx=10, pady=10)
        
        elif filter_name == "emboss":
            if not hasattr(self, 'emboss_controls'):
                self.emboss_controls = EffectIntensityFrame(
                    self.effect_control_frame,
                    "Kabartma Seviyesi",
                    1, 5, 1.0,
                    lambda v: self.update_effect_param("emboss", "intensity", v)
                )
            self.emboss_controls.grid(row=0, column=0, padx=10, pady=10)
        
        elif filter_name == "bw":
            if not hasattr(self, 'bw_controls'):
                self.bw_controls = EffectIntensityFrame(
                    self.effect_control_frame,
                    "Eşik Değeri",
                    0, 255, 128,
                    lambda v: self.update_effect_param("bw", "threshold", v),
                    integer=True
                )
            self.bw_controls.grid(row=0, column=0, padx=10, pady=10)
        
        elif filter_name == "invert":
            if not hasattr(self, 'invert_controls'):
                self.invert_controls = EffectIntensityFrame(
                    self.effect_control_frame,
                    "Ters Çevirme Gücü",
                    0, 1, 1.0,
                    lambda v: self.update_effect_param("invert", "intensity", v),
                    step_size=0.1
                )
            self.invert_controls.grid(row=0, column=0, padx=10, pady=10)
            
        # Önizleme ve uygulama butonlarını ekle
        self.add_preview_controls()
        self.preview_checkbox.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="w")
        self.apply_effect_btn.grid(row=2, column=0, padx=10, pady=(10, 10), sticky="ew")
        
        # Durumu güncelle
        self.show_status(f"Filtre gücünü ayarlayın ve 'Efekti Uygula' düğmesine tıklayın")
        
        # Önizlemeyi başlat
        self.preview_effect()
    
    def apply_advanced_filter(self, filter_name):
        """Show controls for the selected advanced filter"""
        if not self.current_image:
            return
            
        try:
            # Show the effect controls for the selected filter
            self.show_effect_controls(filter_name)
            
            # Update status
            filter_display = {
                "sepia": "Sepia",
                "cartoon": "Çizgi Film Efekti",
                "vignette": "Vinyet Efekti",
                "pixelate": "Pikselleştirme",
                "red_splash": "Renk Sıçratma",
                "oil": "Yağlı Boya Efekti",
                "noise": "Gürültü Efekti"
            }.get(filter_name, filter_name)
            
            self.status_label.configure(text=f"Adjust {filter_display} settings and click Apply")
            
        except Exception as e:
            print(f"Error setting up filter controls {filter_name}: {e}")
            self.status_label.configure(text=f"Error setting up filter controls")
    
    def update_brightness(self, value):
        """Adjust image brightness"""
        if self.original_image:
            # Apply all adjustments in sequence
            self.current_image = ImageEnhance.Brightness(self.original_image).enhance(value)
            # Apply contrast
            self.current_image = ImageEnhance.Contrast(self.current_image).enhance(self.contrast_frame.get_value())
            # Apply saturation
            self.current_image = ImageEnhance.Color(self.current_image).enhance(self.saturation_frame.get_value())
            self.display_image()
            self.status_label.configure(text=f"Brightness: {value:.2f}")
    
    def update_contrast(self, value):
        """Adjust image contrast"""
        if self.original_image:
            # Apply all adjustments in sequence
            self.current_image = ImageEnhance.Brightness(self.original_image).enhance(self.brightness_frame.get_value())
            # Apply contrast
            self.current_image = ImageEnhance.Contrast(self.current_image).enhance(value)
            # Apply saturation
            self.current_image = ImageEnhance.Color(self.current_image).enhance(self.saturation_frame.get_value())
            self.display_image()
            self.status_label.configure(text=f"Contrast: {value:.2f}")
    
    def update_saturation(self, value):
        """Adjust image saturation"""
        if self.original_image:
            # Apply all adjustments in sequence
            self.current_image = ImageEnhance.Brightness(self.original_image).enhance(self.brightness_frame.get_value())
            # Apply contrast
            self.current_image = ImageEnhance.Contrast(self.current_image).enhance(self.contrast_frame.get_value())
            # Apply saturation
            self.current_image = ImageEnhance.Color(self.current_image).enhance(value)
            self.display_image()
            self.status_label.configure(text=f"Saturation: {value:.2f}")
    
    def rotate_image(self, direction):
        """Rotate the image left or right"""
        if not self.current_image:
            return
            
        try:
            if direction == "left":
                self.current_image = self.current_image.rotate(90, expand=True)
                self.status_label.configure(text="Rotated left")
            elif direction == "right":
                self.current_image = self.current_image.rotate(-90, expand=True)
                self.status_label.configure(text="Rotated right")
                
            self.display_image()
        except Exception as e:
            print(f"Error rotating image: {e}")
            self.status_label.configure(text="Error rotating image")
    
    def flip_image(self, direction):
        """Flip the image horizontally or vertically"""
        if not self.current_image:
            return
            
        try:
            if direction == "horizontal":
                self.current_image = ImageOps.mirror(self.current_image)
                self.status_label.configure(text="Flipped horizontally")
            elif direction == "vertical":
                self.current_image = ImageOps.flip(self.current_image)
                self.status_label.configure(text="Flipped vertically")
                
            self.display_image()
        except Exception as e:
            print(f"Error flipping image: {e}")
            self.status_label.configure(text="Error flipping image")
    
    def update_canvas_size(self, event):
        """Pencere boyutu değiştiğinde tuvali güncelle"""
        self.display_image()
        
        # Görüntü yoksa, karşılama mesajını ortala
        if not self.current_image:
            self.canvas.delete("all")
            
            # Karşılama mesajı ve Logo
            center_x = self.canvas.winfo_width() // 2
            center_y = self.canvas.winfo_height() // 2
            
            # Karşılama paneli arka planı
            panel_width = 400
            panel_height = 200
            
            # Tema için tek bir renk kullan
            panel_bg = "#2b2b2b"  # Koyu tema için varsayılan renk
            if ctk.get_appearance_mode() == "light":
                panel_bg = "#ebebeb"  # Açık tema için varsayılan renk
            
            self.canvas.create_rectangle(
                center_x - panel_width//2, center_y - panel_height//2,
                center_x + panel_width//2, center_y + panel_height//2,
                fill=panel_bg,
                outline=ACCENT_COLOR,
                width=2,
                stipple="gray50"
            )
            
            # Uygulama başlığı
            self.canvas.create_text(
                center_x, center_y - 40,
                text="Pro Image Editor",
                fill=ACCENT_COLOR, 
                font=TITLE_FONT
            )
            
            # Karşılama mesajı
            self.canvas.create_text(
                center_x, center_y + 10,
                text="Görüntü düzenlemeye başlamak için bir dosya açın",
                fill="white", 
                font=LABEL_FONT
            )
            
            # Dosya aç talimatı
            self.canvas.create_text(
                center_x, center_y + 50,
                text="Sol panelden 'Dosya Aç' düğmesine tıklayın",
                fill="light gray", 
                font=SMALL_FONT
            )

    def create_effect_controls(self):
        """Efekt yoğunluk kontrol kaydırıcılarını oluştur"""
        # Efekt kontrolleri için çerçeve oluştur - sabit renk değeri kullan
        border_color = "#444444"  # Koyu tema için varsayılan border rengi
        if ctk.get_appearance_mode() == "light":
            border_color = "#cccccc"  # Açık tema için varsayılan border rengi
            
        self.effect_control_frame = ctk.CTkFrame(
            self.scrollable_frame,
            corner_radius=10,
            border_width=1,
            border_color=border_color
        )
        self.effect_control_frame.grid(row=30, column=0, padx=15, pady=15, sticky="ew")
        self.effect_control_frame.grid_columnconfigure(0, weight=1)
        
        # Başlık bölümü
        self.effect_title_frame = ctk.CTkFrame(self.effect_control_frame, fg_color="transparent")
        self.effect_title_frame.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="ew")
        
        self.effect_title = ctk.CTkLabel(
            self.effect_title_frame, 
            text="Efekt Ayarları", 
            font=SUBTITLE_FONT,
            text_color=ACCENT_COLOR
        )
        self.effect_title.pack(anchor="center")
        
        # Efekt kontrol kaydırıcıları burada oluşturulacak
        # Her efekt için ayrı bir kontrol çerçevesi oluşturalım
        
        # ------- TEMEL FİLTRELER -------
        
        # Blur controls
        self.blur_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Bulanıklaştırma Düzeyi", 
            0.5, 10.0, 2.0, 
            lambda v: self.update_effect_param("blur", "radius", v),
            step_size=0.5
        )
        
        # Sharpen controls
        self.sharpen_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Keskinleştirme Düzeyi", 
            0.1, 3.0, 1.0, 
            lambda v: self.update_effect_param("sharpen", "intensity", v),
            step_size=0.1
        )
        
        # Contour controls
        self.contour_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Kontur Yoğunluğu", 
            0.1, 2.0, 1.0, 
            lambda v: self.update_effect_param("contour", "intensity", v),
            step_size=0.1
        )
        
        # Emboss controls
        self.emboss_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Kabartma Yoğunluğu", 
            0.1, 2.0, 1.0, 
            lambda v: self.update_effect_param("emboss", "intensity", v),
            step_size=0.1
        )
        
        # Black & White controls
        self.bw_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Siyah-Beyaz Eşiği", 
            0, 255, 128, 
            lambda v: self.update_effect_param("bw", "threshold", v),
            step_size=1,
            integer=True
        )
        
        # Invert controls
        self.invert_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Ters Çevirme Opaklığı", 
            0.1, 1.0, 1.0, 
            lambda v: self.update_effect_param("invert", "intensity", v),
            step_size=0.05
        )
        
        # ------- GELİŞMİŞ FİLTRELER -------
        
        # Sepia controls
        self.sepia_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Sepya Yoğunluğu", 
            0.1, 1.0, 1.0, 
            lambda v: self.update_effect_param("sepia", "intensity", v),
            step_size=0.05
        )
        
        # Cartoon controls
        self.cartoon_edge_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Kenar Belirginliği", 
            1, 10, 3, 
            lambda v: self.update_effect_param("cartoon", "edge_intensity", v),
            step_size=1,
            integer=True
        )
        self.cartoon_simplify_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Renk Sadeleştirme", 
            2, 20, 5, 
            lambda v: self.update_effect_param("cartoon", "simplify", int(v)),
            step_size=1,
            integer=True
        )
        
        # Vignette controls
        self.vignette_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Vinyetleme Miktarı", 
            0.1, 1.0, 0.5, 
            lambda v: self.update_effect_param("vignette", "amount", v),
            step_size=0.05
        )
        
        # Pixelate controls
        self.pixelate_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Piksel Boyutu", 
            2, 50, 10, 
            lambda v: self.update_effect_param("pixelate", "pixel_size", int(v)),
            step_size=1,
            integer=True
        )
        
        # Color Splash controls
        self.splash_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Efekt Yoğunluğu", 
            0.1, 1.0, 1.0, 
            lambda v: self.update_effect_param("red_splash", "intensity", v),
            step_size=0.05
        )
        
        # Color Splash channel selection
        self.splash_channel_frame = ctk.CTkFrame(self.effect_control_frame, fg_color="transparent")
        color_label = ctk.CTkLabel(
            self.splash_channel_frame, 
            text="Renk Kanalı:",
            font=LABEL_FONT
        )
        color_label.pack(side="left", padx=10, pady=5)
        
        # Kanal seçimi için değişken
        self.splash_channel_var = ctk.StringVar(value="red")
        
        # Kanal radyo butonları
        channel_frame = ctk.CTkFrame(self.splash_channel_frame, fg_color="transparent")
        channel_frame.pack(side="right", fill="x", expand=True, padx=10)
        
        self.splash_red_btn = ctk.CTkRadioButton(
            channel_frame, 
            text="Kırmızı", 
            variable=self.splash_channel_var, 
            value="red",
            command=lambda: self.update_effect_param("red_splash", "color", "red"),
            fg_color=ACCENT_COLOR
        )
        self.splash_red_btn.pack(side="left", padx=5, pady=5)
        
        self.splash_green_btn = ctk.CTkRadioButton(
            channel_frame, 
            text="Yeşil", 
            variable=self.splash_channel_var, 
            value="green",
            command=lambda: self.update_effect_param("red_splash", "color", "green"),
            fg_color=ACCENT_COLOR
        )
        self.splash_green_btn.pack(side="left", padx=5, pady=5)
        
        self.splash_blue_btn = ctk.CTkRadioButton(
            channel_frame, 
            text="Mavi", 
            variable=self.splash_channel_var, 
            value="blue",
            command=lambda: self.update_effect_param("red_splash", "color", "blue"),
            fg_color=ACCENT_COLOR
        )
        self.splash_blue_btn.pack(side="left", padx=5, pady=5)
        
        # Oil Paint controls
        self.oil_brush_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Fırça Boyutu", 
            1, 10, 3, 
            lambda v: self.update_effect_param("oil", "brush_size", int(v)),
            step_size=1,
            integer=True
        )
        self.oil_levels_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Renk Düzeyleri", 
            3, 20, 8, 
            lambda v: self.update_effect_param("oil", "levels", int(v)),
            step_size=1,
            integer=True
        )
        
        # Noise controls
        self.noise_controls = EffectIntensityFrame(
            self.effect_control_frame, 
            "Gürültü Miktarı", 
            0.1, 1.0, 0.5, 
            lambda v: self.update_effect_param("noise", "amount", v),
            step_size=0.05
        )
        
        # Önizleme onay kutusu
        self.preview_frame = ctk.CTkFrame(self.effect_control_frame, fg_color="transparent")
        
        self.preview_var = ctk.BooleanVar(value=True)
        self.preview_checkbox = ctk.CTkCheckBox(
            self.preview_frame, 
            text="Önizleme", 
            variable=self.preview_var,
            command=self.toggle_preview,
            checkbox_width=24,
            checkbox_height=24,
            corner_radius=4,
            fg_color=ACCENT_COLOR,
            hover_color=SECONDARY_COLOR,
            font=BUTTON_FONT
        )
        self.preview_checkbox.pack(side="left", padx=10, pady=5)
        
        # Efekt uygulama butonu
        self.apply_effect_btn = ctk.CTkButton(
            self.effect_control_frame, 
            text="Efekti Uygula",
            command=self.apply_effect,
            height=40,
            corner_radius=8,
            fg_color=SUCCESS_COLOR,
            hover_color="#247545",
            font=BUTTON_FONT
        )
        
        # İptal butonu
        self.cancel_effect_btn = ctk.CTkButton(
            self.effect_control_frame, 
            text="İptal",
            command=self.hide_all_effect_controls,
            height=40,
            corner_radius=8,
            fg_color=ERROR_COLOR,
            hover_color="#933232",
            font=BUTTON_FONT
        )
        
        # Butonları bir frame içinde düzenle
        self.effect_button_frame = ctk.CTkFrame(self.effect_control_frame, fg_color="transparent")
        self.effect_button_frame.grid_columnconfigure(0, weight=1)
        self.effect_button_frame.grid_columnconfigure(1, weight=1)
        
        self.apply_effect_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew", in_=self.effect_button_frame)
        self.cancel_effect_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew", in_=self.effect_button_frame)
    
    def toggle_preview(self, is_preview=None):
        """Preview seçeneğini aç/kapa"""
        if is_preview is None:
            is_preview = self.preview_var.get()
            
        if is_preview:
            # Önizleme açıldığında orijinal görüntüyü sakla
            if not hasattr(self, 'pre_preview_image'):
                self.pre_preview_image = self.current_image.copy()
            
            # Önizleme işlemini arka planda başlat
            self.apply_effect(is_preview=True)
        else:
            # Önizleme kapalıysa, orijinal görüntüyü göster
            if hasattr(self, 'pre_preview_image'):
                self.current_image = self.pre_preview_image.copy()
                self.display_image(self.current_image)
                if hasattr(self, 'pre_preview_image'):
                    del self.pre_preview_image
                    
    def apply_effect(self, is_preview=False):
        """Efekti uygula ve sonucu kaydet"""
        if not self.current_image or not self.current_effect:
            self.show_status("Efekt uygulanamadı: Görüntü veya efekt seçilmemiş.")
            return
            
        try:
            # Önizleme için sadece yeni görüntüyü göster
            if is_preview:
                # İşlemin başladığını bildir
                self.show_status(f"{self.current_effect} efekti önizleniyor...")
                
                # Büyük görüntüler için gecikmeli işleme kullan
                if hasattr(self, 'preview_thread') and self.preview_thread.is_alive():
                    print("Önceki önizleme iptal edildi")
                    # Önceki önizleme hala çalışıyor, yeni bir tane başlatıyoruz
                    # Burada bir iptal mekanizması olabilir, ama basit tutuyoruz
                    pass
                    
                # Ağır efektler için asenkron işleme kullan
                heavy_effects = ["oil", "cartoon", "noise"]
                
                if self.current_effect in heavy_effects and (
                    self.current_image.width > 800 or self.current_image.height > 800
                ):
                    # Ağır efektler için arka planda işleme yap
                    self.preview_thread = threading.Thread(
                        target=self._threaded_preview_effect,
                        daemon=True
                    )
                    self.preview_thread.start()
                else:
                    # Hafif efektler için normal işleme
                    self.preview_effect()
                    
                return
            
            # Önizleme görüntüsünü mevcut görüntü olarak ayarla
            if self.preview_image:
                self.current_image = self.preview_image.copy()
                self.display_image(self.current_image)
                self.show_status(f"{self.current_effect} efekti uygulandı.")
            else:
                self.show_status("Önizleme görüntüsü oluşturulmadı.")
        except Exception as e:
            self.show_status(f"Efekt uygulama hatası: {e}")
    
    def _threaded_preview_effect(self):
        """Arka planda çalışacak önizleme işlevidir"""
        try:
            # Orijinal görüntüden başla
            if hasattr(self, 'pre_preview_image'):
                # Yüksek çözünürlüklü görüntüler için daha küçük bir sürüm kullan
                img = self.pre_preview_image.copy()
                
                # Görüntü büyükse ve ağır bir efekt ise, işlem için küçültme
                if (img.width > 800 or img.height > 800) and self.current_effect in ["oil", "cartoon"]:
                    # İşleme için görüntüyü küçült
                    ratio = min(800 / img.width, 800 / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"Efekt için görüntü boyutu küçültüldü: {new_width}x{new_height}")
                
                # Efekti uygula (aynı kodu burada yeniden tanımlamak yerine process_effect kullanıyoruz)
                img = self.process_effect(img)
                
                # Sonucu ana thread'e gönder
                self.after(100, lambda: self._update_preview_result(img))
            
        except Exception as e:
            print(f"Arka plan önizleme hatası: {e}")
            self.after(100, lambda: self.show_status(f"Önizleme hatası: {e}"))
    
    def _update_preview_result(self, result_image):
        """Arka plan işlemi tamamlandığında sonucu günceller"""
        if result_image:
            self.preview_image = result_image
            self.display_image(result_image)
            self.show_status(f"{self.current_effect} önizlemesi tamamlandı")
    
    def process_effect(self, img):
        """Verilen görüntüye mevcut efekti uygular"""
        if not self.current_effect:
            return img
            
        # Efektin türüne göre işlem uygula - preview_effect'ten kodu kopyaladık
        if self.current_effect == "brightness":
            value = self.brightness_frame.get_value()
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(value)
            
        elif self.current_effect == "contrast":
            value = self.contrast_frame.get_value()
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(value)
            
        elif self.current_effect == "saturation":
            value = self.saturation_frame.get_value()
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(value)
        
        # Diğer tüm efektler buraya eklenmeli, ancak kod tekrarı önlemek için
        # preview_effect metodunun mevcut içeriğini kopyalayın
            
        # Burada sadece birkaç örnek gösteriyoruz
        elif self.current_effect == "sepia":
            intensity = self.effect_params["sepia"]["intensity"]
            # Düşük yoğunluk değerleri için de çalışmasını sağla
            if intensity > 0:
                # Orijinal ve tamamen sepia uygulanmış görüntü arasında blend yapalım
                sepia_img = advanced_filters.apply_sepia(img.copy(), intensity=1.0)
                img = Image.blend(img, sepia_img, intensity)
            
        elif self.current_effect == "noise":
            amount = self.effect_params["noise"]["amount"]
            # Düşük yoğunluk değerleri için de çalışmasını sağla
            if amount > 0:
                noise_img = advanced_filters.apply_noise(img.copy(), amount=max(0.1, amount))
                # Eğer amount 0.1'den küçükse, blend kullanarak daha az belirgin hale getir
                if amount < 0.1:
                    blend_factor = amount / 0.1  # 0-0.1 aralığını 0-1 aralığına ölçeklendir
                    img = Image.blend(img, noise_img, blend_factor)
                else:
                    img = noise_img
            
        # Diğer efektler buraya eklenebilir
            
        return img
            
    def preview_effect(self):
        """Seçili efektin önizlemesini göster"""
        if not self.current_image or not self.current_effect:
            return
            
        # Önizleme aktif değilse, orjinal görüntüyü göster
        if not self.preview_var.get():
            self.toggle_preview(False)
            return
            
        # Debug
        print(f"Önizleme: {self.current_effect} efekti, parametreler: {self.effect_params.get(self.current_effect, {})}")
        
        # Orijinal görüntüden başla (önizleme öncesi orijinal görüntü)
        if hasattr(self, 'pre_preview_image'):
            # Önizleme için saklanmış olan orijinal görüntüyü kullan
            img = self.pre_preview_image.copy()
        else:
            # Eğer saklanmış bir orijinal görüntü yoksa mevcut görüntüyü kullan
            img = self.current_image.copy()
            # Ve bunu sakla
            self.pre_preview_image = self.current_image.copy()
        
        # Efekti uygula
        img = self.process_effect(img)
        
        # Değiştirilmiş görüntüyü önizleme olarak ayarla        
        self.preview_image = img
        self.display_image(self.preview_image)

    def hide_all_effect_controls(self):
        """Hide all effect controls"""
        for widget in self.effect_control_frame.winfo_children():
            widget.grid_forget()
            
        # Reset preview if active
        if hasattr(self, 'preview_var') and self.preview_var.get():
            self.preview_var.set(False)
            if hasattr(self, 'pre_preview_image'):
                self.current_image = self.pre_preview_image.copy()
                del self.pre_preview_image
                self.display_image()
        
        self.effect_control_frame.grid_forget()
        self.current_effect = None
        
    def update_effect_param(self, effect, param, value):
        """Update effect parameter value"""
        # Parametreyi güncelle
        self.effect_params[effect][param] = value
        
        # Debug çıktısı ekleyelim
        print(f"Parametre güncellendi: {effect}.{param} = {value}")
        
        # If preview is active, update the preview
        if hasattr(self, 'preview_var') and self.preview_var.get():
            # Önizlemeyi yeniden oluştur
            self.apply_effect(is_preview=True)

    def show_effect_controls(self, effect_name):
        """Belirtilen efekt için kontrolleri göster"""
        # Önce tüm kontrolleri gizle
        self.hide_all_effect_controls()
        
        # Mevcut efekti ayarla
        self.current_effect = effect_name
        
        # Efekt başlığını ayarla
        effect_titles = {
            "sepia": "Sepya Efekti",
            "cartoon": "Çizgi Film Efekti",
            "vignette": "Vinyet Efekti",
            "pixelate": "Pikselleştirme",
            "red_splash": "Renk Sıçratma",
            "oil": "Yağlı Boya Efekti",
            "noise": "Gürültü Efekti",
            "blur": "Bulanıklaştırma",
            "sharpen": "Keskinleştirme",
            "contour": "Kontur",
            "emboss": "Kabartma",
            "bw": "Siyah-Beyaz",
            "invert": "Negatif"
        }
        
        self.effect_title.configure(text=effect_titles.get(effect_name, "Efekt Ayarları"))
        
        # Efekt türüne göre kontrolleri göster
        if effect_name == "sepia":
            self.sepia_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "cartoon":
            self.cartoon_edge_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            self.cartoon_simplify_controls.grid(row=20, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "vignette":
            self.vignette_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "pixelate":
            self.pixelate_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "red_splash":
            self.splash_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            self.splash_channel_frame.grid(row=20, column=0, padx=15, pady=10, sticky="ew")
            # Mevcut ayara göre radyo düğmesini güncelle
            current_color = self.effect_params["red_splash"].get("color", "red")
            self.splash_channel_var.set(current_color)
            
        elif effect_name == "oil":
            self.oil_brush_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            self.oil_levels_controls.grid(row=20, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "noise":
            self.noise_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "blur":
            self.blur_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "sharpen":
            self.sharpen_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "contour":
            self.contour_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "emboss":
            self.emboss_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "bw":
            self.bw_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
            
        elif effect_name == "invert":
            self.invert_controls.grid(row=10, column=0, padx=15, pady=10, sticky="ew")
        
        # Önizleme onay kutusunu göster
        self.preview_frame.grid(row=90, column=0, padx=15, pady=(15, 5), sticky="ew")
        
        # Buton çerçevesini göster
        self.effect_button_frame.grid(row=100, column=0, padx=15, pady=(5, 15), sticky="ew")
        
        # Kontrol çerçevesini göster
        self.effect_control_frame.grid(row=30, column=0, padx=15, pady=15, sticky="ew")
        
        # Efekti önizle
        self.preview_var.set(True)
        self.toggle_preview(True)
        
        # Durum mesajını güncelle
        self.show_status(f"{effect_titles.get(effect_name, 'Efekt')} ayarlarını düzenleyin")
    
    def add_preview_controls(self):
        """Önizleme kontrolleri oluştur"""
        if not self.preview_controls_added:
            preview_frame = ctk.CTkFrame(self.effect_control_frame)
            preview_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            
            self.preview_var = ctk.BooleanVar(value=True)
            preview_check = ctk.CTkCheckBox(preview_frame, text="Önizleme", 
                                             variable=self.preview_var,
                                             command=self.toggle_preview)
            preview_check.grid(row=0, column=0, padx=5)
            
            apply_button = ctk.CTkButton(preview_frame, text="Uygula", 
                                       command=self.apply_effect)
            apply_button.grid(row=0, column=1, padx=5)
            
            cancel_button = ctk.CTkButton(preview_frame, text="İptal", 
                                        command=lambda: self.hide_all_effect_controls())
            cancel_button.grid(row=0, column=2, padx=5)
            
            self.preview_controls_frame = preview_frame
            self.preview_controls_added = True

    def show_status(self, message):
        """Durum çubuğu mesajını güncelle"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
            
            # Durum mesajını 5 saniye sonra temizle
            self.after(5000, lambda: self.status_label.configure(text="Hazır") if self.status_label.cget("text") == message else None)


if __name__ == "__main__":
    app = ImageEditor()
    
    # Bind window resize event to update canvas
    app.bind("<Configure>", app.update_canvas_size)
    
    app.mainloop() 