#!/bin/bash
# YouTube Downloader - Sync Releases Between Repositories
# Synchronizuje releases i assets między private i public repo

set -e

# Konfiguracja domyślna
DEFAULT_PRIVATE_REPO=""
DEFAULT_PUBLIC_REPO=""

# Kolory dla output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Funkcje pomocnicze
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Parsowanie argumentów
FROM_REPO=""
TO_REPO=""
SPECIFIC_TAG=""
DRY_RUN=false
WATCH_MODE=false
FORCE_SYNC=false
INCLUDE_PRERELEASE=true
SYNC_ASSETS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --from)
            FROM_REPO="$2"
            shift 2
            ;;
        --to)
            TO_REPO="$2"
            shift 2
            ;;
        --tag)
            SPECIFIC_TAG="$2"
            shift 2
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --watch|-w)
            WATCH_MODE=true
            shift
            ;;
        --force|-f)
            FORCE_SYNC=true
            shift
            ;;
        --no-prerelease)
            INCLUDE_PRERELEASE=false
            shift
            ;;
        --no-assets)
            SYNC_ASSETS=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 --from SOURCE_REPO --to TARGET_REPO [OPTIONS]"
            echo ""
            echo "Synchronizuje releases między repozytoriami GitHub"
            echo ""
            echo "REQUIRED:"
            echo "  --from REPO        Source repository (format: owner/repo)"
            echo "  --to REPO          Target repository (format: owner/repo)"
            echo ""
            echo "OPTIONS:"
            echo "  --tag TAG          Synchronizuj tylko określony tag"
            echo "  --dry-run, -n      Pokaż co zostanie wykonane"
            echo "  --watch, -w        Tryb ciągłego monitorowania"
            echo "  --force, -f        Nadpisz istniejące releases"
            echo "  --no-prerelease    Pomiń pre-releases"
            echo "  --no-assets        Nie synchronizuj assets"
            echo "  --help, -h         Pokaż tę pomoc"
            echo ""
            echo "Przykłady:"
            echo "  $0 --from owner/private-repo --to owner/public-repo"
            echo "  $0 --from owner/repo --to owner/repo --tag v1.0.0"
            echo "  $0 --from owner/repo --to owner/repo --watch"
            exit 0
            ;;
        *)
            log_error "Nieznany argument: $1"
            echo "Użyj --help dla pomocy"
            exit 1
            ;;
    esac
done

# Sprawdź wymagane argumenty
if [ -z "$FROM_REPO" ] || [ -z "$TO_REPO" ]; then
    log_error "Wymagane argumenty --from i --to"
    echo "Użyj --help dla pomocy"
    exit 1
fi

check_gh_cli() {
    if ! command -v gh >/dev/null 2>&1; then
        log_error "GitHub CLI (gh) nie jest dostępne"
        log_info "Zainstaluj: https://cli.github.com/"
        return 1
    fi
    
    # Sprawdź autoryzację
    if ! gh auth status >/dev/null 2>&1; then
        log_error "GitHub CLI nie jest autoryzowane"
        log_info "Uruchom: gh auth login"
        return 1
    fi
    
    return 0
}

check_repo_access() {
    local repo="$1"
    local repo_type="$2"
    
    log_info "Sprawdzanie dostępu do $repo_type repo: $repo"
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: gh repo view $repo"
        return 0
    fi
    
    if gh repo view "$repo" >/dev/null 2>&1; then
        log_success "Dostęp do $repo: OK"
        return 0
    else
        log_error "Brak dostępu do repo: $repo"
        log_info "Sprawdź czy repo istnieje i masz uprawnienia"
        return 1
    fi
}

get_releases() {
    local repo="$1"
    local include_prerelease="$2"
    
    log_info "Pobieranie listy releases z $repo..."
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: gh release list --repo $repo"
        echo "v1.0.3	Latest	v1.0.3	2025-08-17T15:47:17Z"
        echo "v1.0.2	Pre-release	v1.0.2	2025-08-17T15:47:29Z"
        return 0
    fi
    
    local cmd="gh release list --repo $repo --limit 50"
    
    if [ "$include_prerelease" = false ]; then
        cmd="$cmd | grep -v 'Pre-release' || true"
    fi
    
    eval "$cmd"
}

