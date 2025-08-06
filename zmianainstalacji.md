# Plan Instalacji - YouTube Downloader v1.0.2

## Cel
Utworzenie samodzielnego pakietu DEB (youtube-downloader_1.0.2_all.deb), który:
- Nie wymaga żadnych lokalnych zależności do instalacji
- Automatycznie sprawdza i instaluje Python jeśli brakuje
- Instaluje aplikację w środowisku wirtualnym Python
- Wszystkie zależności są izolowane w venv
- Czysta deinstalacja - usuwa aplikację, katalog roboczy i środowisko wirtualne, ale nie systemowy Python

## Analiza obecnych problemów

### Obecne problemy w wersji 1.0.1:
1. **Zależności systemowe**: Pakiet wymaga `python3-tk`, `python3-pip` - może nie być dostępne na wszystkich systemach
2. **Konflikty zależności**: Instalacja globalna może kolidować z innymi aplikacjami
3. **Brak izolacji**: Zależności są instalowane globalnie
4. **Zależność od zewnętrznych pakietów**: Wymaga systemowych pakietów Python

### Zalety nowego podejścia:
1. **Automatyczna instalacja Pythona**: Sprawdzenie i instalacja jeśli brakuje
2. **Środowisko wirtualne**: Pełna izolacja zależności
3. **Czysta deinstalacja**: Usuwa tylko aplikację, nie systemowy Python
4. **Samodzielność**: Pakiet nie wymaga zewnętrznych zależności

## Plan działania

### 1. Struktura pakietu DEB v1.0.2

```
youtube-downloader_1.0.2_all.deb
├── DEBIAN/
│   ├── control (bez zależności systemowych)
│   ├── postinst (sprawdzenie/instalacja Python + venv)
│   ├── postrm (czysta deinstalacja)
│   └── prerm (usuwanie venv)
├── usr/
│   ├── bin/youtube-downloader (skrypt uruchamiający)
│   ├── share/
│   │   ├── applications/youtube-downloader.desktop
│   │   ├── icons/hicolor/.../youtube-downloader.png
│   │   └── youtube-downloader/ (pliki aplikacji)
```

### 2. Kluczowe zmiany w plikach DEB

#### DEBIAN/control
```deb
Source: youtube-downloader
Section: utils
Priority: optional
Maintainer: Jerzy Maczewski <jerzy.maczewski@example.com>
Build-Depends: debhelper (>= 11), dh-python, python3-all
Standards-Version: 4.5.1

Package: youtube-downloader
Architecture: all
Depends: python3 | python3-minimal
Description: YouTube Downloader - Aplikacja do pobierania filmów z YouTube
 Prosta aplikacja w Python do pobierania filmów z YouTube z interfejsem graficznym.
 .
 Funkcje:
  - Pobieranie filmów z YouTube z wklejanego linku
  - Pobieranie z dźwiękiem w formacie MP4
  - Wybór rozdzielczości przed pobieraniem
  - Wybór katalogu docelowego dla pobieranych plików
  - Walidacja linku YouTube przed pobieraniem
  - Progress bar pokazujący postęp pobierania
  - Obsługa błędów (film nie istnieje, brak połączenia)
  - Informacje o filmie (tytuł, czas trwania, dostępne formaty)
  - Przycisk "Anuluj" podczas pobierania
  - Możliwość pobierania tylko audio (MP3)
  - Automatyczne sanityzowanie nazw plików
 .
 ⚠️ UWAGA PRAWNA: Ta aplikacja jest narzędziem technicznym. 
 Użytkownik odpowiada za legalność pobierania treści.
```

#### DEBIAN/postinst
```bash
#!/bin/bash

# Sprawdź czy Python jest zainstalowany
if ! command -v python3 >/dev/null 2>&1; then
    echo "🐍 Python3 nie jest zainstalowany. Instalowanie..."
    apt-get update
    apt-get install -y python3 python3-venv python3-pip
fi

# Utwórz środowisko wirtualne
echo "🔧 Tworzenie środowiska wirtualnego..."
python3 -m venv /usr/share/youtube-downloader/venv

# Zainstaluj zależności w środowisku wirtualnym
echo "📚 Instalowanie zależności w środowisku wirtualnym..."
/usr/share/youtube-downloader/venv/bin/pip install yt-dlp

# Aktualizuj ikony i desktop
if command -v update-icon-caches >/dev/null 2>&1; then
    update-icon-caches /usr/share/icons/hicolor
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Utwórz katalog logów użytkownika
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    USER_HOME=$HOME
fi

if [ -n "$USER_HOME" ] && [ -d "$USER_HOME" ]; then
    mkdir -p "$USER_HOME/.youtube-downloader" || true
fi

chmod 755 /usr/bin/youtube-downloader || true
chmod 644 /usr/share/applications/youtube-downloader.desktop || true

echo "✅ YouTube Downloader v1.0.2 został zainstalowany pomyślnie!"
echo "🚀 Uruchom aplikację komendą: youtube-downloader"
echo "📱 Lub znajdź w menu aplikacji systemu"
echo "📝 Logi będą zapisywane w: ~/.youtube-downloader/youtube_downloader.log"
echo ""
echo "⚠️  UWAGA PRAWNA: Ta aplikacja jest narzędziem technicznym."
echo "Użytkownik odpowiada za legalność pobierania treści."
```

