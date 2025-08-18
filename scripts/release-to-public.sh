#!/bin/bash
# YouTube Downloader - Release to Public Repository
# Publikuje main branch z private repo do public repo z pełną weryfikacją

set -e

# Konfiguracja
PRIVATE_REMOTE="origin"
PUBLIC_REMOTE="public"
SOURCE_BRANCH="main"
TARGET_BRANCH="main"
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
VERIFY_ONLY=false
SKIP_SECURITY=false
FORCE_PUSH=false
SYNC_TAGS=true
SYNC_RELEASES=true
AUTO_APPROVE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verify|-v)
            VERIFY_ONLY=true
            shift
            ;;
        --skip-security)
            SKIP_SECURITY=true
            log_warning "Pomijanie sprawdzenia bezpieczeństwa (NIEBEZPIECZNE!)"
            shift
            ;;
        --force|-f)
            FORCE_PUSH=true
            shift
            ;;
        --no-tags)
            SYNC_TAGS=false
            shift
            ;;
        --no-releases)
            SYNC_RELEASES=false
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
            echo "Publikuje main branch z private repo do public repo"
            echo ""
            echo "OPTIONS:"
            echo "  --verify, -v       Tylko zweryfikuj - nie wykonuj publikacji"
            echo "  --skip-security    Pomiń sprawdzenie bezpieczeństwa (NIEBEZPIECZNE)"
            echo "  --force, -f        Force push do public repo"
            echo "  --no-tags          Nie synchronizuj tagów"
            echo "  --no-releases      Nie synchronizuj releases"
            echo "  --auto-approve, -y Automatycznie zatwierdź wszystkie pytania"
            echo "  --dry-run, -n      Pokaż co zostanie wykonane"
            echo "  --help, -h         Pokaż tę pomoc"
            echo ""
            echo "Przykłady:"
            echo "  $0 --verify        # Sprawdź tylko czy publikacja jest możliwa"
            echo "  $0 --no-releases   # Tylko kod, bez releases"
            echo "  $0                 # Pełna publikacja"
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
    log_info "🔒 OSTATNIE SPRAWDZENIE BEZPIECZEŃSTWA"
    log_info "======================================"
    
    if [ ! -f "$SECURITY_SCRIPT" ]; then
        log_error "Skrypt bezpieczeństwa nie znaleziony: $SECURITY_SCRIPT"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "DRY RUN: $SECURITY_SCRIPT $SOURCE_BRANCH strict"
        return 0
    fi
    
    # Uruchom w strict mode dla public release
    if "$SECURITY_SCRIPT" "$SOURCE_BRANCH" "true" "public-release"; then
        log_success "Sprawdzenie bezpieczeństwa: PASSED (public-release context)"
        return 0
    else
        log_error "Sprawdzenie bezpieczeństwa: FAILED"
        log_error "KRYTYCZNE: Znaleziono problemy bezpieczeństwa!"
        log_error "Nie można publikować do public repo"
        return 1
    fi
}

check_repositories() {
    log_info "Sprawdzanie konfiguracji repozytoriów..."
    
    # Sprawdź remotes
    if ! git remote get-url "$PRIVATE_REMOTE" >/dev/null 2>&1; then
        log_error "Private remote '$PRIVATE_REMOTE' nie istnieje"
        return 1
    fi
    
    if ! git remote get-url "$PUBLIC_REMOTE" >/dev/null 2>&1; then
        log_error "Public remote '$PUBLIC_REMOTE' nie istnieje"
        return 1
    fi
    
    local private_url=$(git remote get-url "$PRIVATE_REMOTE")
    local public_url=$(git remote get-url "$PUBLIC_REMOTE")
    
    log_info "Private repo: $private_url"
    log_info "Public repo: $public_url"
    
    # Sprawdź czy public repo jest rzeczywiście publiczne
    if echo "$public_url" | grep -q "private"; then
        log_warning "UWAGA: Public repo URL zawiera 'private' - sprawdź konfigurację!"
    fi
    
    # Fetch najnowsze zmiany
    log_info "Pobieranie najnowszych zmian..."
    if [ "$DRY_RUN" = false ]; then
        git fetch "$PRIVATE_REMOTE"
        git fetch "$PUBLIC_REMOTE"
    else
        echo "DRY RUN: git fetch $PRIVATE_REMOTE"
        echo "DRY RUN: git fetch $PUBLIC_REMOTE"
    fi
    
    return 0
}

