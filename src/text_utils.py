import os
import platform
import logging
from PIL import Image, ImageDraw, ImageFont
def get_pil_font(family, size, style="Regular"):
    font_file = None
    try:
        if platform.system() == "Windows":
            font_dir = "C:/Windows/Fonts"
            potential_files = [f for f in os.listdir(font_dir) if f.lower().endswith(('.ttf', '.otf')) and family.lower() in f.lower()]
            if potential_files:
                style_matches = [f for f in potential_files if style.lower() in f.lower()]
                if style_matches:
                    font_file = os.path.join(font_dir, style_matches[0])
                else:
                    font_file = os.path.join(font_dir, potential_files[0]) 
            else: 
                 font_file = os.path.join(font_dir, "arial.ttf")
        elif platform.system() == "Darwin": 
            font_dir = "/Library/Fonts" 
            user_font_dir = os.path.expanduser("~/Library/Fonts")
            found = False
            for d in [font_dir, user_font_dir]:
                 if os.path.exists(d):
                    potential_files = [f for f in os.listdir(d) if f.lower().endswith(('.ttf', '.otf', '.ttc')) and family.lower() in f.lower()]
                    if potential_files:
                        style_matches = [f for f in potential_files if style.lower() in f.lower()]
                        if style_matches:
                            font_file = os.path.join(d, style_matches[0])
                        else:
                            font_file = os.path.join(d, potential_files[0])
                        found = True
                        break
            if not found: 
                font_file = "/System/Library/Fonts/Helvetica.ttc" 
        else: 
            font_dirs = ["/usr/share/fonts/truetype", "/usr/share/fonts/opentype", os.path.expanduser("~/.fonts")]
            found = False
            for d in font_dirs:
                if os.path.exists(d):
                    for root, _, files in os.walk(d):
                        potential_files = [f for f in files if f.lower().endswith(('.ttf', '.otf')) and family.lower() in f.lower()]
                        if potential_files:
                            style_matches = [f for f in potential_files if style.lower() in f.lower()]
                            if style_matches:
                                font_file = os.path.join(root, style_matches[0])
                            else:
                                font_file = os.path.join(root, potential_files[0])
                            found = True
                            break
                if found: break
            if not found: 
                dejavu_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                if os.path.exists(dejavu_path):
                    font_file = dejavu_path
                else: 
                    font_file = "arial.ttf" 
        if font_file and os.path.exists(font_file):
             logging.info(f"Using font file: {font_file} for family {family}, size {size}")
             return ImageFont.truetype(font_file, size)
        else:
             logging.warning(f"Font file for '{family}' not found or path invalid: {font_file}. Falling back to default.")
             return ImageFont.load_default()
    except ImportError:
        logging.error("PIL/Pillow ImageFont not found. Please install Pillow.")
        return None
    except Exception as e:
        logging.error(f"Error loading font '{family}' size {size}: {e}. Falling back to default.")
        try:
            return ImageFont.load_default() 
        except:
             return None 
def draw_text_on_image(img: Image.Image, text: str, position: tuple, font: ImageFont.FreeTypeFont, color: tuple):
    if img is None or font is None:
        logging.error("draw_text_on_image: Görüntü veya font geçersiz.")
        return None
    try:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        draw = ImageDraw.Draw(img)
        draw.text(position, text, fill=color, font=font)
        return img
    except Exception as e:
        logging.error(f"Metin çizilirken hata: {e}")
        return None