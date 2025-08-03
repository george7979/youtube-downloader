# YouTube Downloader - Plan Aplikacji

## 🎯 Cel
Aplikacja w Python do pobierania filmów z YouTube z interfejsem graficznym.

## ✅ Wymagania Podstawowe
- [x] Pobieranie filmów z YouTube z wklejanego linku
- [x] Pobieranie z dźwiękiem
- [x] Wybór rozdzielczości przed pobieraniem
- [x] Wybór katalogu docelowego
- [x] Format MP4
- [x] Walidacja linku YouTube
- [x] Progress bar pokazujący postęp pobierania
- [x] Obsługa błędów (film nie istnieje, brak połączenia)
- [x] Informacje o filmie (tytuł, czas trwania, dostępne formaty)
- [x] Przycisk "Anuluj" podczas pobierania
- [x] Możliwość pobierania tylko audio (MP3)

## 🔍 Dodatkowe Funkcje (Rozszerzenia)
- [ ] Historia pobierania
- [ ] Limit rozmiaru pliku z ostrzeżeniem
- [ ] Zapisywanie metadanych (opis, tagi)
- [ ] Pobieranie playlist
- [ ] Automatyczne konwertowanie formatów
- [ ] Ustawienia domyślne (katalog, jakość)
- [ ] Eksport listy pobierania
- [ ] Automatyczne wykrywanie najlepszej jakości

## 🛠️ Plan Techniczny

### Biblioteki
- **yt-dlp** - pobieranie z YouTube (nowsza wersja youtube-dl)
- **tkinter** - interfejs graficzny (wbudowany w Python)
- **threading** - pobieranie w tle bez blokowania GUI
- **os, pathlib** - operacje na plikach i ścieżkach
- **re** - parsowanie tekstu
- **markdown** - formatowanie plików .md (opcjonalnie)

### Struktura Aplikacji
```
youtube-downloader/
├── .venv/               # Środowisko wirtualne Python (izolowane)
├── main.py              # Główny plik aplikacji
├── gui.py               # Interfejs graficzny
├── downloader.py        # Logika pobierania
├── utils.py             # Funkcje pomocnicze
├── requirements.txt     # Zależności dla środowiska wirtualnego
├── run.py               # Skrypt uruchamiający (opcjonalnie)
└── README.md           # Dokumentacja
```

### Funkcjonalności GUI
1. **Pole tekstowe** - wklejanie linku YouTube
2. **Przycisk "Sprawdź"** - walidacja linku i pobranie informacji o filmie
3. **Pole informacyjne** - wyświetlanie tytułu, czasu trwania, dostępnych formatów
4. **Checkbox "Tylko audio"** - opcja pobierania tylko MP3
5. **Lista rozwijana** - wybór rozdzielczości (automatyczne wykrywanie najlepszej)
6. **Przycisk "Wybierz folder"** - wybór katalogu docelowego
7. **Przycisk "Pobierz"** - rozpoczęcie pobierania
8. **Progress bar** - postęp pobierania z procentami
9. **Przycisk "Anuluj"** - przerwanie pobierania
10. **Status bar** - komunikaty o stanie aplikacji i błędach
11. **Pole błędów** - wyświetlanie szczegółowych informacji o błędach



### Obsługa Błędów
- **Walidacja linku** - sprawdzanie poprawności URL YouTube
- **Brak połączenia** - sprawdzanie dostępności internetu
- **Film niedostępny** - prywatne, usunięte lub zablokowane filmy
- **Brak miejsca** - sprawdzanie wolnego miejsca na dysku
- **Błędy pobierania** - problemy z yt-dlp, timeout, itp.
- **Nieprawidłowe formaty** - gdy wybrana rozdzielczość nie jest dostępna
- **Błędy zapisu** - problemy z uprawnieniami do katalogu
- **Timeout** - zbyt długie pobieranie



### Izolowane Środowisko Wirtualne
- **.venv** - izolowane środowisko Python
- **Automatyczne wykrywanie** - VS Code/Cursor automatycznie używa .venv
- **requirements.txt** - lista zależności dla środowiska wirtualnego
- **Uruchamianie** - bezpośrednio z IDE lub przez skrypt run.py
- **Czyszczenie** - łatwe usunięcie całego środowiska
- **Bezpieczeństwo** - nie wpływa na systemowe instalacje Python

## 🚀 Następne Kroki
1. Utworzenie struktury projektu
2. Instalacja zależności w środowisku wirtualnym
3. Implementacja podstawowej funkcjonalności
4. Dodanie interfejsu graficznego
5. Testowanie i debugowanie
6. Dodanie dodatkowych funkcji

## 📝 Uwagi
- Aplikacja powinna być przyjazna dla użytkownika
- Obsługa różnych formatów YouTube
- Kompatybilność z różnymi systemami operacyjnymi
- Możliwość łatwego rozszerzania funkcjonalności
- **Izolowane środowisko wirtualne** - bezpieczna instalacja bez wpływu na system 