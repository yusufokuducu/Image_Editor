# 🖼️ Image Editor

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern, efficient, and user-friendly image editing application built with Python and CustomTkinter.
</div>

## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## 🔍 Overview

Image Editor is a lightweight yet powerful image editing tool that provides real-time image manipulation capabilities. Built with Python and CustomTkinter, it offers a modern dark-themed interface and supports a wide range of image formats.

### Key Benefits
- 🚀 Fast and responsive real-time preview
- 🎨 Intuitive user interface with dark theme
- 📦 Small installation footprint
- 🔧 Easy to use, minimal learning curve

## ✨ Features

### Image Processing Capabilities
- **Brightness Adjustment**: Fine-tune image luminosity
- **Contrast Control**: Enhance image definition
- **Saturation Management**: Adjust color intensity
- **Sharpness Enhancement**: Improve image clarity
- **Noise Effects**: Add artistic noise effects

### Supported Image Formats
- PNG (*.png)
- JPEG (*.jpg, *.jpeg, *.jpe, *.jfif)
- BMP (*.bmp)
- GIF (*.gif)
- TIFF (*.tiff, *.tif)
- WebP (*.webp)
- And more...

### User Interface
- Modern, dark-themed design
- Real-time effect preview
- Intuitive slider controls
- Responsive layout
- File drag-and-drop support

## 💻 System Requirements

### Minimum Requirements
- Operating System: Windows 7/8/10/11
- Python 3.8 or higher
- RAM: 2GB
- Storage: 100MB free space
- Display: 1280x720 resolution

### Dependencies
```plaintext
customtkinter>=5.2.0
opencv-python>=4.8.0
pillow>=10.0.0
numpy>=1.24.0
```

## 🚀 Installation

### Method 1: From Source
1. Clone the repository:
   ```bash
   git clone https://github.com/faust-lvii/Image_Editor.git
   cd Image_Editor
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Using pip (if published)
```bash
pip install image-editor
```

## 📖 Usage Guide

### Starting the Application
```bash
python main_app.py
```

### Basic Operations
1. **Opening Images**
   - Click "Open Image" button
   - Or drag and drop an image file
   - Supported formats will be automatically filtered

2. **Applying Effects**
   - Use sliders in the control panel to adjust:
     - Brightness (-100 to +100)
     - Contrast (-100 to +100)
     - Saturation (-100 to +100)
     - Sharpness (-100 to +100)
     - Noise (0 to 100)

3. **Saving Images**
   - Click "Save Image" button
   - Choose desired format and location
   - Original quality is preserved

### Keyboard Shortcuts
- `Ctrl+O`: Open image
- `Ctrl+S`: Save image
- `Ctrl+Z`: Undo last change
- `Ctrl+R`: Reset all effects
- `Esc`: Close current window

## 🏗️ Architecture

### Project Structure
```
Image_Editor/
├── main_app.py          # Application entry point
├── Image_Noise.py       # Core image processing logic
├── requirements.txt     # Project dependencies
└── README.md           # Documentation
```

### Components
- **Main Application (main_app.py)**
  - Handles window management
  - Provides main user interface
  - Manages editor instances

- **Image Editor (Image_Noise.py)**
  - Implements image processing logic
  - Manages effect application
  - Handles file operations

### Design Patterns
- Model-View-Controller (MVC) architecture
- Event-driven programming
- Factory pattern for effect creation
- Observer pattern for UI updates

## 👥 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

Please ensure your code follows our style guide and includes appropriate tests.

## 🔧 Troubleshooting

### Common Issues

1. **Image Won't Load**
   - Check if the file format is supported
   - Verify file permissions
   - Ensure sufficient memory is available

2. **Performance Issues**
   - Check system requirements
   - Close other resource-intensive applications
   - Reduce image size for large files

3. **UI Elements Not Visible**
   - Verify minimum resolution requirements
   - Update graphics drivers
   - Check for CustomTkinter updates

### Getting Help
- Open an issue on GitHub
- Check existing issues for solutions
- Contact the maintainers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- CustomTkinter for the modern UI framework
- Pillow team for image processing capabilities
- OpenCV contributors for additional image processing features
- The Python community for invaluable resources and support

---

<div align="center">
Made with ❤️ by faust-lvii

[Report Bug](https://github.com/faust-lvii/Image_Editor/issues) · [Request Feature](https://github.com/faust-lvii/Image_Editor/issues)
</div>
