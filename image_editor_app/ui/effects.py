"""
Effects UI controls and related functions
"""
import customtkinter as ctk
from image_editor_app.utils.constants import *
from image_editor_app.widgets.effect_intensity import EffectIntensityFrame
from image_editor_app.widgets.toggle_button import ToggleButton

def create_effect_controls(self):
    """Create controls for applying effects"""
    # Efekt kontrol çerçevesi
    self.effect_control_frame = ctk.CTkFrame(self.content_frame)
    self.effect_control_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    self.effect_control_frame.grid_rowconfigure(0, weight=1)
    self.effect_control_frame.grid_columnconfigure(0, weight=1)
    
    # Frame başlığı
    self.effect_title = ctk.CTkLabel(
        self.effect_control_frame, 
        text="Efekt Ayarları", 
        font=SUBTITLE_FONT,
        text_color=ACCENT_COLOR
    )
    self.effect_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
    
    # Filtre açıklaması
    self.effect_description = ctk.CTkLabel(
        self.effect_control_frame, 
        text="Efekt ayarlarını yapılandırmak için aşağıdaki kontrolleri kullanın.",
        font=SMALL_FONT, 
        wraplength=200
    )
    self.effect_description.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
    
    # Ayarlar için bir iç çerçeve
    self.settings_frame = ctk.CTkFrame(self.effect_control_frame, fg_color="transparent")
    self.settings_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    
    # Sepia efekt kontrolü
    self.sepia_frame = EffectIntensityFrame(
        self.settings_frame,
        "Sepya Yoğunluğu",
        min_val=0.0,
        max_val=1.0,
        default_val=1.0,
        callback=lambda value: self.update_effect_param("sepia", "intensity", value)
    )
    
    # Cartoon efekt kontrolü
    self.cartoon_edge_frame = EffectIntensityFrame(
        self.settings_frame,
        "Kenar Belirginliği",
        min_val=1,
        max_val=10,
        default_val=3,
        callback=lambda value: self.update_effect_param("cartoon", "edge_intensity", value),
        integer=True
    )
    
    self.cartoon_simplify_frame = EffectIntensityFrame(
        self.settings_frame,
        "Renk Sadeleştirme",
        min_val=2,
        max_val=20,
        default_val=5,
        callback=lambda value: self.update_effect_param("cartoon", "simplify", value),
        integer=True
    )
    
    # Vignette efekt kontrolü
    self.vignette_frame = EffectIntensityFrame(
        self.settings_frame,
        "Vinyet Efekti",
        min_val=0.0,
        max_val=1.0,
        default_val=0.5,
        callback=lambda value: self.update_effect_param("vignette", "amount", value)
    )
    
    # Pixelate efekt kontrolü
    self.pixelate_frame = EffectIntensityFrame(
        self.settings_frame,
        "Piksel Boyutu",
        min_val=2,
        max_val=50,
        default_val=10,
        callback=lambda value: self.update_effect_param("pixelate", "pixel_size", value),
        integer=True
    )
    
    # Color splash (renk sıçratma) kontrolü
    self.splash_intensity_frame = EffectIntensityFrame(
        self.settings_frame,
        "Efekt Yoğunluğu",
        min_val=0.0,
        max_val=1.0,
        default_val=1.0,
        callback=lambda value: self.update_effect_param("red_splash", "intensity", value)
    )
    
    # Renk seçimi
    self.splash_color_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
    self.splash_color_label = ctk.CTkLabel(
        self.splash_color_frame,
        text="Korunacak Renk:",
        font=LABEL_FONT
    )
    self.splash_color_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    self.splash_color_var = ctk.StringVar(value="red")
    self.splash_color_red = ctk.CTkRadioButton(
        self.splash_color_frame,
        text="Kırmızı",
        variable=self.splash_color_var,
        value="red",
        command=lambda: self.update_effect_param("red_splash", "color", "red")
    )
    self.splash_color_red.grid(row=0, column=1, padx=5, pady=5)
    
    self.splash_color_green = ctk.CTkRadioButton(
        self.splash_color_frame,
        text="Yeşil",
        variable=self.splash_color_var,
        value="green",
        command=lambda: self.update_effect_param("red_splash", "color", "green")
    )
    self.splash_color_green.grid(row=0, column=2, padx=5, pady=5)
    
    self.splash_color_blue = ctk.CTkRadioButton(
        self.splash_color_frame,
        text="Mavi",
        variable=self.splash_color_var,
        value="blue",
        command=lambda: self.update_effect_param("red_splash", "color", "blue")
    )
    self.splash_color_blue.grid(row=0, column=3, padx=5, pady=5)
    
    # Oil painting efekt kontrolü
    self.oil_brush_frame = EffectIntensityFrame(
        self.settings_frame,
        "Fırça Boyutu",
        min_val=1,
        max_val=10,
        default_val=3,
        callback=lambda value: self.update_effect_param("oil", "brush_size", value),
        integer=True
    )
    
    self.oil_levels_frame = EffectIntensityFrame(
        self.settings_frame,
        "Detay Seviyesi",
        min_val=3,
        max_val=20,
        default_val=8,
        callback=lambda value: self.update_effect_param("oil", "levels", value),
        integer=True
    )
    
    # Geliştirilmiş Noise (Gürültü) efekt kontrolü
    self.noise_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
    self.noise_frame.columnconfigure(0, weight=1)
    
    # Ana gürültü yoğunluğu kontrolü
    self.noise_amount_frame = EffectIntensityFrame(
        self.noise_frame,
        "Gürültü Miktarı",
        min_val=0.1,
        max_val=1.0,
        default_val=0.5,
        callback=lambda value: self.update_effect_param("noise", "amount", value)
    )
    self.noise_amount_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    
    # Gürültü tipi seçimi
    self.noise_type_frame = ctk.CTkFrame(self.noise_frame, fg_color="transparent")
    self.noise_type_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    
    self.noise_type_label = ctk.CTkLabel(
        self.noise_type_frame,
        text="Gürültü Tipi:",
        font=LABEL_FONT
    )
    self.noise_type_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    self.noise_type_var = ctk.StringVar(value="uniform")
    
    self.noise_type_uniform = ctk.CTkRadioButton(
        self.noise_type_frame,
        text="Uniform",
        variable=self.noise_type_var,
        value="uniform",
        command=lambda: self.update_effect_param("noise", "noise_type", "uniform")
    )
    self.noise_type_uniform.grid(row=0, column=1, padx=5, pady=5)
    
    self.noise_type_gaussian = ctk.CTkRadioButton(
        self.noise_type_frame,
        text="Gaussian",
        variable=self.noise_type_var,
        value="gaussian",
        command=lambda: self.update_effect_param("noise", "noise_type", "gaussian")
    )
    self.noise_type_gaussian.grid(row=0, column=2, padx=5, pady=5)
    
    self.noise_type_salt = ctk.CTkRadioButton(
        self.noise_type_frame,
        text="Salt & Pepper",
        variable=self.noise_type_var,
        value="salt_pepper",
        command=lambda: self.update_effect_param("noise", "noise_type", "salt_pepper")
    )
    self.noise_type_salt.grid(row=0, column=3, padx=5, pady=5)
    
    # Renk kanalı seçimi için bir frame
    self.channels_frame = ctk.CTkFrame(self.noise_frame, fg_color="transparent") 
    self.channels_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
    
    self.channels_label = ctk.CTkLabel(
        self.channels_frame,
        text="Kanallar:",
        font=LABEL_FONT
    )
    self.channels_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    # Kanalların başlangıç durumu - hepsi açık
    channels = ["r", "g", "b"]
    self.effect_params["noise"] = {
        "amount": 0.5,
        "noise_type": "uniform",
        "channels": channels
    }
    
    # Butonlar
    self.channel_button_frame = ctk.CTkFrame(self.channels_frame, fg_color="transparent")
    self.channel_button_frame.grid(row=0, column=1, padx=5, pady=5)
    
    # Tek kanallar için inline butonlar
    self.r_button = ctk.CTkButton(
        self.channel_button_frame,
        text="R",
        width=30,
        height=24,
        fg_color=SUCCESS_COLOR if "r" in channels else SECONDARY_COLOR,
        command=lambda: self.toggle_channel("r")
    )
    self.r_button.grid(row=0, column=0, padx=2)
    
    self.g_button = ctk.CTkButton(
        self.channel_button_frame,
        text="G",
        width=30,
        height=24,
        fg_color=SUCCESS_COLOR if "g" in channels else SECONDARY_COLOR,
        command=lambda: self.toggle_channel("g")
    )
    self.g_button.grid(row=0, column=1, padx=2)
    
    self.b_button = ctk.CTkButton(
        self.channel_button_frame,
        text="B",
        width=30,
        height=24,
        fg_color=SUCCESS_COLOR if "b" in channels else SECONDARY_COLOR,
        command=lambda: self.toggle_channel("b")
    )
    self.b_button.grid(row=0, column=2, padx=2)
    
    self.all_button = ctk.CTkButton(
        self.channel_button_frame,
        text="Tümü",
        width=50,
        height=24,
        command=lambda: self.set_all_channels()
    )
    self.all_button.grid(row=0, column=3, padx=5)
    
    # Add preview controls to the bottom
    self.add_preview_controls()
    
    # Hide all controls initially
    self.hide_all_effect_controls()

