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
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Maksimum önizleme boyutu - daha büyük görüntüler önizleme için bu boyuta küçültülecek
MAX_PREVIEW_WIDTH = 1200
MAX_PREVIEW_HEIGHT = 800

class EffectIntensityFrame(ctk.CTkFrame):
    """A frame containing sliders to control filter intensity"""
    def __init__(self, parent, title, min_val, max_val, default_val, callback, step_size=None, integer=False, **kwargs):
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
        
        # Create title label
        self.title_label = ctk.CTkLabel(self, text=title)
        self.title_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        
        # Create slider
        self.slider = ctk.CTkSlider(self, from_=min_val, to=max_val, number_of_steps=self.number_of_steps, command=self.on_change)
        self.slider.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")
        self.slider.set(default_val)
        
        # Create value label
        self.value_str = self._format_value(default_val)
        self.value_label = ctk.CTkLabel(self, text=self.value_str, width=40)
        self.value_label.grid(row=1, column=1, padx=(0, 5), pady=(0, 5))
        
        # Create controls for direct value input
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.controls_frame.grid_columnconfigure(1, weight=1)
        
        # Add preset buttons
        self.min_btn = ctk.CTkButton(self.controls_frame, text="Min", width=40, 
                                    command=lambda: self.set_value(min_val), 
                                    font=ctk.CTkFont(size=12))
        self.min_btn.grid(row=0, column=0, padx=2, pady=2, sticky="w")
        
        self.max_btn = ctk.CTkButton(self.controls_frame, text="Max", width=40, 
                                    command=lambda: self.set_value(max_val), 
                                    font=ctk.CTkFont(size=12))
        self.max_btn.grid(row=0, column=1, padx=2, pady=2, sticky="w")
        
        self.default_btn = ctk.CTkButton(self.controls_frame, text="Varsayılan", width=70, 
                                       command=self.reset, 
                                       font=ctk.CTkFont(size=12))
        self.default_btn.grid(row=0, column=2, padx=2, pady=2, sticky="e")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
    
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
        self.title("Advanced Image Editor")
        self.geometry("1300x800")
        self.minsize(900, 700)
        
        # Set icon
        self.set_app_icon()
        
        # Variables
        self.current_image = None
        self.original_image = None
        self.image_path = None
        self.filename = None
        self.current_effect = None
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
        self.hide_effect_controls()
        
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
        # Main frame structure - use weight to ensure proper scaling
        self.grid_columnconfigure(0, weight=1)  # sidebar
        self.grid_columnconfigure(1, weight=3)  # canvas
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar frame with scrollable content
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create scrollable frame for sidebar - make it fill the entire sidebar
        self.scrollable_frame = ctk.CTkScrollableFrame(self.sidebar_frame, width=250)
        self.scrollable_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        
        # App title
        self.logo_label = ctk.CTkLabel(self.scrollable_frame, text="Image Editor Pro", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(10, 10))
        
        # File operations section
        self.file_frame = ctk.CTkFrame(self.scrollable_frame)
        self.file_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)
        self.file_frame.grid_columnconfigure(1, weight=1)
        
        # Add open file button
        self.open_button = ctk.CTkButton(self.file_frame, text="Open Image", command=self.open_image)
        self.open_button.grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        
        # Add save file button
        self.save_button = ctk.CTkButton(self.file_frame, text="Save Image", command=self.save_image)
        self.save_button.grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        
        # Add reset button
        self.reset_button = ctk.CTkButton(self.scrollable_frame, text="Reset Image", command=self.reset_image)
        self.reset_button.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        # Create basic filter section
        self.filter_label = ctk.CTkLabel(self.scrollable_frame, text="Basic Filters", font=ctk.CTkFont(size=16, weight="bold"))
        self.filter_label.grid(row=3, column=0, padx=10, pady=(15, 5))
        
        # Basic filter buttons frame
        self.basic_filter_frame = ctk.CTkFrame(self.scrollable_frame)
        self.basic_filter_frame.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        
        # Configure columns for better distribution
        for i in range(3):
            self.basic_filter_frame.grid_columnconfigure(i, weight=1)
        
        # Basic filter buttons (2x3 grid)
        filters = [
            ("Blur", lambda: self.apply_filter("blur")),
            ("Sharpen", lambda: self.apply_filter("sharpen")),
            ("Contour", lambda: self.apply_filter("contour")),
            ("Emboss", lambda: self.apply_filter("emboss")),
            ("B&W", lambda: self.apply_filter("bw")),
            ("Invert", lambda: self.apply_filter("invert"))
        ]
        
        for i, (name, command) in enumerate(filters):
            btn = ctk.CTkButton(self.basic_filter_frame, text=name, command=command, width=70, height=28)
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
        
        # Create advanced filter section
        self.adv_filter_label = ctk.CTkLabel(self.scrollable_frame, text="Advanced Filters", font=ctk.CTkFont(size=16, weight="bold"))
        self.adv_filter_label.grid(row=5, column=0, padx=10, pady=(15, 5))
        
        # Advanced filter buttons frame
        self.adv_filter_frame = ctk.CTkFrame(self.scrollable_frame)
        self.adv_filter_frame.grid(row=6, column=0, padx=5, pady=5, sticky="ew")
        
        # Configure columns for better distribution
        for i in range(3):
            self.adv_filter_frame.grid_columnconfigure(i, weight=1)
        
        # Advanced filter buttons (3x3 grid with responsive layout)
        adv_filters = [
            ("Sepia", lambda: self.apply_advanced_filter("sepia")),
            ("Cartoon", lambda: self.apply_advanced_filter("cartoon")),
            ("Vignette", lambda: self.apply_advanced_filter("vignette")),
            ("Pixelate", lambda: self.apply_advanced_filter("pixelate")),
            ("Red Only", lambda: self.apply_advanced_filter("red_splash")),
            ("Oil Paint", lambda: self.apply_advanced_filter("oil")),
            ("Noise", lambda: self.apply_advanced_filter("noise"))
        ]
        
        for i, (name, command) in enumerate(adv_filters):
            btn = ctk.CTkButton(self.adv_filter_frame, text=name, command=command, width=70, height=28)
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky="ew")
        
        # Create adjustments section
        self.adjust_label = ctk.CTkLabel(self.scrollable_frame, text="Adjustments", font=ctk.CTkFont(size=16, weight="bold"))
        self.adjust_label.grid(row=7, column=0, padx=10, pady=(15, 5))
        
        # Brightness slider
        self.brightness_frame = EffectIntensityFrame(self.scrollable_frame, "Brightness", 0.1, 2.0, 1.0, self.update_brightness)
        self.brightness_frame.grid(row=8, column=0, padx=5, pady=(5, 0), sticky="ew")
        
        # Contrast slider
        self.contrast_frame = EffectIntensityFrame(self.scrollable_frame, "Contrast", 0.1, 2.0, 1.0, self.update_contrast)
        self.contrast_frame.grid(row=9, column=0, padx=5, pady=(5, 0), sticky="ew")
        
        # Saturation slider
        self.saturation_frame = EffectIntensityFrame(self.scrollable_frame, "Saturation", 0.0, 2.0, 1.0, self.update_saturation)
        self.saturation_frame.grid(row=10, column=0, padx=5, pady=(5, 0), sticky="ew")
        
        # Rotation section
        self.rotate_label = ctk.CTkLabel(self.scrollable_frame, text="Rotate & Flip", font=ctk.CTkFont(size=16, weight="bold"))
        self.rotate_label.grid(row=11, column=0, padx=10, pady=(15, 5))
        
        # Rotation buttons frame
        self.rotate_frame = ctk.CTkFrame(self.scrollable_frame)
        self.rotate_frame.grid(row=12, column=0, padx=5, pady=5, sticky="ew")
        
        # Configure columns for equal distribution
        for i in range(4):
            self.rotate_frame.grid_columnconfigure(i, weight=1)
        
        # Create rotation buttons
        self.rotate_left = ctk.CTkButton(self.rotate_frame, text="↺", width=40, command=lambda: self.rotate_image("left"))
        self.rotate_left.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.rotate_right = ctk.CTkButton(self.rotate_frame, text="↻", width=40, command=lambda: self.rotate_image("right"))
        self.rotate_right.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        self.flip_h = ctk.CTkButton(self.rotate_frame, text="↔", width=40, command=lambda: self.flip_image("horizontal"))
        self.flip_h.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        self.flip_v = ctk.CTkButton(self.rotate_frame, text="↕", width=40, command=lambda: self.flip_image("vertical"))
        self.flip_v.grid(row=0, column=3, padx=2, pady=2, sticky="ew")
        
        # Status label
        self.status_label = ctk.CTkLabel(self.scrollable_frame, text="Ready", height=20)
        self.status_label.grid(row=13, column=0, padx=5, pady=(15, 5), sticky="ew")
        
        # Main content area (image canvas)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create canvas for image
        self.canvas = ctk.CTkCanvas(self.main_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Display welcome message
        self.canvas.create_text(
            self.winfo_width() // 2, self.winfo_height() // 2,
            text="Open an image to begin editing",
            fill="white", font=("Helvetica", 16)
        )
        
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
                self.hide_effect_controls()
    
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
        """Update the canvas when window size changes"""
        self.display_image()

    def create_effect_controls(self):
        """Create the effect intensity control sliders"""
        # Create frame for effect controls
        self.effect_control_frame = ctk.CTkFrame(self.scrollable_frame)
        self.effect_control_frame.grid(row=20, column=0, padx=10, pady=10, sticky="ew")
        self.effect_control_frame.grid_columnconfigure(0, weight=1)
        
        # Section title
        self.effect_title = ctk.CTkLabel(self.effect_control_frame, text="Efekt Ayarları", 
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.effect_title.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
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
            "Sepia Yoğunluğu", 
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
        self.splash_channel_frame = ctk.CTkFrame(self.effect_control_frame)
        self.splash_channel_label = ctk.CTkLabel(self.splash_channel_frame, text="Renk Kanalı:")
        self.splash_channel_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Create channel radio buttons with variable
        self.splash_channel_var = ctk.StringVar(value="red")
        
        self.splash_red_btn = ctk.CTkRadioButton(
            self.splash_channel_frame, text="Kırmızı", 
            variable=self.splash_channel_var, value="red",
            command=lambda: self.update_effect_param("red_splash", "color", "red")
        )
        self.splash_red_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.splash_green_btn = ctk.CTkRadioButton(
            self.splash_channel_frame, text="Yeşil", 
            variable=self.splash_channel_var, value="green",
            command=lambda: self.update_effect_param("red_splash", "color", "green")
        )
        self.splash_green_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.splash_blue_btn = ctk.CTkRadioButton(
            self.splash_channel_frame, text="Mavi", 
            variable=self.splash_channel_var, value="blue",
            command=lambda: self.update_effect_param("red_splash", "color", "blue")
        )
        self.splash_blue_btn.grid(row=0, column=3, padx=5, pady=5)
        
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
        
        # Preview checkbox
        self.preview_frame = ctk.CTkFrame(self.effect_control_frame)
        self.preview_frame.grid(row=90, column=0, padx=5, pady=(10, 2), sticky="ew")
        
        self.preview_var = ctk.BooleanVar(value=False)
        self.preview_checkbox = ctk.CTkCheckBox(
            self.preview_frame, text="Önizleme", 
            variable=self.preview_var,
            command=self.toggle_preview
        )
        self.preview_checkbox.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Apply button
        self.apply_effect_btn = ctk.CTkButton(
            self.effect_control_frame, 
            text="Efekti Uygula", 
            command=self.apply_effect,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.apply_effect_btn.grid(row=100, column=0, padx=10, pady=10, sticky="ew")
        
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
        """Show the controls for the specified effect"""
        # Hide all controls first
        self.hide_effect_controls()
        
        # Set current effect
        self.current_effect = effect_name
        
        # Set effect title
        effect_titles = {
            "sepia": "Sepia Efekti",
            "cartoon": "Çizgi Film Efekti",
            "vignette": "Vinyet Efekti",
            "pixelate": "Pikselleştirme",
            "red_splash": "Renk Sıçratma",
            "oil": "Yağlı Boya Efekti",
            "noise": "Gürültü Efekti"
        }
        
        self.effect_title.configure(text=effect_titles.get(effect_name, "Efekt Ayarları"))
        
        # Show controls based on effect type
        if effect_name == "sepia":
            self.sepia_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
            
        elif effect_name == "cartoon":
            self.cartoon_edge_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
            self.cartoon_simplify_controls.grid(row=20, column=0, padx=5, pady=5, sticky="ew")
            
        elif effect_name == "vignette":
            self.vignette_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
            
        elif effect_name == "pixelate":
            self.pixelate_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
            
        elif effect_name == "red_splash":
            self.splash_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
            self.splash_channel_frame.grid(row=20, column=0, padx=5, pady=5, sticky="ew")
            # Update radio button to match current setting
            current_color = self.effect_params["red_splash"].get("color", "red")
            self.splash_channel_var.set(current_color)
            
        elif effect_name == "oil":
            self.oil_brush_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
            self.oil_levels_controls.grid(row=20, column=0, padx=5, pady=5, sticky="ew")
            
        elif effect_name == "noise":
            self.noise_controls.grid(row=10, column=0, padx=5, pady=5, sticky="ew")
        
        # Show preview checkbox
        self.preview_frame.grid(row=90, column=0, padx=5, pady=(10, 2), sticky="ew")
        
        # Show apply button
        self.apply_effect_btn.grid(row=100, column=0, padx=10, pady=10, sticky="ew")
        
        # Show control frame
        self.effect_control_frame.grid(row=20, column=0, padx=10, pady=10, sticky="ew")
        
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
        """Status bar mesajını güncelle"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)


if __name__ == "__main__":
    app = ImageEditor()
    
    # Bind window resize event to update canvas
    app.bind("<Configure>", app.update_canvas_size)
    
    app.mainloop() 