# -*- coding: utf-8 -*-
"""
Main entry point for the Pycture Perfect Image Editor.
"""

import dearpygui.dearpygui as dpg
from ui.theme import apply_theme
import config
from core.image_handler import ImageHandler

# --- Constants ---
RIGHT_PANEL_TAG = "right_panel"
CENTER_PANEL_TAG = "center_panel"
BOTTOM_PANEL_TAG = "bottom_panel"
OPEN_FILE_DIALOG_TAG = "open_file_dialog"
SAVE_FILE_DIALOG_TAG = "save_file_dialog"
TEXTURE_REGISTRY_TAG = "texture_registry"
RAW_TEXTURE_TAG = "raw_texture"
IMAGE_ITEM_TAG = "image_item"
BRIGHTNESS_SLIDER_TAG = "brightness_slider"
BLUR_SLIDER_TAG = "blur_slider"
WIDTH_INPUT_TAG = "width_input"
HEIGHT_INPUT_TAG = "height_input"

# --- Global State ---
image_handler = ImageHandler()

# --- Callbacks ---
def _update_canvas_image():
    if image_handler.image_pil is None or not dpg.does_item_exist(RAW_TEXTURE_TAG):
        return
    texture_data = image_handler.get_texture_data()
    if texture_data is not None:
        dpg.set_value(RAW_TEXTURE_TAG, texture_data)
        dpg.configure_item(IMAGE_ITEM_TAG, width=image_handler.width, height=image_handler.height)

def _apply_brightness_callback(sender, app_data):
    if image_handler.image_pil is None: return
    image_handler.apply_brightness(app_data, is_final=True)
    _update_canvas_image()

def _apply_blur_callback(sender, app_data):
    if image_handler.image_pil is None: return
    image_handler.apply_blur(app_data, is_final=True)
    _update_canvas_image()

def _apply_grayscale_callback():
    if image_handler.image_pil is None: return
    image_handler.apply_grayscale(is_final=True)
    _update_canvas_image()

def _resize_callback():
    if image_handler.image_pil is None: return
    width = dpg.get_value(WIDTH_INPUT_TAG)
    height = dpg.get_value(HEIGHT_INPUT_TAG)
    if width > 0 and height > 0:
        image_handler.resize_image(width, height, is_final=True)
        _update_canvas_image()

def _undo_callback(sender, app_data):
    if image_handler.image_pil is None: return
    if dpg.is_key_down(dpg.mvKey_LControl):
        if image_handler.undo():
            _update_canvas_image()
            dpg.set_value(WIDTH_INPUT_TAG, image_handler.width)
            dpg.set_value(HEIGHT_INPUT_TAG, image_handler.height)

def _redo_callback(sender, app_data):
    if image_handler.image_pil is None: return
    if dpg.is_key_down(dpg.mvKey_LControl):
        if image_handler.redo(): 
            _update_canvas_image()
            dpg.set_value(WIDTH_INPUT_TAG, image_handler.width)
            dpg.set_value(HEIGHT_INPUT_TAG, image_handler.height)

def _open_file_callback(sender, app_data):
    if dpg.is_key_down(dpg.mvKey_LControl):
        dpg.show_item(OPEN_FILE_DIALOG_TAG)

def _save_file_callback(sender, app_data):
    if dpg.is_key_down(dpg.mvKey_LControl):
        dpg.show_item(SAVE_FILE_DIALOG_TAG)

def open_image_callback(sender, app_data):
    if image_handler.load_image(app_data['file_path_name']):
        texture_data = image_handler.get_texture_data()
        if dpg.does_item_exist(RAW_TEXTURE_TAG):
            dpg.delete_item(RAW_TEXTURE_TAG)
        dpg.add_raw_texture(image_handler.width, image_handler.height, texture_data, format=dpg.mvFormat_Float_rgba, tag=RAW_TEXTURE_TAG, parent=TEXTURE_REGISTRY_TAG)
        if not dpg.does_item_exist(IMAGE_ITEM_TAG):
            dpg.add_image(RAW_TEXTURE_TAG, parent=CENTER_PANEL_TAG, tag=IMAGE_ITEM_TAG)
        else:
            dpg.configure_item(IMAGE_ITEM_TAG, texture_tag=RAW_TEXTURE_TAG)
        dpg.configure_item(IMAGE_ITEM_TAG, width=image_handler.width, height=image_handler.height)
        dpg.set_value(BRIGHTNESS_SLIDER_TAG, 1.0)
        dpg.set_value(BLUR_SLIDER_TAG, 0.0)
        dpg.set_value(WIDTH_INPUT_TAG, image_handler.width)
        dpg.set_value(HEIGHT_INPUT_TAG, image_handler.height)

