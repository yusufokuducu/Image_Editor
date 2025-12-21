# Professional Image Editor

A sophisticated, production-ready image editing application built with PyQt5 and OpenCV. Designed for professionals and enthusiasts who demand precision, performance and an elegant user experience.

---

## Overview

Professional Image Editor is a comprehensive desktop application that brings professional-grade image manipulation capabilities to your fingertips. With an intuitive dark-themed interface inspired by modern design systems, powerful color correction tools and advanced filtering capabilities, it's the ideal companion for photographers, designers and visual content creators.

Built on battle-tested libraries (PyQt5, OpenCV, Pillow), the application prioritizes stability, performance and user experience while maintaining an elegant codebase.

---

## Core Capabilities

### Image Adjustment & Correction

**Real-time Adjustments**
- Brightness control with precise value display
- Contrast enhancement for tonal range optimization
- Saturation adjustment for color intensity control
- Sharpness enhancement for detail accentuation
- Hue rotation for creative color grading
- Levels tool for advanced tone mapping

**Color Grading**
- Professional-grade color temperature control
- Warm/Cool tone presets for quick stylization
- HSV color space manipulation
- Black/white point adjustment
- RGB channel analysis via histogram

### Filtering Engine

**Standard Filters**
- Gaussian blur with variable radius (1-50)
- Additive noise generation for texture
- Grayscale conversion
- Sepia tone application
- Canny edge detection

**Advanced Effects**
- Vignette effect with intensity control
- Posterization with adjustable color levels
- Custom preset filters

### Image Transformation

**Geometric Operations**
- Precise crop tool with interactive selection
- Arbitrary resize with dimension control
- 360-degree rotation
- Horizontal and vertical flip

**Interactive Tools**
- Visual crop rectangle with handles
- Real-time preview during transformations
- Zoom functionality (10-300% magnification)

### Professional Analysis

**Histogram & Statistics**
- Real-time histogram calculation
- Per-channel RGB visualization
- Image statistics (dimensions, mean values, standard deviation)
- Statistical guidance for exposure correction

**Image Information**
- File metadata display
- Pixel dimensions
- File size reporting

### Workflow Management

**History & Undo System**
- Comprehensive undo/redo stack (20-state memory)
- Non-destructive editing (original preserved)
- Before/after comparison toggle
- State visualization in status bar

**File Operations**
- Multi-format support (PNG, JPEG, BMP, GIF, TIFF)
- Drag-and-drop image loading
- Recent files tracking (10-file memory)
- Save and Save As functionality
- Format selection on export

---

## Installation & Setup

### Requirements

- Python 3.8 or higher
- Operating System: Windows, macOS, or Linux
- Minimum 2GB RAM recommended
- 50MB disk space

### Quick Start

1. **Clone or download the repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application**
   ```bash
   python main.py
   ```

### Dependency Details

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt5 | 5.15.9+ | GUI framework |
| OpenCV | 4.9.0+ | Image processing |
| Pillow | 11.0.0+ | Image enhancement |
| NumPy | 1.24.0+ | Numerical operations |

---

## Usage Guide

### Basic Workflow

```
Load Image → Analyze → Adjust → Preview → Save
```

### Step-by-Step Tutorial

**1. Loading Images**
- Use File → Open Image or press Ctrl+O
- Alternatively, drag and drop image file onto canvas
- Recent files accessible via File → Recent Files

**2. Image Analysis**
- Switch to Analysis tab for histogram visualization
- Review image statistics for exposure guidance
- Use histogram to inform adjustment decisions

**3. Applying Adjustments**
- Navigate to Adjustments tab
- Use sliders for real-time preview
- Stack multiple adjustments for custom looks
- Click "Confirm Adjustments" to save to history

**4. Color Grading**
- Colors tab provides professional color tools
- Adjust levels for precise tone mapping
- Apply color presets as starting points
- Fine-tune with hue/saturation controls

**5. Applying Filters**
- Select desired filter from Filters tab
- Adjust intensity with sliders
- Preview updates in real-time
- Confirm to add to undo history

**6. Transformations**
- Transform tab contains resize, rotate, crop
- Crop tool: activate, click-drag to select, release to confirm
- Rotation: slider adjusts angle in real-time
- Resize: set dimensions and apply

**7. Exporting**
- File → Save or press Ctrl+S
- Select format (PNG recommended for quality)
- Choose destination directory
- Confirm export

### Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| Ctrl+O | Open Image |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+R | Reset to Original |
| C | Activate Crop Tool |
| Ctrl+Q | Exit Application |
| Ctrl+0 | Fit to Window |

---

## Advanced Features

### Professional Color Correction Workflow

1. **Exposure & Levels**
   - Open Colors tab
   - Use Levels tool to set black/white points
   - Target histogram: no clipping in shadows/highlights

2. **Color Cast Removal**
   - Adjust Color Temperature slider
   - Fine-tune with Hue Rotation

