import PIL.Image as pil_image

class Layer:
    def __init__(self, image: pil_image.Image, name: str = 'Layer', visible: bool = True):
        self.image = image.copy()
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
        import logging
        if not self.layers:
            return None
        base_size = self.layers[0].image.size  # (width, height)
        # PIL ile boş RGBA görüntü
        merged = pil_image.new('RGBA', base_size, (0, 0, 0, 0))
        for idx, l in enumerate(self.layers):
            img = l.image
            logging.debug(f'Layer {idx}: mode={getattr(img, "mode", None)}, size={getattr(img, "size", None)}')
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            if img.size != base_size:
                img = img.resize(base_size)
            # Recursive referans kontrolü
            if hasattr(img, '__dict__') and any(id(img) == id(v) for v in img.__dict__.values()):
                logging.error(f'Layer {idx} image recursive referans içeriyor!')
                continue
            if l.visible:
                # Alpha kompozisyon
                merged = pil_image.alpha_composite(merged, img)
        if merged.mode != 'RGBA':
            merged = merged.convert('RGBA')
        return merged
    def toggle_visibility(self, index):
        if 0 <= index < len(self.layers):
            self.layers[index].visible = not self.layers[index].visible
