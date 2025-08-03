#!/usr/bin/env python3
"""
YouTube Downloader - Interfejs graficzny
GUI aplikacji do pobierania filmów z YouTube
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
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
        
        self.setup_ui()
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        # Główny kontener
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguracja siatki
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 1. Pole tekstowe - link YouTube
        ttk.Label(main_frame, text="Link YouTube:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 2. Przycisk "Sprawdź"
        self.check_button = ttk.Button(main_frame, text="Sprawdź", command=self.check_video)
        self.check_button.grid(row=0, column=3, padx=5, pady=5)
        
        # 3. Pole informacyjne o filmie
        ttk.Label(main_frame, text="Informacje o filmie:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.info_text = tk.Text(main_frame, height=4, width=60, wrap=tk.WORD)
        self.info_text.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 4. Checkbox "Tylko audio"
        self.audio_only_var = tk.BooleanVar()
        self.audio_checkbox = ttk.Checkbutton(main_frame, text="Tylko audio (MP3)", 
                                            variable=self.audio_only_var, command=self.on_audio_change)
        self.audio_checkbox.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 5. Lista rozwijana - wybór rozdzielczości
        ttk.Label(main_frame, text="Rozdzielczość:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.resolution_var = tk.StringVar()
        self.resolution_combo = ttk.Combobox(main_frame, textvariable=self.resolution_var, state="readonly")
        self.resolution_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 6. Przycisk "Wybierz folder"
        self.folder_button = ttk.Button(main_frame, text="Wybierz folder", command=self.select_directory)
        self.folder_button.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # 7. Pole wybranej ścieżki
        self.path_label = ttk.Label(main_frame, text="Nie wybrano folderu")
        self.path_label.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 8. Przycisk "Pobierz"
        self.download_button = ttk.Button(main_frame, text="Pobierz", command=self.start_download)
        self.download_button.grid(row=5, column=0, sticky=tk.W, pady=10)
        
        # 9. Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 10. Przycisk "Anuluj"
        self.cancel_button = ttk.Button(main_frame, text="Anuluj", command=self.cancel_download, state="disabled")
        self.cancel_button.grid(row=5, column=3, pady=10)
        
        # 11. Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Gotowy do pobierania")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # 12. Pole błędów
        ttk.Label(main_frame, text="Błędy:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.error_text = tk.Text(main_frame, height=3, width=60, wrap=tk.WORD, fg="red")
        self.error_text.grid(row=7, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
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
            
            # Aktualizacja listy rozdzielczości
            formats = self.video_info.get('formats', [])
            resolutions = [f.get('resolution', 'Nieznana') for f in formats if f.get('resolution')]
            self.resolution_combo['values'] = list(set(resolutions))
            if resolutions:
                self.resolution_combo.set(resolutions[0])
                
            self.status_var.set("Film sprawdzony")
        else:
            self.show_error("Nie udało się pobrać informacji o filmie")
            
    def on_audio_change(self):
        """Obsługa zmiany opcji audio"""
        if self.audio_only_var.get():
            self.resolution_combo.config(state="disabled")
        else:
            self.resolution_combo.config(state="readonly")
            
    def select_directory(self):
        """Wybór katalogu docelowego"""
        directory = filedialog.askdirectory()
        if directory:
            self.selected_directory = directory
            self.path_label.config(text=directory)
            
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
        else:
            self.show_error("Nie udało się pobrać filmu")
            
    def cancel_download(self):
        """Anulowanie pobierania"""
        if self.download_thread and self.download_thread.is_alive():
            self.downloader.cancel_download()
            self.status_var.set("Pobieranie anulowane")
            
    def _reset_ui(self):
        """Reset interfejsu po pobieraniu"""
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
    def show_error(self, message):
        """Wyświetlenie błędu"""
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(1.0, message)
        self.status_var.set("Błąd")
