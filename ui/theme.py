# -*- coding: utf-8 -*-
"""
Applies the custom AMOLED-style dark theme to the Dear PyGui UI.

This module reads color definitions from config.py and applies them to
all relevant UI items using a global theme.
"""

import dearpygui.dearpygui as dpg
import config

def apply_theme():
    """Creates and binds a global theme for the application."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Main background color for the entire application
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, config.COLOR_BACKGROUND, category=dpg.mvThemeCat_Core)
            
            # Panel and child window backgrounds
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, config.COLOR_PANEL_BG, category=dpg.mvThemeCat_Core)
            
            # General text color
            dpg.add_theme_color(dpg.mvThemeCol_Text, config.COLOR_TEXT, category=dpg.mvThemeCat_Core)
            
            # Borders for windows and frames
            dpg.add_theme_color(dpg.mvThemeCol_Border, config.COLOR_BORDER, category=dpg.mvThemeCat_Core)
            
            # Title bar color
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, config.COLOR_PANEL_BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, config.COLOR_PANEL_BG, category=dpg.mvThemeCat_Core)

            # Interactive elements (buttons, sliders, etc.)
            dpg.add_theme_color(dpg.mvThemeCol_Button, config.COLOR_PANEL_BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, config.COLOR_PANEL_BG, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, config.COLOR_PRIMARY, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, config.COLOR_PRIMARY, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (int(config.COLOR_PRIMARY[0]*1.2), int(config.COLOR_PRIMARY[1]*1.2), int(config.COLOR_PRIMARY[2]*1.2)), category=dpg.mvThemeCat_Core)

            # Style settings
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 5, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 8, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1, category=dpg.mvThemeCat_Core)

    dpg.bind_theme(global_theme)
