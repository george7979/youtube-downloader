#!/bin/bash

# YouTube Downloader - Version Manager
# Manages version information across the project

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Handle both direct execution and symlink execution
if [[ -L "${BASH_SOURCE[0]}" ]]; then
    # If run via symlink, get the real script location
    REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}")"
    SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
fi
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION_FILE="$PROJECT_DIR/version.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" >&2
}

log_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

# Get current version from version.py
get_version() {
    if [[ ! -f "$VERSION_FILE" ]]; then
        log_error "Plik version.py nie istnieje: $VERSION_FILE"
        exit 1
    fi
    
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
from version import __version__
print(__version__)
"
}

# Show version information
show_version() {
    local version
    version=$(get_version)
    
    echo "YouTube Downloader - Informacje o wersji"
    echo "======================================="
    echo "Aktualna wersja: $version"
    echo "Lokalizacja: $VERSION_FILE"
    echo "Data kompilacji: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Show git info if available
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
        echo "Git branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    fi
}

# Validate version format (semver)
validate_version() {
    local version="$1"
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        log_error "Nieprawidłowy format wersji: $version (oczekiwano X.Y.Z lub X.Y.Z-suffix)"
        return 1
    fi
}

# Set new version
set_version() {
    local new_version="$1"
    
    validate_version "$new_version"
    
    log_info "Ustawianie nowej wersji: $new_version"
    
    # Update version.py
    cat > "$VERSION_FILE" << EOF
"""
YouTube Downloader Version Information
"""

__version__ = "$new_version"
__version_info__ = tuple(map(int, __version__.split('.')[:3]))

# For backwards compatibility
VERSION = __version__
EOF

    log_success "Wersja zaktualizowana do $new_version"
    
    # Show what was changed
    log_info "Zaktualizowany plik: $VERSION_FILE"
}

# Compare versions
compare_version() {
    local version1="$1"
    local version2="$2"
    
    python3 -c "
import sys
from packaging import version

v1 = version.parse('$version1')
v2 = version.parse('$version2')

if v1 < v2:
    print('less')
    sys.exit(1)
elif v1 > v2:
    print('greater')
    sys.exit(2)
else:
    print('equal')
    sys.exit(0)
" 2>/dev/null || {
    # Fallback if packaging is not available
    if [[ "$version1" == "$version2" ]]; then
        echo "equal"
        return 0
    else
        echo "unknown"
        return 3
    fi
}
}

# Main command handling
case "${1:-show}" in
    "show"|"current")
        show_version
        ;;
    "get")
        get_version
        ;;
    "set")
        if [[ $# -lt 2 ]]; then
            log_error "Użycie: $0 set <wersja>"
            exit 1
        fi
        set_version "$2"
        ;;
    "validate")
        if [[ $# -lt 2 ]]; then
            log_error "Użycie: $0 validate <wersja>"
            exit 1
        fi
        if validate_version "$2"; then
            log_success "Wersja $2 jest prawidłowa"
        fi
        ;;
    "compare")
        if [[ $# -lt 3 ]]; then
            log_error "Użycie: $0 compare <wersja1> <wersja2>"
            exit 1
        fi
        result=$(compare_version "$2" "$3")
        echo "$2 is $result than $3"
        ;;
    "bump")
        if [[ $# -lt 2 ]]; then
            log_error "Użycie: $0 bump <patch|minor|major>"
            exit 1
        fi
        current_version=$(get_version)
        case "$2" in
            "patch")
                # 1.2.3 -> 1.2.4
                new_version=$(python3 -c "
version = '$current_version'.split('.')
version[2] = str(int(version[2]) + 1)
print('.'.join(version))")
                ;;
            "minor")
                # 1.2.3 -> 1.3.0
                new_version=$(python3 -c "
version = '$current_version'.split('.')
version[1] = str(int(version[1]) + 1)
version[2] = '0'
print('.'.join(version))")
                ;;
            "major")
                # 1.2.3 -> 1.3.0
                new_version=$(python3 -c "
version = '$current_version'.split('.')
version[0] = str(int(version[0]) + 1)
version[1] = '0'
version[2] = '0'
print('.'.join(version))")
                ;;
            *)
                log_error "Nieprawidłowy typ bump: $2 (dozwolone: patch, minor, major)"
                exit 1
                ;;
        esac
        
        log_info "Zwiększanie wersji $2: $current_version → $new_version"
        set_version "$new_version"
        log_success "Wersja zwiększona z $current_version do $new_version"
        ;;
    "help"|"-h"|"--help")
        echo "YouTube Downloader - Version Manager"
        echo ""
        echo "Użycie: $0 <komenda> [argumenty]"
        echo ""
        echo "Komendy:"
        echo "  show, current    Pokaż aktualne informacje o wersji"
        echo "  get              Pokaż tylko numer wersji"
        echo "  set <wersja>     Ustaw nową wersję (format X.Y.Z)"
        echo "  bump <typ>       Zwiększ wersję (patch|minor|major)"
        echo "  validate <wersja> Sprawdź format wersji"
        echo "  compare <v1> <v2> Porównaj dwie wersje"
        echo "  help             Pokaż tę pomoc"
        echo ""
        echo "Przykłady:"
        echo "  $0 show          # Pokaż szczegóły wersji"
        echo "  $0 get           # Pokaż tylko 1.2.0"
        echo "  $0 set 1.3.0     # Ustaw nową wersję"
        echo "  $0 bump patch    # 1.2.0 → 1.2.1"
        echo "  $0 bump minor    # 1.2.0 → 1.3.0"
        echo "  $0 bump major    # 1.2.0 → 1.3.0"
        ;;
    *)
        log_error "Nieznana komenda: $1"
        log_info "Użyj '$0 help' aby zobaczyć dostępne komendy"
        exit 1
        ;;
esac