#!/usr/bin/env python3
"""
YouTube Downloader - Internationalization
Translation dictionary for English UI
"""

# Complete Polish → English translation dictionary
TRANSLATIONS = {
    # Button labels
    "Sprawdź": "Check",
    "Anuluj": "Cancel", 
    "Wybierz folder": "Select Folder",
    
    # Form labels
    "Rozdzielczość:": "Resolution:",
    "Tylko audio (MP3)": "Audio only (MP3)",
    "Pobieranie": "Download",
    
    # Video information
    "Tytuł": "Title",
    "Czas trwania": "Duration", 
    "Dostępne formaty": "Available formats",
    "Nieznany": "Unknown",
    "Nieznany tytuł": "Unknown title",
    "Nieznany autor": "Unknown author",
    "Nieznana": "Unknown",
    
    # Status messages
    "Film sprawdzony": "Video checked",
    "Pobieranie...": "Downloading...",
    "Pobieranie zakończone": "Download complete",
    "Pobieranie anulowane": "Download cancelled",
    "Rozpocznij pobieranie": "Start Download",
    "Rozpoczynanie pobierania...": "Starting download...",
    
    # Error messages
    "Błąd": "Error",
    "Błąd podczas sprawdzania": "Error during checking",
    "Błąd podczas pobierania": "Error during download",
    "Nie udało się pobrać informacji o filmie": "Failed to get video information",
    "Nie udało się pobrać filmu": "Failed to download video",
    "Najpierw sprawdź film": "Check the video first",
    "Wybierz folder docelowy": "Select destination folder",
    "Nie wybrano folderu": "No folder selected",
    "Nie udało się uruchomić aplikacji": "Failed to start application",
    
    # Success messages
    "Sukces": "Success",
    "Film został pobrany": "Video has been downloaded",
    
    # Downloader error messages
    "Nie udało się pobrać informacji o filmie żadną z dostępnych metod. YouTube może blokować dostęp z Twojego IP.": "Failed to get video information with any available method. YouTube may be blocking access from your IP.",
    "Pobieranie zostało anulowane": "Download was cancelled",
    "Nie udało się pobrać filmu żadnym z dostępnych klientów. YouTube może blokować dostęp lub film może być niedostępny.": "Failed to download video with any available client. YouTube may be blocking access or the video may be unavailable.",
    "Nie udało się pobrać formatów": "Failed to get formats",
    "FFmpeg nie jest zainstalowany. Konwersja MP3 wymaga FFmpeg.": "FFmpeg is not installed. MP3 conversion requires FFmpeg.",
    
    # Log messages
    "Zapisano timestamps": "Saved timestamps",
    "Błąd podczas zapisywania timestampów": "Error saving timestamps",
    
    # Utils messages
    "Nie udało się wyczyścić logów": "Failed to clean logs",
    
    # UI Section Headers and Labels
    "Pobieraj filmy z YouTube w wysokiej jakości": "Download YouTube videos in high quality",
    "Link YouTube": "YouTube Link",
    "Informacje o filmie": "Video Information",
    "Opcje pobierania": "Download Options",
    "Folder docelowy:": "Destination Folder:",
    "Postęp": "Progress",
    "Błędy i komunikaty": "Errors and Messages",
    
    # Status and Input Messages
    "Gotowy do pobierania": "Ready to download",
    "Wprowadź link YouTube": "Enter YouTube link",
    "Nieprawidłowy link YouTube": "Invalid YouTube link",
    "Sprawdzanie filmu...": "Checking video...",
    
    # Comments in code (for documentation purposes)
    "Inicjalizacja downloadera": "Downloader initialization",
    "Pobieranie informacji o filmie": "Getting video information", 
    "Pobieranie filmu": "Downloading video",
    "Anulowanie pobierania": "Canceling download",
    "Sprawdzenie filmu w osobnym wątku": "Check video in separate thread",
    "Aktualizacja informacji o filmie": "Update video information",
    "Obsługa zmiany opcji audio": "Handle audio option change",
    "Wybór katalogu docelowego z domyślną lokalizacją": "Select destination directory with default location",
    "Rozpoczęcie pobierania": "Start download",
    "Pobieranie w osobnym wątku": "Download in separate thread",
    "Aktualizacja postępu pobierania": "Update download progress",
    "Zakończenie pobierania": "Download complete",
    "Reset interfejsu po pobieraniu": "Reset UI after download",
    "Wyświetlenie błędu": "Display error",
    "Formatowanie czasu trwania": "Format duration",
    "Zapisywanie timestampów do pliku .md": "Save timestamps to .md file",
    "Pobieranie dostępnych formatów": "Get available formats",
    "Walidacja URL YouTube": "YouTube URL validation",
}

def t(text):
    """
    Simple translation function
    
    Args:
        text (str): Polish text to translate
        
    Returns:
        str: English translation or original text if not found
    """
    return TRANSLATIONS.get(text, text)

def tf(text, *args, **kwargs):
    """
    Translation function with formatting support
    
    Args:
        text (str): Polish text to translate (may contain format placeholders)
        *args: Positional arguments for string formatting
        **kwargs: Keyword arguments for string formatting
        
    Returns:
        str: Formatted English translation
    """
    translated = TRANSLATIONS.get(text, text)
    if args or kwargs:
        return translated.format(*args, **kwargs)
    return translated