def hide_all_effect_controls(self):
    """Hide all effect control frames"""
    for widget in self.settings_frame.winfo_children():
        widget.grid_forget()
    
    # Preview control frame is not in settings_frame
    if hasattr(self, 'preview_frame'):
        self.preview_frame.grid_forget()
    
    # Effect control frame'ini gizle
    if hasattr(self, 'effect_control_frame'):
        self.effect_control_frame.grid_forget()
    
    self.current_effect = None

def show_effect_controls(self, effect_name):
    """Show control frames for the specified effect"""
    # First hide any currently visible controls
    self.hide_all_effect_controls()
    
    # Set the current effect
    self.current_effect = effect_name
    
    # Initialize appropriate values in effect_params if not already set
    if effect_name == "sepia" and "intensity" not in self.effect_params[effect_name]:
        self.effect_params[effect_name]["intensity"] = 1.0
    elif effect_name == "cartoon":
        if "edge_intensity" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["edge_intensity"] = 3
        if "simplify" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["simplify"] = 5
    elif effect_name == "vignette" and "amount" not in self.effect_params[effect_name]:
        self.effect_params[effect_name]["amount"] = 0.5
    elif effect_name == "pixelate" and "pixel_size" not in self.effect_params[effect_name]:
        self.effect_params[effect_name]["pixel_size"] = 10
    elif effect_name == "red_splash":
        if "intensity" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["intensity"] = 1.0
        if "color" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["color"] = "red"
    elif effect_name == "oil":
        if "brush_size" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["brush_size"] = 3
        if "levels" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["levels"] = 8
    elif effect_name == "noise":
        if "amount" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["amount"] = 0.5
        if "noise_type" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["noise_type"] = "uniform"
        if "channels" not in self.effect_params[effect_name]:
            self.effect_params[effect_name]["channels"] = ["r", "g", "b"]
    
    # Effect control frame
    self.effect_control_frame.grid(row=0, column=1, sticky="n", padx=10, pady=10)
    
    # Update the effect title and description
    if effect_name == "sepia":
        self.effect_title.configure(text="Sepya Efekti")
        self.effect_description.configure(text="Nostaljik bir görünüm için görüntüye kahverengi tonlaması uygular.")
        self.sepia_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.sepia_frame.set_value(self.effect_params[effect_name]["intensity"])
    
    elif effect_name == "cartoon":
        self.effect_title.configure(text="Çizgi Film Efekti")
        self.effect_description.configure(text="Görüntüyü çizgi film veya çizim stilinde yapar. Kenar belirginliği ve renk sadeleştirme ayarlanabilir.")
        self.cartoon_edge_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.cartoon_simplify_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.cartoon_edge_frame.set_value(self.effect_params[effect_name]["edge_intensity"])
        self.cartoon_simplify_frame.set_value(self.effect_params[effect_name]["simplify"])
    
    elif effect_name == "vignette":
        self.effect_title.configure(text="Vinyet Efekti")
        self.effect_description.configure(text="Görüntünün kenarlarını koyulaştırarak merkeze odaklanmayı sağlar.")
        self.vignette_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.vignette_frame.set_value(self.effect_params[effect_name]["amount"])
    
    elif effect_name == "pixelate":
        self.effect_title.configure(text="Pikselleştirme")
        self.effect_description.configure(text="Görüntüyü büyük pikseller halinde gösterir. Piksel boyutu ayarlanabilir.")
        self.pixelate_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.pixelate_frame.set_value(self.effect_params[effect_name]["pixel_size"])
    
    elif effect_name == "red_splash":
        self.effect_title.configure(text="Renk Sıçratma")
        self.effect_description.configure(text="Seçili renk kanalını koruyarak diğer renkleri siyah-beyaz yapar.")
        self.splash_intensity_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.splash_color_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.splash_intensity_frame.set_value(self.effect_params[effect_name]["intensity"])
        self.splash_color_var.set(self.effect_params[effect_name]["color"])
    
    elif effect_name == "oil":
        self.effect_title.configure(text="Yağlı Boya Efekti")
        self.effect_description.configure(text="Görüntüye yağlı boya tablosu görünümü verir.")
        self.oil_brush_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.oil_levels_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.oil_brush_frame.set_value(self.effect_params[effect_name]["brush_size"])
        self.oil_levels_frame.set_value(self.effect_params[effect_name]["levels"])
    
    elif effect_name == "noise":
        self.effect_title.configure(text="Gürültü Efekti")
        self.effect_description.configure(text="Görüntüye çeşitli tipte gürültü ekler. Gürültü tipi, yoğunluğu ve etkilenen kanallar ayarlanabilir.")
        self.noise_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Ayarla noise parametrelerini
        self.noise_amount_frame.set_value(self.effect_params[effect_name]["amount"])
        self.noise_type_var.set(self.effect_params[effect_name]["noise_type"])
        
        # Kanalları ayarla
        channels = self.effect_params[effect_name]["channels"]
        self.r_button.configure(fg_color=SUCCESS_COLOR if "r" in channels else SECONDARY_COLOR)
        self.g_button.configure(fg_color=SUCCESS_COLOR if "g" in channels else SECONDARY_COLOR)
        self.b_button.configure(fg_color=SUCCESS_COLOR if "b" in channels else SECONDARY_COLOR)
        self.all_button.configure(fg_color=SUCCESS_COLOR if len(channels) == 3 else SECONDARY_COLOR)
    
    # Show the preview controls
    self.preview_frame.grid(row=20, column=0, padx=10, pady=(15, 5), sticky="ew")
    
    # Reset preview switch to off
    self.preview_switch.deselect()

