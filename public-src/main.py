#!/usr/bin/env python3
"""
YouTube Downloader - Główny plik aplikacji
Aplikacja do pobierania filmów z YouTube z interfejsem graficznym
"""

import sys
import tkinter as tk
from tkinter import messagebox
from gui import YouTubeDownloaderGUI
from downloader import YouTubeDownloader
from utils import setup_logging, cleanup_old_logs
from version import __version__

def main():
    """Główna funkcja aplikacji"""
    try:
        # Konfiguracja logowania
        setup_logging()
        
        # Czyszczenie starych logów jeśli są za duże
        cleanup_old_logs()
        
        # Utworzenie głównego okna aplikacji
        root = tk.Tk()
        root.title(f"YouTube Downloader v{__version__}")
        root.geometry("1100x1000")
        root.minsize(1000, 900)
        root.resizable(True, True)
        
        # Inicjalizacja GUI
        app = YouTubeDownloaderGUI(root)
        
        # Uruchomienie aplikacji
        root.mainloop()
        
    except Exception as e:
        # Zaloguj błąd, a komunikat pokaż w GUI
        messagebox.showerror("Błąd", f"Nie udało się uruchomić aplikacji:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
