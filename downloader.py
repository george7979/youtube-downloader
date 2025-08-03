#!/usr/bin/env python3
"""
YouTube Downloader - Logika pobierania
Główna logika pobierania filmów z YouTube
"""

import os
import yt_dlp
import threading
from pathlib import Path
from utils import sanitize_filename

class YouTubeDownloader:
    def __init__(self):
        """Inicjalizacja downloadera"""
        self.cancel_flag = False
        self.current_download = None
        
    def get_video_info(self, url):
        """Pobieranie informacji o filmie"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Przygotowanie informacji
                video_info = {
                    'title': info.get('title', 'Nieznany tytuł'),
                    'duration': self._format_duration(info.get('duration', 0)),
                    'description': info.get('description', ''),
                    'formats': info.get('formats', []),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Nieznany autor'),
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),
                }
                
                return video_info
                
        except Exception as e:
            raise Exception(f"Nie udało się pobrać informacji o filmie: {e}")
            
    def download_video(self, url, output_dir, resolution=None, audio_only=False, progress_callback=None):
        """Pobieranie filmu"""
        try:
            # Przygotowanie opcji yt-dlp
            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)] if progress_callback else None,
            }
            
            # Konfiguracja formatu
            if audio_only:
                ydl_opts['format'] = 'bestaudio[ext=mp3]/bestaudio'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                if resolution:
                    ydl_opts['format'] = f'best[height<={resolution.split("x")[1]}]/best'
                else:
                    ydl_opts['format'] = 'best[ext=mp4]/best'
                    
            # Pobieranie
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.current_download = ydl
                info = ydl.extract_info(url, download=True)
                
                # Przygotowanie wyniku
                filename = ydl.prepare_filename(info)
                if audio_only and not filename.endswith('.mp3'):
                    filename = filename.rsplit('.', 1)[0] + '.mp3'
                    
                return {
                    'filename': os.path.basename(filename),
                    'full_path': filename,
                    'title': info.get('title', 'Nieznany tytuł'),
                    'duration': info.get('duration', 0),
                    'filesize': os.path.getsize(filename) if os.path.exists(filename) else 0,
                }
                
        except Exception as e:
            if self.cancel_flag:
                raise Exception("Pobieranie zostało anulowane")
            else:
                raise Exception(f"Błąd podczas pobierania: {e}")
        finally:
            self.current_download = None
            self.cancel_flag = False
            
    def _progress_hook(self, d, callback):
        """Hook do śledzenia postępu pobierania"""
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
            return "Nieznany"
            
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    def cancel_download(self):
        """Anulowanie pobierania"""
        self.cancel_flag = True
        if self.current_download:
            self.current_download.break_on_existing = True
            
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
                
            print(f"Zapisano timestamps: {timestamp_filename}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania timestampów: {e}")
            
    def get_available_formats(self, url):
        """Pobieranie dostępnych formatów"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
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
            raise Exception(f"Nie udało się pobrać formatów: {e}")
            
    def validate_url(self, url):
        """Walidacja URL YouTube"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
                return True
                
        except Exception:
            return False
