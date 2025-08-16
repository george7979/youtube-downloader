#!/bin/bash
# Demo: Safe Merge Process develop → main
# Pokazuje jak będzie działał bezpieczny merge bez faktycznego wykonania

set -e

echo "🎬 DEMO: Bezpieczny proces merge develop → main"
echo "=============================================="
echo ""

# Current status
echo "📍 AKTUALNY STAN:"
echo "   develop branch: $(git rev-parse --short develop) - Development version"
echo "   main branch:    $(git rev-parse --short main) - Requires cleanup"
echo ""

# Step 1: Security Check
echo "🔍 KROK 1: Security Check"
echo "-------------------------"
echo "Sprawdzenie czy develop jest bezpieczny dla main..."
echo ""

./scripts/security-check-main.sh develop && SAFE=true || SAFE=false

if [ "$SAFE" = "false" ]; then
    echo ""
    echo "❌ BLOK: develop zawiera wrażliwe pliki"
    echo ""
    echo "📋 Pliki które MUSZĄ być odfiltrowane:"
    echo "   - cursorrules (konfiguracja IDE - wrażliwa)"
    echo "   - youtube-downloader_1.1.0_all.deb (development build)"
    echo "   - Potencjalnie: backup/, private scripts"
    echo ""
fi

# Step 2: Show what would be merged
echo "🎯 KROK 2: Selective Merge Strategy"
echo "-----------------------------------"
echo "Pliki które POWINNY iść na main (src/, docs/, configs):"
echo ""

# Safe files for main
git ls-tree -r --name-only develop | grep -E "^(src/|docs/|\.github/|README\.md|requirements\.txt|main\.py|tests/)" | head -10
echo "   ... (tylko bezpieczne pliki)"
echo ""

echo "Pliki które NIE POWINNY iść na main:"
git ls-tree -r --name-only develop | grep -E "(cursorrules|backup/|private)" | head -5 || echo "   (żadne nie znalezione w tym demo)"
echo ""

# Step 3: Version handling
echo "🏷️ KROK 3: Version Management"
echo "-----------------------------"
DEVELOP_VERSION=$(git show develop:version.py | grep __version__ | cut -d'"' -f2)
echo "   develop version.py: $DEVELOP_VERSION"
echo "   main powinno mieć: 1.0.3 (stable) lub nowy stable release"
echo ""

# Step 4: .deb handling
echo "📦 KROK 4: .deb Files Strategy"
echo "------------------------------"
echo "Pliki .deb na develop:"
git ls-tree -r --name-only develop | grep '\.deb$' || echo "   (brak)"
echo ""
echo "Strategia dla main:"
echo "   ✅ DOZWOLONE: youtube-downloader_1.0.3_all.deb (stable)"
echo "   ❌ BLOKOWANE: youtube-downloader_1.1.0_all.deb (development)"
echo ""

# Step 5: Proposed merge process
echo "🚀 KROK 5: Proponowany proces merge"
echo "-----------------------------------"
echo ""
echo "1. git checkout main"
echo "2. git checkout -b release/v1.0.4  # Nowy stable release"
echo "3. # Selective checkout safe files:"
echo "   git checkout develop -- src/"
echo "   git checkout develop -- docs/"
echo "   git checkout develop -- .github/"
echo "   git checkout develop -- README.md"
echo "   git checkout develop -- requirements.txt"
echo "   git checkout develop -- tests/"
echo ""
echo "4. # Fix version for stable release:"
echo "   echo '__version__ = \"1.0.4\"' > version.py"
echo ""
echo "5. # Add only stable .deb (if needed):"
echo "   # git add -f youtube-downloader_1.0.4_all.deb"
echo ""
echo "6. # Final security check:"
echo "   ./scripts/security-check-main.sh HEAD"
echo ""
echo "7. # Commit and merge:"
echo "   git commit -m 'release: v1.0.4 - Stable release'"
echo "   git checkout main"
echo "   git merge --no-ff release/v1.0.4"
echo "   git tag v1.0.4"
echo ""

# Summary
echo "📊 PODSUMOWANIE STRATEGII"
echo "========================"
echo ""
echo "✅ MAIN BRANCH otrzyma:"
echo "   - Czyste pliki źródłowe (src/)"
echo "   - Dokumentację (docs/, README.md)"
echo "   - CI/CD workflows (.github/)"
echo "   - Testy (tests/)"
echo "   - Stabilną wersję (1.0.4)"
echo "   - Tylko stable .deb builds"
echo ""
echo "❌ MAIN BRANCH NIE otrzyma:"
echo "   - cursorrules (wrażliwe)"
echo "   - backup/ directories"
echo "   - development .deb builds"
echo "   - prywatne skrypty"
echo "   - pliki konfiguracyjne IDE"
echo ""
echo "🔒 Bezpieczeństwo: Zautomatyzowane skrypty blokują wrażliwe pliki"
echo "⚡ Wydajność: Trunk-based development z bezpiecznym release process"
echo "🧪 Testowanie: Pełna walidacja przed każdym merge"
echo ""
echo "✨ Rezultat: Clean, professional main branch ready for public use!"