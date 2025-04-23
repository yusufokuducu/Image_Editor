import customtkinter as ctk
from image_editor_app.utils.constants import *

class ToggleButton(ctk.CTkButton):
    """Açılıp kapanabilen buton sınıfı"""
    def __init__(self, master, text="", command=None, variable=None, **kwargs):
        # customtkinter'ın CTkButton sınıfı variable parametresini doğrudan desteklemez
        # Bu yüzden variable parametresini kwargs'dan çıkarıp kendimiz yönetiyoruz
        self.variable = variable
        
        # command için kendi toggle metodumuzu kullanacağız
        super().__init__(master, text=text, command=self._toggle, **kwargs)
        
        self.user_command = command
        self.active = False
        
        # Başlangıç durumunu ayarla
        if self.variable:
            self.active = bool(self.variable.get())
            
        # Başlangıç rengini ayarla
        if self.active:
            self.configure(fg_color=SUCCESS_COLOR)
        else:
            self.configure(fg_color=ACCENT_COLOR)
    
    def _toggle(self):
        """Butonun durumunu değiştir"""
        self.active = not self.active
        
        # Görünümü güncelle
        if self.active:
            self.configure(fg_color=SUCCESS_COLOR)
        else:
            self.configure(fg_color=ACCENT_COLOR)
        
        # Variable'ı güncelle
        if self.variable:
            self.variable.set(1 if self.active else 0)
        
        # Kullanıcı komutunu çağır
        if self.user_command:
            self.user_command()
    
    def select(self):
        """Toggle butonunu aktif duruma getir"""
        if not self.active:
            self._toggle()
    
    def deselect(self):
        """Toggle butonunu pasif duruma getir"""
        if self.active:
            self._toggle() 