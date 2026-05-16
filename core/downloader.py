#!/usr/bin/env python3
"""
YouTube Downloader v1.2.0 - Download Engine

YouTube download engine with robust fallback client configurations.
Part of the modular architecture introduced in v1.2.0.

Features:
- Multiple client fallback strategies (Android TV, Android, iOS, Web)
- Anti-bot bypass measures with optimized user agents
- Format selection with dynamic quality sorting
- Comprehensive error handling and logging

Architecture: Dual-Repository Workflow v1.2.0
"""

import os
import threading
import logging
import yt_dlp
from pathlib import Path
from .utils import sanitize_filename
from .translations import t

class YouTubeDownloader:
    def __init__(self):
        """Inicjalizacja downloadera"""
        self._cancel_event = threading.Event()
        self.current_download = None
        
    def _get_client_configs(self):
        """
        Zwraca ustandaryzowane konfiguracje klientów YouTube.
        Używane konsekwentnie przez get_video_info i download_video.
        """
        return [
            {
                'name': 'Android TV Client',
                'opts': {
                    'user_agent': 'com.google.android.youtube.tv/1.3.15 (Linux; U; Android 9.0) gzip',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv'],
                        }
                    },
                }
            },
            {
                'name': 'iOS Client',
                'opts': {
                    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios'],
                            'player_skip': ['configs'],
                        }
                    },
                }
            },
            {
                'name': 'Android Client',
                'opts': {
                    'user_agent': 'com.google.android.youtube/17.31.35',
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['configs'],
                        }
                    },
                }
            }
        ]
        
    def get_video_info(self, url):
        """Pobieranie informacji o filmie"""
        # Użyj standardowych konfiguracji klientów
        base_configs = self._get_client_configs()
        
        # Dodaj specyficzne opcje dla pobierania informacji
        configs = []
        for config in base_configs:
            info_config = {
                'name': config['name'],
                'opts': {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    **config['opts']  # Dodaj opcje z base config
                }
            }
            configs.append(info_config)
        
        # Próbuj każdą konfigurację
        for config in configs:
            try:
                logging.info(f"🔄 Próba z {config['name']}...")
                with yt_dlp.YoutubeDL(config['opts']) as ydl:
                    info = ydl.extract_info(url, download=False)
                
                    # Przygotowanie informacji
                    video_info = {
                        'title': info.get('title', t('Nieznany tytuł')),
                        'duration': self._format_duration(info.get('duration', 0)),
                        'description': info.get('description', ''),
                        'formats': info.get('formats', []),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', t('Nieznany autor')),
                        'view_count': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', ''),
                    }
                    
                    logging.info(f"✅ {config['name']} zadziałał!")
                    return video_info
                    
            except Exception as e:
                logging.warning(f"❌ {config['name']} nie zadziałał: {str(e)[:100]}...")
                continue
                
        # Jeśli żadna konfiguracja nie zadziałała
        raise Exception(t("Nie udało się pobrać informacji o filmie żadną z dostępnych metod. YouTube może blokować dostęp z Twojego IP."))
            
    def download_video(self, url, output_dir, resolution=None, audio_only=False, progress_callback=None):
        """Pobieranie filmu"""
        
        # Użyj standardowych konfiguracji klientów dla pobierania
        download_configs = self._get_client_configs()
        
        # Bazowe opcje dla wszystkich klientów
        base_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)],
            'extractor_retries': 1,  # Tylko 1 retry per client
            'retry_sleep_functions': {'http': lambda n: 2},
            'skip_unavailable_fragments': True,
            'fragment_retries': 3,
            'abort_on_unavailable_fragments': False,
        }
        
        # Próbuj każdy klient
        for config in download_configs:
            try:
                logging.info(f"🔄 Pobieranie z {config['name']}...")
                
                # Połącz bazowe opcje z opcjami klienta
                ydl_opts = {**base_opts, **config['opts']}
                
                # Konfiguracja formatu
                if audio_only:
                    ydl_opts['format'] = 'bestaudio[ext=mp3]/bestaudio'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                    # Sprawdź czy ffmpeg jest dostępny
                    if not os.system('which ffmpeg >/dev/null 2>&1') == 0:
                        raise Exception(t("FFmpeg nie jest zainstalowany. Konwersja MP3 wymaga FFmpeg."))
                else:
                    # Ulepszona logika wyboru formatu dla wideo
                    ydl_opts['format'] = self._get_video_format_selector(resolution)
                        
                # Pobieranie
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self.current_download = ydl
                    info = ydl.extract_info(url, download=True)
                    
                    # Przygotowanie wyniku
                    filename = ydl.prepare_filename(info)
                    if audio_only and not filename.endswith('.mp3'):
                        filename = filename.rsplit('.', 1)[0] + '.mp3'
                        
                    logging.info(f"✅ {config['name']} - pobieranie zakończone pomyślnie!")
                    return {
                        'filename': os.path.basename(filename),
                        'full_path': filename,
                        'title': info.get('title', t('Nieznany tytuł')),
                        'duration': info.get('duration', 0),
                        'filesize': os.path.getsize(filename) if os.path.exists(filename) else 0,
                    }
                    
            except Exception as e:
                error_msg = str(e)
                logging.warning(f"❌ {config['name']} nie zadziałał: {error_msg[:100]}...")
                
                # Sprawdź czy to błąd anulowania
                if self._cancel_event.is_set():
                    raise Exception(t("Pobieranie zostało anulowane"))
                
                # Sprawdź czy to błędy YouTube lub formatów - spróbuj następny klient
                format_errors = [
                    'sign in to confirm', 'not available on this app', 
                    'requested format is not available', 'this video is not available',
                    'no suitable formats found', 'format not available',
                    'unable to extract', 'video unavailable',
                    'format selector', 'no video formats found'
                ]
                
                if any(keyword in error_msg.lower() for keyword in format_errors):
                    logging.info(f"🔄 Format/client error with {config['name']}, trying next client...")
                    continue
                else:
                    # Inny błąd - spróbuj jeszcze jeden fallback z podstawowym formatem
                    if resolution:
                        try:
                            logging.info(f"🔄 Trying fallback format for {config['name']}...")
                            fallback_opts = {**ydl_opts}
                            fallback_opts['format'] = 'best'  # Najprostszy możliwy format
                            
                            with yt_dlp.YoutubeDL(fallback_opts) as ydl_fallback:
                                self.current_download = ydl_fallback
                                info = ydl_fallback.extract_info(url, download=True)
                                
                                filename = ydl_fallback.prepare_filename(info)
                                logging.info(f"✅ {config['name']} - fallback format worked!")
                                return {
                                    'filename': os.path.basename(filename),
                                    'full_path': filename,
                                    'title': info.get('title', t('Nieznany tytuł')),
                                    'duration': info.get('duration', 0),
                                    'filesize': os.path.getsize(filename) if os.path.exists(filename) else 0,
                                }
                        except Exception:
                            pass  # Fallback też nie zadziałał, spróbuj następny klient
                    
                    continue  # Przejdź do następnego klienta zamiast przerywać
                
        # Jeśli żaden klient nie zadziałał
        self.current_download = None
        self._cancel_event.clear()
        raise Exception(t("Nie udało się pobrać filmu żadnym z dostępnych klientów. YouTube może blokować dostęp lub film może być niedostępny."))
            
    def _progress_hook(self, d, callback):
        """Hook do śledzenia postępu pobierania"""
        if self._cancel_event.is_set():
            raise Exception(t("Pobieranie zostało anulowane"))
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes']:
                percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
                if callback:
                    callback(int(percentage))
        elif d['status'] == 'finished':
            if callback:
                callback(100)
                
    def _format_duration(self, seconds):
        """Formatowanie czasu trwania"""
        if not seconds:
            return t("Nieznany")
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def cancel_download(self):
        """Anulowanie pobierania"""
        self._cancel_event.set()
            
    def save_timestamps(self, timestamps, video_filename):
        """Zapisywanie timestampów do pliku .md"""
        try:
            if not timestamps:
                return
                
            # Przygotowanie nazwy pliku timestampów
            base_name = os.path.splitext(video_filename)[0]
            timestamp_filename = f"{base_name}-timestamps.md"
            
            # Przygotowanie zawartości
            content = f"# {base_name} - Timestamps\n\n"
            content += "## Timestamps z opisu:\n\n"
            
            for timestamp in timestamps:
                content += f"- {timestamp['time']} - {timestamp['description']}\n"
                
            # Zapisywanie pliku
            timestamp_path = os.path.join(os.path.dirname(video_filename), timestamp_filename)
            with open(timestamp_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logging.info(f"{t('Zapisano timestamps')}: {timestamp_filename}")
            
        except Exception as e:
            logging.error(f"{t('Błąd podczas zapisywania timestampów')}: {e}")
            
    def get_available_formats(self, url):
        """Pobieranie dostępnych formatów"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                
                # Mobilny user agent dla mweb client
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'referer': 'https://m.youtube.com/',
                'extractor_retries': 3,
                
                # YouTube 2025 - spróbuj różnych klientów
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android'],  # Natywne klienty mobilne
                        'skip': ['hls', 'dash'],
                        'player_skip': ['configs', 'webpage'],  # Pomiń więcej requestów
                    }
                },
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                # Filtrowanie i sortowanie formatów
                video_formats = []
                for fmt in formats:
                    if fmt.get('height') and fmt.get('ext'):
                        video_formats.append({
                            'format_id': fmt.get('format_id', ''),
                            'resolution': f"{fmt.get('width', 0)}x{fmt.get('height', 0)}",
                            'ext': fmt.get('ext', ''),
                            'filesize': fmt.get('filesize', 0),
                        })
                        
                # Sortowanie po rozdzielczości
                video_formats.sort(key=lambda x: int(x['resolution'].split('x')[1]), reverse=True)
                
                return video_formats
                
        except Exception as e:
            raise Exception(f"{t('Nie udało się pobrać formatów')}: {e}")
            
    def validate_url(self, url):
        """Walidacja URL YouTube"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                
                # Mobilny user agent dla mweb client
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'referer': 'https://m.youtube.com/',
                'extractor_retries': 3,
                
                # YouTube 2025 - spróbuj różnych klientów
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android'],  # Natywne klienty mobilne
                        'skip': ['hls', 'dash'],
                        'player_skip': ['configs', 'webpage'],  # Pomiń więcej requestów
                    }
                },
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
                return True
                
        except Exception:
            return False
            
    def _get_video_format_selector(self, resolution):
        """
        Generuje optymalny selektor formatu dla żądanej rozdzielczości.
        
        Implementuje hierarchię selektorów dla maksymalnej kompatybilności
        z różnymi klientami YouTube (Android TV, iOS, Android).
        """
        if not resolution:
            # Brak konkretnej rozdzielczości - użyj najlepszego dostępnego formatu
            return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
        
        try:
            # Wyciągnij wysokość z rozdzielczości (np. "1920x1080" -> 1080)
            target_height = int(resolution.split('x')[1])
            
            # Buduj hierarchię selektorów od najbardziej precyzyjnego do fallback
            format_selectors = [
                # 1. Najlepszy format wideo + audio dla dokładnej wysokości
                f'bestvideo[height={target_height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height={target_height}]+bestaudio',
                
                # 2. Najlepszy format dla wysokości <= target (preferowane)
                f'bestvideo[height<={target_height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={target_height}]+bestaudio',
                
                # 3. Najlepszy format ogólnie z ograniczeniem wysokości
                f'best[height<={target_height}][ext=mp4]/best[height<={target_height}]',
                
                # 4. Fallback - jakikolwiek format z ograniczeniem wysokości
                f'worst[height>={max(360, target_height//2)}][height<={target_height}]/best[height<={target_height}]',
                
                # 5. Ostateczny fallback - najlepszy dostępny
                'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
            ]
            
            # Połącz wszystkie selektory w jeden ciąg fallback
            return '/'.join(format_selectors)
            
        except (ValueError, IndexError):
            logging.warning(f"Nieprawidłowy format rozdzielczości: {resolution}. Używam domyślnego.")
            return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
