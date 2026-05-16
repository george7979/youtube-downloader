#!/usr/bin/env python3
"""
YouTube Downloader v1.2.0 - Intelligent Launcher
Smart launcher that automatically detects GUI availability and chooses appropriate interface
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from version import __version__
from core.utils import setup_logging
from core.translations import t

class LauncherDiagnostics:
    """Diagnostic tools for GUI/CLI capability detection"""
    
    @staticmethod
    def check_display():
        """Check if DISPLAY is available"""
        return bool(os.environ.get('DISPLAY'))
    
    @staticmethod
    def check_tkinter():
        """Test if tkinter can be imported and basic window created"""
        try:
            import tkinter as tk
            # Try to create a test window
            test_root = tk.Tk()
            test_root.withdraw()  # Hide immediately
            test_root.update()    # Process events
            test_root.destroy()   # Clean up
            return True
        except Exception:
            return False
    
    @staticmethod
    def check_wsl():
        """Detect if running in WSL"""
        return bool(os.environ.get('WSL_DISTRO_NAME'))
    
    @staticmethod
    def test_gui_window():
        """Test if GUI window can be displayed"""
        try:
            import tkinter as tk
            
            # Create test window
            test_root = tk.Tk()
            test_root.title("GUI Test")
            test_root.geometry("300x200")
            test_root.withdraw()
            
            # Try to make it visible
            test_root.deiconify()
            test_root.update()
            
            # Schedule close
            test_root.after(100, test_root.quit)
            test_root.mainloop()
            
            return True
        except Exception as e:
            logging.debug(f"GUI test failed: {e}")
            return False

class YouTubeDownloaderLauncher:
    """Main launcher class"""
    
    def __init__(self):
        self.diagnostics = LauncherDiagnostics()
        setup_logging()
        
    def print_diagnostics(self):
        """Print environment diagnostics"""
        print(f"🔍 YouTube Downloader v{__version__} - Environment Diagnostics")
        print("=" * 60)
        print(f"📺 DISPLAY:     {self.diagnostics.check_display()}")
        print(f"🖼️  Tkinter:     {self.diagnostics.check_tkinter()}")
        print(f"🐧 WSL:         {self.diagnostics.check_wsl()}")
        print(f"🖱️  GUI Test:    {self.diagnostics.test_gui_window()}")
        print("=" * 60)
    
    def can_use_gui(self):
        """Determine if GUI can be used"""
        # On Windows, DISPLAY is not used — skip that check
        if sys.platform != 'win32':
            if not self.diagnostics.check_display():
                logging.info("No DISPLAY environment variable")
                return False

        if not self.diagnostics.check_tkinter():
            logging.info("Tkinter not available or failed import")
            return False

        return True
    
    def launch_gui(self):
        """Launch GUI interface"""
        try:
            from ui.gui import YouTubeDownloaderGUI
            import customtkinter as ctk

            print(f"🚀 Starting YouTube Downloader v{__version__} (GUI Mode)")

            root = ctk.CTk()
            root.title(f"YouTube Downloader v{__version__}")
            root.geometry("770x800")
            root.minsize(700, 700)
            root.resizable(True, True)
            
            # Initialize GUI
            app = YouTubeDownloaderGUI(root)
            
            # Simple visibility - no aggressive forcing
            root.update()
            root.lift()
            
            # Start application
            root.mainloop()
            
        except Exception as e:
            import traceback
            log_path = os.path.join(os.environ.get('TEMP', '/tmp'), 'youtube-downloader-error.log')
            with open(log_path, 'w') as f:
                f.write(f"GUI error: {e}\n\n")
                traceback.print_exc(file=f)
            print(f"❌ GUI failed to start: {e}")
            print(f"📄 Error log: {log_path}")
            self.launch_cli()
    
    def launch_cli(self):
        """Launch CLI interface"""
        try:
            from ui.cli import YouTubeDownloaderCLI
            
            print(f"💻 Starting YouTube Downloader v{__version__} (CLI Mode)")
            cli = YouTubeDownloaderCLI()
            cli.run_interactive()
            
        except Exception as e:
            print(f"❌ CLI failed to start: {e}")
            sys.exit(1)
    
    def run(self, args):
        """Main run method"""
        if args.test:
            self.print_diagnostics()
            return
            
        if args.cli:
            self.launch_cli()
            return
            
        if args.gui:
            if self.can_use_gui():
                self.launch_gui()
            else:
                print("❌ GUI not available in this environment")
                print("🔄 Use --cli flag for command line interface")
                sys.exit(1)
            return
        
        # Auto-detect mode (default behavior)
        if self.can_use_gui():
            # Try GUI first, but with fallback
            try:
                print("🎨 GUI available - starting graphical interface...")
                self.launch_gui()
            except Exception as e:
                print(f"⚠️  GUI failed: {e}")
                print("🔄 Falling back to CLI...")
                self.launch_cli()
        else:
            print("💻 GUI not available - starting CLI interface...")
            self.launch_cli()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=f"YouTube Downloader v{__version__} - Intelligent Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Auto-detect and use best available interface
  %(prog)s --gui        # Force GUI mode (fails if not available)
  %(prog)s --cli        # Force CLI mode
  %(prog)s --test       # Show environment diagnostics
        """
    )
    
    parser.add_argument('--gui', action='store_true',
                       help='Force GUI mode')
    parser.add_argument('--cli', action='store_true',
                       help='Force CLI mode')
    parser.add_argument('--test', action='store_true',
                       help='Show environment diagnostics')
    parser.add_argument('--version', action='version',
                       version=f'YouTube Downloader {__version__}')
    
    args = parser.parse_args()
    
    # Validate arguments
    if sum([args.gui, args.cli, args.test]) > 1:
        parser.error("Only one mode can be specified")
    
    launcher = YouTubeDownloaderLauncher()
    launcher.run(args)

if __name__ == "__main__":
    main()