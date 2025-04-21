"""
Menubar Module
Provides the main menu bar for the application.
"""

import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger("Image_Editor.Menubar")

def create_menubar(root, main_window):
    """
    Create the application menu bar.
    
    Args:
        root: Root Tk instance
        main_window: Reference to the main window
        
    Returns:
        The menu bar instance
    """
    # Create main menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="New...", command=main_window.new_file, accelerator="Ctrl+N")
    file_menu.add_command(label="Open...", command=main_window.open_file, accelerator="Ctrl+O")
    file_menu.add_separator()
    file_menu.add_command(label="Save", command=main_window.save_file, accelerator="Ctrl+S")
    file_menu.add_command(label="Save As...", command=main_window.save_file_as, accelerator="Ctrl+Shift+S")
    file_menu.add_separator()
    
    # Export submenu
    export_menu = tk.Menu(file_menu, tearoff=0)
    export_menu.add_command(label="JPEG...", command=lambda: _export_file(main_window, "jpeg"))
    export_menu.add_command(label="PNG...", command=lambda: _export_file(main_window, "png"))
    export_menu.add_command(label="TIFF...", command=lambda: _export_file(main_window, "tiff"))
    export_menu.add_command(label="BMP...", command=lambda: _export_file(main_window, "bmp"))
    export_menu.add_command(label="WebP...", command=lambda: _export_file(main_window, "webp"))
    file_menu.add_cascade(label="Export", menu=export_menu)
    
    file_menu.add_separator()
    
    # Recent files submenu
    recent_files_menu = tk.Menu(file_menu, tearoff=0)
    _update_recent_files_menu(recent_files_menu, main_window)
    file_menu.add_cascade(label="Recent Files", menu=recent_files_menu)
    
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=main_window.on_close)
    
    menubar.add_cascade(label="File", menu=file_menu)
    
    # Edit menu
    edit_menu = tk.Menu(menubar, tearoff=0)
    edit_menu.add_command(label="Undo", command=main_window.undo, accelerator="Ctrl+Z")
    edit_menu.add_command(label="Redo", command=main_window.redo, accelerator="Ctrl+Y")
    edit_menu.add_separator()
    edit_menu.add_command(label="Cut", command=lambda: _placeholder(main_window, "Cut"), accelerator="Ctrl+X")
    edit_menu.add_command(label="Copy", command=lambda: _placeholder(main_window, "Copy"), accelerator="Ctrl+C")
    edit_menu.add_command(label="Paste", command=lambda: _placeholder(main_window, "Paste"), accelerator="Ctrl+V")
    edit_menu.add_separator()
    edit_menu.add_command(label="Select All", command=lambda: _placeholder(main_window, "Select All"), accelerator="Ctrl+A")
    edit_menu.add_command(label="Deselect", command=lambda: _placeholder(main_window, "Deselect"), accelerator="Ctrl+D")
    
    menubar.add_cascade(label="Edit", menu=edit_menu)
    
    # Image menu
    image_menu = tk.Menu(menubar, tearoff=0)
    image_menu.add_command(label="Resize...", command=lambda: _placeholder(main_window, "Resize"))
    image_menu.add_command(label="Canvas Size...", command=lambda: _placeholder(main_window, "Canvas Size"))
    image_menu.add_command(label="Crop", command=lambda: _placeholder(main_window, "Crop"))
    image_menu.add_separator()
    image_menu.add_command(label="Rotate 90° CW", command=lambda: _placeholder(main_window, "Rotate 90° CW"))
    image_menu.add_command(label="Rotate 90° CCW", command=lambda: _placeholder(main_window, "Rotate 90° CCW"))
    image_menu.add_command(label="Rotate 180°", command=lambda: _placeholder(main_window, "Rotate 180°"))
    image_menu.add_command(label="Flip Horizontal", command=lambda: _placeholder(main_window, "Flip Horizontal"))
    image_menu.add_command(label="Flip Vertical", command=lambda: _placeholder(main_window, "Flip Vertical"))
    
    menubar.add_cascade(label="Image", menu=image_menu)
    
    # Layer menu
    layer_menu = tk.Menu(menubar, tearoff=0)
    layer_menu.add_command(label="New Layer", command=lambda: _placeholder(main_window, "New Layer"))
    layer_menu.add_command(label="Duplicate Layer", command=lambda: _placeholder(main_window, "Duplicate Layer"))
    layer_menu.add_command(label="Delete Layer", command=lambda: _placeholder(main_window, "Delete Layer"))
    layer_menu.add_separator()
    layer_menu.add_command(label="Add Layer Mask", command=lambda: _placeholder(main_window, "Add Layer Mask"))
    layer_menu.add_command(label="Apply Layer Mask", command=lambda: _placeholder(main_window, "Apply Layer Mask"))
    layer_menu.add_separator()
    layer_menu.add_command(label="Merge Down", command=lambda: _placeholder(main_window, "Merge Down"))
    layer_menu.add_command(label="Merge Visible", command=lambda: _placeholder(main_window, "Merge Visible"))
    layer_menu.add_command(label="Flatten Image", command=lambda: _placeholder(main_window, "Flatten Image"))
    
    menubar.add_cascade(label="Layer", menu=layer_menu)
    
    # Adjustments menu
    adjustments_menu = tk.Menu(menubar, tearoff=0)
    adjustments_menu.add_command(label="Brightness/Contrast...", command=lambda: _placeholder(main_window, "Brightness/Contrast"))
    adjustments_menu.add_command(label="Levels...", command=lambda: _placeholder(main_window, "Levels"))
    adjustments_menu.add_command(label="Curves...", command=lambda: _placeholder(main_window, "Curves"))
    adjustments_menu.add_command(label="Hue/Saturation...", command=lambda: _placeholder(main_window, "Hue/Saturation"))
    adjustments_menu.add_command(label="Color Balance...", command=lambda: _placeholder(main_window, "Color Balance"))
    adjustments_menu.add_separator()
    adjustments_menu.add_command(label="Invert", command=lambda: _placeholder(main_window, "Invert"))
    adjustments_menu.add_command(label="Auto Levels", command=lambda: _placeholder(main_window, "Auto Levels"))
    adjustments_menu.add_command(label="Threshold...", command=lambda: _placeholder(main_window, "Threshold"))
    adjustments_menu.add_command(label="Posterize...", command=lambda: _placeholder(main_window, "Posterize"))
    
    menubar.add_cascade(label="Adjustments", menu=adjustments_menu)
    
    # Filter menu
    filter_menu = tk.Menu(menubar, tearoff=0)
    
    # Blur submenu
    blur_menu = tk.Menu(filter_menu, tearoff=0)
    blur_menu.add_command(label="Gaussian Blur...", command=lambda: _placeholder(main_window, "Gaussian Blur"))
    blur_menu.add_command(label="Box Blur...", command=lambda: _placeholder(main_window, "Box Blur"))
    blur_menu.add_command(label="Motion Blur...", command=lambda: _placeholder(main_window, "Motion Blur"))
    filter_menu.add_cascade(label="Blur", menu=blur_menu)
    
    # Sharpen submenu
    sharpen_menu = tk.Menu(filter_menu, tearoff=0)
    sharpen_menu.add_command(label="Sharpen", command=lambda: _placeholder(main_window, "Sharpen"))
    sharpen_menu.add_command(label="Unsharp Mask...", command=lambda: _placeholder(main_window, "Unsharp Mask"))
    filter_menu.add_cascade(label="Sharpen", menu=sharpen_menu)
    
    # Noise submenu
    noise_menu = tk.Menu(filter_menu, tearoff=0)
    noise_menu.add_command(label="Add Noise...", command=lambda: _placeholder(main_window, "Add Noise"))
    noise_menu.add_command(label="Reduce Noise...", command=lambda: _placeholder(main_window, "Reduce Noise"))
    filter_menu.add_cascade(label="Noise", menu=noise_menu)
    
    filter_menu.add_separator()
    filter_menu.add_command(label="Edge Detect...", command=lambda: _placeholder(main_window, "Edge Detect"))
    filter_menu.add_command(label="Emboss...", command=lambda: _placeholder(main_window, "Emboss"))
    filter_menu.add_separator()
    filter_menu.add_command(label="Artistic...", command=lambda: _placeholder(main_window, "Artistic Filters"))
    filter_menu.add_command(label="Distort...", command=lambda: _placeholder(main_window, "Distort"))
    
    menubar.add_cascade(label="Filter", menu=filter_menu)
    
    # View menu
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="Zoom In", command=lambda: main_window.canvas.zoom_in(), accelerator="Ctrl++")
    view_menu.add_command(label="Zoom Out", command=lambda: main_window.canvas.zoom_out(), accelerator="Ctrl+-")
    view_menu.add_command(label="Zoom to Fit", command=lambda: main_window.canvas.zoom_to_fit(), accelerator="Ctrl+0")
    view_menu.add_command(label="Actual Size", command=lambda: main_window.set_zoom_level(1.0), accelerator="Ctrl+1")
    view_menu.add_separator()
    
    # Create checkbuttons for showing/hiding panels
    show_toolbar_var = tk.BooleanVar(value=True)
    view_menu.add_checkbutton(label="Show Toolbar", variable=show_toolbar_var, 
                            command=lambda: _toggle_panel(main_window.left_panel, show_toolbar_var.get()))
    
    show_layers_var = tk.BooleanVar(value=True)
    view_menu.add_checkbutton(label="Show Layers Panel", variable=show_layers_var, 
                            command=lambda: _toggle_panel(main_window.right_panel, show_layers_var.get()))
    
    view_menu.add_separator()
    view_menu.add_command(label="Show Grid", command=lambda: _placeholder(main_window, "Show Grid"))
    view_menu.add_command(label="Show Rulers", command=lambda: _placeholder(main_window, "Show Rulers"))
    view_menu.add_command(label="Show Guides", command=lambda: _placeholder(main_window, "Show Guides"))
    
    menubar.add_cascade(label="View", menu=view_menu)
    
    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="User Guide", command=lambda: _placeholder(main_window, "User Guide"))
    help_menu.add_command(label="Keyboard Shortcuts", command=lambda: _placeholder(main_window, "Keyboard Shortcuts"))
    help_menu.add_separator()
    help_menu.add_command(label="About", command=lambda: _show_about_dialog(main_window))
    
    menubar.add_cascade(label="Help", menu=help_menu)
    
    logger.info("Menu bar created")
    return menubar

