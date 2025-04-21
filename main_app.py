import customtkinter as ctk
from Image_Noise import ImageEditor
import logging
import sys
from tkinter import messagebox

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('media_editor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MainApplication(ctk.CTk):
    """
    Main application window that serves as a launcher for Image Editor.
    Provides a clean interface for image editing tools.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_window()
        self.create_ui()
        
    def setup_window(self):
        """Configure main window properties and geometry"""
        self.title("Image Editor")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Siyah-beyaz tema ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.configure(fg_color=("#ffffff", "#000000"))
        
        # Ana başlık
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(20, 10), fill="x")
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Image Editor",
            font=ctk.CTkFont(family="Helvetica", size=32, weight="bold"),
            text_color=("#1a1a1a", "#ffffff")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Simple Image Editing Tool",
            font=ctk.CTkFont(family="Helvetica", size=14),
            text_color=("#4a4a4a", "#b0b0b0")
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self):
        """Create and setup all UI elements"""
        # Create header frame
        self.header_frame = ctk.CTkFrame(self, bg_color="#2E2E2E")
        self.header_frame.pack(padx=10, pady=10, fill="x")
        
        # Create button with hover effect
        self.create_buttons()
        
        # Content frame for editor
        self.content_frame = ctk.CTkFrame(self, bg_color="#1E1E1E")
        self.content_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        self.current_editor = None
        
    def create_buttons(self):
        """Create button for image editor with modern design"""
        button_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color=("#f0f0f0", "#1a1a1a"),
            corner_radius=15
        )
        button_frame.pack(pady=20, padx=30, fill="x")
        
        # Image Editor Button
        self.image_button = ctk.CTkButton(
            button_frame,
            text="Open Image Editor",
            command=self.open_image_editor,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color=("#2a2a2a", "#ffffff"),
            hover_color=("#4a4a4a", "#b0b0b0"),
            text_color=("#ffffff", "#000000")
        )
        self.image_button.pack(pady=10, padx=20, fill="x")
        
    def open_image_editor(self):
        """Open the image editor window and handle any errors"""
        try:
            self.safely_close_current_editor()
            
            # Hide main window
            self.withdraw()
            
            # Create and show image editor
            self.current_editor = ImageEditor(self)
            self.current_editor.focus_force()
            
            # Set up callback for when editor is closed
            def on_editor_close():
                self.current_editor.destroy()
                self.current_editor = None
                self.deiconify()  # Show main window again
                self.focus_force()
            
            self.current_editor.protocol("WM_DELETE_WINDOW", on_editor_close)
            
        except Exception as e:
            self.logger.error(f"Error opening image editor: {str(e)}")
            self.show_error(f"Failed to open image editor: {str(e)}")
            self.deiconify()  # Show main window if there's an error
            
    def safely_close_current_editor(self):
        """Safely close the current editor if one exists"""
        if self.current_editor:
            try:
                self.current_editor.destroy()
                self.deiconify()  # Show main window
                self.focus_force()
            except Exception as e:
                self.logger.error(f"Error closing editor: {str(e)}")
            self.current_editor = None
            
    def show_error(self, message):
        """Display error message to user"""
        messagebox.showerror("Error", message)
        
    def on_closing(self):
        """Clean up resources before closing"""
        self.safely_close_current_editor()
        self.quit()

if __name__ == "__main__":
    try:
        app = MainApplication()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        messagebox.showerror("Error", f"Application error: {str(e)}")
