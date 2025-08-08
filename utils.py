#!/usr/bin/env python3
"""
YouTube Downloader - Funkcje pomocnicze
Wspólne funkcje używane w aplikacji
"""

import re
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

def setup_logging(enable_file_logging=True):
    """Konfiguracja logowania
    
    Args:
        enable_file_logging (bool): Czy włączyć logowanie do pliku
    """
    handlers = [logging.StreamHandler()]
    
    if enable_file_logging:
        # Zawsze używaj /tmp/ - prostsze i bardziej niezawodne
        log_dir = "/tmp"
        log_file = os.path.join(log_dir, "youtube_downloader.log")
        handlers.append(logging.FileHandler(log_file))
        print(f"📝 Logi zapisywane w: {log_file}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def validate_youtube_url(url):
    """Walidacja URL YouTube"""
    if not url or not isinstance(url, str):
        return False
        
    # Podstawowe sprawdzenie
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
            
    return False

def extract_timestamps(description):
    """Ekstrakcja timestampów z opisu filmu"""
    if not description:
        return []
        
    timestamps = []
    
    # Wzorce timestampów
    patterns = [
        # 0:00 - Tekst
        r'(\d{1,2}:\d{2})\s*[-–]\s*(.+)',
        # 0:00 Tekst
        r'(\d{1,2}:\d{2})\s+(.+)',
        # 0:00:00 - Tekst
        r'(\d{1,2}:\d{2}:\d{2})\s*[-–]\s*(.+)',
        # 0:00:00 Tekst
        r'(\d{1,2}:\d{2}:\d{2})\s+(.+)',
        # (0:00) Tekst
        r'\((\d{1,2}:\d{2})\)\s+(.+)',
        # [0:00] Tekst
        r'\[(\d{1,2}:\d{2})\]\s+(.+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        for match in matches:
            time_str = match[0]
            description = match[1].strip()
            
            # Walidacja czasu
            if is_valid_timestamp(time_str):
                timestamps.append({
                    'time': time_str,
                    'description': description,
                    'seconds': timestamp_to_seconds(time_str)
                })
    
    # Usuwanie duplikatów i sortowanie
    unique_timestamps = []
    seen_times = set()
    
    for ts in timestamps:
        if ts['time'] not in seen_times:
            unique_timestamps.append(ts)
            seen_times.add(ts['time'])
    
    # Sortowanie chronologiczne
    unique_timestamps.sort(key=lambda x: x['seconds'])
    
    return unique_timestamps

def is_valid_timestamp(timestamp):
    """Sprawdzenie czy timestamp jest poprawny"""
    # Wzorce dla różnych formatów czasu
    patterns = [
        r'^\d{1,2}:\d{2}$',           # MM:SS
        r'^\d{1,2}:\d{2}:\d{2}$',     # HH:MM:SS
    ]
    
    for pattern in patterns:
        if re.match(pattern, timestamp):
            return True
    return False

def timestamp_to_seconds(timestamp):
    """Konwersja timestamp na sekundy"""
    parts = timestamp.split(':')
    
    if len(parts) == 2:
        # MM:SS
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    elif len(parts) == 3:
        # HH:MM:SS
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    else:
        return 0

def sanitize_filename(filename):
    """Sanityzacja nazwy pliku z wzmocnioną walidacją"""
    if not filename or not isinstance(filename, str):
        return "unknown_file"
    
    # Usuwanie niedozwolonych znaków i potencjalnie niebezpiecznych sekwencji
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Zabezpieczenie przed path traversal
    filename = filename.replace('..', '_')
    filename = filename.replace('./', '_')
    filename = filename.replace('\\', '_')
    
    # Usuwanie znaków kontrolnych i nie-ASCII w niebezpiecznym kontekście
    filename = ''.join(char if (char.isprintable() and ord(char) < 127) or char in ' .-_' else '_' for char in filename)
    
    # Usuwanie wielokrotnych spacji i podkreślników
    filename = re.sub(r'\s+', ' ', filename)
    filename = re.sub(r'_+', '_', filename)
    
    # Usuwanie kropek na początku/końcu (ukryte pliki/rozszerzenia)
    filename = filename.strip('. ')
    
    # Zabezpieczenie przed pustym wynikiem
    if not filename:
        filename = "sanitized_file"
    
    # Ograniczenie długości (kompatybilność z systemami plików)
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

def get_file_size_mb(file_path):
    """Pobieranie rozmiaru pliku w MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except OSError:
        return 0

def format_file_size(size_bytes):
    """Formatowanie rozmiaru pliku"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def check_disk_space(directory, required_mb=100):
    """Sprawdzenie wolnego miejsca na dysku"""
    try:
        stat = os.statvfs(directory)
        free_bytes = stat.f_frsize * stat.f_bavail
        free_mb = free_bytes / (1024 * 1024)
        return free_mb >= required_mb
    except OSError:
        return False

def create_directory_if_not_exists(directory):
    """Tworzenie katalogu jeśli nie istnieje"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False

def is_valid_directory(directory):
    """Sprawdzenie czy katalog jest poprawny z wzmocnioną walidacją"""
    try:
        if not directory or not isinstance(directory, str):
            return False
            
        # Zabezpieczenie przed path traversal
        if '..' in directory or directory.startswith('.'):
            return False
            
        # Sprawdzenie czy ścieżka jest bezwzględna lub względna względem home
        if not (os.path.isabs(directory) or directory.startswith('~')):
            return False
            
        # Rozszerzenie ścieżki jeśli zawiera ~
        expanded_path = os.path.expanduser(directory)
        
        # Sprawdzenie czy katalog istnieje i ma uprawnienia do zapisu
        return (os.path.isdir(expanded_path) and 
                os.access(expanded_path, os.W_OK) and
                os.access(expanded_path, os.R_OK))
    except (OSError, TypeError, ValueError):
        return False

def get_safe_filename(title, extension='.mp4'):
    """Generowanie bezpiecznej nazwy pliku"""
    # Sanityzacja tytułu
    safe_title = sanitize_filename(title)
    
    # Dodanie rozszerzenia
    if not safe_title.endswith(extension):
        safe_title += extension
    
    return safe_title

def parse_youtube_id(url):
    """Parsowanie ID filmu z URL YouTube"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([\w-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def format_duration(seconds):
    """Formatowanie czasu trwania"""
    if not seconds or seconds <= 0:
        return "Nieznany"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def clean_text(text):
    """Czyszczenie tekstu z niepotrzebnych znaków"""
    if not text:
        return ""
    
    # Usuwanie wielokrotnych spacji
    text = re.sub(r'\s+', ' ', text)
    
    # Usuwanie znaków kontrolnych
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()

def cleanup_old_logs(max_size_mb=10):
    """Czyszczenie starych logów jeśli są za duże
    
    Args:
        max_size_mb (int): Maksymalny rozmiar pliku log w MB
    """
    try:
        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".youtube-downloader")
        log_file = os.path.join(log_dir, "youtube_downloader.log")
        
        if os.path.exists(log_file):
            size_mb = get_file_size_mb(log_file)
            if size_mb > max_size_mb:
                # Tworzenie kopii zapasowej
                backup_file = log_file + ".backup"
                os.rename(log_file, backup_file)
                
                # Tworzenie nowego pliku log z informacją o rotacji
                with open(log_file, 'w') as f:
                    f.write(f"# Log został zrotowany o {size_mb:.1f}MB\n")
                    f.write(f"# Stary log: {backup_file}\n")
                    f.write(f"# Data: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n\n")
                
                print(f"📝 Log został zrotowany (rozmiar: {size_mb:.1f}MB)")
    except Exception as e:
        print(f"⚠️ Nie udało się wyczyścić logów: {e}")