compare_releases() {
    local from_repo="$1"
    local to_repo="$2"
    
    log_info "Porównywanie releases między repozytoriami..."
    
    # Pobierz releases z obu repos
    local from_releases=$(get_releases "$from_repo" "$INCLUDE_PRERELEASE")
    local to_releases=$(get_releases "$to_repo" "$INCLUDE_PRERELEASE")
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: Porównanie releases"
        echo "Missing in target: v1.0.3, v1.0.2"
        return 0
    fi
    
    # Znajdź różnice (releases w source ale nie w target)
    local from_tags=$(echo "$from_releases" | awk '{print $3}' | sort)
    local to_tags=$(echo "$to_releases" | awk '{print $3}' | sort)
    
    local missing_releases=$(comm -23 <(echo "$from_tags") <(echo "$to_tags"))
    
    if [ -n "$missing_releases" ]; then
        log_info "Releases do synchronizacji:"
        echo "$missing_releases" | while read -r tag; do
            echo "  - $tag"
        done
        echo "$missing_releases"
    else
        log_success "Wszystkie releases są zsynchronizowane"
        echo ""
    fi
}

download_release_assets() {
    local repo="$1"
    local tag="$2"
    local download_dir="$3"
    
    log_info "Pobieranie assets dla $tag z $repo..."
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: gh release download $tag --repo $repo --dir $download_dir"
        return 0
    fi
    
    # Utwórz katalog jeśli nie istnieje
    mkdir -p "$download_dir"
    
    # Pobierz assets
    if gh release download "$tag" --repo "$repo" --dir "$download_dir" 2>/dev/null; then
        local asset_count=$(ls -1 "$download_dir" 2>/dev/null | wc -l)
        log_success "Pobrano $asset_count assets"
        return 0
    else
        log_info "Brak assets dla release $tag"
        return 0
    fi
}