def add_preview_controls(self):
    """Add preview switch and apply button"""
    # Preview controls frame
    self.preview_frame = ctk.CTkFrame(self.effect_control_frame, fg_color="transparent")
    
    # Preview switch with label
    preview_label = ctk.CTkLabel(
        self.preview_frame,
        text="Önizleme:",
        font=LABEL_FONT
    )
    preview_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    self.preview_var = ctk.BooleanVar(value=False)
    self.preview_switch = ToggleButton(
        self.preview_frame,
        variable=self.preview_var,
        command=self.toggle_preview,
        width=40
    )
    self.preview_switch.grid(row=0, column=1, padx=5, pady=5)
    
    # Apply button
    apply_btn = ctk.CTkButton(
        self.preview_frame,
        text="Efekti Uygula",
        command=self.apply_effect,
        font=BUTTON_FONT,
        fg_color=ACCENT_COLOR,
        hover_color=SECONDARY_COLOR
    )
    apply_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

def update_effect_param(self, effect, param, value):
    """Update an effect parameter and refresh preview if active"""
    # Update parameter value
    self.effect_params[effect][param] = value
    
    # If preview is active, update it
    if hasattr(self, 'preview_var') and self.preview_var.get() and self.current_effect == effect:
        self.preview_effect()

def toggle_channel(self, channel):
    """Toggle a single noise channel"""
    channels = self.effect_params["noise"]["channels"]
    
    # Toggle channel state
    if channel in channels:
        # Tüm kanallar kapatılamaz, en az bir kanal açık olmalı
        if len(channels) > 1:
            channels.remove(channel)
    else:
        channels.append(channel)
    
    # Update button colors
    self.r_button.configure(fg_color=SUCCESS_COLOR if "r" in channels else SECONDARY_COLOR)
    self.g_button.configure(fg_color=SUCCESS_COLOR if "g" in channels else SECONDARY_COLOR)
    self.b_button.configure(fg_color=SUCCESS_COLOR if "b" in channels else SECONDARY_COLOR)
    self.all_button.configure(fg_color=SUCCESS_COLOR if len(channels) == 3 else SECONDARY_COLOR)
    
    self.update_effect_param("noise", "channels", channels)

def set_all_channels(self):
    """Set all noise channels"""
    channels = ["r", "g", "b"]
    self.effect_params["noise"]["channels"] = channels
    self.update_effect_param("noise", "channels", channels)

    # Update button colors
    self.r_button.configure(fg_color=SUCCESS_COLOR)
    self.g_button.configure(fg_color=SUCCESS_COLOR)
    self.b_button.configure(fg_color=SUCCESS_COLOR)
    self.all_button.configure(fg_color=SUCCESS_COLOR) 