def _export_file(main_window, format_name):
    """
    Export the current image in the specified format.
    
    Args:
        main_window: Reference to the main window
        format_name: Format to export (jpeg, png, etc.)
    """
    if not main_window.layer_manager:
        messagebox.showerror("Error", "No image to export.")
        return
    
    # Map format names to file extensions
    format_extensions = {
        "jpeg": ".jpg",
        "png": ".png",
        "tiff": ".tif",
        "bmp": ".bmp",
        "webp": ".webp"
    }
    
    ext = format_extensions.get(format_name, ".png")
    
    # Show save dialog
    file_path = filedialog.asksaveasfilename(
        title=f"Export as {format_name.upper()}",
        defaultextension=ext,
        filetypes=[(format_name.upper(), f"*{ext}"), ("All Files", "*.*")]
    )
    
    if not file_path:
        return  # User cancelled
    
    # Render composite image
    composite = main_window.layer_manager.render_composite()
    
    # Get quality setting for JPEG
    quality = main_window.app_state.settings["file_handling"]["export_quality_jpeg"] if format_name == "jpeg" else 95
    
    # Save the image
    error = main_window.image_handler.save_image(composite, file_path, quality)
    
    if error:
        messagebox.showerror("Error", f"Failed to export image: {error}")
        return
    
    main_window.set_status(f"Exported image to {file_path}")
    logger.info(f"Exported image as {format_name} to: {file_path}")

