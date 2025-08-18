#!/usr/bin/env python3
"""
Basic tests for YouTube Downloader v1.2.0
"""
import unittest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestBasic(unittest.TestCase):
    """Basic functionality tests for v1.2.0 modular architecture"""
    
    def test_launcher_import(self):
        """Test that launcher module can be imported"""
        try:
            import launcher
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Launcher import failed: {e}")
    
    def test_core_modules_import(self):
        """Test that core modules can be imported"""
        try:
            from core import downloader
            from core import utils
            from core import translations
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Core modules import failed: {e}")
    
    def test_ui_modules_import(self):
        """Test that UI modules can be imported"""
        try:
            from ui import gui
            from ui import cli
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"UI modules import failed: {e}")
    
    def test_version_exists(self):
        """Test that version file exists and is readable"""
        version_file = os.path.join(os.path.dirname(__file__), '..', 'version.py')
        self.assertTrue(os.path.exists(version_file))
        
        with open(version_file, 'r') as f:
            content = f.read()
            self.assertIn('__version__', content)

if __name__ == '__main__':
    unittest.main()