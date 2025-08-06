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

def main():
    """Główna funkcja aplikacji"""
    try:
        # Konfiguracja logowania
        setup_logging()
        
        # Czyszczenie starych logów jeśli są za duże
        cleanup_old_logs()
        
        # Utworzenie głównego okna aplikacji
        root = tk.Tk()
        root.title("YouTube Downloader v1.0.2")
        root.geometry("1100x1000")
        root.minsize(1000, 900)
        root.resizable(True, True)
        
        # Inicjalizacja GUI
        app = YouTubeDownloaderGUI(root)
        
        # Uruchomienie aplikacji
        root.mainloop()
        
    except Exception as e:
        print(f"Błąd podczas uruchamiania aplikacji: {e}")
        messagebox.showerror("Błąd", f"Nie udało się uruchomić aplikacji:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
