from PIL import ImageDraw

class ShapeTool:
    def __init__(self, color, shape_type='rectangle', fill=True):
        self.color = color
        self.shape_type = shape_type
        self.fill = fill
        self.size = 2  # Default stroke size

class LineTool(ShapeTool):
    def __init__(self, color, fill=False):
        super().__init__(color, shape_type='line', fill=fill)

class RectangleTool(ShapeTool):
    def __init__(self, color, fill=True):
        super().__init__(color, shape_type='rectangle', fill=fill)

class EllipseTool(ShapeTool):
    def __init__(self, color, fill=True):
        super().__init__(color, shape_type='ellipse', fill=fill)
        
    def set_color(self, color):
        self.color = color
        
    def set_size(self, size):
        self.size = size
        
    def apply_to_layer(self, layer, points):
        """Draw shape on layer between start and end points"""
        if not points or len(points) < 2:
            return False
            
        start = points[0]
        end = points[-1]
        
        # Convert points to PIL coordinates
        x1, y1 = int(start.x()), int(start.y())
        x2, y2 = int(end.x()), int(end.y())
        
        # Create a new image for the shape
        shape_img = layer.image.copy()
        draw = ImageDraw.Draw(shape_img)
        
        # Calculate stroke width
        stroke_width = self.size
        
        # Draw the shape based on type
        if self.shape_type == 'rectangle':
            if self.fill:
                draw.rectangle((x1, y1, x2, y2), fill=self.color)
            else:
                draw.rectangle((x1, y1, x2, y2), outline=self.color, width=stroke_width)
                
        elif self.shape_type == 'ellipse':
            if self.fill:
                draw.ellipse((x1, y1, x2, y2), fill=self.color)
            else:
                draw.ellipse((x1, y1, x2, y2), outline=self.color, width=stroke_width)
                
        elif self.shape_type == 'line':
            draw.line((x1, y1, x2, y2), fill=self.color, width=stroke_width)
            
        # Update the layer with the new image
        layer.image = shape_img
        return True
