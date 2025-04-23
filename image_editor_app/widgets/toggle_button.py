import customtkinter as ctk
from image_editor_app.utils.constants import *

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