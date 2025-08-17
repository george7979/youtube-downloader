#!/bin/bash
# YouTube Downloader - Promote to Main Branch
# Przenosi zmiany z develop na main branch z weryfikacją bezpieczeństwa

set -e

# Konfiguracja
SOURCE_BRANCH="develop"
TARGET_BRANCH="main"
REMOTE_NAME="origin"
SECURITY_SCRIPT="./scripts/security-check-main.sh"

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
CHECK_ONLY=false
SQUASH_MERGE=false
SKIP_SECURITY=false
AUTO_APPROVE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only|-c)
            CHECK_ONLY=true
            shift
            ;;
        --squash|-s)
            SQUASH_MERGE=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            log_warning "Pomijanie sprawdzenia bezpieczeństwa (NIEBEZPIECZNE!)"
            shift
            ;;
        --auto-approve|-y)
            AUTO_APPROVE=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Przenosi zmiany z develop na main branch z weryfikacją bezpieczeństwa"
            echo ""
            echo "OPTIONS:"
            echo "  --check-only, -c   Tylko sprawdź - nie wykonuj merge"
            echo "  --squash, -s       Squash commits podczas merge"
            echo "  --skip-security    Pomiń sprawdzenie bezpieczeństwa (NIEBEZPIECZNE)"
            echo "  --auto-approve, -y Automatycznie zatwierdź wszystkie pytania"
            echo "  --dry-run, -n      Pokaż co zostanie wykonane"
            echo "  --help, -h         Pokaż tę pomoc"
            echo ""
            echo "Przykłady:"
            echo "  $0 --check-only    # Sprawdź tylko czy promote jest możliwe"
            echo "  $0 --squash        # Squash commits w jeden"
            echo "  $0                 # Standardowa promocja"
            exit 0
            ;;
        *)
            log_error "Nieznany argument: $1"
            echo "Użyj --help dla pomocy"
            exit 1
            ;;
    esac
done

run_security_check() {
    local branch="$1"
    
    log_info "Uruchamianie sprawdzenia bezpieczeństwa dla branch: $branch"
    
    if [ ! -f "$SECURITY_SCRIPT" ]; then
        log_error "Skrypt bezpieczeństwa nie znaleziony: $SECURITY_SCRIPT"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: $SECURITY_SCRIPT $branch"
        return 0
    fi
    
    if "$SECURITY_SCRIPT" "$branch"; then
        log_success "Sprawdzenie bezpieczeństwa: PASSED"
        return 0
    else
        log_error "Sprawdzenie bezpieczeństwa: FAILED"
        return 1
    fi
}

check_branch_status() {
    log_info "Sprawdzanie statusu branches..."
    
    # Sprawdź czy source branch istnieje
    if ! git show-ref --verify --quiet "refs/heads/$SOURCE_BRANCH"; then
        if git show-ref --verify --quiet "refs/remotes/$REMOTE_NAME/$SOURCE_BRANCH"; then
            log_info "Checkout zdalnego branch $SOURCE_BRANCH"
            if [ "$DRY_RUN" = false ]; then
                git checkout -b "$SOURCE_BRANCH" "$REMOTE_NAME/$SOURCE_BRANCH"
            else
                echo "DRY RUN: git checkout -b $SOURCE_BRANCH $REMOTE_NAME/$SOURCE_BRANCH"
            fi
        else
            log_error "Branch $SOURCE_BRANCH nie istnieje lokalnie ani na remote"
            return 1
        fi
    fi
    
    # Sprawdź czy target branch istnieje
    if ! git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH"; then
        log_error "Branch $TARGET_BRANCH nie istnieje lokalnie"
        return 1
    fi
    
    # Fetch najnowsze zmiany
    log_info "Pobieranie najnowszych zmian..."
    if [ "$DRY_RUN" = false ]; then
        git fetch "$REMOTE_NAME"
    else
        echo "DRY RUN: git fetch $REMOTE_NAME"
    fi
    
    # Sprawdź różnice między branches
    if git merge-base --is-ancestor "$TARGET_BRANCH" "$SOURCE_BRANCH"; then
        local ahead_count=$(git rev-list --count "$TARGET_BRANCH".."$SOURCE_BRANCH")
        log_info "Branch $SOURCE_BRANCH jest $ahead_count commits przed $TARGET_BRANCH"
        
        if [ "$ahead_count" -eq 0 ]; then
            log_warning "Brak zmian do przeniesienia - branches są identyczne"
            return 2
        fi
    else
        log_warning "Branches $SOURCE_BRANCH i $TARGET_BRANCH mają rozbieżną historię"
        log_info "Sprawdź czy potrzebujesz rebase"
    fi
    
    return 0
}

preview_changes() {
    log_info "Podgląd zmian które zostaną przeniesione:"
    echo "========================================"
    
    # Pokaż commits
    echo ""
    log_info "Nowe commits:"
    git log --oneline "$TARGET_BRANCH".."$SOURCE_BRANCH" | head -10
    
    # Pokaż zmienione pliki
    echo ""
    log_info "Zmienione pliki:"
    git diff --name-status "$TARGET_BRANCH".."$SOURCE_BRANCH" | head -20
    
    # Sprawdź czy są duże pliki
    echo ""
    log_info "Sprawdzanie wielkości plików..."
    local large_files=$(git diff --name-only "$TARGET_BRANCH".."$SOURCE_BRANCH" | xargs -I {} sh -c 'test -f "{}" && ls -la "{}" | awk "\$5 > 1048576 {print \$9, \$5}"' | head -5)
    
    if [ -n "$large_files" ]; then
        log_warning "Znaleziono duże pliki (>1MB):"
        echo "$large_files"
    else
        log_success "Brak dużych plików"
    fi
    
    echo ""
}

