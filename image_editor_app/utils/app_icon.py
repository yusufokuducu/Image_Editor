from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """Create a simple app icon for the image editor"""
    # Create a new image with a dark background
    icon_size = 256
    icon = Image.new('RGBA', (icon_size, icon_size), (40, 44, 52, 255))
    draw = ImageDraw.Draw(icon)
    
    # Draw a stylized camera/editor icon
    # Draw lens circle
    center = icon_size // 2
    radius = icon_size // 3
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), 
                 fill=(90, 95, 120, 255), outline=(120, 125, 160, 255), width=3)
    
    # Draw inner lens
    inner_radius = radius * 0.7
    draw.ellipse((center - inner_radius, center - inner_radius, center + inner_radius, center + inner_radius), 
                 fill=(65, 70, 95, 255), outline=(100, 105, 140, 255), width=2)
    
    # Draw camera body
    body_width = icon_size * 0.8
    body_height = icon_size * 0.18
    body_left = (icon_size - body_width) / 2
    body_top = center + radius * 0.8
    draw.rounded_rectangle((body_left, body_top, body_left + body_width, body_top + body_height), 
                          radius=10, fill=(100, 105, 140, 255))
    
    # Draw small buttons on top of camera
    button_size = icon_size * 0.08
    for i in range(3):
        x_pos = body_left + body_width * (0.25 + i * 0.25)
        draw.ellipse((x_pos - button_size/2, body_top + body_height/4, 
                      x_pos + button_size/2, body_top + body_height*3/4), 
                     fill=(65, 70, 95, 255))
    
    # Draw edit pen
    pen_length = icon_size * 0.5
    pen_width = icon_size * 0.06
    pen_x = center + radius * 0.5
    pen_y = center - radius * 0.6
    # Angle the pen
    draw.line((pen_x, pen_y, pen_x - pen_length * 0.8, pen_y + pen_length * 0.6), 
              fill=(230, 230, 250, 255), width=int(pen_width))
    # Pen tip
    draw.polygon([(pen_x - pen_length * 0.85, pen_y + pen_length * 0.65),
                  (pen_x - pen_length * 0.75, pen_y + pen_length * 0.55),
                  (pen_x - pen_length * 0.95, pen_y + pen_length * 0.7)], 
                 fill=(240, 100, 100, 255))
    
    # Save the icon
    os.makedirs('resources', exist_ok=True)
    icon_path = os.path.join('resources', 'app_icon.png')
    icon.save(icon_path)
    
    return icon_path

if __name__ == "__main__":
    # Generate the icon if this script is run directly
    icon_path = create_app_icon()
    print(f"Icon created and saved to {icon_path}")
    
    # Display the icon
    try:
        Image.open(icon_path).show()
    except Exception as e:
        print(f"Error displaying icon: {e}") 