analyze_differences() {
    log_info "Analiza różnic między repozytoriami..."
    
    # Sprawdź czy public repo ma target branch
    if git ls-remote --heads "$PUBLIC_REMOTE" "$TARGET_BRANCH" | grep -q "$TARGET_BRANCH"; then
        log_info "Public repo ma branch $TARGET_BRANCH"
        
        # Porównaj branches
        local private_commit=$(git rev-parse "$PRIVATE_REMOTE/$SOURCE_BRANCH")
        local public_commit=$(git rev-parse "$PUBLIC_REMOTE/$TARGET_BRANCH")
        
        if [ "$private_commit" = "$public_commit" ]; then
            log_success "Repozytoria są zsynchronizowane"
            return 2
        else
            log_info "Private commit: ${private_commit:0:8}"
            log_info "Public commit:  ${public_commit:0:8}"
            
            # Sprawdź czy private jest ahead
            if git merge-base --is-ancestor "$PUBLIC_REMOTE/$TARGET_BRANCH" "$PRIVATE_REMOTE/$SOURCE_BRANCH"; then
                local ahead_count=$(git rev-list --count "$PUBLIC_REMOTE/$TARGET_BRANCH".."$PRIVATE_REMOTE/$SOURCE_BRANCH")
                log_info "Private repo jest $ahead_count commits przed public"
            else
                log_warning "Repozytoria mają rozbieżną historię!"
                if [ "$FORCE_PUSH" = false ]; then
                    log_error "Użyj --force żeby wymusić synchronizację"
                    return 1
                fi
            fi
        fi
    else
        log_info "Public repo nie ma branch $TARGET_BRANCH - zostanie utworzony"
    fi
    
    return 0
}

preview_publication() {
    log_info "📋 PODGLĄD PUBLIKACJI"
    log_info "===================="
    
    # Pokaż zmiany które zostaną opublikowane
    if git ls-remote --heads "$PUBLIC_REMOTE" "$TARGET_BRANCH" | grep -q "$TARGET_BRANCH"; then
        echo ""
        log_info "Nowe commits do publikacji:"
        git log --oneline "$PUBLIC_REMOTE/$TARGET_BRANCH".."$PRIVATE_REMOTE/$SOURCE_BRANCH" | head -10
        
        echo ""
        log_info "Zmienione pliki:"
        git diff --name-status "$PUBLIC_REMOTE/$TARGET_BRANCH".."$PRIVATE_REMOTE/$SOURCE_BRANCH" | head -20
    else
        echo ""
        log_info "Pierwszy push do public repo - wszystkie pliki będą opublikowane"
        git ls-tree -r --name-only "$PRIVATE_REMOTE/$SOURCE_BRANCH" | head -20
        local total_files=$(git ls-tree -r --name-only "$PRIVATE_REMOTE/$SOURCE_BRANCH" | wc -l)
        log_info "Łącznie plików: $total_files"
    fi
    
    # Sprawdź wrażliwe pliki
    echo ""
    log_info "Sprawdzanie wrażliwych plików..."
    local sensitive_files=$(git ls-tree -r --name-only "$PRIVATE_REMOTE/$SOURCE_BRANCH" | grep -E '\\.(env|key|pem|p12)$|cursorrules|secrets' || true)
    
    if [ -n "$sensitive_files" ]; then
        log_error "ZNALEZIONO WRAŻLIWE PLIKI:"
        echo "$sensitive_files"
        return 1
    else
        log_success "Brak wrażliwych plików"
    fi
    
    # Sprawdź wielkość repo
    echo ""
    log_info "Statystyki publikacji:"
    local total_size=$(git count-objects -v | grep 'size-pack' | awk '{print $2}' || echo "0")
    local total_commits=$(git rev-list --count "$PRIVATE_REMOTE/$SOURCE_BRANCH")
    
    echo "  - Rozmiar repo: ${total_size} KB"
    echo "  - Liczba commits: $total_commits"
    
    return 0
}

sync_tags() {
    if [ "$SYNC_TAGS" = false ]; then
        log_info "Pomijanie synchronizacji tagów (--no-tags)"
        return 0
    fi
    
    log_info "Synchronizacja tagów..."
    
    # Pobierz listę tagów z private repo
    local private_tags=$(git ls-remote --tags "$PRIVATE_REMOTE" | grep -v '\\^{}' | awk '{print $2}' | sed 's|refs/tags/||' || true)
    
    if [ -z "$private_tags" ]; then
        log_info "Brak tagów do synchronizacji"
        return 0
    fi
    
    log_info "Znalezione tagi: $(echo $private_tags | tr '\n' ' ')"
    
    if [ "$DRY_RUN" = false ]; then
        if git push "$PUBLIC_REMOTE" --tags; then
            log_success "Tagi zsynchronizowane"
        else
            log_warning "Część tagów mogła już istnieć"
        fi
    else
        echo "DRY RUN: git push $PUBLIC_REMOTE --tags"
    fi
    
    return 0
}

