#!/usr/bin/env python3
"""
YouTube Downloader - Entry Point
Single Repository Architecture
"""
import sys
import os

# Add src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import and run main application
if __name__ == '__main__':
    from main import main
    main()