import dearpygui.dearpygui as dpg

for attr in dir(dpg):
    if "Key_" in attr:
        print(attr)
