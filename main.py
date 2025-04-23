#!/usr/bin/env python
"""
Pro Image Editor - Main application entry point
"""
import sys
import os

# Add the parent directory to sys.path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from image_editor_app import run

if __name__ == "__main__":
    print("Starting Pro Image Editor...")
    run() 