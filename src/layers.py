import PIL.Image as pil_image
import logging
from PIL import ImageChops # Import ImageChops for blending

# Define available blend modes (keys are for internal use, values are display names)
# Map keys to potential ImageChops functions or custom logic
BLEND_MODES = {
    'normal': 'Normal',
    'multiply': 'Multiply',
    'screen': 'Screen',
    'overlay': 'Overlay', # Requires custom implementation or approximation
    'darken': 'Darken',
    'lighten': 'Lighten',
    'add': 'Add',
    'subtract': 'Subtract',
    'difference': 'Difference',
    # Add more modes as needed
}


class Layer:
    def __init__(self, image: pil_image.Image, name: str = 'Layer', visible: bool = True):
        try:
            if image is None:
                raise ValueError("Layer oluşturulurken görüntü None olamaz")

            # Görüntünün geçerli bir PIL görüntüsü olduğundan emin ol
            if not isinstance(image, pil_image.Image):
                raise TypeError(f"Görüntü PIL.Image türünde olmalı, alınan: {type(image)}")

            # Görüntünün kopyasını al
            self.image = image.copy()

            # Görüntünün RGBA modunda olduğundan emin ol
            if self.image.mode != 'RGBA':
                self.image = self.image.convert('RGBA')

            self.name = name
            self.visible = visible
            self.blend_mode = 'normal' # Default blend mode
            self.opacity = 100  # Default opacity (0-100)
            # Orijinal boyutu sakla
            self.original_size = self.image.size
        except Exception as e:
            logging.error(f"Layer oluşturulurken hata: {e}")
            # Hata durumunda boş bir görüntü oluştur
            self.image = pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))
            self.name = name
            self.visible = visible
            self.original_size = (100, 100)
            
    def resize(self, width, height, resample=pil_image.Resampling.LANCZOS, keep_aspect_ratio=True):
        """Katman görüntüsünün çözünürlüğünü değiştirir."""
        try:
            if keep_aspect_ratio:
                # En-boy oranını koru (thumbnail metodu)
                new_img = self.image.copy()
                new_img.thumbnail((width, height), resample)
                self.image = new_img
            else:
                # En-boy oranını korumadan yeniden boyutlandır
                self.image = self.image.resize((width, height), resample)
            
            return True
        except Exception as e:
            logging.error(f"Katman yeniden boyutlandırılırken hata: {e}")
            return False
            
    def restore_original_size(self):
        """Katmanı orijinal boyutuna geri döndürür."""
        if hasattr(self, 'original_size') and self.original_size != self.image.size:
            try:
                self.image = self.image.resize(self.original_size, pil_image.Resampling.LANCZOS)
                return True
            except Exception as e:
                logging.error(f"Orijinal boyut geri yüklenirken hata: {e}")
                return False
        return False # Zaten orijinal boyutta

class LayerManager:
    def __init__(self):
        self.layers = []
        self.active_index = -1
    def add_layer(self, image: pil_image.Image, name: str = None):
        name = name or f'Layer {len(self.layers)+1}'
        layer = Layer(image.copy(), name)  # Daima kopya ile katman oluştur
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
        """
        Görünür katmanları birleştirerek tek bir görüntü oluşturur.
        Özyinelemeli referans sorunlarını önlemek için optimize edilmiştir.
        """
        try:
            # Katman yoksa None döndür
            if not self.layers:
                logging.warning("Birleştirilecek katman yok")
                return None

            # Görünür katmanları filtrele
            visible_layers = [l for l in self.layers if l.visible]
            if not visible_layers:
                logging.warning("Görünür katman yok")
                return pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))

            # Temel boyutu belirle
            base_size = self.layers[0].image.size  # (width, height)

            # Boş RGBA görüntü oluştur
            merged = pil_image.new('RGBA', base_size, (0, 0, 0, 0))

            # Görünür katmanları birleştir
            for idx, layer in enumerate(visible_layers):
                try:
                    # Katman görüntüsünün kopyasını al (özyinelemeli referansları önlemek için)
                    img_copy = layer.image.copy()

                    # Görüntü modunu kontrol et
                    if img_copy.mode != 'RGBA':
                        img_copy = img_copy.convert('RGBA')

                    # Görüntü boyutunu kontrol et
                    if img_copy.size != base_size:
                        img_copy = img_copy.resize(base_size, pil_image.Resampling.LANCZOS)

                    # Apply opacity to the layer
                    if layer.opacity < 100:
                        # Create a copy of the image with adjusted alpha
                        alpha = img_copy.getchannel('A')
                        alpha = alpha.point(lambda x: int(x * layer.opacity / 100))
                        img_copy.putalpha(alpha)

                    # --- Apply Blend Mode ---
                    blend_mode = layer.blend_mode
                    if blend_mode == 'normal':
                        # Normal blend is just alpha compositing
                        merged = pil_image.alpha_composite(merged, img_copy)
                    else:
                        # For other modes, blend RGB channels first, then composite alpha
                        # Ensure both images are RGB for ImageChops
                        merged_rgb = merged.convert('RGB')
                        layer_rgb = img_copy.convert('RGB')
                        blended_rgb = merged_rgb # Default to base if mode unknown

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
                            # Overlay is complex, approximate using screen/multiply
                            # Formula: if base < 0.5: 2 * base * blend else: 1 - 2 * (1-base) * (1-blend)
                            # Simplified: Screen for dark areas, Multiply for light areas
                            dark = ImageChops.multiply(merged_rgb, layer_rgb.point(lambda i: i * 2))
                            light = ImageChops.screen(merged_rgb, layer_rgb.point(lambda i: (i - 128) * 2))
                            # Use layer's RGB as mask to choose between dark/light based on layer brightness
                            mask = layer_rgb.convert('L').point(lambda i: 255 if i > 127 else 0)
                            blended_rgb = pil_image.composite(light, dark, mask)
                        else:
                            logging.warning(f"Bilinmeyen blend modu: {blend_mode}, 'normal' kullanılıyor.")
                            merged = pil_image.alpha_composite(merged, img_copy) # Fallback to normal
                            continue # Skip alpha compositing below if falling back

                        # Convert blended RGB back to RGBA using the *layer's* alpha as the mask
                        blended_rgba = blended_rgb.convert('RGBA')
                        blended_rgba.putalpha(img_copy.getchannel('A'))

                        # Composite the blended layer onto the merged image using alpha compositing
                        # This correctly handles the transparency of the blended layer itself
                        merged = pil_image.alpha_composite(merged, blended_rgba)

                    # Ara referansları temizle
                    img_copy = None
                    blended_rgb = None
                    blended_rgba = None
                    merged_rgb = None
                    layer_rgb = None
                except Exception as e:
                    logging.error(f"Katman {idx} birleştirilirken hata: {e}")
                    continue

            # Sonuç görüntüsünün kopyasını döndür (özyinelemeli referansları önlemek için)
            result = merged.copy()

            # Ara referansları temizle
            merged = None

            return result
        except Exception as e:
            logging.error(f"Katmanlar birleştirilirken hata: {e}")
            # Hata durumunda boş bir görüntü döndür
            return pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))
    def toggle_visibility(self, index):
        if 0 <= index < len(self.layers):
            self.layers[index].visible = not self.layers[index].visible