confirm_promotion() {
    if [ "$AUTO_APPROVE" = true ]; then
        log_info "Auto-approve włączony - kontynuuję bez pytania"
        return 0
    fi
    
    echo ""
    log_warning "UWAGA: Ta operacja przeniesie zmiany z $SOURCE_BRANCH na $TARGET_BRANCH"
    log_warning "Upewnij się, że sprawdziłeś wszystkie zmiany powyżej!"
    echo ""
    
    read -p "Czy chcesz kontynuować promocję? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        log_info "Promocja anulowana przez użytkownika"
        return 1
    fi
}

perform_promotion() {
    log_info "Rozpoczynam promocję $SOURCE_BRANCH → $TARGET_BRANCH"
    
    # Checkout target branch
    if [ "$DRY_RUN" = false ]; then
        git checkout "$TARGET_BRANCH"
    else
        echo "DRY RUN: git checkout $TARGET_BRANCH"
    fi
    
    # Sprawdź czy target jest up-to-date z remote
    if git rev-parse --verify "$REMOTE_NAME/$TARGET_BRANCH" >/dev/null 2>&1; then
        local behind_count=$(git rev-list --count HEAD.."$REMOTE_NAME/$TARGET_BRANCH" 2>/dev/null || echo "0")
        if [ "$behind_count" -gt 0 ]; then
            log_warning "Branch $TARGET_BRANCH jest $behind_count commits za remote"
            log_info "Aktualizuję z remote..."
            if [ "$DRY_RUN" = false ]; then
                git pull "$REMOTE_NAME" "$TARGET_BRANCH"
            else
                echo "DRY RUN: git pull $REMOTE_NAME $TARGET_BRANCH"
            fi
        fi
    fi
    
    # Wykonaj merge
    local merge_cmd="git merge"
    if [ "$SQUASH_MERGE" = true ]; then
        merge_cmd="$merge_cmd --squash"
    fi
    merge_cmd="$merge_cmd $SOURCE_BRANCH"
    
    log_info "Wykonuję merge..."
    if [ "$DRY_RUN" = false ]; then
        if eval "$merge_cmd"; then
            if [ "$SQUASH_MERGE" = true ]; then
                log_info "Tworzę squash commit..."
                git commit -m "Promote $SOURCE_BRANCH to $TARGET_BRANCH

$(git log --oneline "$TARGET_BRANCH"^.."$SOURCE_BRANCH" | head -10)

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            fi
            log_success "Merge zakończony pomyślnie!"
        else
            log_error "Merge nie powiódł się!"
            log_info "Sprawdź konflikty i rozwiąż je ręcznie"
            return 1
        fi
    else
        echo "DRY RUN: $merge_cmd"
        if [ "$SQUASH_MERGE" = true ]; then
            echo "DRY RUN: git commit (squash message)"
        fi
    fi
    
    # Push do remote
    log_info "Pushowanie zmian do remote..."
    if [ "$DRY_RUN" = false ]; then
        git push "$REMOTE_NAME" "$TARGET_BRANCH"
    else
        echo "DRY RUN: git push $REMOTE_NAME $TARGET_BRANCH"
    fi
    
    return 0
}

main() {
    log_info "YouTube Downloader - Promote to Main Branch"
    echo "============================================="
    
    # Sprawdź czy jesteśmy w git repo
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Nie jesteś w katalogu git repository"
        exit 1
    fi
    
    # Sprawdź czy remote istnieje
    if ! git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
        log_error "Remote '$REMOTE_NAME' nie istnieje"
        exit 1
    fi
    
    # Informacje o operacji
    log_info "Source branch: $SOURCE_BRANCH"
    log_info "Target branch: $TARGET_BRANCH"
    log_info "Remote: $REMOTE_NAME"
    
    # Sprawdź status branches
    local status_result
    check_branch_status
    status_result=$?
    
    if [ $status_result -eq 1 ]; then
        exit 1
    elif [ $status_result -eq 2 ]; then
        log_success "Brak zmian do przeniesienia"
        exit 0
    fi
    
    # Sprawdzenie bezpieczeństwa
    if [ "$SKIP_SECURITY" = false ]; then
        if ! run_security_check "$SOURCE_BRANCH"; then
            log_error "Promocja zatrzymana z powodu problemów bezpieczeństwa"
            exit 1
        fi
    else
        log_warning "POMIJAM sprawdzenie bezpieczeństwa!"
    fi
    
    # Pokaż podgląd zmian
    preview_changes
    
    # Jeśli tylko sprawdzenie
    if [ "$CHECK_ONLY" = true ]; then
        log_success "Sprawdzenie zakończone - promocja jest możliwa"
        exit 0
    fi
    
    # Potwierdź promocję
    if ! confirm_promotion; then
        exit 0
    fi
    
    # Wykonaj promocję
    if perform_promotion; then
        echo ""
        log_success "=== PROMOCJA ZAKOŃCZONA ==="
        log_info "Branch: $SOURCE_BRANCH → $TARGET_BRANCH"
        log_info "Commit: $(git log --oneline -1)"
        
        # Pokaż link do GitHub
        local remote_url=$(git remote get-url "$REMOTE_NAME")
        if echo "$remote_url" | grep -q "github.com"; then
            local repo_path=$(echo "$remote_url" | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/\.git$//')
            log_info "GitHub: https://github.com/$repo_path/tree/$TARGET_BRANCH"
        fi
        
        echo ""
        log_info "Następne kroki:"
        log_info "1. Sprawdź GitHub Actions (jeśli skonfigurowane)"
        log_info "2. Utwórz release jeśli gotowy"
        log_info "3. Użyj ./scripts/release-to-public.sh dla publikacji"
    else
        log_error "Promocja nie powiodła się!"
        exit 1
    fi
}

# Wywołaj main function
main "$@"