3. **Tonal Enhancement**
   - Apply Brightness/Contrast adjustments
   - Use Saturation for color intensity
   - Verify with histogram

4. **Detail Enhancement**
   - Apply Sharpness from Adjustments tab
   - Avoid over-sharpening (halo artifacts)

5. **Creative Styling**
   - Apply color presets for starting point
   - Layer effects from Effects tab
   - Compare before/after regularly

### Batch Processing Tips

While single-image focus, you can:
- Save edits as PNG with alpha channel
- Use recent files for quick sequential editing
- Reset between images with Ctrl+R

---

## Technical Architecture

### Module Structure

```
main.py
├── ImageEditor (QMainWindow)
│   ├── Menu Bar System
│   ├── Image Display & Zoom
│   ├── Control Panels
│   └── Status Management
│
image_processor.py
├── ImageProcessor
│   ├── Image I/O
│   ├── Color Space Conversions
│   └── Filter Pipeline
│
crop_tool.py
├── CropTool (Custom QLabel)
│   ├── Interactive Selection
│   └── Visual Feedback
│
undo_redo.py
├── UndoRedoManager
│   └── State Stack Management
```

### Performance Characteristics

| Operation | Time Estimate | Resolution |
|-----------|---------------|------------|
| Load Image | <500ms | Up to 16MP |
| Real-time Adjustment | Instant | Up to 8MP |
| Export PNG | 1-3s | Up to 8MP |
| Histogram Calculation | <100ms | Up to 16MP |

Larger images may require proportionally longer processing times.

---

## Supported File Formats

### Input Formats
- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff, .tif)

### Output Formats
- PNG (.png) - Recommended for lossless quality
- JPEG (.jpg) - Recommended for web
- BMP (.bmp) - Uncompressed bitmap

---

## Configuration & Preferences

### Persistent Settings
- Window geometry and state automatically saved
- Recent files list maintained in `recent_files.json`
- Application restores previous state on launch

### Customization
- Dark theme applied automatically
- Color accent: Professional blue (#4a9eff)
- Zoom range: 10% to 300%

---

## Project Structure

```
Image_Editor/
├── main.py                 # Primary application entry point
├── image_processor.py      # Core image processing engine
├── crop_tool.py           # Interactive crop widget
├── undo_redo.py           # History management system
├── requirements.txt       # Dependency specification
├── recent_files.json      # Auto-generated recent files list
└── README.md              # Documentation
```

---

## Best Practices

### For Image Quality
1. Always review histogram before/after adjustments
2. Avoid extreme adjustments (preserve tonal range)
3. Use PNG format for archival
4. Save original unedited version separately

### For Performance
1. Work with appropriately-sized images (avoid >8MP for real-time)
2. Apply filters in logical order
3. Use presets as starting points vs manual adjustments
4. Zoom to 100% for detail-critical work

### For Workflows
1. Analyze image before making edits
2. Start with exposure/levels
3. Add color corrections
4. Apply effects last
5. Compare before/after regularly
6. Save incrementally during complex edits

---

## Troubleshooting

### Application Won't Start
- Verify Python 3.8+ installation
- Confirm all dependencies installed: `pip install -r requirements.txt`
- Check that PyQt5 libraries are properly installed

### Slow Performance
- Reduce image resolution
- Close other memory-intensive applications
- Work with PNG instead of complex formats
- Limit undo history to critical operations

### Export Issues
- Ensure write permissions to destination folder
- Verify sufficient disk space
- Try different format (PNG vs JPEG)
- Check file path for invalid characters

### Histogram Not Displaying
- Load image first
- Click "Refresh Analysis" in Analysis tab
- Ensure image has color data (not corrupt)

---

## System Requirements

### Minimum
- CPU: Dual-core 2GHz processor
- RAM: 2GB
- Storage: 100MB
- Display: 1024x768 resolution

### Recommended
- CPU: Quad-core 2.5GHz or higher
- RAM: 8GB+
- Storage: 500MB SSD
- Display: 1920x1080 or higher

---

## Future Roadmap

Potential enhancements:
- Batch processing capabilities
- Custom preset saving/loading
- Plugin architecture for filters
- GPU acceleration for large images
- Layer-based editing
- Non-destructive filter stacks

---

## Technical Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | PyQt5 |
| Image Processing | OpenCV (cv2) |
| Image Enhancement | Pillow (PIL) |
| Numerical Computing | NumPy |
| Color Space Handling | OpenCV HSV/BGR conversion |

---

## Contributing

Bug reports and feature suggestions are welcome. Please document:
- Steps to reproduce issues
- Python version and OS
- Expected vs actual behavior

---

## License

MIT License - Free for personal and commercial use

---

## About

Crafted with precision for professionals and enthusiasts who value clean code, elegant design and powerful functionality. Built to handle real-world image editing workflows without unnecessary complexity.

---

**Image Editor v1.0**  
*Precise. Powerful. Professional.*