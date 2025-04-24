from PIL import Image

class Layer:
    def __init__(self, image: Image.Image, name: str = 'Layer', visible: bool = True):
        self.image = image.copy()
        self.name = name
        self.visible = visible

class LayerManager:
    def __init__(self):
        self.layers = []
        self.active_index = -1
    def add_layer(self, image: Image.Image, name: str = None):
        name = name or f'Layer {len(self.layers)+1}'
        layer = Layer(image, name)
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
        # Basit üst üste bindirme (alttan üste)
        if not self.layers:
            return None
        base = self.layers[0].image.copy()
        for l in self.layers[1:]:
            if l.visible:
                base.alpha_composite(l.image)
        return base
    def toggle_visibility(self, index):
        if 0 <= index < len(self.layers):
            self.layers[index].visible = not self.layers[index].visible
