import os

# UI Teması
ACCENT_COLOR = "#3a7ebf"
SECONDARY_COLOR = "#2a5d8f"
SUCCESS_COLOR = "#2d9657"
WARNING_COLOR = "#d19a41"
ERROR_COLOR = "#b33f3f"

# UI Yazı Tipleri
FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Helvetica"
TITLE_FONT = (FONT_FAMILY, 20, "bold")
SUBTITLE_FONT = (FONT_FAMILY, 16, "bold")
BUTTON_FONT = (FONT_FAMILY, 12)
LABEL_FONT = (FONT_FAMILY, 12)
SMALL_FONT = (FONT_FAMILY, 10)

# Maksimum önizleme boyutu - daha büyük görüntüler önizleme için bu boyuta küçültülecek
MAX_PREVIEW_WIDTH = 1200
MAX_PREVIEW_HEIGHT = 800 