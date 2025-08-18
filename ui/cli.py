#!/usr/bin/env python3
"""
YouTube Downloader v1.2.0 - Command Line Interface

Comprehensive CLI for YouTube video downloading with WSL compatibility.
Part of the modular architecture introduced in v1.2.0.

Features:
- Interactive command-line interface with safe input handling
- EOF and KeyboardInterrupt error handling for WSL environments
- Dynamic format selection and directory management
- Progress tracking with real-time download status
- Fallback mode when GUI is unavailable

Architecture: Dual-Repository Workflow v1.2.0
"""

import os
import sys
import logging
from pathlib import Path
from core.downloader import YouTubeDownloader
from core.utils import validate_youtube_url
from version import __version__
from core.translations import t

def safe_input(prompt, default="n", auto_exit=False):
    """Bezpieczny input z obsługą błędów EOF w WSL"""
    try:
        if not sys.stdin.isatty():
            # Jeśli nie mamy terminala, użyj domyślnych odpowiedzi
            if auto_exit:
                print(f"{prompt}[auto: q]")
                return "q"
            print(f"{prompt}[auto: {default}]")
            return default
        return input(prompt)
    except EOFError:
        if auto_exit:
            print("[EOF - wychodzę z aplikacji]")
            return "q"
        print(f"[EOF - używam domyślnej odpowiedzi: {default}]")
        return default
    except KeyboardInterrupt:
        print("\n[Przerwano przez użytkownika]")
        raise
    except Exception as e:
        if auto_exit:
            print(f"[Błąd wejścia: {e} - wychodzę z aplikacji]")
            return "q"
        print(f"[Błąd wejścia: {e} - używam domyślnej odpowiedzi: {default}]")
        return default

