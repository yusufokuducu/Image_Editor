# Image Editor - Ampcode Style

Modern, professional image editor built with PyQt5, featuring a dark Ampcode-inspired design.

## Features

✨ **Adjustments**
- Brightness control (-100 to 100)
- Contrast adjustment (-100 to 100)
- Saturation control (-100 to 100)
- Sharpness enhancement (0 to 100)

🎨 **Filters**
- Blur (1 to 50)
- Noise addition (0 to 50)
- Grayscale conversion
- Sepia tone
- Edge detection

🔄 **Transform**
- Resize with custom dimensions
- Rotate (±180 degrees)
- Flip horizontal
- Flip vertical

⏮️ **Edit Controls**
- Undo/Redo functionality (up to 20 states)
- Reset to original image
- Save in PNG or JPEG format

## Installation

1. Install Python 3.8 or higher
2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

1. Click "Load Image" to open an image file
2. Use the three tabs to adjust, filter, or transform your image
3. Use Undo/Redo to revert or restore changes
4. Click "Save Image" to export your edited image
5. Click "Reset" to return to the original image

## Project Structure

- `main.py` - Main PyQt5 application
- `image_processor.py` - Image processing logic using OpenCV and Pillow
- `undo_redo.py` - Undo/Redo state management
- `requirements.txt` - Python dependencies

## Requirements

- PyQt5 5.15.9
- Pillow 10.1.0
- OpenCV 4.8.1.78
- NumPy 1.24.3

## License

MIT License
