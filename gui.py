#!/usr/bin/env python3
"""
YouTube Downloader - Interfejs graficzny
GUI aplikacji do pobierania filmów z YouTube
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
from downloader import YouTubeDownloader
from utils import validate_youtube_url, extract_timestamps

class YouTubeDownloaderGUI:
    def __init__(self, root):
        """Inicjalizacja interfejsu graficznego"""
        self.root = root
        self.downloader = YouTubeDownloader()
        self.selected_directory = ""
        self.video_info = None
        self.download_thread = None
        
        # Konfiguracja pliku konfiguracyjnego
        self.config_file = os.path.expanduser("~/.youtube-downloader/config.json")
        
        # Ustawienie ikony aplikacji
        self.setup_icon()
        
        # Konfiguracja stylów
        self.setup_styles()
        
        # Konfiguracja głównego okna
        self.setup_window()
        
        # Wczytanie ostatnio użytego katalogu
        self.load_last_directory()
        
        # Inicjalizacja interfejsu
        self.setup_ui()
        
    def setup_icon(self):
        """Ustawienie ikony aplikacji"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icons", "youtube-downloader-32.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception:
            pass  # Ignoruj błędy z ikoną
            
    def setup_styles(self):
        """Konfiguracja stylów aplikacji"""
        style = ttk.Style()
        
        # Konfiguracja motywu
        style.theme_use('clam')
        
        # Styl dla głównych ramek
        style.configure('Main.TFrame', background='#f0f0f0')
        style.configure('Card.TFrame', background='white', relief='solid', borderwidth=1)
        
        # Styl dla nagłówków
        style.configure('Title.TLabel', 
                      font=('Segoe UI', 14, 'bold'), 
                      foreground='#2c3e50',
                      background='white')
        
        style.configure('Subtitle.TLabel', 
                      font=('Segoe UI', 10, 'bold'), 
                      foreground='#34495e',
                      background='white')
        
        # Styl dla przycisków
        style.configure('Primary.TButton', 
                      font=('Segoe UI', 9, 'bold'),
                      padding=(15, 8))
        
        style.configure('Secondary.TButton', 
                      font=('Segoe UI', 9),
                      padding=(12, 6))
        
        # Styl dla pól tekstowych
        style.configure('Entry.TEntry', 
                      padding=(8, 6),
                      fieldbackground='white')
        
        # Usuwam niestandardowy styl dla progress bar - używam domyślnego
            
    def setup_window(self):
        """Konfiguracja głównego okna"""
        self.root.title("YouTube Downloader v1.0.2")
        self.root.geometry("1100x1000")
        self.root.minsize(1000, 900)
        
        # Centrowanie okna
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.root.winfo_screenheight() // 2) - (1000 // 2)
        self.root.geometry(f"1100x1000+{x}+{y}")
        
    def load_last_directory(self):
        """Wczytanie ostatnio użytego katalogu"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    last_dir = config.get('last_directory')
                    if last_dir and os.path.exists(last_dir):
                        self.selected_directory = last_dir
        except Exception:
            # W przypadku błędu używamy domyślnej lokalizacji
            pass
            
    def save_last_directory(self, directory):
        """Zapisanie ostatnio użytego katalogu"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config = {'last_directory': directory}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception:
            # Ignoruj błędy zapisu konfiguracji
            pass
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Główny kontener z paddingiem
        main_container = ttk.Frame(self.root, style='Main.TFrame', padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Konfiguracja siatki głównego kontenera
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # 1. Nagłówek aplikacji
        self.create_header(main_container)
        
        # 2. Główna zawartość (bez scrollbara - wszystko widoczne)
        self.create_main_content(main_container)
        
        # 3. Status bar
        self.create_status_bar(main_container)
        
    def create_header(self, parent):
        """Tworzenie nagłówka aplikacji"""
        header_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        # Tytuł aplikacji
        title_label = ttk.Label(header_frame, 
                               text="YouTube Downloader", 
                               style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 3))
        
        # Opis
        desc_label = ttk.Label(header_frame, 
                              text="Pobieraj filmy z YouTube w wysokiej jakości", 
                              style='Subtitle.TLabel')
        desc_label.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
    def create_main_content(self, parent):
        """Tworzenie głównej zawartości"""
        # Kontener bez scrollbara - wszystko widoczne
        content_frame = ttk.Frame(parent, style='Main.TFrame')
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        content_frame.columnconfigure(0, weight=1)
        
        # Sekcje interfejsu
        self.create_url_section(content_frame)
        self.create_video_info_section(content_frame)
        self.create_download_options_section(content_frame)
        self.create_download_section(content_frame)
        self.create_progress_section(content_frame)
        self.create_error_section(content_frame)
        
    def create_url_section(self, parent):
        """Sekcja wprowadzania URL"""
        url_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        url_frame.columnconfigure(1, weight=1)
        
        # Nagłówek sekcji
        ttk.Label(url_frame, text="Link YouTube", style='Subtitle.TLabel').grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))
        
        # Pole URL
        self.url_entry = ttk.Entry(url_frame, font=('Segoe UI', 10), style='Entry.TEntry')
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Przycisk sprawdzania
        self.check_button = ttk.Button(url_frame, text="Sprawdź", 
                                      command=self.check_video, style='Primary.TButton')
        self.check_button.grid(row=1, column=2)
        
    def create_video_info_section(self, parent):
        """Sekcja informacji o filmie"""
        info_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        info_frame.columnconfigure(0, weight=1)
        
        # Nagłówek sekcji
        ttk.Label(info_frame, text="Informacje o filmie", style='Subtitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        # Pole informacji
        info_container = ttk.Frame(info_frame)
        info_container.grid(row=1, column=0, sticky=(tk.W, tk.E))
        info_container.columnconfigure(0, weight=1)
        
        self.info_text = tk.Text(info_container, height=3, wrap=tk.WORD, 
                                font=('Segoe UI', 9), bg='#f8f9fa', 
                                relief='solid', borderwidth=1)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar dla tekstu
        info_scrollbar = ttk.Scrollbar(info_container, orient="vertical", command=self.info_text.yview)
        info_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
    def create_download_options_section(self, parent):
        """Sekcja opcji pobierania"""
        options_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        options_frame.columnconfigure(1, weight=1)
        
        # Nagłówek sekcji
        ttk.Label(options_frame, text="Opcje pobierania", style='Subtitle.TLabel').grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        
        # Checkbox audio
        self.audio_only_var = tk.BooleanVar()
        self.audio_checkbox = ttk.Checkbutton(options_frame, 
                                            text="Tylko audio (MP3)", 
                                            variable=self.audio_only_var, 
                                            command=self.on_audio_change)
        self.audio_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))
        
        # Rozdzielczość
        ttk.Label(options_frame, text="Rozdzielczość:", style='Subtitle.TLabel').grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.resolution_var = tk.StringVar()
        self.resolution_combo = ttk.Combobox(options_frame, 
                                           textvariable=self.resolution_var, 
                                           state="readonly",
                                           font=('Segoe UI', 9))
        self.resolution_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(0, 5))
        
        # Folder docelowy
        ttk.Label(options_frame, text="Folder docelowy:", style='Subtitle.TLabel').grid(
            row=3, column=0, sticky=tk.W, pady=(8, 5))
        
        folder_container = ttk.Frame(options_frame)
        folder_container.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(8, 5))
        folder_container.columnconfigure(0, weight=1)
        
        self.folder_button = ttk.Button(folder_container, text="Wybierz folder", 
                                       command=self.select_directory, style='Secondary.TButton')
        self.folder_button.grid(row=0, column=1, padx=(10, 0))
        
        self.path_label = ttk.Label(folder_container, text="Nie wybrano folderu", 
                                   style='Subtitle.TLabel', foreground='#7f8c8d')
        self.path_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Wyświetl zapisaną lokalizację jeśli istnieje
        if self.selected_directory:
            self.path_label.config(text=self.selected_directory, foreground='#2c3e50')
            
    def create_download_section(self, parent):
        """Sekcja pobierania"""
        download_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        download_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        download_frame.columnconfigure(1, weight=1)
        
        # Nagłówek sekcji
        ttk.Label(download_frame, text="Pobieranie", style='Subtitle.TLabel').grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))
        
        # Przycisk pobierania
        self.download_button = ttk.Button(download_frame, text="Rozpocznij pobieranie", 
                                        command=self.start_download, style='Primary.TButton')
        self.download_button.grid(row=1, column=0, sticky=tk.W)
        
        # Przycisk anulowania
        self.cancel_button = ttk.Button(download_frame, text="Anuluj", 
                                      command=self.cancel_download, 
                                      state="disabled", style='Secondary.TButton')
        self.cancel_button.grid(row=1, column=2, padx=(10, 0))
        
    def create_progress_section(self, parent):
        """Sekcja postępu"""
        progress_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        progress_frame.columnconfigure(0, weight=1)
        
        # Nagłówek sekcji
        ttk.Label(progress_frame, text="Postęp", style='Subtitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        # Progress bar
        self.progress = ttk.Progressbar(progress_frame)
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Gotowy do pobierania")
        self.status_bar = ttk.Label(progress_frame, textvariable=self.status_var, 
                                   style='Subtitle.TLabel', foreground='#27ae60')
        self.status_bar.grid(row=2, column=0, sticky=tk.W)
        
    def create_error_section(self, parent):
        """Sekcja błędów"""
        error_frame = ttk.Frame(parent, style='Card.TFrame', padding="12")
        error_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        error_frame.columnconfigure(0, weight=1)
        
        # Nagłówek sekcji
        ttk.Label(error_frame, text="Błędy i komunikaty", style='Subtitle.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        # Pole błędów
        error_container = ttk.Frame(error_frame)
        error_container.grid(row=1, column=0, sticky=(tk.W, tk.E))
        error_container.columnconfigure(0, weight=1)
        
        self.error_text = tk.Text(error_container, height=2, wrap=tk.WORD, 
                                 font=('Segoe UI', 9), fg="#e74c3c", 
                                 bg='#fdf2f2', relief='solid', borderwidth=1)
        self.error_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar dla błędów
        error_scrollbar = ttk.Scrollbar(error_container, orient="vertical", command=self.error_text.yview)
        error_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.error_text.configure(yscrollcommand=error_scrollbar.set)
        
    def create_status_bar(self, parent):
        """Tworzenie status bara"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        # Status aplikacji
        app_status = ttk.Label(status_frame, text="YouTube Downloader v1.0.2", 
                              font=('Segoe UI', 8), foreground='#7f8c8d')
        app_status.grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
    def check_video(self):
        """Sprawdzenie informacji o filmie"""
        url = self.url_entry.get().strip()
        if not url:
            self.show_error("Wprowadź link YouTube")
            return
            
        if not validate_youtube_url(url):
            self.show_error("Nieprawidłowy link YouTube")
            return
            
        self.status_var.set("Sprawdzanie filmu...")
        self.status_bar.configure(foreground='#f39c12')
        self.check_button.config(state="disabled")
        
        # Sprawdzenie w osobnym wątku
        thread = threading.Thread(target=self._check_video_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _check_video_thread(self, url):
        """Sprawdzenie filmu w osobnym wątku"""
        try:
            self.video_info = self.downloader.get_video_info(url)
            self.root.after(0, self._update_video_info)
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Błąd podczas sprawdzania: {e}"))
        finally:
            self.root.after(0, lambda: self.check_button.config(state="normal"))
            
    def _update_video_info(self):
        """Aktualizacja informacji o filmie"""
        if self.video_info:
            info_text = f"Tytuł: {self.video_info.get('title', 'Nieznany')}\n"
            info_text += f"Czas trwania: {self.video_info.get('duration', 'Nieznany')}\n"
            info_text += f"Dostępne formaty: {len(self.video_info.get('formats', []))}"
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            
            # Aktualizacja listy rozdzielczości z sortowaniem
            formats = self.video_info.get('formats', [])
            resolutions = [f.get('resolution', 'Nieznana') for f in formats if f.get('resolution')]
            
            # Usunięcie duplikatów i sortowanie od najwyższej do najniższej
            unique_resolutions = list(set(resolutions))
            
            # Funkcja do parsowania rozdzielczości
            def parse_resolution(res):
                if 'x' in res:
                    try:
                        return int(res.split('x')[1])  # Wyciągamy wysokość
                    except (ValueError, IndexError):
                        return 0
                return 0
            
            # Sortowanie od najwyższej do najniższej rozdzielczości
            sorted_resolutions = sorted(unique_resolutions, 
                                     key=parse_resolution, 
                                     reverse=True)
            
            self.resolution_combo['values'] = sorted_resolutions
            if sorted_resolutions:
                self.resolution_combo.set(sorted_resolutions[0])  # Ustawiamy najwyższą rozdzielczość
                
            self.status_var.set("Film sprawdzony")
            self.status_bar.configure(foreground='#27ae60')
        else:
            self.show_error("Nie udało się pobrać informacji o filmie")
            
    def on_audio_change(self):
        """Obsługa zmiany opcji audio"""
        if self.audio_only_var.get():
            self.resolution_combo.config(state="disabled")
        else:
            self.resolution_combo.config(state="readonly")
            
    def select_directory(self):
        """Wybór katalogu docelowego z domyślną lokalizacją"""
        # Domyślna lokalizacja: Downloads użytkownika
        default_dir = os.path.expanduser("~/Downloads")
        
        # Jeśli mamy zapisaną lokalizację i istnieje, użyj jej
        if self.selected_directory and os.path.exists(self.selected_directory):
            default_dir = self.selected_directory
        
        directory = filedialog.askdirectory(initialdir=default_dir)
        if directory:
            self.selected_directory = directory
            self.path_label.config(text=directory, foreground='#2c3e50')
            # Zapisz nową lokalizację
            self.save_last_directory(directory)
            
    def start_download(self):
        """Rozpoczęcie pobierania"""
        if not self.video_info:
            self.show_error("Najpierw sprawdź film")
            return
            
        if not self.selected_directory:
            self.show_error("Wybierz folder docelowy")
            return
            
        url = self.url_entry.get().strip()
        resolution = self.resolution_var.get()
        audio_only = self.audio_only_var.get()
        
        self.download_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress['value'] = 0
        self.status_var.set("Rozpoczynanie pobierania...")
        self.status_bar.configure(foreground='#f39c12')
        
        # Pobieranie w osobnym wątku
        self.download_thread = threading.Thread(
            target=self._download_thread, 
            args=(url, resolution, audio_only)
        )
        self.download_thread.daemon = True
        self.download_thread.start()
        
    def _download_thread(self, url, resolution, audio_only):
        """Pobieranie w osobnym wątku"""
        try:
            # Pobieranie filmu
            result = self.downloader.download_video(
                url, self.selected_directory, resolution, audio_only,
                progress_callback=self._update_progress
            )
            
            # Pobieranie timestampów
            if result and not audio_only:
                timestamps = extract_timestamps(self.video_info.get('description', ''))
                if timestamps:
                    self.downloader.save_timestamps(timestamps, result['filename'])
                    
            self.root.after(0, lambda: self._download_complete(result))
            
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Błąd podczas pobierania: {e}"))
        finally:
            self.root.after(0, self._reset_ui)
            
    def _update_progress(self, percentage):
        """Aktualizacja postępu pobierania"""
        self.root.after(0, lambda: self.progress.config(value=percentage))
        self.root.after(0, lambda: self.status_var.set(f"Pobieranie... {percentage}%"))
        
    def _download_complete(self, result):
        """Zakończenie pobierania"""
        if result:
            messagebox.showinfo("Sukces", f"Film został pobrany:\n{result['filename']}")
            self.status_var.set("Pobieranie zakończone")
            self.status_bar.configure(foreground='#27ae60')
        else:
            self.show_error("Nie udało się pobrać filmu")
            
    def cancel_download(self):
        """Anulowanie pobierania"""
        if self.download_thread and self.download_thread.is_alive():
            self.downloader.cancel_download()
            self.status_var.set("Pobieranie anulowane")
            self.status_bar.configure(foreground='#e74c3c')
            
    def _reset_ui(self):
        """Reset interfejsu po pobieraniu"""
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
    def show_error(self, message):
        """Wyświetlenie błędu"""
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(1.0, message)
        self.status_var.set("Błąd")
        self.status_bar.configure(foreground='#e74c3c')
