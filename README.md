# Image_Editor

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📋 Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage](#usage)
- [Tools](#tools)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## 🔭 Overview

Image_Editor is a professional-grade image editing application developed in Python. Built on powerful libraries like CustomTkinter, PIL (Pillow), NumPy, and OpenCV, this application stands out with its advanced image processing capabilities and user-friendly interface.

This project aims to provide a comprehensive image editing solution for both professional photographers and hobbyists.

## ✨ Features

### Image Processing
- **Basic Edits**: Cropping, rotation, flipping, resizing
- **Color Adjustments**: Brightness, contrast, saturation, hue
- **Layers**: Multi-layer support, blending modes, opacity settings
- **Filters**: Blur, sharpen, edge detection, noise reduction
- **Selection Tools**: Rectangle, ellipse, freehand, and color-based selectors

### User Interface
- **Modern Design**: Contemporary interface created with CustomTkinter
- **Customizable Workspace**: Customize panel layouts
- **Dark/Light Mode**: Theme options compatible with system settings
- **Toolbars**: Intuitively organized tools

### File Operations
- **Multiple Format Support**: JPG, PNG, TIFF, BMP, GIF, WebP
- **Project Files**: Save/load including layers and editing history
- **Batch Processing**: Apply the same operations across multiple files

## 📸 Screenshots

*Screenshots to be added here*

## 🚀 Installation

### Requirements
- Python 3.8 or above
- pip (Python package manager)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/faust-lvii/Image_Editor.git
   cd Image_Editor
   ```

2. Create a virtual environment (optional):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:
   ```bash
   python main.py
   ```

## 📖 Usage

### Basic Usage
1. Create a new image or open an existing file
2. Select the desired editing tool from the toolbar
3. Use the selected tool on the image
4. Apply changes and save

### Working with Layers
1. Click the "+" button in the layers panel to add a new layer
2. Navigate between layers using the layer list
3. Use layer properties to adjust blending modes and opacity

### Filters and Effects
1. Select the desired effect from the filters menu
2. Customize settings and check the preview
3. Click "Apply" to apply the changes

## 🧰 Tools

- **Selection Tools**: Rectangle, ellipse, lasso, magic wand
- **Editing Tools**: Brush, eraser, fill, text, crop, move
- **Filters**: Blur, sharpen, noise reduction
- **Adjustments**: Brightness/contrast, HSL, levels, curves

## 📂 Project Structure

```
Image_Editor/
├── core/                  # Core functionality
│   ├── app_state.py       # Application state management
│   ├── image_handler.py   # Image processing functions
│   └── layer_manager.py   # Layer management
├── ui/                    # User interface
│   ├── canvas.py          # Editing canvas
│   ├── main_window.py     # Main application window
│   ├── menubar.py         # Application menu
│   ├── toolbar.py         # Toolbar
│   └── panels/            # UI panels
├── operations/            # Image processing operations
│   ├── adjustments/       # Color adjustments
│   ├── effects/           # Visual effects
│   ├── filters/           # Filters
│   └── transformations/   # Transformations
├── tools/                 # Editing tools
├── resources/             # Application resources
├── utils/                 # Helper functions
├── config/                # Configuration files
├── main.py                # Main entry point
└── requirements.txt       # Dependencies
```

## 🗺️ Roadmap

- [ ] Advanced selection tools (magnetic lasso, edge detection)
- [ ] Adjustment layers and non-destructive editing support
- [ ] Layer masks and effects
- [ ] Brush engine improvements
- [ ] Macro and action recording
- [ ] Content-aware fill and erasure
- [ ] GPU acceleration
- [ ] Color profile support
- [ ] Plugin system
- [ ] Scripting automation

## 👥 Contributing

If you would like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to your branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

Project Manager - [@faust-lvii](https://github.com/faust-lvii)

Project Link: [https://github.com/faust-lvii/Image_Editor](https://github.com/faust-lvii/Image_Editor) 