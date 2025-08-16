#!/usr/bin/env python3
"""
Basic tests for YouTube Downloader
"""
import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestBasic(unittest.TestCase):
    """Basic functionality tests"""
    
    def test_imports(self):
        """Test that main modules can be imported"""
        try:
            import main
            import gui
            import downloader
            import utils
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_version_exists(self):
        """Test that version file exists and is readable"""
        version_file = os.path.join(os.path.dirname(__file__), '..', 'version.py')
        self.assertTrue(os.path.exists(version_file))
        
        with open(version_file, 'r') as f:
            content = f.read()
            self.assertIn('__version__', content)

if __name__ == '__main__':
    unittest.main()