sync_releases() {
    if [ "$SYNC_RELEASES" = false ]; then
        log_info "Pomijanie synchronizacji releases (--no-releases)"
        return 0
    fi
    
    log_info "Sprawdzanie releases do synchronizacji..."
    
    # Sprawdź czy mamy narzędzie gh
    if ! command -v gh >/dev/null 2>&1; then
        log_warning "GitHub CLI (gh) nie jest dostępne - pomijam synchronizację releases"
        return 0
    fi
    
    # Pobierz repozytoria paths
    local private_url=$(git remote get-url "$PRIVATE_REMOTE")
    local public_url=$(git remote get-url "$PUBLIC_REMOTE")
    
    local private_repo=$(echo "$private_url" | sed 's/.*github.com[:/]\\([^/]*\/[^/]*\\).*/\\1/' | sed 's/\\.git$//')
    local public_repo=$(echo "$public_url" | sed 's/.*github.com[:/]\\([^/]*\/[^/]*\\).*/\\1/' | sed 's/\\.git$//')
    
    log_info "Private repo: $private_repo"
    log_info "Public repo: $public_repo"
    
    if [ "$DRY_RUN" = false ]; then
        # Użyj sync-releases.sh jeśli istnieje
        if [ -f "./scripts/sync-releases.sh" ]; then
            log_info "Używam skryptu sync-releases.sh..."
            ./scripts/sync-releases.sh --from "$private_repo" --to "$public_repo"
        else
            log_info "Skrypt sync-releases.sh nie istnieje - pomijam synchronizację"
        fi
    else
        echo "DRY RUN: sync releases $private_repo -> $public_repo"
    fi
    
    return 0
}

