import customtkinter as ctk
from image_editor_app.utils.constants import *
from image_editor_app.widgets.tooltip import ToolTip

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