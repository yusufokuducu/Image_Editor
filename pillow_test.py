from PIL import Image

# Create two RGBA images
base = Image.new('RGBA', (100, 100), (255, 0, 0, 255))
over = Image.new('RGBA', (100, 100), (0, 255, 0, 128))

# Paste the overlay onto the base with itself as mask
base.paste(over, (0, 0), over)

# Save the result
base.save('pillow_test_output.png')
print('Saved pillow_test_output.png successfully.')
