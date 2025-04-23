"""
Pro Image Editor Package
A professional image editing application with advanced filters and effects
"""

__version__ = "1.0.0"

from image_editor_app.app import ImageEditor

# Provide a simple way to run the application
def run():
    app = ImageEditor()
    app.mainloop() 