def _update_recent_files_menu(menu, main_window):
    """
    Update the recent files submenu with the list of recent files.
    
    Args:
        menu: Menu to update
        main_window: Reference to the main window
    """
    # Clear existing items
    menu.delete(0, tk.END)
    
    # Get recent files from settings
    recent_files = main_window.app_state.settings["file_handling"]["recent_files"]
    
    if recent_files:
        # Add recent files to menu
        for i, file_path in enumerate(recent_files):
            # Truncate path if too long
            display_name = os.path.basename(file_path)
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
            
            menu.add_command(
                label=f"{i+1}. {display_name}",
                command=lambda p=file_path: main_window.open_file(p)
            )
        
        menu.add_separator()
        menu.add_command(label="Clear Recent Files", command=lambda: _clear_recent_files(main_window, menu))
    else:
        menu.add_command(label="No Recent Files", state=tk.DISABLED)

def _clear_recent_files(main_window, menu):
    """
    Clear the recent files list.
    
    Args:
        main_window: Reference to the main window
        menu: Menu to update
    """
    main_window.app_state.settings["file_handling"]["recent_files"] = []
    main_window.app_state.save_settings()
    _update_recent_files_menu(menu, main_window)
    logger.info("Cleared recent files list")

def _toggle_panel(panel, show):
    """
    Toggle the visibility of a panel.
    
    Args:
        panel: Panel to toggle
        show: True to show, False to hide
    """
    if show:
        panel.pack(side=tk.LEFT if panel.pack_info()["side"] == tk.LEFT else tk.RIGHT, 
                 fill=tk.Y, padx=5, pady=5)
    else:
        panel.pack_forget()

def _placeholder(main_window, feature_name):
    """
    Placeholder function for unimplemented features.
    
    Args:
        main_window: Reference to the main window
        feature_name: Name of the feature
    """
    main_window.set_status(f"Feature not implemented: {feature_name}")
    logger.info(f"Placeholder called for: {feature_name}")

def _show_about_dialog(main_window):
    """
    Show the about dialog.
    
    Args:
        main_window: Reference to the main window
    """
    messagebox.showinfo(
        "About Image_Editor",
        f"Image_Editor v{main_window.app_state.app_version}\n\n"
        "An advanced image editor built with Python and CustomTkinter.\n\n"
        "© 2023 Image_Editor Team"
    ) 