class YouTubeDownloaderCLI:
    def __init__(self):
        """Inicjalizacja interfejsu CLI"""
        self.downloader = YouTubeDownloader()
        self.download_directory = os.path.expanduser("~/Downloads")
        
    def print_header(self):
        """Wyświetl nagłówek aplikacji"""
        print("=" * 60)
        print(f"📺 YouTube Downloader v{__version__} - Tryb CLI")
        print("=" * 60)
        print("✨ Prosty sposób na pobieranie filmów z YouTube")
        print()
        
    def get_download_directory(self):
        """Pozwól użytkownikowi wybrać katalog pobierania"""
        print(f"📁 Aktualny katalog pobierania: {self.download_directory}")
        change = safe_input("💡 Czy chcesz zmienić katalog? (t/N): ").strip().lower()
        
        if change in ['t', 'tak', 'y', 'yes']:
            while True:
                new_dir = safe_input("📂 Podaj nową ścieżkę (lub Enter aby anulować): ").strip()
                if not new_dir:
                    break
                    
                new_dir = os.path.expanduser(new_dir)
                if os.path.exists(new_dir) and os.path.isdir(new_dir):
                    self.download_directory = new_dir
                    print(f"✅ Katalog zmieniony na: {self.download_directory}")
                    break
                else:
                    print(f"❌ Katalog nie istnieje: {new_dir}")
        print()
    
    def get_video_url(self):
        """Pobierz URL filmu od użytkownika"""
        while True:
            url = safe_input("🔗 Podaj URL filmu z YouTube (lub 'q' aby wyjść): ", auto_exit=True).strip()
            
            if url.lower() in ['q', 'quit', 'exit']:
                return None
                
            if validate_youtube_url(url):
                return url
            else:
                print("❌ Nieprawidłowy URL YouTube. Spróbuj ponownie.")
                print("💡 Przykład: https://www.youtube.com/watch?v=...")
                print()
    
    def get_video_info(self, url):
        """Pobierz informacje o filmie"""
        print("🔍 Sprawdzam film...")
        
        def progress_callback(progress):
            # Prosty progress dla CLI
            if progress.get('status') == 'downloading':
                percent = progress.get('percent', 0)
                if percent:
                    print(f"\r📥 Pobieranie: {percent:.1f}%", end='', flush=True)
        
        try:
            info = self.downloader.get_video_info(url)
            if info:
                print("✅ Film znaleziony!")
                print(f"📺 Tytuł: {info.get('title', 'Nieznany')}")
                print(f"⏱️  Czas: {info.get('duration_string', 'Nieznany')}")
                print(f"👤 Autor: {info.get('uploader', 'Nieznany')}")
                print()
                return info
            else:
                print("❌ Nie można pobrać informacji o filmie")
                return None
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return None
    
    def select_format(self, info):
        """Pozwól użytkownikowi wybrać format"""
        formats = info.get('formats', [])
        if not formats:
            print("⚠️  Brak dostępnych formatów")
            return None
            
        print("📋 Dostępne formaty:")
        print("0. 🎵 Tylko audio (MP3)")
        
        # Filtruj i sortuj formaty wideo
        video_formats = []
        for f in formats:
            if (f.get('vcodec') != 'none' and 
                f.get('acodec') != 'none' and 
                f.get('height')):
                video_formats.append(f)
        
        # Sortuj według jakości (wysokość)
        video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
        
        # Pokaż unikalne rozdzielczości
        shown_heights = set()
        format_options = []
        
        for i, fmt in enumerate(video_formats):
            height = fmt.get('height')
            if height and height not in shown_heights:
                shown_heights.add(height)
                format_options.append(fmt)
                print(f"{len(format_options)}. 📺 {height}p - {fmt.get('ext', 'mp4')}")
                
                if len(format_options) >= 5:  # Maksymalnie 5 opcji wideo
                    break
        
        print()
        
        while True:
            try:
                choice = safe_input("🎯 Wybierz format (numer): ", default="0").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    return {'audio_only': True}
                elif 1 <= choice_num <= len(format_options):
                    return {'format_id': format_options[choice_num - 1]['format_id']}
                else:
                    print(f"❌ Nieprawidłowy wybór. Podaj liczbę od 0 do {len(format_options)}")
            except ValueError:
                print("❌ Podaj prawidłową liczbę")
    
    def download_video(self, url, format_choice):
        """Pobierz film"""
        print("🚀 Rozpoczynam pobieranie...")
        
        def progress_callback(progress):
            if progress.get('status') == 'downloading':
                percent = progress.get('percent', 0)
                speed = progress.get('speed', 0)
                if percent and speed:
                    speed_mb = speed / 1024 / 1024
                    print(f"\r📥 Pobieranie: {percent:.1f}% | {speed_mb:.1f} MB/s", end='', flush=True)
            elif progress.get('status') == 'finished':
                print(f"\n✅ Pobieranie zakończone!")
        
        try:
            result = self.downloader.download_video(
                url=url,
                output_dir=self.download_directory,
                audio_only=format_choice.get('audio_only', False),
                format_id=format_choice.get('format_id'),
                progress_callback=progress_callback
            )
            
            if result['success']:
                print(f"🎉 Sukces! Plik zapisany w: {result['file_path']}")
                return True
            else:
                print(f"❌ Błąd pobierania: {result['error']}")
                return False
                
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd: {e}")
            return False
    
    def run_interactive(self):
        """Uruchom interaktywny tryb CLI"""
        self.print_header()
        
        print("💡 Ten tryb CLI jest dostępny gdy GUI nie działa w WSL")
        print("🔧 Aby wyjść, wpisz 'q' przy podawaniu URL")
        print()
        
        self.get_download_directory()
        
        while True:
            # Pobierz URL
            url = self.get_video_url()
            if url is None:
                break
            
            # Pobierz informacje o filmie
            info = self.get_video_info(url)
            if not info:
                print("⚠️  Spróbuj z innym URL")
                print()
                continue
            
            # Wybierz format
            format_choice = self.select_format(info)
            if not format_choice:
                print("⚠️  Nie wybrano formatu")
                print()
                continue
            
            # Pobierz film
            success = self.download_video(url, format_choice)
            
            print()
            if success:
                another = safe_input("🔄 Czy chcesz pobrać kolejny film? (T/n): ").strip().lower()
                if another in ['n', 'nie', 'no']:
                    break
            
            print()
        
        print("👋 Dziękujemy za używanie YouTube Downloader!")
        print("💡 Jeśli potrzebujesz GUI, spróbuj VcXsrv lub użyj natywnego Linux/Windows")

def main():
    """Główna funkcja CLI"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print(f"YouTube Downloader v{__version__} - CLI Mode")
        print("Użycie:")
        print("  python cli.py                 # Tryb interaktywny")
        print("  youtube-downloader --cli      # Tryb CLI przez główną aplikację")
        return
    
    try:
        cli = YouTubeDownloaderCLI()
        cli.run_interactive()
    except KeyboardInterrupt:
        print("\n👋 Przerwano przez użytkownika")
    except Exception as e:
        print(f"\n❌ Błąd CLI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()