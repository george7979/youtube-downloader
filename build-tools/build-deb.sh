#!/bin/bash
# YouTube Downloader - Build Script for DEB Package
# Autor: george7979
# Wersja: 1.0.0

set -e  # Zakończ na pierwszym błędzie

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcja do wyświetlania kolorowych komunikatów
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Konfiguracja
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
BUILD_DIR="$PROJECT_ROOT/build"
DEBIAN_DIR="$BUILD_DIR/debian"
PACKAGE_DIR="$DEBIAN_DIR/youtube-downloader"

# Wczytaj wersję z main.py
get_version_from_source() {
    if [[ -f "$PROJECT_ROOT/main.py" ]]; then
        grep -o 'YouTube Downloader v[0-9]\+\.[0-9]\+\.[0-9]\+' "$PROJECT_ROOT/main.py" | sed 's/YouTube Downloader v//' || echo "1.0.3"
    else
        echo "1.0.3"
    fi
}

VERSION="${1:-$(get_version_from_source)}"
PACKAGE_NAME="youtube-downloader"
FULL_PACKAGE_NAME="${PACKAGE_NAME}_${VERSION}_all"

log_info "=== YouTube Downloader DEB Builder ==="
log_info "Wersja: $VERSION"
log_info "Katalog roboczy: $PROJECT_ROOT"

