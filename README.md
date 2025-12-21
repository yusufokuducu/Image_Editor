# Professional Image Editor

A comprehensive, professional-grade image editing application built with PyQt5, featuring advanced color correction, powerful filters, and an intuitive dark-themed interface.

## ✨ Features

### Core Editing
- **Real-time Preview** - See changes instantly
- **Undo/Redo** - Up to 20 action history
- **Crop Tool** - Interactive crop with visual feedback
- **Zoom & Pan** - 10-300% zoom levels
- **Before/After Compare** - Toggle to view original vs edited

### Adjustments
- Brightness (-100 to 100)
- Contrast (-100 to 100)
- Saturation (-100 to 100)
- Sharpness (0 to 100)
- Hue Rotation (-180° to 180°)
- **Levels** - Black/white point adjustment
- **Color Grading** - Warm/Cool/Dark/Bright presets

### Filters & Effects
- Gaussian Blur (1-50)
- Noise Addition (0-50)
- Grayscale Conversion
- Sepia Tone
- Edge Detection
- Vignette (0-100)
- Posterize (2-256 levels)

### Professional Tools
- **Histogram Analysis** - RGB channel visualization
- **Image Statistics** - Mean, std dev, dimensions
- **Color Temperature** - Warm/Cool adjustments
- **HSV Adjustment** - Direct hue, saturation, value control

### Transform Operations
- **Resize** - Custom dimensions
- **Rotate** - 360° rotation
- **Flip** - Horizontal & vertical
- **Crop** - Interactive selection

### Interface
- **Menu Bar** - File, Edit, Tools, View, Help
- **Status Bar** - Real-time feedback
- **Keyboard Shortcuts** - Ctrl+O, Ctrl+S, Ctrl+Z, etc.
- **Recent Files** - Quick access to last 10 images
- **Dark Mode** - Professional Ampcode-style theme
- **Responsive Layout** - Optimized for various screen sizes

### File Management
- **Multiple Formats** - PNG, JPG, BMP, GIF, TIFF
- **Drag & Drop** - Load images by dragging
- **Save As** - Multiple format export
- **Recent Files** - Auto-saved history

## 🚀 Installation

1. Install Python 3.8+
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📖 Usage

```bash
python main.py
```

### Basic Workflow
1. **Open** → File > Open Image (Ctrl+O) or drag & drop
2. **Edit** → Use tabs to adjust, filter, or transform
3. **Confirm** → Click "Confirm" to save to history
4. **Undo/Redo** → Ctrl+Z / Ctrl+Y for history navigation
5. **Save** → File > Save (Ctrl+S) in desired format
6. **Reset** → Start over with Ctrl+R

### Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open Image |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+R | Reset |
| C | Crop Tool |
| Ctrl+Q | Exit |
| Ctrl+0 | Fit to Window |

## 🎨 Advanced Features

### Color Correction
1. Go to **Colors** tab
2. Adjust **Levels** for precise control
3. Use **Color Presets** for quick styling
4. Fine-tune with **Saturation** in Adjustments

### Image Analysis
1. Open **Analysis** tab
2. View histogram for RGB channels
3. Check image statistics
4. Use for exposure decision-making

### Professional Workflow
1. Load image and analyze histogram
2. Apply basic adjustments (brightness, contrast)
3. Use levels for precise tone mapping
4. Apply color presets or manual color grading
5. Add effects and filters
6. Compare before/after
7. Save in appropriate format

## 📁 Project Structure

```
Image_Editor/
├── main.py                 # Main application & UI
├── image_processor.py      # Image processing engine
├── crop_tool.py           # Interactive crop tool
├── undo_redo.py           # History management
├── requirements.txt       # Python dependencies
├── recent_files.json      # Auto-generated recent files
└── README.md              # This file
```

## 🔧 Technical Details

- **Image Processing** → OpenCV (cv2)
- **PIL Enhancement** → Pillow
- **Color Spaces** → BGR, HSV, RGB support
- **History** → Memory-efficient state management
- **Theme** → Dark mode with accent colors
- **Performance** → Optimized for 4K+ images

## 📊 Supported Formats

| Format | Read | Write |
|--------|------|-------|
| PNG | ✓ | ✓ |
| JPEG | ✓ | ✓ |
| BMP | ✓ | ✓ |
| GIF | ✓ | ✗ |
| TIFF | ✓ | ✗ |

## ⚙️ Requirements

- PyQt5 >= 5.15.9
- OpenCV >= 4.9.0
- Pillow >= 11.0.0
- NumPy >= 1.24.0

## 🎯 Tips & Tricks

1. **Adjustment Combos** - Stack multiple adjustments for custom looks
2. **Histogram Guide** - Use histogram to check exposure
3. **Smart Presets** - Color presets are starting points, tweak further
4. **Zoom For Details** - Use zoom (10-300%) to inspect pixel-level edits
5. **Compare Always** - Use Before/After toggle to verify changes

## 🐛 Known Limitations

- Large images (>10MP) may require more processing time
- Real-time filters work best on images <8MP
- Some effects best viewed at 100% zoom

## 📝 License

MIT License - Free to use and modify

## 🤝 Contributing

Feel free to report issues or suggest features!

---

**Made with ❤️ using PyQt5 and OpenCV**
