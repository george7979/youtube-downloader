# YouTube Downloader - Instrukcja Budowania

## 📋 Spis treści
- [Wymagania systemowe](#wymagania-systemowe)
- [Szybki start](#szybki-start)
- [Struktura projektu](#struktura-projektu)
- [Zarządzanie wersjami](#zarządzanie-wersjami)
- [Proces budowania](#proces-budowania)
- [Testowanie](#testowanie)
- [Publikacja](#publikacja)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [CI/CD](#cicd)

## 🛠️ Wymagania systemowe

### Podstawowe wymagania
- **System operacyjny**: Linux (Ubuntu, Debian, inne dystrybucje z dpkg)
- **Python**: 3.8 lub nowszy
- **Git**: do zarządzania wersjami kodu

### Wymagane pakiety do budowania
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    debhelper \
    devscripts \
    dh-python \
    dpkg-dev \
    fakeroot \
    python3-all \
    python3-setuptools \
    python3-dev \
    python3-pip \
    python3-venv \
    lintian \
    git

# Opcjonalnie dla weryfikacji pakietów
sudo apt-get install -y reprepro
```

### Sprawdź instalację
```bash
# Sprawdź wersje narzędzi
dpkg --version
python3 --version
git --version
fakeroot --version

# Sprawdź czy wszystko jest gotowe
./version-manager.sh show
```

## 🚀 Szybki start

### 1. Sklonuj lub pobierz repozytorium
```bash
git clone https://github.com/george7979/youtube-downloader.git
cd youtube-downloader
```

### 2. Zbuduj pakiet DEB
```bash
# Zbuduj z aktualną wersją
./build-deb.sh

# Lub zbuduj z konkretną wersją
./build-deb.sh 1.0.4
```

### 3. Przetestuj pakiet
```bash
# Sprawdź pakiet
dpkg --info youtube-downloader_*.deb
dpkg --contents youtube-downloader_*.deb

# Zainstaluj lokalnie (opcjonalnie)
sudo dpkg -i youtube-downloader_*.deb
```

## 📁 Struktura projektu

```
youtube-downloader/
├── 📄 build-deb.sh              # Główny skrypt budowania
├── 📄 version-manager.sh        # Zarządzanie wersjami
├── 📄 BUILDING.md               # Ta dokumentacja
├── 📄 README.md                 # Dokumentacja użytkownika
├── 📄 plan.md                   # Plan rozwoju aplikacji
├── 
├── 🐍 Pliki aplikacji Python:
├── 📄 main.py                   # Główny plik aplikacji
├── 📄 gui.py                    # Interfejs graficzny
├── 📄 downloader.py             # Logika pobierania
├── 📄 utils.py                  # Funkcje pomocnicze
├── 📄 requirements.txt          # Zależności Python
├── 
├── 🎨 Zasoby:
├── 📁 icons/                    # Ikony aplikacji (różne rozmiary)
├── 📁 pics/                     # Zrzuty ekranu i obrazki
├── 
├── 📦 Debian packaging:
├── 📁 debian-src/               # Standardowe pliki debian
│   ├── 📄 changelog             # Historia wersji
│   ├── 📄 control               # Metadane pakietu
│   ├── 📄 rules                 # Reguły budowania
│   ├── 📄 compat                # Wersja debhelper
│   ├── 📄 copyright             # Informacje o licencji
│   ├── 📄 youtube-downloader.install
│   └── 📄 youtube-downloader.desktop
├── 
├── 📁 debian/ (legacy)          # Stara struktura (zachowana dla kompatybilności)
├── 📁 build/                    # Katalog tymczasowy (tworzony automatycznie)
├── 📄 *.deb                     # Pakiety wyjściowe (tworzone automatycznie)
└── 📄 .version-backup           # Backup tagów git (tworzony automatycznie)
```

## 🔢 Zarządzanie wersjami

### Sprawdzenie aktualnej wersji
```bash
./version-manager.sh show
```

### Ręczne ustawienie wersji
```bash
# Ustaw konkretną wersję
./version-manager.sh set 1.0.4

# Sprawdź czy zaktualizowano
./version-manager.sh show
```

### Automatyczne zwiększanie wersji (Semantic Versioning)
```bash
# Zwiększ wersję patch (1.0.3 -> 1.0.4)
./version-manager.sh bump patch

# Zwiększ wersję minor (1.0.3 -> 1.1.0)
./version-manager.sh bump minor

# Zwiększ wersję major (1.0.3 -> 2.0.0)
./version-manager.sh bump major
```

### Pliki aktualizowane automatycznie
- `main.py` - tytuł okna aplikacji
- `README.md` - linki do pakietów i wersji
- `debian-src/changelog` - historia wersji (wymaga ręcznego opisu zmian)

### Workflow zarządzania wersjami
1. **Zwiększ wersję**: `./version-manager.sh bump patch`
2. **Uzupełnij changelog**: Edytuj `debian-src/changelog` i dodaj opis zmian
3. **Commit zmian**: `git commit -am "Bump version to 1.0.4"`
4. **Utwórz tag**: `git tag v1.0.4`
5. **Zbuduj pakiet**: `./build-deb.sh`
6. **Push z tagami**: `git push origin main --tags`

## 🔨 Proces budowania

### Standardowe budowanie
```bash
# Zbuduj z aktualną wersją z main.py
./build-deb.sh

# Zbuduj z konkretną wersją
./build-deb.sh 1.0.4
```

### Co robi skrypt budowania:
1. **Sprawdza wymagane pliki** - weryfikuje obecność wszystkich plików źródłowych
2. **Czyści poprzedni build** - usuwa katalog `build/` i stare pliki `.deb`
3. **Tworzy strukturę katalogów** - przygotowuje hierarchię plików dla pakietu
4. **Kopiuje pliki aplikacji** - pliki Python, dokumentację, ikony
5. **Tworzy plik wykonywalny** - skrypt `/usr/bin/youtube-downloader`
6. **Generuje metadane** - `control`, `desktop`, `changelog.gz`
7. **Kopiuje skrypty maintenance** - `postinst`, `prerm`, `postrm`
8. **Generuje MD5 sumy** - weryfikacja integralności plików
9. **Buduje pakiet** - używa `dpkg-deb --build`
10. **Weryfikuje rezultat** - sprawdza pakiet i wyświetla informacje

### Struktura tworzona w build/
```
build/
└── debian/
    └── youtube-downloader/
        ├── DEBIAN/
        │   ├── control
        │   ├── md5sums
        │   ├── postinst
        │   ├── prerm
        │   └── postrm
        └── usr/
            ├── bin/
            │   └── youtube-downloader
            ├── share/
            │   ├── applications/
            │   │   └── youtube-downloader.desktop
            │   ├── doc/
            │   │   └── youtube-downloader/
            │   │       └── changelog.gz
            │   ├── icons/
            │   │   └── hicolor/
            │   │       ├── 16x16/apps/
            │   │       ├── 32x32/apps/
            │   │       ├── 48x48/apps/
            │   │       ├── 64x64/apps/
            │   │       ├── 128x128/apps/
            │   │       └── 256x256/apps/
            │   └── youtube-downloader/
            │       ├── *.py
            │       ├── requirements.txt
            │       ├── README.md
            │       └── pics/
```

## 🧪 Testowanie

> **Uwaga**: Ta sekcja obejmuje testowanie techniczne pakietów. Dla kompleksowych procedur Testowania Akceptacji Użytkownika (UAT), bram jakości i przepływów zatwierdzania, zobacz [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md).

### Testy pakietu
```bash
# Sprawdź metadane pakietu
dpkg --info youtube-downloader_*.deb

# Sprawdź zawartość pakietu
dpkg --contents youtube-downloader_*.deb

# Weryfikuj integralność (jeśli lintian jest dostępny)
lintian youtube-downloader_*.deb

# Sprawdź zależności
dpkg-deb --field youtube-downloader_*.deb Depends
```

### Testy instalacji (w środowisku testowym)
```bash
# Zainstaluj pakiet
sudo dpkg -i youtube-downloader_*.deb

# Napraw ewentualne problemy z zależnościami
sudo apt-get install -f

# Przetestuj uruchomienie
youtube-downloader --version  # (jeśli obsługiwane)

# Sprawdź czy aplikacja się uruchamia
youtube-downloader

# Sprawdź logi instalacji
journalctl -u systemd-* | grep youtube-downloader

# Usuń pakiet po testach
sudo dpkg -r youtube-downloader
```

### Testy funkcjonalne
```bash
# Sprawdź czy środowisko wirtualne zostało utworzone
ls -la /usr/share/youtube-downloader/venv/

# Sprawdź czy zależności są zainstalowane
/usr/share/youtube-downloader/venv/bin/pip list

# Sprawdź czy ikony są na miejscu
ls -la /usr/share/icons/hicolor/*/apps/youtube-downloader.png

# Sprawdź plik .desktop
desktop-file-validate /usr/share/applications/youtube-downloader.desktop
```

## 🐍 Architektura Środowiska Wirtualnego

### 🎯 **Przegląd architektury**

YouTube Downloader używa **izolowanego środowiska wirtualnego Python** dla maksymalnej kompatybilności i bezpieczeństwa:

```
System Linux
├── /usr/bin/youtube-downloader          # Punkt wejścia
├── /usr/share/youtube-downloader/       # Pliki aplikacji
│   ├── venv/                            # 🔒 Izolowane środowisko Python
│   │   ├── bin/python                   # Dedykowana instancja Python
│   │   ├── bin/pip                      # Menedżer pakietów venv
│   │   ├── bin/activate                 # Skrypt aktywacji
│   │   └── lib/python3.*/site-packages/ # Zależności aplikacji
│   ├── main.py                          # Kod aplikacji
│   ├── gui.py, downloader.py, utils.py  # Moduły aplikacji
│   └── requirements.txt                 # Specyfikacja zależności
```

### 🔄 **Cykl życia środowiska wirtualnego**

#### **1. Instalacja pakietu (`dpkg -i`):**
```bash
# Automatycznie wykonywany skrypt postinst (282 linie)
DEBIAN/postinst
├── 🔍 Sprawdzenie zależności systemowych (python3-venv, python3-tk)
├── 🔧 Tworzenie środowiska wirtualnego (3 metody fallback)
├── 🔒 Bezpieczne pobieranie pip przez SSL (jeśli potrzeba)
├── 📦 Instalacja zależności aplikacji (yt-dlp>=2024.10,<2026.0)
└── ✅ Weryfikacja poprawności instalacji
```

#### **2. Uruchomienie aplikacji (`youtube-downloader`):**
```bash
# Skrypt /usr/bin/youtube-downloader
#!/bin/bash
source /usr/share/youtube-downloader/venv/bin/activate  # 🔄 Aktywacja venv
cd /usr/share/youtube-downloader                        # 📁 Przejście do katalogu
python main.py                                          # 🚀 Uruchomienie aplikacji
```

#### **3. Deinstalacja (`dpkg -r`):**
```bash
# Automatycznie wykonywane skrypty
DEBIAN/prerm   (17 linii)  # Przygotowanie do usunięcia
DEBIAN/postrm  (72 linie)  # Całkowite czyszczenie venv i plików
```

### 🛡️ **Zaawansowane tworzenie środowiska wirtualnego**

Skrypt **postinst** (282 linie) implementuje **3-poziomową strategię fallback** dla maksymalnej kompatybilności:

#### **Poziom 1: Standardowa metoda (linie 140-155)**
```bash
echo "🔄 Tworzenie środowiska wirtualnego (metoda standardowa)..."
if python3 -m venv "$VENV_DIR"; then
    echo "✅ Standardowe utworzenie venv zakończone sukcesem"
    VENV_CREATED=true
else
    echo "❌ Standardowa metoda nie zadziałała, przechodzę do metody 2"
fi
```

#### **Poziom 2: Bez wbudowanego pip + SSL curl (linie 156-189)**
```bash
if [ "$VENV_CREATED" = false ]; then
    echo "🔄 Tworzenie venv bez pip + SSL pobieranie..."
    
    # Tworzenie venv bez pip
    if python3 -m venv --without-pip "$VENV_DIR"; then
        echo "✅ Venv bez pip utworzony"
        
        # Bezpieczne pobieranie get-pip.py
        if curl --tlsv1.2 --proto '=https' \
               --cacert /etc/ssl/certs/ca-certificates.crt \
               --cert-status \
               --connect-timeout 10 --max-time 60 \
               https://bootstrap.pypa.io/get-pip.py \
               -o /tmp/get-pip.py; then
               
            # Instalacja pip
            "$VENV_DIR/bin/python" /tmp/get-pip.py --no-warn-script-location
            rm -f /tmp/get-pip.py
            VENV_CREATED=true
        fi
    fi
fi
```

#### **Poziom 3: Metoda manualna - ostateczność (linie 190-240)**
```bash
if [ "$VENV_CREATED" = false ]; then
    echo "🔄 Ręczne tworzenie struktury venv (metoda 3)..."
    
    # Tworzenie struktury katalogów
    mkdir -p "$VENV_DIR"/{bin,lib,include}
    mkdir -p "$VENV_DIR/lib/python$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)/site-packages"
    
    # Kopiowanie interpretera Python
    PYTHON_BIN=$(which python3)
    cp "$PYTHON_BIN" "$VENV_DIR/bin/python3"
    ln -sf python3 "$VENV_DIR/bin/python"
    
    # Tworzenie pyvenv.cfg
    cat > "$VENV_DIR/pyvenv.cfg" << EOF
home = $(dirname "$PYTHON_BIN")
include-system-site-packages = false
version = $(python3 --version | cut -d' ' -f2)
EOF
    
    # Pobieranie i instalacja pip przez SSL
    if curl --tlsv1.2 --proto '=https' \
           --cacert /etc/ssl/certs/ca-certificates.crt \
           https://bootstrap.pypa.io/get-pip.py | \
           "$VENV_DIR/bin/python"; then
        VENV_CREATED=true
        echo "✅ Manualne tworzenie venv zakończone sukcesem"
    fi
fi
```

### 📦 **Zarządzanie zależnościami**

#### **Zależności systemowe (DEBIAN/control):**
```
Depends: ${misc:Depends}, ${python3:Depends}, python3, python3-tk, python3-venv, python3-pip
Recommends: ffmpeg
Suggests: vlc
```

#### **Zależności aplikacji (instalowane w venv postinst:242-280):**
```bash
# Upgrade pip z zabezpieczeniami SSL
"$VENV_DIR/bin/pip" install --upgrade pip \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org

# Instalacja głównych zależności
"$VENV_DIR/bin/pip" install \
    "yt-dlp>=2024.10,<2026.0" requests urllib3 certifi brotli pycryptodomex \
    --no-warn-script-location
```

#### **Automatyczna instalacja FFmpeg w tle (postinst:95-121):**
```bash
install_ffmpeg_background() {
    echo "🔄 Instalowanie FFmpeg w tle..."
    (
        # Cicha aktualizacja listy pakietów
        apt-get update -qq 2>/dev/null
        
        # Instalacja bez interakcji użytkownika
        DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg 2>/dev/null
        
        # Sprawdzenie wyniku
        if which ffmpeg >/dev/null 2>&1; then
            echo "✅ FFmpeg zainstalowany pomyślnie"
        else
            echo "⚠️ Nie udało się zainstalować FFmpeg automatycznie"
        fi
    ) &
    
    FFMPEG_PID=$!
    echo "FFmpeg instaluje się w tle (PID: $FFMPEG_PID)"
}
```

### 🔒 **Bezpieczeństwo i izolacja**

#### **Korzyści izolacji:**
- ✅ **Brak konfliktów** - nie wpływa na systemowe pakiety Python
- ✅ **Czysta deinstalacja** - usuwa wszystkie zależności (postrm:45-58)
- ✅ **Wersjonowanie** - precyzyjna kontrola wersji zależności
- ✅ **Przenośność** - identyczne środowisko na każdym systemie
- ✅ **Bezpieczeństwo** - ograniczone uprawnienia

#### **Zaawansowane zabezpieczenia SSL (postinst):**
```bash
# Maksymalne zabezpieczenia SSL
curl --tlsv1.2 --proto '=https' \
     --cacert /etc/ssl/certs/ca-certificates.crt \
     --cert-status \
     --connect-timeout 10 --max-time 60 \
     --fail --silent --show-error \
     https://bootstrap.pypa.io/get-pip.py

# Trusted hosts jako fallback
"$VENV_DIR/bin/pip" install package_name \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org
```

#### **Weryfikacja integralności (postinst:267-280):**
```bash
# Test importowania po instalacji
if "$VENV_DIR/bin/python" -c "import yt_dlp; print(f'yt-dlp {yt_dlp.__version__} zaimportowany pomyślnie')" 2>/dev/null; then
    echo "✅ Weryfikacja yt-dlp: SUKCES"
else
    echo "❌ Weryfikacja yt-dlp: BŁĄD"
    exit 1
fi

# Test podstawowych funkcji Python
if "$VENV_DIR/bin/python" -c "import sys, os; print('Python działa poprawnie')" 2>/dev/null; then
    echo "✅ Weryfikacja środowiska Python: SUKCES"
else
    echo "❌ Weryfikacja środowiska Python: BŁĄD"
fi
```

### 🔍 **Diagnostyka środowiska wirtualnego**

#### **Sprawdzenie stanu venv:**
```bash
# Sprawdź czy venv istnieje
ls -la /usr/share/youtube-downloader/venv/

# Sprawdź wersję Pythona w venv
/usr/share/youtube-downloader/venv/bin/python --version

# Lista zainstalowanych pakietów
/usr/share/youtube-downloader/venv/bin/pip list

# Test importowania głównej zależności
/usr/share/youtube-downloader/venv/bin/python -c "import yt_dlp; print(f'yt-dlp: {yt_dlp.__version__}')"
```

#### **Sprawdzenie aktywacji:**
```bash
# Test skryptu aktywacji
source /usr/share/youtube-downloader/venv/bin/activate
which python  # Powinno wskazać na venv
echo $VIRTUAL_ENV  # Powinno pokazać ścieżkę venv
```

### 🚨 **Troubleshooting środowiska wirtualnego**

#### **Problem: Venv nie została utworzona**
```bash
# Sprawdź dostępność python3-venv
python3 -c "import venv"

# Sprawdź uprawnienia
ls -la /usr/share/youtube-downloader/

# Ręczne odtworzenie venv
sudo rm -rf /usr/share/youtube-downloader/venv
sudo python3 -m venv /usr/share/youtube-downloader/venv
sudo /usr/share/youtube-downloader/venv/bin/pip install "yt-dlp>=2024.10,<2026.0"
```

#### **Problem: Brak pip w venv**
```bash
# Zainstaluj pip ręcznie
curl https://bootstrap.pypa.io/get-pip.py | \
    sudo /usr/share/youtube-downloader/venv/bin/python
```

#### **Problem: Aplikacja nie uruchamia się**
```bash
# Debug uruchomienia
bash -x /usr/bin/youtube-downloader

# Sprawdź logi systemd
journalctl | grep youtube-downloader

# Test bezpośredni
cd /usr/share/youtube-downloader
source venv/bin/activate
python main.py
```

#### **Problem: Import Error yt_dlp**
```bash
# Reinstalacja zależności
sudo /usr/share/youtube-downloader/venv/bin/pip install --upgrade "yt-dlp>=2024.10,<2026.0"

# Sprawdź konflikt z systemowym yt-dlp
which yt-dlp  # Nie powinno znajdować jeśli używamy venv
```

### 📊 **Monitoring i logi**

#### **Logi instalacji postinst:**
```bash
# Logi podczas instalacji pakietu
sudo dpkg -i youtube-downloader_*.deb 2>&1 | tee install.log

# Logi systemd
journalctl -u dpkg | grep youtube-downloader
```

#### **Testowanie środowiska po instalacji:**
```bash
# Kompletny test środowiska
echo "=== Test środowiska wirtualnego ==="
ls -la /usr/share/youtube-downloader/venv/bin/
/usr/share/youtube-downloader/venv/bin/python --version
/usr/share/youtube-downloader/venv/bin/pip list
echo "=== Test importu ==="
/usr/share/youtube-downloader/venv/bin/python -c "
import sys
print(f'Python: {sys.version}')
import yt_dlp
print(f'yt-dlp: {yt_dlp.__version__}')
print('✅ Wszystkie zależności dostępne')
"
```

### 🔄 **Inteligentna obsługa aktualizacji**

#### **Wykrywanie typu operacji (prerm:8-15)**
```bash
case "$1" in
    upgrade|failed-upgrade)
        echo "Aktualizacja wykryta - zachowuję środowisko wirtualne"
        # NIE usuwaj venv podczas upgrade
        ;;
    remove|deconfigure)
        echo "Usuwanie pakietu - przygotowanie do czyszczenia"
        # Przygotuj do usunięcia venv
        ;;
esac
```

#### **Czyste usuwanie (postrm:32-72)**
```bash
# Wykrywanie katalogów użytkownika
detect_user_directories() {
    USER_DIRS=""
    for user_dir in /home/*/Downloads /home/*/Pobrane; do
        if [ -d "$user_dir" ]; then
            USER_DIRS="$USER_DIRS $user_dir"
        fi
    done
}

# Ostrzeżenie o zachowanych plikach
warn_about_user_files() {
    if [ -n "$USER_DIRS" ]; then
        echo "⚠️ UWAGA: Pobrane pliki w katalogach użytkownika zostają zachowane"
        echo "   Jeśli chcesz je usunąć, zrób to ręcznie:"
        for dir in $USER_DIRS; do
            echo "   - Sprawdź: $dir"
        done
    fi
}

# Pełne czyszczenie przy usuwaniu
if [ "$1" = "purge" ] || [ "$1" = "remove" ]; then
    if [ -d "/usr/share/youtube-downloader/venv" ]; then
        rm -rf /usr/share/youtube-downloader/venv
        echo "✅ Środowisko wirtualne usunięte"
    fi
    
    # Usunięcie głównego katalogu
    rmdir /usr/share/youtube-downloader 2>/dev/null || true
    
    # Usunięcie pliku wykonywalnego
    rm -f /usr/bin/youtube-downloader
fi
```

### 🔧 **Ręczna rekonstrukcja środowiska**

Jeśli wszystkie automatyczne metody zawiodą, użyj identycznej logiki co postinst:

```bash
#!/bin/bash
# Skrypt odtwarzania środowiska na podstawie postinst

VENV_DIR="/usr/share/youtube-downloader/venv"
VENV_CREATED=false

echo "🧹 Usuwanie uszkodzonego środowiska..."
sudo rm -rf "$VENV_DIR"

echo "🔄 Poziom 1: Standardowa metoda..."
if sudo python3 -m venv "$VENV_DIR"; then
    echo "✅ Standardowe venv utworzone"
    VENV_CREATED=true
fi

if [ "$VENV_CREATED" = false ]; then
    echo "🔄 Poziom 2: Bez pip + SSL..."
    if sudo python3 -m venv --without-pip "$VENV_DIR"; then
        if curl --tlsv1.2 --proto '=https' \
               --cacert /etc/ssl/certs/ca-certificates.crt \
               https://bootstrap.pypa.io/get-pip.py | \
               sudo "$VENV_DIR/bin/python"; then
            VENV_CREATED=true
            echo "✅ Venv z SSL pip utworzony"
        fi
    fi
fi

if [ "$VENV_CREATED" = true ]; then
    echo "📦 Instalacja zależności..."
    sudo "$VENV_DIR/bin/pip" install --upgrade pip \
        --trusted-host pypi.org \
        --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org
    
    sudo "$VENV_DIR/bin/pip" install \
        yt-dlp requests urllib3 certifi brotli pycryptodomex
    
    echo "✅ Test końcowy..."
    youtube-downloader
else
    echo "❌ Wszystkie metody zawiodły"
    exit 1
fi
```

---

## 📤 Publikacja

### GitHub Releases
1. **Utwórz release na GitHub**:
   ```bash
   # Upewnij się że masz utworzony tag
   git tag v1.0.4
   git push origin v1.0.4
   ```

2. **Wgraj pakiet .deb** do GitHub Release

3. **Zaktualizuj README.md** z linkiem do nowego release

### Repozytorium APT (opcjonalnie)
```bash
# Jeśli masz swoje repozytorium APT
reprepro includedeb stable youtube-downloader_*.deb
```

### Suma kontrolna
```bash
# Wygeneruj sumy kontrolne dla publikacji
sha256sum youtube-downloader_*.deb > youtube-downloader_*.deb.sha256
md5sum youtube-downloader_*.deb > youtube-downloader_*.deb.md5
```

## 🚨 Rozwiązywanie problemów

### Problem: "dpkg-deb: command not found"
```bash
# Zainstaluj dpkg-dev
sudo apt-get install dpkg-dev
```

### Problem: "fakeroot: command not found"
```bash
# Zainstaluj fakeroot
sudo apt-get install fakeroot
```

### Problem: Błędy w skrypcie postinst
```bash
# Sprawdź składnię
bash -n debian-src/postinst

# Sprawdź logi systemd po instalacji
journalctl -f

# Debuguj instalację
sudo dpkg -i --debug=scripts youtube-downloader_*.deb
```

### Problem: Błędny format changelog
```bash
# Sprawdź format changelog
dpkg-parsechangelog -l debian-src/changelog
```

### Problem: Błędne uprawnienia
```bash
# Napraw uprawnienia
chmod +x build-deb.sh version-manager.sh
chmod +x debian-src/rules
```

### Problem: Brak ikon
```bash
# Sprawdź czy ikony istnieją
ls -la icons/
file icons/youtube-downloader-*.png

# Sprawdź czy zostały skopiowane
ls -la build/debian/youtube-downloader/usr/share/icons/hicolor/*/apps/
```

### Debug mode
```bash
# Uruchom build script w trybie debug
DEBUG=1 ./build-deb.sh

# Sprawdź szczegółowe logi
bash -x ./build-deb.sh 2>&1 | tee build.log
```

## 🔄 CI/CD

### GitHub Actions (przykład)
Stwórz `.github/workflows/build.yml`:

```yaml
name: Build DEB Package

on:
  push:
    tags:
      - 'v*'
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install build dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          build-essential debhelper devscripts \
          dh-python dpkg-dev fakeroot python3-all \
          python3-setuptools lintian
    
    - name: Build DEB package
      run: ./build-deb.sh
    
    - name: Test package
      run: |
        dpkg --info *.deb
        lintian *.deb || true
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: deb-package
        path: "*.deb"
    
    - name: Create Release
      if: startsWith(github.ref, 'refs/tags/')
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
```

### Makefile (opcjonalnie)
```makefile
# Makefile dla YouTube Downloader
VERSION := $(shell ./version-manager.sh show | grep "Aktualna wersja:" | cut -d: -f2 | xargs)

.PHONY: build clean test install version help

help:
	@echo "YouTube Downloader Build System"
	@echo "Available targets:"
	@echo "  build    - Build DEB package"
	@echo "  clean    - Clean build artifacts"
	@echo "  test     - Test the package"
	@echo "  install  - Install locally"
	@echo "  version  - Show current version"

build:
	./build-deb.sh

clean:
	rm -rf build/
	rm -f *.deb *.md5 *.sha256

test: build
	dpkg --info *.deb
	dpkg --contents *.deb
	-lintian *.deb

install: build
	sudo dpkg -i *.deb
	sudo apt-get install -f

version:
	./version-manager.sh show

bump-patch:
	./version-manager.sh bump patch

bump-minor:
	./version-manager.sh bump minor

bump-major:
	./version-manager.sh bump major
```

---

## 📞 Wsparcie

Jeśli masz problemy z budowaniem:

1. **Sprawdź ten dokument** - większość problemów jest tu opisana
2. **Sprawdź logi** - używaj `bash -x` do debugowania
3. **Sprawdź GitHub Issues** - może ktoś już miał podobny problem
4. **Utwórz Issue** - opisz problem i dołącz logi

---

**Powodzenia w budowaniu! 🚀**