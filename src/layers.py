import PIL.Image as pil_image
import logging

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
        except Exception as e:
            logging.error(f"Layer oluşturulurken hata: {e}")
            # Hata durumunda boş bir görüntü oluştur
            self.image = pil_image.new('RGBA', (100, 100), (0, 0, 0, 0))
            self.name = name
            self.visible = visible

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

                    # Alpha kompozisyon
                    merged = pil_image.alpha_composite(merged, img_copy)

                    # Ara referansları temizle
                    img_copy = None
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
