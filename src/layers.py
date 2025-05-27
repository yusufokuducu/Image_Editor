import PIL.Image as pil_image
import logging
from PIL import ImageChops 
BLEND_MODES = {
    'normal': 'Normal',
    'multiply': 'Multiply',
    'screen': 'Screen',
    'overlay': 'Overlay', 
    'darken': 'Darken',
    'lighten': 'Lighten',
    'add': 'Add',
    'subtract': 'Subtract',
    'difference': 'Difference',
}
class Layer:
    def __init__(self, image: pil_image.Image, name: str = 'Layer', visible: bool = True):
        try:
            if image is None:
                raise ValueError("Layer oluşturulurken görüntü None olamaz")
            if not isinstance(image, pil_image.Image):
                raise TypeError(f"Görüntü PIL.Image türünde olmalı, alınan: {type(image)}")
            self.image = image.copy()
            if self.image.mode != 'RGBA':
                self.image = self.image.convert('RGBA')
            self.name = name
            self.visible = visible
            self.blend_mode = 'normal' 
            self.opacity = 100  
            self.original_size = self.image.size
        except Exception as e:
            logging.error(f"Layer oluşturulurken hata: {e}")
            self.image = pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))
            self.name = name
            self.visible = visible
            self.original_size = (100, 100)
    def resize(self, width, height, resample=pil_image.Resampling.LANCZOS, keep_aspect_ratio=True):
        try:
            if keep_aspect_ratio:
                new_img = self.image.copy()
                new_img.thumbnail((width, height), resample)
                self.image = new_img
            else:
                self.image = self.image.resize((width, height), resample)
            return True
        except Exception as e:
            logging.error(f"Katman yeniden boyutlandırılırken hata: {e}")
            return False
    def restore_original_size(self):
        if hasattr(self, 'original_size') and self.original_size != self.image.size:
            try:
                self.image = self.image.resize(self.original_size, pil_image.Resampling.LANCZOS)
                return True
            except Exception as e:
                logging.error(f"Orijinal boyut geri yüklenirken hata: {e}")
                return False
        return False 
class LayerManager:
    def __init__(self):
        self.layers = []
        self.active_index = -1
    def add_layer(self, image: pil_image.Image, name: str = None):
        name = name or f'Layer {len(self.layers)+1}'
        layer = Layer(image.copy(), name)  
        self.layers.append(layer)
        self.active_index = len(self.layers) - 1
    def remove_layer(self, index):
        if 0 <= index < len(self.layers):
            del self.layers[index]
            self.active_index = min(self.active_index, len(self.layers)-1)
    def move_layer(self, from_idx, to_idx):
        if 0 <= from_idx < len(self.layers) and 0 <= to_idx < len(self.layers):
            layer = self.layers.pop(from_idx)
            self.layers.insert(to_idx, layer)
            self.active_index = to_idx
    def get_active_layer(self):
        if 0 <= self.active_index < len(self.layers):
            return self.layers[self.active_index]
        return None
    def set_active_layer(self, index):
        if 0 <= index < len(self.layers):
            self.active_index = index
    def merge_visible(self):
        try:
            if not self.layers:
                logging.warning("Birleştirilecek katman yok")
                return None
            visible_layers = [l for l in self.layers if l.visible]
            if not visible_layers:
                logging.warning("Görünür katman yok")
                return pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))
            base_size = self.layers[0].image.size  
            merged = pil_image.new('RGBA', base_size, (0, 0, 0, 0))
            for idx, layer in enumerate(visible_layers):
                try:
                    img_copy = layer.image.copy()
                    if img_copy.mode != 'RGBA':
                        img_copy = img_copy.convert('RGBA')
                    if img_copy.size != base_size:
                        img_copy = img_copy.resize(base_size, pil_image.Resampling.LANCZOS)
                    if layer.opacity < 100:
                        alpha = img_copy.getchannel('A')
                        alpha = alpha.point(lambda x: int(x * layer.opacity / 100))
                        img_copy.putalpha(alpha)
                    blend_mode = layer.blend_mode
                    if blend_mode == 'normal':
                        merged = pil_image.alpha_composite(merged, img_copy)
                    else:
                        merged_rgb = merged.convert('RGB')
                        layer_rgb = img_copy.convert('RGB')
                        blended_rgb = merged_rgb 
                        if blend_mode == 'multiply':
                            blended_rgb = ImageChops.multiply(merged_rgb, layer_rgb)
                        elif blend_mode == 'screen':
                            blended_rgb = ImageChops.screen(merged_rgb, layer_rgb)
                        elif blend_mode == 'darken':
                            blended_rgb = ImageChops.darker(merged_rgb, layer_rgb)
                        elif blend_mode == 'lighten':
                            blended_rgb = ImageChops.lighter(merged_rgb, layer_rgb)
                        elif blend_mode == 'add':
                            blended_rgb = ImageChops.add(merged_rgb, layer_rgb, scale=1.0, offset=0)
                        elif blend_mode == 'subtract':
                            blended_rgb = ImageChops.subtract(merged_rgb, layer_rgb, scale=1.0, offset=0)
                        elif blend_mode == 'difference':
                            blended_rgb = ImageChops.difference(merged_rgb, layer_rgb)
                        elif blend_mode == 'overlay':
                            dark = ImageChops.multiply(merged_rgb, layer_rgb.point(lambda i: i * 2))
                            light = ImageChops.screen(merged_rgb, layer_rgb.point(lambda i: (i - 128) * 2))
                            mask = layer_rgb.convert('L').point(lambda i: 255 if i > 127 else 0)
                            blended_rgb = pil_image.composite(light, dark, mask)
                        else:
                            logging.warning(f"Bilinmeyen blend modu: {blend_mode}, 'normal' kullanılıyor.")
                            merged = pil_image.alpha_composite(merged, img_copy) 
                            continue 
                        blended_rgba = blended_rgb.convert('RGBA')
                        blended_rgba.putalpha(img_copy.getchannel('A'))
                        merged = pil_image.alpha_composite(merged, blended_rgba)
                    img_copy = None
                    blended_rgb = None
                    blended_rgba = None
                    merged_rgb = None
                    layer_rgb = None
                except Exception as e:
                    logging.error(f"Katman {idx} birleştirilirken hata: {e}")
                    continue
            result = merged.copy()
            merged = None
            return result
        except Exception as e:
            logging.error(f"Katmanlar birleştirilirken hata: {e}")
            return pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))
    def toggle_visibility(self, index):
        if 0 <= index < len(self.layers):
            self.layers[index].visible = not self.layers[index].visible