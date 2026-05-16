#!/usr/bin/env python3
"""
YouTube Downloader v1.2.0 - Graphical User Interface

Complete Tkinter-based GUI with threading support and progress tracking.
Part of the modular architecture introduced in v1.2.0.

Features:
- Real-time download progress with cancel functionality
- Configuration persistence (directory, settings)
- Dynamic format selection and quality sorting
- Cross-platform file path handling
- Enhanced WSL window handling and visibility forcing

Architecture: Dual-Repository Workflow v1.2.0
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import logging

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
import os
import json
from core.downloader import YouTubeDownloader
from version import __version__
from core.utils import validate_youtube_url, extract_timestamps
from core.translations import t

class YouTubeDownloaderGUI:
    def __init__(self, root):
        """Inicjalizacja interfejsu graficznego"""
        self.root = root
        self.downloader = YouTubeDownloader()
        self.selected_directory = ""
        self.video_info = None
        self.download_thread = None
        
        # Konfiguracja pliku konfiguracyjnego (z fallback)
        self.config_file = self._get_config_path()
        
        # Ustawienie ikony aplikacji
        self.setup_icon()
        
        # Konfiguracja stylów
        self.setup_styles()
        
        # Konfiguracja głównego okna
        self.setup_window()
        
        # Wczytanie ostatnio użytego katalogu
        self.load_last_directory()
        
        # Jeśli nie ma zapisanej lokalizacji, ustaw domyślną i zapisz
        if not self.selected_directory:
            default_dir = os.path.expanduser("~/Downloads")
            if os.path.exists(default_dir):
                self.selected_directory = default_dir
                logging.info(f"📁 Ustawiam domyślną lokalizację: {default_dir}")
                self.save_last_directory(default_dir)
        
        # Inicjalizacja interfejsu
        self.setup_ui()
        
    def _get_config_path(self):
        """Znajdź odpowiednią ścieżkę dla konfiguracji"""
        # Zawsze używaj /tmp/ - prostsze i bardziej niezawodne
        config_file = "/tmp/youtube-downloader-config.json"
        logging.info(f"✅ Używam konfiguracji: {config_file}")
        return config_file
        
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
        """Konfiguracja stylów — obsługiwane przez CustomTkinter"""
        pass
            
    def setup_window(self):
        """Konfiguracja głównego okna"""
        self.root.title(f"YouTube Downloader v{__version__}")
        self.root.geometry("1100x1000")
        self.root.minsize(1000, 900)
        
        # Centrowanie okna
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.root.winfo_screenheight() // 2) - (1000 // 2)
        self.root.geometry(f"1100x1000+{x}+{y}")
        
        # Centrowanie okna bez agresywnego wymuszania widoczności
        
    def load_last_directory(self):
        """Wczytanie ostatnio użytego katalogu"""
        config_file = "/tmp/youtube-downloader-config.json"
        try:
            logging.debug(f"🔍 Sprawdzam konfigurację: {config_file}")
            if os.path.exists(config_file):
                logging.debug(f"✅ Plik konfiguracyjny istnieje")
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    last_dir = config.get('last_directory')
                    logging.debug(f"📁 Ostatni katalog: {last_dir}")
                    if last_dir and os.path.exists(last_dir):
                        self.selected_directory = last_dir
                        logging.info(f"✅ Wczytano katalog: {last_dir}")
                    else:
                        logging.warning(f"❌ Katalog nie istnieje lub jest pusty: {last_dir}")
            else:
                logging.debug(f"❌ Plik konfiguracyjny nie istnieje: {config_file}")
        except Exception as e:
            logging.error(f"❌ Błąd wczytywania konfiguracji: {e}")
            pass
            
    def save_last_directory(self, directory):
        """Zapisanie ostatnio użytego katalogu"""
        try:
            config_dir = os.path.dirname(self.config_file)
            logging.debug(f"Tworzenie katalogu: {config_dir}")
            os.makedirs(config_dir, exist_ok=True)
            
            config = {'last_directory': directory}
            logging.debug(f"Zapisywanie do: {self.config_file}")
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            logging.info(f"✅ Zapisano konfigurację: {self.config_file}")
        except Exception as e:
            logging.error(f"❌ Błąd zapisu konfiguracji: {e}")
            # Ignoruj błędy zapisu konfiguracji
            pass
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
        header_frame = ctk.CTkFrame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10), padx=5)
        header_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(header_frame, text="YouTube Downloader",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky=tk.W, padx=12, pady=(10, 2))

        ctk.CTkLabel(header_frame, text=t("Pobieraj filmy z YouTube w wysokiej jakości"),
                     font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, sticky=tk.W, padx=12, pady=(0, 10))
        
    def create_main_content(self, parent):
        """Tworzenie głównej zawartości"""
        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
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
        url_frame = ctk.CTkFrame(parent)
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=5)
        url_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text=t("Link YouTube"),
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, padx=12, pady=(10, 6))

        self.url_entry = ctk.CTkEntry(url_frame, font=ctk.CTkFont(size=11),
                                      placeholder_text="https://youtube.com/watch?v=...")
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E),
                            padx=(12, 8), pady=(0, 10))

        self.check_button = ctk.CTkButton(url_frame, text=t("Sprawdź"),
                                          command=self.check_video)
        self.check_button.grid(row=1, column=2, padx=(0, 12), pady=(0, 10))
        
    def create_video_info_section(self, parent):
        """Sekcja informacji o filmie"""
        info_frame = ctk.CTkFrame(parent)
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=5)
        info_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(info_frame, text=t("Informacje o filmie"),
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky=tk.W, padx=12, pady=(10, 6))

        info_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_container.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=12, pady=(0, 10))
        info_container.columnconfigure(0, weight=1)

        self.info_text = tk.Text(info_container, height=3, wrap=tk.WORD,
                                 font=('Segoe UI', 9), bg='#2b2b2b', fg='#dce4ee',
                                 relief='flat', borderwidth=0)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        info_scrollbar = tk.Scrollbar(info_container, orient="vertical",
                                       command=self.info_text.yview)
        info_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
    def create_download_options_section(self, parent):
        """Sekcja opcji pobierania"""
        options_frame = ctk.CTkFrame(parent)
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=5)
        options_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(options_frame, text=t("Opcje pobierania"),
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=12, pady=(10, 6))

        self.audio_only_var = tk.BooleanVar()
        self.audio_checkbox = ctk.CTkCheckBox(options_frame, text=t("Tylko audio (MP3)"),
                                               variable=self.audio_only_var,
                                               command=self.on_audio_change)
        self.audio_checkbox.grid(row=1, column=0, columnspan=2, sticky=tk.W,
                                  padx=12, pady=(0, 8))

        ctk.CTkLabel(options_frame, text=t("Rozdzielczość:"),
                     font=ctk.CTkFont(size=11)).grid(row=2, column=0, sticky=tk.W,
                                                      padx=12, pady=(0, 5))

        self.resolution_var = tk.StringVar()
        self.resolution_combo = ctk.CTkComboBox(options_frame, variable=self.resolution_var,
                                                 state="readonly",
                                                 font=ctk.CTkFont(size=11), values=[])
        self.resolution_combo.grid(row=2, column=1, sticky=(tk.W, tk.E),
                                    padx=(8, 12), pady=(0, 5))

        ctk.CTkLabel(options_frame, text=t("Folder docelowy:"),
                     font=ctk.CTkFont(size=11)).grid(row=3, column=0, sticky=tk.W,
                                                      padx=12, pady=(8, 5))

        folder_container = ctk.CTkFrame(options_frame, fg_color="transparent")
        folder_container.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(8, 12), pady=(8, 10))
        folder_container.columnconfigure(0, weight=1)

        self.path_label = ctk.CTkLabel(folder_container, text=t("Nie wybrano folderu"),
                                        text_color="gray", font=ctk.CTkFont(size=10))
        self.path_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.folder_button = ctk.CTkButton(folder_container, text=t("Wybierz folder"),
                                            command=self.select_directory, width=130)
        self.folder_button.grid(row=0, column=1, padx=(10, 0))

        if self.selected_directory:
            self.path_label.configure(text=self.selected_directory, text_color="white")
            
    def create_download_section(self, parent):
        """Sekcja pobierania"""
        download_frame = ctk.CTkFrame(parent)
        download_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=5)
        download_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(download_frame, text=t("Pobieranie"),
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky=tk.W, padx=12, pady=(10, 6))

        self.download_button = ctk.CTkButton(download_frame, text=t("Rozpocznij pobieranie"),
                                              command=self.start_download)
        self.download_button.grid(row=1, column=0, sticky=tk.W, padx=12, pady=(0, 10))

        self.cancel_button = ctk.CTkButton(download_frame, text=t("Anuluj"),
                                            command=self.cancel_download,
                                            state="disabled",
                                            fg_color="transparent",
                                            border_width=2)
        self.cancel_button.grid(row=1, column=2, padx=(10, 12), pady=(0, 10))
        
    def create_progress_section(self, parent):
        """Sekcja postępu"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=5)
        progress_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(progress_frame, text=t("Postęp"),
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky=tk.W, padx=12, pady=(10, 6))

        self.progress = ctk.CTkProgressBar(progress_frame)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=12, pady=(0, 5))

        self.status_var = tk.StringVar()
        self.status_var.set(t("Gotowy do pobierania"))
        self.status_bar = ctk.CTkLabel(progress_frame, textvariable=self.status_var,
                                        text_color="#27ae60",
                                        font=ctk.CTkFont(size=11))
        self.status_bar.grid(row=2, column=0, sticky=tk.W, padx=12, pady=(0, 10))
        
    def create_error_section(self, parent):
        """Sekcja błędów"""
        error_frame = ctk.CTkFrame(parent)
        error_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=5)
        error_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(error_frame, text=t("Błędy i komunikaty"),
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, sticky=tk.W, padx=12, pady=(10, 6))

        error_container = ctk.CTkFrame(error_frame, fg_color="transparent")
        error_container.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=12, pady=(0, 10))
        error_container.columnconfigure(0, weight=1)

        self.error_text = tk.Text(error_container, height=2, wrap=tk.WORD,
                                   font=('Segoe UI', 9), fg="#e74c3c",
                                   bg='#2b2b2b', relief='flat', borderwidth=0)
        self.error_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        error_scrollbar = tk.Scrollbar(error_container, orient="vertical",
                                        command=self.error_text.yview)
        error_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.error_text.configure(yscrollcommand=error_scrollbar.set)
        
    def create_status_bar(self, parent):
        """Tworzenie status bara"""
        status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        ctk.CTkLabel(status_frame, text=f"YouTube Downloader v{__version__}",
                     font=ctk.CTkFont(size=9), text_color="gray").grid(
            row=0, column=0, sticky=tk.W, padx=8, pady=2)
        
    def check_video(self):
        """Sprawdzenie informacji o filmie"""
        url = self.url_entry.get().strip()
        if not url:
            self.show_error(t("Wprowadź link YouTube"))
            return
            
        if not validate_youtube_url(url):
            self.show_error(t("Nieprawidłowy link YouTube"))
            return
            
        self.status_var.set(t("Sprawdzanie filmu..."))
        self.status_bar.configure(text_color='#f39c12')
        self.check_button.configure(state="disabled")
        
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
            error_msg = f"{t('Błąd podczas sprawdzania')}: {e}"
            self.root.after(0, lambda: self.show_error(error_msg))
        finally:
            self.root.after(0, lambda: self.check_button.configure(state="normal"))
            
    def _update_video_info(self):
        """Aktualizacja informacji o filmie"""
        if self.video_info:
            info_text = f"{t('Tytuł')}: {self.video_info.get('title', t('Nieznany'))}\n"
            info_text += f"{t('Czas trwania')}: {self.video_info.get('duration', t('Nieznany'))}\n"
            info_text += f"{t('Dostępne formaty')}: {len(self.video_info.get('formats', []))}"
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            
            # Aktualizacja listy rozdzielczości z sortowaniem
            formats = self.video_info.get('formats', [])
            resolutions = [f.get('resolution', t('Nieznana')) for f in formats if f.get('resolution')]
            
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
            
            self.resolution_combo.configure(values=sorted_resolutions)
            if sorted_resolutions:
                self.resolution_combo.set(sorted_resolutions[0])
                
            self.status_var.set(t("Film sprawdzony"))
            self.status_bar.configure(text_color='#27ae60')
        else:
            self.show_error(t("Nie udało się pobrać informacji o filmie"))
            
    def on_audio_change(self):
        """Obsługa zmiany opcji audio"""
        state = "disabled" if self.audio_only_var.get() else "normal"
        self.resolution_combo.configure(state=state)
            
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
            self.path_label.configure(text=directory, text_color="white")
            # Zapisz nową lokalizację
            self.save_last_directory(directory)
            
    def start_download(self):
        """Rozpoczęcie pobierania"""
        if not self.video_info:
            self.show_error(t("Najpierw sprawdź film"))
            return
            
        if not self.selected_directory:
            self.show_error(t("Wybierz folder docelowy"))
            return
            
        url = self.url_entry.get().strip()
        resolution = self.resolution_var.get()
        audio_only = self.audio_only_var.get()
        
        self.download_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress.set(0)
        self.status_var.set(t("Rozpoczynanie pobierania..."))
        self.status_bar.configure(text_color='#f39c12')
        
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
            error_msg = str(e)
            if t("Pobieranie zostało anulowane") not in error_msg and "anulowane" not in error_msg.lower() and "cancelled" not in error_msg.lower():
                display_msg = f"{t('Błąd podczas pobierania')}: {e}"
                self.root.after(0, lambda msg=display_msg: self.show_error(msg))
        finally:
            self.root.after(0, self._reset_ui)
            
    def _update_progress(self, percentage):
        """Aktualizacja postępu pobierania"""
        self.root.after(0, lambda: self.progress.set(percentage / 100))
        self.root.after(0, lambda: self.status_var.set(f"{t('Pobieranie...')} {percentage}%"))
        
    def _download_complete(self, result):
        """Zakończenie pobierania"""
        if result:
            # Zapisz lokalizację po udanym pobieraniu
            if self.selected_directory:
                self.save_last_directory(self.selected_directory)
            messagebox.showinfo(t("Sukces"), f"{t('Film został pobrany')}:\n{result['filename']}")
            self.status_var.set(t("Pobieranie zakończone"))
            self.status_bar.configure(text_color='#27ae60')
        else:
            self.show_error(t("Nie udało się pobrać filmu"))
            
    def cancel_download(self):
        """Anulowanie pobierania"""
        if self.download_thread and self.download_thread.is_alive():
            self.downloader.cancel_download()
            self.status_var.set(t("Anulowanie..."))
            self.cancel_button.config(state="disabled")
            self.status_bar.configure(text_color='#e74c3c')
            
    def _reset_ui(self):
        """Reset interfejsu po pobieraniu"""
        self.download_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        
    def show_error(self, message):
        """Wyświetlenie błędu"""
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(1.0, message)
        self.status_var.set(t("Błąd"))
        self.status_bar.configure(text_color='#e74c3c')
