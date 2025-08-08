#!/bin/bash
# YouTube Downloader - Version Management Script
# Autor: george7979
# Wersja: 1.0.0

set -e

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Konfiguracja
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Pliki do aktualizacji wersji
VERSION_FILES=(
    "main.py"
    "debian-src/changelog"
    "README.md"
)

# Funkcja do pobierania aktualnej wersji z main.py
get_current_version() {
    if [[ -f "$PROJECT_ROOT/main.py" ]]; then
        grep -o 'YouTube Downloader v[0-9]\+\.[0-9]\+\.[0-9]\+' "$PROJECT_ROOT/main.py" | sed 's/YouTube Downloader v//' || echo "1.0.3"
    else
        echo "1.0.3"
    fi
}

# Funkcja do walidacji formatu wersji
validate_version() {
    local version="$1"
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Nieprawidłowy format wersji: $version"
        log_info "Użyj formatu: MAJOR.MINOR.PATCH (np. 1.0.4)"
        return 1
    fi
    return 0
}

# Funkcja do porównywania wersji
version_compare() {
    local version1="$1"
    local version2="$2"
    
    # Konwertuj wersje na tablice
    IFS='.' read -ra V1 <<< "$version1"
    IFS='.' read -ra V2 <<< "$version2"
    
    # Porównaj każdą część
    for i in {0..2}; do
        if [[ ${V1[i]} -gt ${V2[i]} ]]; then
            return 1  # version1 > version2
        elif [[ ${V1[i]} -lt ${V2[i]} ]]; then
            return 2  # version1 < version2
        fi
    done
    return 0  # version1 == version2
}

# Funkcja do aktualizacji wersji w main.py
update_main_py() {
    local new_version="$1"
    local file="$PROJECT_ROOT/main.py"
    
    if [[ ! -f "$file" ]]; then
        log_error "Plik main.py nie istnieje"
        return 1
    fi
    
    # Aktualizuj tytuł okna
    sed -i "s/YouTube Downloader v[0-9]\+\.[0-9]\+\.[0-9]\+/YouTube Downloader v$new_version/g" "$file"
    
    log_success "Zaktualizowano main.py"
}

# Funkcja do aktualizacji README.md
update_readme() {
    local new_version="$1"
    local file="$PROJECT_ROOT/README.md"
    
    if [[ ! -f "$file" ]]; then
        log_warning "Plik README.md nie istnieje"
        return 0
    fi
    
    # Aktualizuj wszystkie wystąpienia wersji w README
    sed -i "s/youtube-downloader_[0-9]\+\.[0-9]\+\.[0-9]\+_all\.deb/youtube-downloader_${new_version}_all.deb/g" "$file"
    sed -i "s/tag\/v[0-9]\+\.[0-9]\+\.[0-9]\+/tag\/v$new_version/g" "$file"
    
    log_success "Zaktualizowano README.md"
}

# Funkcja do aktualizacji changelog
update_changelog() {
    local new_version="$1"
    local changelog_file="$PROJECT_ROOT/debian-src/changelog"
    
    if [[ ! -f "$changelog_file" ]]; then
        log_error "Plik changelog nie istnieje"
        return 1
    fi
    
    # Utwórz backup
    cp "$changelog_file" "${changelog_file}.backup"
    
    # Utwórz nowy wpis changelog
    local temp_file=$(mktemp)
    
    cat > "$temp_file" << EOF
youtube-downloader ($new_version) stable; urgency=medium

  * Aktualizacja do wersji $new_version
  * [DODAJ OPIS ZMIAN TUTAJ]

 -- Jerzy Maczewski <jerzy.maczewski@example.com>  $(date -R)

$(cat "$changelog_file")
EOF
    
    mv "$temp_file" "$changelog_file"
    
    log_success "Zaktualizowano changelog (dodaj opis zmian ręcznie)"
    log_info "Plik: $changelog_file"
}

# Funkcja do wyświetlania aktualnej wersji
show_current_version() {
    local current_version=$(get_current_version)
    log_info "Aktualna wersja: $current_version"
    
    # Sprawdź spójność wersji we wszystkich plikach
    log_info "Sprawdzanie spójności wersji..."
    
    if [[ -f "$PROJECT_ROOT/README.md" ]]; then
        local readme_versions=$(grep -o 'youtube-downloader_[0-9]\+\.[0-9]\+\.[0-9]\+_all\.deb' "$PROJECT_ROOT/README.md" | sed 's/youtube-downloader_\(.*\)_all\.deb/\1/' | sort -u)
        if [[ -n "$readme_versions" ]]; then
            echo "Wersje w README.md: $readme_versions"
        fi
    fi
    
    if [[ -f "$PROJECT_ROOT/debian-src/changelog" ]]; then
        local changelog_version=$(head -1 "$PROJECT_ROOT/debian-src/changelog" | sed 's/.*(\([^)]*\)).*/\1/')
        echo "Wersja w changelog: $changelog_version"
    fi
}

