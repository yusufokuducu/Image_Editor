import os
import tkinter as tk
from image_editor_app.utils.constants import *

class ToolTip:
    """Optimized lightweight tooltip class for UI elements"""
    # Class variable to track active tooltips
    _tooltip_window = None
    _active_tooltip = None
    _after_id = None
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.timer_id = None
        
        # Bind only necessary events
        self.widget.bind("<Enter>", self.schedule_show)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<ButtonPress>", self.hide)
    
    def schedule_show(self, event=None):
        """Delay showing tooltip to prevent accidental triggering"""
        self.cancel_schedule()
        self.timer_id = self.widget.after(700, self.show)  # Longer delay (700ms)
    
    def cancel_schedule(self):
        """Cancel any pending timers"""
        if self.timer_id:
            self.widget.after_cancel(self.timer_id)
            self.timer_id = None
    
    @classmethod
    def _init_tooltip_window(cls, widget):
        """Create a single tooltip window for all tooltips"""
        # Clean up any existing window
        if cls._tooltip_window and cls._tooltip_window.winfo_exists():
            cls._tooltip_window.destroy()
        
        # Create basic tooltip window
        cls._tooltip_window = tk.Toplevel(widget)
        cls._tooltip_window.withdraw()
        
        # Configure as basic overlay window
        cls._tooltip_window.wm_overrideredirect(True)
        cls._tooltip_window.wm_transient(widget.winfo_toplevel())  # Be transient to main window
        
        if os.name == "nt":  # Windows-specific optimization
            cls._tooltip_window.attributes("-toolwindow", True)
            cls._tooltip_window.attributes("-alpha", 0.9)  # Slight transparency
        
        # Simple frame and label
        cls._frame = tk.Frame(cls._tooltip_window, background="#333333", borderwidth=1, relief="solid")
        cls._frame.pack(fill="both", expand=True)
        
        cls._label = tk.Label(
            cls._frame, 
            text="", 
            background="#333333", 
            foreground="white",
            font=("Segoe UI", 9),
            padx=6, 
            pady=3,
            justify="left"
        )
        cls._label.pack()
        
        return cls._tooltip_window
    
    def show(self):
        """Show tooltip with optimized positioning and display"""
        self.cancel_schedule()
        
        # Track active tooltip
        ToolTip._active_tooltip = self
        
        # Create window if needed
        if not ToolTip._tooltip_window or not ToolTip._tooltip_window.winfo_exists():
            ToolTip._init_tooltip_window(self.widget)
        
        # Update content
        ToolTip._label.configure(text=self.text)
        ToolTip._tooltip_window.update_idletasks()  # Force geometry calculation
        
        # Calculate optimal position
        widget_width = self.widget.winfo_width()
        widget_height = self.widget.winfo_height()
        widget_x = self.widget.winfo_rootx()
        widget_y = self.widget.winfo_rooty()
        
        # Get tooltip dimensions
        tooltip_width = ToolTip._tooltip_window.winfo_reqwidth()
        tooltip_height = ToolTip._tooltip_window.winfo_reqheight()
        
        # Screen dimensions to prevent going off-screen
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        # Calculate position (centered below widget by default)
        x = widget_x + (widget_width - tooltip_width) // 2
        y = widget_y + widget_height + 5
        
        # Ensure tooltip stays on screen
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 5
        if x < 0:
            x = 5
        if y + tooltip_height > screen_height:
            y = widget_y - tooltip_height - 5  # Show above widget
        
        # Position and show tooltip
        ToolTip._tooltip_window.geometry(f"+{x}+{y}")
        ToolTip._tooltip_window.deiconify()
        
        # Set auto-hide after 5 seconds as a fallback
        if ToolTip._after_id:
            ToolTip._tooltip_window.after_cancel(ToolTip._after_id)
        ToolTip._after_id = ToolTip._tooltip_window.after(5000, self.hide)
    
    def hide(self, event=None):
        """Hide tooltip and clean up timers"""
        self.cancel_schedule()
        
        # Cancel auto-hide timer if active
        if ToolTip._after_id:
            try:
                ToolTip._tooltip_window.after_cancel(ToolTip._after_id)
                ToolTip._after_id = None
            except:
                pass
        
        # Only hide if this tooltip is still active
        if ToolTip._active_tooltip == self and ToolTip._tooltip_window and ToolTip._tooltip_window.winfo_exists():
            try:
                ToolTip._tooltip_window.withdraw()
            except:
                pass
            ToolTip._active_tooltip = None 