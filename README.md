# YouTube Downloader

Prosta aplikacja w Python do pobierania filmów z YouTube z interfejsem graficznym.

![YouTube Downloader Interface](pics/youtube-downloader-2.png)

## ✨ Funkcje

- 📥 **Pobieranie filmów** z YouTube i innych platform
- 🎨 **Intuicyjny interfejs** graficzny
- 📊 **Wybór jakości** wideo i audio
- 📁 **Zapamiętywanie ścieżki** pobierania
- ⚡ **Szybka i stabilna** praca

## ⚠️ Uwaga Prawna

**Ta aplikacja jest narzędziem technicznym. Użytkownik odpowiada za legalność pobierania treści.**

### ✅ Dozwolone użycie:
- Własne treści YouTube (autor może pobierać swoje filmy)
- Treści na licencjach Creative Commons, public domain
- Backup własnych materiałów
- Użycie edukacyjne w ramach dozwolonego użytku

### ❌ Niedozwolone użycie:
- Pobieranie cudzych treści bez zgody autora
- Komercyjna dystrybucja pobranych treści
- Naruszenie praw autorskich

**Respektuj prawa autorskie i [Warunki serwisu YouTube](https://www.youtube.com/t/terms).**

## 🛠️ Instalacja

### Wymagania systemowe:
- Linux (Ubuntu, Debian, inne dystrybucje)
- Python 3.8+ (instalowany automatycznie)
- Dostęp do internetu

### Instalacja z pakietu .deb (zalecana)

1. **Pobierz najnowszy pakiet:**
   ```bash
   # Przejdź do: https://github.com/george7979/youtube-downloader/releases
   # Pobierz youtube-downloader_X.X.X_all.deb
   ```

2. **Zainstaluj pakiet:**
   ```bash
   sudo dpkg -i youtube-downloader_*.deb
   sudo apt-get install -f  # napraw zależności jeśli potrzeba
   ```

**Uwaga:** Pakiet automatycznie instaluje wszystkie wymagane zależności w izolowanym środowisku, nie wpływając na inne aplikacje.

## 🚀 Uruchomienie

```bash
youtube-downloader
```

Lub znajdź aplikację w menu systemu.

## 🎮 Jak używać

### 1. Uruchom aplikację
```bash
youtube-downloader
```

### 2. Wklej link YouTube
Wprowadź adres URL filmu w pole tekstowe.

### 3. Sprawdź film
Kliknij "Sprawdź" aby pobrać informacje o filmie.

### 4. Wybierz opcje
- **Tylko audio**: Zaznacz dla pobierania MP3
- **Jakość**: Wybierz rozdzielczość z listy
- **Folder**: Kliknij "Wybierz folder" aby wybrać katalog

### 5. Pobierz
Kliknij "Pobierz" aby rozpocząć pobieranie.

## 🔧 Rozwiązywanie problemów

### Aplikacja nie uruchamia się:
```bash
sudo apt reinstall youtube-downloader
```

### Błędy instalacji:
```bash
sudo apt-get install -f
sudo dpkg -i youtube-downloader_*.deb
```

### Błędy pobierania:
- Sprawdź połączenie internetowe
- Upewnij się, że link jest prawidłowy
- Niektóre filmy mogą być zablokowane regionalnie

## 🗑️ Deinstalacja

```bash
# Standardowa deinstalacja
sudo dpkg -r youtube-downloader

# Kompletne usunięcie z konfiguracją
sudo dpkg -P youtube-downloader
```

## 🐛 Zgłaszanie problemów

Znalazłeś błąd? Masz propozycję nowej funkcji?

**Zgłoś w GitHub Issues:** https://github.com/george7979/youtube-downloader/issues

## 📈 Historia wersji

| Wersja | Data | Opis |
|--------|------|------|
| v1.2.0 | 2025-08 | Ulepszona architektura i bezpieczeństwo |
| v1.0.3 | 2025-08 | Poprawki bezpieczeństwa |
| v1.0.2 | 2025-08 | Poprawki błędów |
| v1.0.1 | 2025-08 | Pierwsze ulepszenia |
| v1.0.0 | 2025-08 | Pierwsze wydanie |

---
*YouTube Downloader - Narzędzie do zarządzania wideo*