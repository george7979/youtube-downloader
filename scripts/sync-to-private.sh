#!/bin/bash
# YouTube Downloader - Sync to Private Repository
# Synchronizuje zmiany lokalne z private/develop branch

set -e

# Konfiguracja
REMOTE_NAME="origin"
BRANCH="develop"
BACKUP_PREFIX="backup-$(date +%Y%m%d-%H%M%S)"

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
FORCE_PUSH=false
CREATE_BACKUP=true
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force|-f)
            FORCE_PUSH=true
            shift
            ;;
        --no-backup)
            CREATE_BACKUP=false
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Synchronizuje lokalne zmiany z private/develop branch"
            echo ""
            echo "OPTIONS:"
            echo "  --force, -f      Force push (nadpisuje remote conflicts)"
            echo "  --no-backup      Nie tworzy backup branch"
            echo "  --dry-run, -n    Pokaż co zostanie wykonane bez zmian"
            echo "  --verbose, -v    Więcej szczegółów"
            echo "  --help, -h       Pokaż tę pomoc"
            echo ""
            echo "Przykłady:"
            echo "  $0                 # Standardowy sync"
            echo "  $0 --force         # Force push"
            echo "  $0 --dry-run       # Sprawdź co zostanie zrobione"
            exit 0
            ;;
        *)
            log_error "Nieznany argument: $1"
            echo "Użyj --help dla pomocy"
            exit 1
            ;;
    esac
done

main() {
    log_info "YouTube Downloader - Sync to Private Repository"
    echo "=================================================="
    
    # Sprawdź czy jesteśmy w git repo
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Nie jesteś w katalogu git repository"
        exit 1
    fi
    
    # Sprawdź czy remote istnieje
    if ! git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
        log_error "Remote '$REMOTE_NAME' nie istnieje"
        log_info "Dostępne remotes: $(git remote | tr '\n' ' ')"
        exit 1
    fi
    
    # Informacje o stanie
    CURRENT_BRANCH=$(git branch --show-current)
    REMOTE_URL=$(git remote get-url "$REMOTE_NAME")
    
    log_info "Current branch: $CURRENT_BRANCH"
    log_info "Remote: $REMOTE_NAME ($REMOTE_URL)"
    log_info "Target branch: $BRANCH"
    
    if [ "$VERBOSE" = true ]; then
        echo ""
        log_info "Git status:"
        git status --short
        echo ""
    fi
    
    # Sprawdź czy są uncommitted changes
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_warning "Masz niezcommitowane zmiany!"
        git status --short
        echo ""
        read -p "Czy chcesz kontynuować? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operacja anulowana"
            exit 0
        fi
    fi
    
    # Fetch latest changes
    log_info "Pobieranie najnowszych zmian z remote..."
    if [ "$DRY_RUN" = false ]; then
        git fetch "$REMOTE_NAME"
    else
        echo "DRY RUN: git fetch $REMOTE_NAME"
    fi
    
    # Sprawdź czy target branch istnieje na remote
    if git ls-remote --heads "$REMOTE_NAME" "$BRANCH" | grep -q "$BRANCH"; then
        log_success "Remote branch $REMOTE_NAME/$BRANCH istnieje"
        
        # Sprawdź różnice
        if git rev-parse --verify "$REMOTE_NAME/$BRANCH" >/dev/null 2>&1; then
            BEHIND=$(git rev-list --count HEAD.."$REMOTE_NAME/$BRANCH" 2>/dev/null || echo "0")
            AHEAD=$(git rev-list --count "$REMOTE_NAME/$BRANCH"..HEAD 2>/dev/null || echo "0")
            
            log_info "Status synchronizacji:"
            echo "  - Commits ahead: $AHEAD"
            echo "  - Commits behind: $BEHIND"
            
            if [ "$BEHIND" -gt 0 ] && [ "$FORCE_PUSH" = false ]; then
                log_warning "Twój branch jest $BEHIND commits za remote"
                log_warning "Użyj --force żeby wymusić push lub najpierw zrób pull"
                exit 1
            fi
        fi
    else
        log_info "Remote branch $REMOTE_NAME/$BRANCH nie istnieje - zostanie utworzony"
    fi
    
    # Utwórz backup branch jeśli wymagane
    if [ "$CREATE_BACKUP" = true ] && [ "$DRY_RUN" = false ]; then
        BACKUP_BRANCH="$BACKUP_PREFIX-$CURRENT_BRANCH"
        log_info "Tworzenie backup branch: $BACKUP_BRANCH"
        git branch "$BACKUP_BRANCH" HEAD
        log_success "Backup utworzony: $BACKUP_BRANCH"
    fi
    
    # Przygotuj push command
    PUSH_CMD="git push $REMOTE_NAME HEAD:$BRANCH"
    if [ "$FORCE_PUSH" = true ]; then
        PUSH_CMD="$PUSH_CMD --force-with-lease"
    fi
    
    # Wykonaj push
    log_info "Synchronizuję z $REMOTE_NAME/$BRANCH..."
    if [ "$DRY_RUN" = false ]; then
        if eval "$PUSH_CMD"; then
            log_success "Synchronizacja zakończona pomyślnie!"
            
            # Pokaż link do GitHub
            if echo "$REMOTE_URL" | grep -q "github.com"; then
                REPO_PATH=$(echo "$REMOTE_URL" | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/\.git$//')
                log_info "GitHub: https://github.com/$REPO_PATH/tree/$BRANCH"
            fi
        else
            log_error "Push nie powiódł się!"
            if [ "$CREATE_BACKUP" = true ]; then
                log_info "Backup dostępny w branch: $BACKUP_BRANCH"
            fi
            exit 1
        fi
    else
        echo "DRY RUN: $PUSH_CMD"
        log_info "DRY RUN: Operacja nie została wykonana"
    fi
    
    # Podsumowanie
    echo ""
    log_success "=== SYNCHRONIZACJA ZAKOŃCZONA ==="
    log_info "Branch: $CURRENT_BRANCH → $REMOTE_NAME/$BRANCH"
    if [ "$CREATE_BACKUP" = true ] && [ "$DRY_RUN" = false ]; then
        log_info "Backup: $BACKUP_BRANCH"
    fi
    log_info "Status: $(git log --oneline -1)"
}

# Wywołaj main function
main "$@"