#### DEBIAN/prerm
```bash
#!/bin/bash

echo "🧹 Usuwanie środowiska wirtualnego..."
rm -rf /usr/share/youtube-downloader/venv || true
```

#### DEBIAN/postrm
```bash
#!/bin/bash

echo "🗑️ Usuwanie plików aplikacji..."

# Usuń pliki aplikacji
rm -rf /usr/share/youtube-downloader || true
rm -f /usr/bin/youtube-downloader || true
rm -f /usr/share/applications/youtube-downloader.desktop || true

# Usuń ikony
rm -f /usr/share/icons/hicolor/*/apps/youtube-downloader.png || true

# Usuń logi użytkownika
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    USER_HOME=$HOME
fi

if [ -n "$USER_HOME" ] && [ -d "$USER_HOME" ]; then
    rm -rf "$USER_HOME/.youtube-downloader" || true
fi

echo "✅ Deinstalacja zakończona!"
echo "🐍 Środowisko wirtualne zostało usunięte"
echo "📝 Systemowy Python pozostaje nienaruszony"
```

### 3. Skrypt uruchamiający (/usr/bin/youtube-downloader)

```bash
#!/bin/bash

# Sprawdź czy środowisko wirtualne istnieje
if [ ! -d "/usr/share/youtube-downloader/venv" ]; then
    echo "❌ Błąd: Środowisko wirtualne nie istnieje"
    echo "Spróbuj przeinstalować aplikację: sudo apt reinstall youtube-downloader"
    exit 1
fi

# Sprawdź czy główny plik aplikacji istnieje
if [ ! -f "/usr/share/youtube-downloader/main.py" ]; then
    echo "❌ Błąd: Plik aplikacji nie istnieje"
    echo "Spróbuj przeinstalować aplikację: sudo apt reinstall youtube-downloader"
    exit 1
fi

# Aktywuj środowisko wirtualne i uruchom aplikację
source /usr/share/youtube-downloader/venv/bin/activate
cd /usr/share/youtube-downloader
python main.py
```

### 4. Plik .desktop

```desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=YouTube Downloader
Comment=Download videos from YouTube with GUI
Exec=youtube-downloader
Icon=youtube-downloader
Terminal=false
Categories=AudioVideo;Video;Network;
```

## Korzyści nowego podejścia

### ✅ Samodzielność
- Pakiet zawiera wszystko co potrzebne
- Nie wymaga zewnętrznych zależności systemowych
- Automatyczna instalacja Python jeśli brakuje

### ✅ Izolacja
- Zależności w venv nie wpływają na system
- Brak konfliktów z innymi aplikacjami
- Czyste środowisko dla aplikacji

### ✅ Czysta deinstalacja
- Usuwa tylko aplikację i jej środowisko
- Nie modyfikuje systemowego Python
- Nie pozostawia śladów w systemie

### ✅ Kompatybilność
- Działa na różnych dystrybucjach Linux
- Obsługuje różne wersje Python
- Nie wymaga konkretnych pakietów systemowych

### ✅ Bezpieczeństwo
- Nie modyfikuje systemowych zależności
- Izolowane środowisko uruchomieniowe
- Kontrolowane zarządzanie zależnościami

## Plan implementacji

### Etap 1: Przygotowanie plików DEB
1. Modyfikacja `debian/control` - usunięcie zależności systemowych
2. Aktualizacja `debian/postinst` - dodanie logiki instalacji Python i venv
3. Aktualizacja `debian/prerm` i `debian/postrm` - czysta deinstalacja
4. Utworzenie nowego skryptu uruchamiającego

### Etap 2: Budowanie pakietu
1. Aktualizacja wersji w `debian/changelog`
2. Budowanie pakietu DEB
3. Testowanie instalacji/deinstalacji

### Etap 3: Testy
1. Test na czystym systemie (bez Python)
2. Test na systemie z Python
3. Test deinstalacji
4. Test kompatybilności z różnymi dystrybucjami

## Wersja docelowa
- **Nazwa**: youtube-downloader_1.0.2_all.deb
- **Rozmiar**: ~50KB (zawiera tylko pliki aplikacji)
- **Zależności**: python3 | python3-minimal
- **Funkcje**: Samodzielna instalacja z automatycznym zarządzaniem Python i venv 