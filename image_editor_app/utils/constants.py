import os

# UI Teması (Siyah/Dark Mode)
ACCENT_COLOR = "#1DB954"  # Canlı yeşil vurgulu (Spotify tarzı)
SECONDARY_COLOR = "#23272A" # Sidebar ve butonlar için koyu gri
SUCCESS_COLOR = "#121212" # Ana arka plan (simsiyah)
WARNING_COLOR = "#393E46" # Hafif koyu bölümler
ERROR_COLOR = "#FF3B30"   # Kırmızı hata vurgusu

# Ana arka plan rengi
BACKGROUND_COLOR = "#18191A"
PRIMARY_COLOR = "#121212"

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