# Sprawdź wymagane pliki
check_required_files() {
    local required_files=(
        "main.py"
        "gui.py" 
        "downloader.py"
        "utils.py"
        "requirements.txt"
        "README.md"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            log_error "Brak wymaganego pliku: $file"
            exit 1
        fi
    done
    log_success "Wszystkie wymagane pliki istnieją"
}

# Wyczyść poprzedni build
clean_build() {
    log_info "Czyszczenie poprzedniego build..."
    rm -rf "$BUILD_DIR"
    rm -f "$PROJECT_ROOT"/*.deb
    log_success "Build directory wyczyszczone"
}

# Stwórz strukturę katalogów
create_directory_structure() {
    log_info "Tworzenie struktury katalogów..."
    
    mkdir -p "$PACKAGE_DIR/DEBIAN"
    mkdir -p "$PACKAGE_DIR/usr/bin"
    mkdir -p "$PACKAGE_DIR/usr/share/applications"
    mkdir -p "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME"
    mkdir -p "$PACKAGE_DIR/usr/share/$PACKAGE_NAME"
    mkdir -p "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/pics"
    
    # Ikony w różnych rozmiarach
    for size in 16x16 32x32 48x48 64x64 128x128 256x256; do
        mkdir -p "$PACKAGE_DIR/usr/share/icons/hicolor/$size/apps"
    done
    
    log_success "Struktura katalogów utworzona"
}

# Kopiuj pliki aplikacji
copy_application_files() {
    log_info "Kopiowanie plików aplikacji..."
    
    # Główne pliki Python
    cp "$PROJECT_ROOT/main.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    cp "$PROJECT_ROOT/gui.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    cp "$PROJECT_ROOT/downloader.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    cp "$PROJECT_ROOT/utils.py" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    cp "$PROJECT_ROOT/requirements.txt" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    
    # Dokumentacja
    cp "$PROJECT_ROOT/README.md" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    cp "$PROJECT_ROOT/plan.md" "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/"
    
    # Obrazki jeśli istnieją
    if [[ -d "$PROJECT_ROOT/pics" ]]; then
        cp -r "$PROJECT_ROOT/pics/"* "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/pics/"
    fi
    
    # Ikony aplikacji
    if [[ -d "$PROJECT_ROOT/icons" ]]; then
        for size in 16x16 32x32 48x48 64x64 128x128 256x256; do
            if [[ -f "$PROJECT_ROOT/icons/youtube-downloader-${size%x*}.png" ]]; then
                cp "$PROJECT_ROOT/icons/youtube-downloader-${size%x*}.png" \
                   "$PACKAGE_DIR/usr/share/icons/hicolor/$size/apps/youtube-downloader.png"
            fi
        done
    fi
    
    # Ustaw uprawnienia
    chmod +x "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/main.py"
    chmod +x "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/gui.py"
    chmod +x "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/downloader.py"
    chmod +x "$PACKAGE_DIR/usr/share/$PACKAGE_NAME/utils.py"
    
    log_success "Pliki aplikacji skopiowane"
}

# Stwórz plik wykonawczy
create_executable() {
    log_info "Tworzenie pliku wykonywalnego..."
    
    cat > "$PACKAGE_DIR/usr/bin/$PACKAGE_NAME" << 'EOF'
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
EOF
    
    chmod +x "$PACKAGE_DIR/usr/bin/$PACKAGE_NAME"
    log_success "Plik wykonywalny utworzony"
}

# Stwórz plik .desktop
create_desktop_file() {
    log_info "Tworzenie pliku .desktop..."
    
    cat > "$PACKAGE_DIR/usr/share/applications/$PACKAGE_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=YouTube Downloader
Name[pl]=YouTube Downloader
Comment=Download videos from YouTube
Comment[pl]=Pobieraj filmy z YouTube
Exec=youtube-downloader
Icon=youtube-downloader
Terminal=false
Categories=Network;Video;AudioVideo;
Keywords=youtube;download;video;mp4;mp3;
StartupNotify=true
EOF
    
    log_success "Plik .desktop utworzony"
}

# Stwórz plik control
create_control_file() {
    log_info "Tworzenie pliku control..."
    
    # Oblicz rozmiar w KB
    INSTALLED_SIZE=$(du -sk "$PACKAGE_DIR/usr" | cut -f1)
    
    cat > "$PACKAGE_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Architecture: all
Maintainer: Jerzy Maczewski <jerzy.maczewski@example.com>
Installed-Size: $INSTALLED_SIZE
Depends: python3 | python3-minimal, python3-tk, python3-venv
Section: utils
Priority: optional
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
EOF
    
    log_success "Plik control utworzony"
}

# Skopiuj lub stwórz skrypty maintenance
copy_maintenance_scripts() {
    log_info "Kopiowanie skryptów maintenance..."
    
    # Jeśli istnieją w oryginalnej strukturze, skopiuj je
    if [[ -f "$PROJECT_ROOT/debian/youtube-downloader/DEBIAN/postinst" ]]; then
        cp "$PROJECT_ROOT/debian/youtube-downloader/DEBIAN/postinst" "$PACKAGE_DIR/DEBIAN/"
        chmod +x "$PACKAGE_DIR/DEBIAN/postinst"
    fi
    
    if [[ -f "$PROJECT_ROOT/debian/youtube-downloader/DEBIAN/prerm" ]]; then
        cp "$PROJECT_ROOT/debian/youtube-downloader/DEBIAN/prerm" "$PACKAGE_DIR/DEBIAN/"
        chmod +x "$PACKAGE_DIR/DEBIAN/prerm"
    fi
    
    if [[ -f "$PROJECT_ROOT/debian/youtube-downloader/DEBIAN/postrm" ]]; then
        cp "$PROJECT_ROOT/debian/youtube-downloader/DEBIAN/postrm" "$PACKAGE_DIR/DEBIAN/"
        chmod +x "$PACKAGE_DIR/DEBIAN/postrm"
    fi
    
    log_success "Skrypty maintenance skopiowane"
}

# Stwórz changelog
create_changelog() {
    log_info "Tworzenie changelog..."
    
    cat > "$BUILD_DIR/changelog" << EOF
youtube-downloader ($VERSION) stable; urgency=medium

  * Aktualizacja do wersji $VERSION
  * Automatycznie wygenerowane przez build script

 -- Jerzy Maczewski <jerzy.maczewski@example.com>  $(date -R)
EOF
    
    gzip -9 -c "$BUILD_DIR/changelog" > "$PACKAGE_DIR/usr/share/doc/$PACKAGE_NAME/changelog.gz"
    
    log_success "Changelog utworzony"
}

# Wygeneruj sumy kontrolne MD5
generate_md5sums() {
    log_info "Generowanie sum kontrolnych MD5..."
    
    cd "$PACKAGE_DIR"
    find . -path './DEBIAN' -prune -o -type f -print0 | xargs -0 md5sum > DEBIAN/md5sums
    cd "$PROJECT_ROOT"
    
    log_success "Sumy kontrolne MD5 wygenerowane"
}

# Zbuduj pakiet DEB
build_package() {
    log_info "Budowanie pakietu DEB..."
    
    cd "$DEBIAN_DIR"
    fakeroot dpkg-deb --build youtube-downloader
    
    if [[ -f "$DEBIAN_DIR/youtube-downloader.deb" ]]; then
        mv "$DEBIAN_DIR/youtube-downloader.deb" "$PROJECT_ROOT/${FULL_PACKAGE_NAME}.deb"
        log_success "Pakiet DEB utworzony: ${FULL_PACKAGE_NAME}.deb"
    else
        log_error "Nie udało się utworzyć pakietu DEB"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
}

# Weryfikuj pakiet
verify_package() {
    log_info "Weryfikacja pakietu..."
    
    local package_file="$PROJECT_ROOT/${FULL_PACKAGE_NAME}.deb"
    
    if [[ -f "$package_file" ]]; then
        log_info "Informacje o pakiecie:"
        dpkg --info "$package_file"
        
        log_info "Zawartość pakietu:"
        dpkg --contents "$package_file" | head -10
        
        log_success "Pakiet zweryfikowany: $(ls -lh "$package_file" | awk '{print $5}')"
    else
        log_error "Pakiet nie istnieje!"
        exit 1
    fi
}

# Główna funkcja
main() {
    log_info "Rozpoczynanie procesu budowania..."
    
    check_required_files
    clean_build
    create_directory_structure
    copy_application_files
    create_executable
    create_desktop_file
    create_control_file
    copy_maintenance_scripts
    create_changelog
    generate_md5sums
    build_package
    verify_package
    
    log_success "=== Build zakończony pomyślnie! ==="
    log_success "Pakiet: ${FULL_PACKAGE_NAME}.deb"
    log_info "Instalacja: sudo dpkg -i ${FULL_PACKAGE_NAME}.deb"
    log_info "Deinstalacja: sudo dpkg -r $PACKAGE_NAME"
}

# Sprawdź czy dpkg-deb jest dostępne
if ! command -v dpkg-deb &> /dev/null; then
    log_error "dpkg-deb nie jest dostępne. Zainstaluj dpkg-dev:"
    log_info "sudo apt-get install dpkg-dev"
    exit 1
fi

# Sprawdź czy fakeroot jest dostępne
if ! command -v fakeroot &> /dev/null; then
    log_error "fakeroot nie jest dostępne. Zainstaluj fakeroot:"
    log_info "sudo apt-get install fakeroot"
    exit 1
fi

# Uruchom główną funkcję
main "$@"