# Funkcja do weryfikacji po aktualizacji
verify_version_update() {
    local expected_version="$1"
    local current_version=$(get_current_version)
    
    if [[ "$current_version" == "$expected_version" ]]; then
        log_success "Weryfikacja pomyślna: wersja $expected_version"
    else
        log_error "Błąd weryfikacji: oczekiwano $expected_version, znaleziono $current_version"
        return 1
    fi
}

# Funkcja do automatycznego zwiększania wersji
bump_version() {
    local bump_type="$1"  # major, minor, patch
    local current_version=$(get_current_version)
    
    IFS='.' read -ra VERSION_PARTS <<< "$current_version"
    local major=${VERSION_PARTS[0]}
    local minor=${VERSION_PARTS[1]}
    local patch=${VERSION_PARTS[2]}
    
    case "$bump_type" in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            log_error "Nieprawidłowy typ bumpu: $bump_type"
            log_info "Użyj: major, minor, lub patch"
            return 1
            ;;
    esac
    
    local new_version="$major.$minor.$patch"
    log_info "Zwiększanie wersji $bump_type: $current_version -> $new_version"
    
    update_version "$new_version"
}

# Główna funkcja aktualizacji wersji
update_version() {
    local new_version="$1"
    local current_version=$(get_current_version)
    
    if ! validate_version "$new_version"; then
        return 1
    fi
    
    # Sprawdź czy nowa wersja jest większa od aktualnej
    version_compare "$new_version" "$current_version" || true
    local comparison=$?
    
    if [[ $comparison -eq 0 ]]; then
        log_warning "Wersja $new_version jest taka sama jak aktualna"
    elif [[ $comparison -eq 2 ]]; then
        log_warning "Nowa wersja $new_version jest mniejsza niż aktualna $current_version"
        read -p "Kontynuować? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Anulowano"
            return 0
        fi
    fi
    
    log_info "Aktualizacja wersji: $current_version -> $new_version"
    
    # Utwórz backup znaczników git
    if git rev-parse --git-dir > /dev/null 2>&1; then
        log_info "Repozytorium Git wykryte"
        git tag -l | grep -E "^v?[0-9]+\.[0-9]+\.[0-9]+$" > .version-backup || true
    fi
    
    # Aktualizuj wszystkie pliki
    update_main_py "$new_version"
    update_readme "$new_version"
    update_changelog "$new_version"
    
    # Weryfikuj aktualizację
    verify_version_update "$new_version"
    
    log_success "Wersja została zaktualizowana do $new_version"
    log_info "Następne kroki:"
    log_info "1. Sprawdź i uzupełnij changelog: debian-src/changelog"
    log_info "2. Zcommituj zmiany: git commit -am 'Bump version to $new_version'"
    log_info "3. Utwórz tag: git tag v$new_version"
    log_info "4. Zbuduj pakiet: ./build-deb.sh $new_version"
}

# Funkcja pomocy
show_help() {
    cat << EOF
YouTube Downloader - Version Manager

Użycie:
  $0 show                    - Pokaż aktualną wersję
  $0 set <version>          - Ustaw konkretną wersję (np. 1.0.4)
  $0 bump <type>            - Zwiększ wersję automatycznie
    gdzie <type> to:
      major - zwiększ wersję główną (1.0.0 -> 2.0.0)
      minor - zwiększ wersję drugorzędną (1.0.0 -> 1.1.0)
      patch - zwiększ wersję poprawki (1.0.0 -> 1.0.1)

Przykłady:
  $0 show
  $0 set 1.0.4
  $0 bump patch
  $0 bump minor

Pliki aktualizowane:
$(printf '  - %s\n' "${VERSION_FILES[@]}")
EOF
}

# Główna logika
main() {
    case "${1:-}" in
        "show")
            show_current_version
            ;;
        "set")
            if [[ -z "${2:-}" ]]; then
                log_error "Nie podano wersji"
                show_help
                exit 1
            fi
            update_version "$2"
            ;;
        "bump")
            if [[ -z "${2:-}" ]]; then
                log_error "Nie podano typu bumpu"
                show_help
                exit 1
            fi
            bump_version "$2"
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            log_error "Nieznana komenda: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"