create_filtered_branch() {
    local filtered_branch="public-filtered-$(date +%s)"
    
    log_info "Tworzenie przefiltrowanego branch: $filtered_branch"
    
    # Checkout source branch
    if [ "$DRY_RUN" = false ]; then
        git checkout "$SOURCE_BRANCH"
        git pull "$PRIVATE_REMOTE" "$SOURCE_BRANCH"
    else
        echo "DRY RUN: git checkout $SOURCE_BRANCH"
        echo "DRY RUN: git pull $PRIVATE_REMOTE $SOURCE_BRANCH"
    fi
    
    # Create filtered branch
    if [ "$DRY_RUN" = false ]; then
        git checkout -b "$filtered_branch"
    else
        echo "DRY RUN: git checkout -b $filtered_branch"
    fi
    
    # Remove files based on .gitignore-public
    if [ -f ".gitignore-public" ]; then
        log_info "Stosowanie filtrów z .gitignore-public..."
        
        local files_to_remove=""
        while IFS= read -r pattern; do
            # Skip comments and empty lines
            [[ "$pattern" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${pattern// }" ]] && continue
            
            # Find matching files
            local matching_files=$(git ls-files | grep -E "^$pattern$" || true)
            if [ -n "$matching_files" ]; then
                files_to_remove="$files_to_remove $matching_files"
                log_info "Usuwanie: $matching_files"
            fi
        done < .gitignore-public
        
        if [ -n "$files_to_remove" ] && [ "$DRY_RUN" = false ]; then
            git rm -f $files_to_remove 2>/dev/null || true
            git commit -m "Filter files for public release

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" || true
        elif [ -n "$files_to_remove" ]; then
            echo "DRY RUN: git rm -f $files_to_remove"
            echo "DRY RUN: git commit (filter commit)"
        fi
    else
        log_warning "Plik .gitignore-public nie znaleziony - publikacja bez filtrowania"
    fi
    
    echo "$filtered_branch"
    return 0
}

cleanup_filtered_branch() {
    local branch_to_delete="$1"
    
    if [ -n "$branch_to_delete" ] && [ "$DRY_RUN" = false ]; then
        log_info "Usuwanie tymczasowego branch: $branch_to_delete"
        git checkout "$SOURCE_BRANCH"
        git branch -D "$branch_to_delete" 2>/dev/null || true
    elif [ -n "$branch_to_delete" ]; then
        echo "DRY RUN: cleanup branch $branch_to_delete"
    fi
}

confirm_publication() {
    if [ "$AUTO_APPROVE" = true ]; then
        log_info "Auto-approve włączony - kontynuuję bez pytania"
        return 0
    fi
    
    echo ""
    log_warning "🚨 PUBLIKACJA DO PUBLIC REPOSITORY 🚨"
    log_warning "========================================"
    log_warning "Ta operacja opublikuje kod z private repo do PUBLIC GitHub!"
    log_warning "Kod będzie widoczny dla wszystkich użytkowników internetu!"
    echo ""
    log_info "Sprawdź ponownie:"
    log_info "✓ Brak wrażliwych danych (hasła, klucze, tokeny)"
    log_info "✓ Brak prywatnych informacji biznesowych"
    log_info "✓ Kod jest gotowy do publicznej dystrybucji"
    log_info "✓ Pliki zostały przefiltrowane zgodnie z .gitignore-public"
    echo ""
    
    read -p "CZY JESTEŚ PEWIEN, ŻE CHCESZ OPUBLIKOWAĆ? (type 'YES'): " -r
    if [ "$REPLY" = "YES" ]; then
        return 0
    else
        log_info "Publikacja anulowana przez użytkownika"
        return 1
    fi
}

perform_publication() {
    log_info "🚀 ROZPOCZYNAM PUBLIKACJĘ"
    log_info "========================"
    
    # Create filtered branch for public release
    local filtered_branch
    filtered_branch=$(create_filtered_branch)
    
    if [ $? -ne 0 ]; then
        log_error "Nie udało się utworzyć przefiltrowanego branch"
        return 1
    fi
    
    # Przygotuj push command z filtered branch
    local push_cmd="git push $PUBLIC_REMOTE $filtered_branch:$TARGET_BRANCH"
    if [ "$FORCE_PUSH" = true ]; then
        push_cmd="$push_cmd --force-with-lease"
    fi
    
    # Wykonaj push
    log_info "Publikuję przefiltrowany kod..."
    local push_success=false
    if [ "$DRY_RUN" = false ]; then
        if eval "$push_cmd"; then
            log_success "Kod opublikowany pomyślnie!"
            push_success=true
        else
            log_error "Publikacja kodu nie powiodła się!"
            cleanup_filtered_branch "$filtered_branch"
            return 1
        fi
    else
        echo "DRY RUN: $push_cmd"
        push_success=true
    fi
    
    # Cleanup filtered branch
    cleanup_filtered_branch "$filtered_branch"
    
    if [ "$push_success" = true ]; then
        # Synchronizuj tagi
        sync_tags
        
        # Synchronizuj releases
        sync_releases
    fi
    
    return 0
}

main() {
    log_info "YouTube Downloader - Release to Public Repository"
    echo "=================================================="
    
    # Sprawdź czy jesteśmy w git repo
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Nie jesteś w katalogu git repository"
        exit 1
    fi
    
    # Sprawdź konfigurację repozytoriów
    if ! check_repositories; then
        exit 1
    fi
    
    # Sprawdzenie bezpieczeństwa
    if [ "$SKIP_SECURITY" = false ]; then
        if ! run_security_check; then
            log_error "Publikacja zatrzymana z powodu problemów bezpieczeństwa"
            exit 1
        fi
    else
        log_warning "POMIJAM sprawdzenie bezpieczeństwa!"
    fi
    
    # Analiza różnic
    local diff_result
    analyze_differences
    diff_result=$?
    
    if [ $diff_result -eq 1 ]; then
        exit 1
    elif [ $diff_result -eq 2 ]; then
        log_success "Repozytoria są już zsynchronizowane"
        if [ "$VERIFY_ONLY" = false ]; then
            log_info "Brak zmian do publikacji"
        fi
        exit 0
    fi
    
    # Podgląd publikacji
    if ! preview_publication; then
        log_error "Wykryto problemy - publikacja zatrzymana"
        exit 1
    fi
    
    # Jeśli tylko weryfikacja
    if [ "$VERIFY_ONLY" = true ]; then
        log_success "Weryfikacja zakończona - publikacja jest możliwa"
        exit 0
    fi
    
    # Potwierdź publikację
    if ! confirm_publication; then
        exit 0
    fi
    
    # Wykonaj publikację
    if perform_publication; then
        echo ""
        log_success "=== PUBLIKACJA ZAKOŃCZONA ==="
        
        # Pokaż linki
        local public_url=$(git remote get-url "$PUBLIC_REMOTE")
        if echo "$public_url" | grep -q "github.com"; then
            local repo_path=$(echo "$public_url" | sed 's/.*github.com[:/]\\([^/]*\/[^/]*\\).*/\\1/' | sed 's/\\.git$//')
            log_info "🌐 Public repo: https://github.com/$repo_path"
            log_info "📊 Commits: https://github.com/$repo_path/commits/$TARGET_BRANCH"
            log_info "🏷️  Releases: https://github.com/$repo_path/releases"
        fi
        
        echo ""
        log_info "Następne kroki:"
        log_info "1. Sprawdź public repo na GitHub"
        log_info "2. Zweryfikuj czy wszystkie pliki są poprawne"
        log_info "3. Sprawdź GitHub Actions (jeśli skonfigurowane)"
        log_info "4. Poinformuj użytkowników o nowej wersji"
    else
        log_error "Publikacja nie powiodła się!"
        exit 1
    fi
}

# Wywołaj main function
main "$@"