def save_image_callback(sender, app_data):
    if image_handler.image_pil is None: return
    try:
        image_handler.image_pil.save(app_data['file_path_name'])
    except Exception as e:
        print(f"Error saving image: {e}")

def setup_ui():
    with dpg.texture_registry(tag=TEXTURE_REGISTRY_TAG):
        pass
    with dpg.file_dialog(directory_selector=False, show=False, callback=open_image_callback, tag=OPEN_FILE_DIALOG_TAG, width=700, height=400):
        dpg.add_file_extension(".png,.jpg,.jpeg,.bmp,.gif", color=(0, 255, 0, 255))
    with dpg.file_dialog(directory_selector=False, show=False, callback=save_image_callback, tag=SAVE_FILE_DIALOG_TAG, width=700, height=400):
        dpg.add_file_extension(".png", color=(0, 255, 0, 255)); dpg.add_file_extension(".jpg", color=(0, 255, 0, 255))
    with dpg.viewport_menu_bar():
        with dpg.menu(label="File"): 
            dpg.add_menu_item(label="Open (Ctrl+O)", callback=lambda: dpg.show_item(OPEN_FILE_DIALOG_TAG))
            dpg.add_menu_item(label="Save (Ctrl+S)", callback=lambda: dpg.show_item(SAVE_FILE_DIALOG_TAG))
            dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())
        with dpg.menu(label="Edit"): 
            dpg.add_menu_item(label="Undo (Ctrl+Z)", callback=_undo_callback)
            dpg.add_menu_item(label="Redo (Ctrl+Y)", callback=_redo_callback)
    with dpg.window(label="Image Canvas", tag=CENTER_PANEL_TAG, width=950, height=750, pos=[10, 30]): pass
    with dpg.window(label="Properties", tag=RIGHT_PANEL_TAG, width=220, height=750, pos=[970, 30]):
        dpg.add_text("Transforms", color=config.COLOR_PRIMARY); dpg.add_separator()
        dpg.add_input_int(label="Width", tag=WIDTH_INPUT_TAG, width=100)
        dpg.add_input_int(label="Height", tag=HEIGHT_INPUT_TAG, width=100)
        dpg.add_button(label="Resize", callback=_resize_callback, width=-1)
        dpg.add_separator()
        dpg.add_text("Adjustments", color=config.COLOR_PRIMARY); dpg.add_separator()
        dpg.add_slider_float(label="Brightness", min_value=0.0, max_value=2.0, default_value=1.0, tag=BRIGHTNESS_SLIDER_TAG, callback=_apply_brightness_callback)
        dpg.add_separator(); dpg.add_text("Filters", color=config.COLOR_PRIMARY); dpg.add_separator()
        dpg.add_button(label="Apply Grayscale", callback=_apply_grayscale_callback, width=-1)
        dpg.add_slider_float(label="Blur Radius", min_value=0.0, max_value=10.0, default_value=0.0, tag=BLUR_SLIDER_TAG, callback=_apply_blur_callback)
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=dpg.mvKey_Z, callback=_undo_callback)
        dpg.add_key_press_handler(key=dpg.mvKey_Y, callback=_redo_callback)
        dpg.add_key_press_handler(key=dpg.mvKey_O, callback=_open_file_callback)
        dpg.add_key_press_handler(key=dpg.mvKey_S, callback=_save_file_callback)

def main():
    dpg.create_context()
    dpg.create_viewport(title='Pycture Perfect', width=1200, height=800)
    dpg.setup_dearpygui()
    apply_theme()
    setup_ui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()