sync_single_release() {
    local from_repo="$1"
    local to_repo="$2"
    local tag="$3"
    
    log_info "🔄 Synchronizuję release: $tag"
    log_info "   From: $from_repo"
    log_info "   To:   $to_repo"
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: Sync release $tag"
        return 0
    fi
    
    # Sprawdź czy release już istnieje w target repo
    if gh release view "$tag" --repo "$to_repo" >/dev/null 2>&1; then
        if [ "$FORCE_SYNC" = false ]; then
            log_warning "Release $tag już istnieje w $to_repo (użyj --force)"
            return 0
        else
            log_info "Usuwam istniejący release $tag..."
            gh release delete "$tag" --repo "$to_repo" --yes >/dev/null 2>&1 || true
        fi
    fi
    
    # Pobierz informacje o release z source repo
    local release_info=$(gh release view "$tag" --repo "$from_repo" --json name,body,isDraft,isPrerelease,tagName)
    local release_name=$(echo "$release_info" | jq -r '.name')
    local release_body=$(echo "$release_info" | jq -r '.body')
    local is_draft=$(echo "$release_info" | jq -r '.isDraft')
    local is_prerelease=$(echo "$release_info" | jq -r '.isPrerelease')
    
    # Przygotuj opcje dla gh release create
    local create_opts="--title \"$release_name\""
    
    if [ "$is_draft" = "true" ]; then
        create_opts="$create_opts --draft"
    fi
    
    if [ "$is_prerelease" = "true" ]; then
        create_opts="$create_opts --prerelease"
    fi
    
    # Utwórz katalog tymczasowy dla assets
    local temp_dir="/tmp/gh-sync-$tag-$$"
    
    # Pobierz assets jeśli wymagane
    if [ "$SYNC_ASSETS" = true ]; then
        download_release_assets "$from_repo" "$tag" "$temp_dir"
    fi
    
    # Utwórz release w target repo
    log_info "Tworzę release $tag w $to_repo..."
    
    # Zapisz body do pliku tymczasowego (obsługa multiline)
    local body_file="/tmp/release-body-$tag-$$"
    echo "$release_body" > "$body_file"
    
    if gh release create "$tag" --repo "$to_repo" $create_opts --notes-file "$body_file"; then
        log_success "Release $tag utworzony"
        
        # Upload assets jeśli istnieją
        if [ "$SYNC_ASSETS" = true ] && [ -d "$temp_dir" ] && [ "$(ls -A "$temp_dir" 2>/dev/null)" ]; then
            log_info "Uploading assets..."
            if gh release upload "$tag" "$temp_dir"/* --repo "$to_repo"; then
                log_success "Assets uploaded"
            else
                log_warning "Błąd podczas upload assets"
            fi
        fi
    else
        log_error "Błąd podczas tworzenia release $tag"
        rm -f "$body_file"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Cleanup
    rm -f "$body_file"
    rm -rf "$temp_dir"
    
    return 0
}

sync_all_releases() {
    local from_repo="$1"
    local to_repo="$2"
    
    log_info "🚀 SYNCHRONIZACJA WSZYSTKICH RELEASES"
    log_info "===================================="
    
    # Pobierz listę releases do synchronizacji
    local missing_releases=$(compare_releases "$from_repo" "$to_repo")
    
    if [ -z "$missing_releases" ]; then
        log_success "Brak releases do synchronizacji"
        return 0
    fi
    
    local sync_count=0
    local error_count=0
    
    # Synchronizuj każdy release
    echo "$missing_releases" | while read -r tag; do
        if [ -n "$tag" ]; then
            if sync_single_release "$from_repo" "$to_repo" "$tag"; then
                ((sync_count++))
            else
                ((error_count++))
            fi
            echo ""
        fi
    done
    
    # Podsumowanie
    log_success "Synchronizacja zakończona"
    log_info "Zsynchronizowane: $sync_count"
    if [ $error_count -gt 0 ]; then
        log_warning "Błędy: $error_count"
    fi
}

watch_releases() {
    local from_repo="$1"
    local to_repo="$2"
    
    log_info "👁️  TRYB MONITOROWANIA"
    log_info "====================="
    log_info "Monitoruję releases w $from_repo..."
    log_info "Automatyczna synchronizacja do $to_repo"
    log_info "Naciśnij Ctrl+C aby zatrzymać"
    echo ""
    
    local last_check=""
    
    while true; do
        local current_releases=$(get_releases "$from_repo" "$INCLUDE_PRERELEASE" | head -5)
        
        if [ "$current_releases" != "$last_check" ]; then
            log_info "Wykryto zmiany w releases - synchronizuję..."
            sync_all_releases "$from_repo" "$to_repo"
            last_check="$current_releases"
        else
            echo -n "."
        fi
        
        sleep 30
    done
}

main() {
    log_info "YouTube Downloader - Sync Releases"
    echo "==================================="
    
    log_info "Source repo: $FROM_REPO"
    log_info "Target repo: $TO_REPO"
    
    if [ -n "$SPECIFIC_TAG" ]; then
        log_info "Specific tag: $SPECIFIC_TAG"
    fi
    
    echo ""
    
    # Sprawdź GitHub CLI
    if ! check_gh_cli; then
        exit 1
    fi
    
    # Sprawdź dostęp do repozytoriów
    if ! check_repo_access "$FROM_REPO" "source"; then
        exit 1
    fi
    
    if ! check_repo_access "$TO_REPO" "target"; then
        exit 1
    fi
    
    echo ""
    
    # Wykonaj odpowiednią operację
    if [ -n "$SPECIFIC_TAG" ]; then
        # Synchronizuj konkretny tag
        sync_single_release "$FROM_REPO" "$TO_REPO" "$SPECIFIC_TAG"
    elif [ "$WATCH_MODE" = true ]; then
        # Tryb monitorowania
        watch_releases "$FROM_REPO" "$TO_REPO"
    else
        # Synchronizuj wszystkie releases
        sync_all_releases "$FROM_REPO" "$TO_REPO"
    fi
    
    log_success "Operacja zakończona"
}

# Obsługa Ctrl+C dla watch mode
trap 'log_info "Zatrzymywanie monitorowania..."; exit 0' INT

# Wywołaj main function
main "$@"