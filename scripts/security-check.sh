#!/bin/bash
set -e

echo "🔍 Security check: scanning for obvious secrets and private files"

EXIT_CODE=0

# 1) Skan pod common secrets (bez .git)
if grep -R -I -n -E "(password|secret|api_key|token|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH)" . --exclude-dir=.git --exclude-dir=build --exclude-dir=__pycache__ >/tmp/security-grep.log 2>/dev/null; then
  echo "⚠️  Potencjalne sekrety znalezione:"
  head -n 10 /tmp/security-grep.log
  EXIT_CODE=1
else
  echo "✅ Brak oczywistych sekretów (w szybkim skanie)"
fi

# 2) Zakazane pliki w public-src
if find public-src -name "cursorrules" -o -name ".cursorrules" | grep -q .; then
  echo "❌ Zakazane pliki (cursorrules) znalezione w public-src/"
  find public-src -name "cursorrules" -o -name ".cursorrules"
  EXIT_CODE=1
else
  echo "✅ Brak zakazanych plików w public-src/"
fi

exit $EXIT_CODE
#!/bin/bash

echo "🔍 SECURITY CHECK - Dual Repository"
echo "===================================="

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Zmienne
ERRORS=0
WARNINGS=0
PUBLIC_DIR="public-src"

if [ ! -d "$PUBLIC_DIR" ]; then
    echo -e "${RED}❌ Directory $PUBLIC_DIR not found${NC}"
    exit 1
fi

echo "📁 Scanning directory: $PUBLIC_DIR"
echo ""

# 1. Sprawdź sekrety
echo "🔐 1. CHECKING FOR SECRETS..."
SECRET_PATTERNS=(
    "API_KEY"
    "SECRET"
    "PASSWORD" 
    "TOKEN"
    "PRIVATE_KEY"
    "CLIENT_SECRET"
    "AUTH_KEY"
    "DATABASE_URL"
    "MONGO_URI"
    "redis://"
    "postgres://"
    "mysql://"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -r -i "$pattern" "$PUBLIC_DIR/" 2>/dev/null | grep -v ".git" | grep -q .; then
        echo -e "${RED}❌ POTENTIAL SECRET FOUND: $pattern${NC}"
        grep -r -i "$pattern" "$PUBLIC_DIR/" 2>/dev/null | grep -v ".git" | head -3
        ((ERRORS++))
    fi
done

# 2. Sprawdź dev comments
echo ""
echo "💬 2. CHECKING FOR DEV COMMENTS..."
DEV_PATTERNS=(
    "TODO-DEV"
    "FIXME-DEV"
    "XXX-DEV"
    "HACK-DEV"
    "DEBUG-DEV"
    "REMOVE-BEFORE-RELEASE"
)

for pattern in "${DEV_PATTERNS[@]}"; do
    if grep -r "$pattern" "$PUBLIC_DIR/" 2>/dev/null | grep -q .; then
        echo -e "${YELLOW}⚠️  DEV COMMENT FOUND: $pattern${NC}"
        grep -r "$pattern" "$PUBLIC_DIR/" 2>/dev/null | head -2
        ((WARNINGS++))
    fi
done

# 3. Sprawdź private files
echo ""
echo "📄 3. CHECKING FOR PRIVATE FILES..."
PRIVATE_FILES=(
    "cursorrules"
    ".cursorrules"
    "*.local"
    "private-*"
    ".env.dev"
    "*.key"
    "*.pem"
    "secrets.json"
    ".git-credentials"
    ".netrc"
)

for pattern in "${PRIVATE_FILES[@]}"; do
    if find "$PUBLIC_DIR/" -name "$pattern" 2>/dev/null | grep -q .; then
        echo -e "${RED}❌ PRIVATE FILE FOUND: $pattern${NC}"
        find "$PUBLIC_DIR/" -name "$pattern" 2>/dev/null
        ((ERRORS++))
    fi
done

# 4. Sprawdź dev directories  
echo ""
echo "📁 4. CHECKING FOR DEV DIRECTORIES..."
DEV_DIRS=(
    "build-scripts"
    "internal-docs"
    "private-configs"
    "dev-tools"
    ".vscode"
    ".idea"
)

for dir in "${DEV_DIRS[@]}"; do
    if [ -d "$PUBLIC_DIR/$dir" ]; then
        echo -e "${YELLOW}⚠️  DEV DIRECTORY FOUND: $dir${NC}"
        ((WARNINGS++))
    fi
done

# 5. Sprawdź README.md
echo ""
echo "📖 5. CHECKING README.md..."
if [ -f "$PUBLIC_DIR/README.md" ]; then
    # Sprawdź czy README zawiera dev-specific sections
    if grep -q -i "development\|internal\|private\|cursorrules" "$PUBLIC_DIR/README.md"; then
        echo -e "${YELLOW}⚠️  README may contain dev-specific content${NC}"
        echo "   Check sections mentioning: development, internal, private, cursorrules"
        ((WARNINGS++))
    fi
    
    # Sprawdź czy README ma user-friendly installation section
    if ! grep -q -i "installation\|install\|download" "$PUBLIC_DIR/README.md"; then
        echo -e "${YELLOW}⚠️  README missing user installation instructions${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}❌ README.md not found in $PUBLIC_DIR${NC}"
    ((ERRORS++))
fi

# 6. Sprawdź .gitignore
echo ""
echo "🚫 6. CHECKING .gitignore..."
if [ -f "$PUBLIC_DIR/.gitignore" ]; then
    # Sprawdź czy .gitignore nie ma dev-specific entries
    if grep -q "cursorrules\|private-\|\.local\|internal-" "$PUBLIC_DIR/.gitignore"; then
        echo -e "${YELLOW}⚠️  .gitignore contains dev-specific patterns${NC}"
        echo "   This might be OK, but verify it's intentional"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠️  .gitignore not found in $PUBLIC_DIR${NC}"
    ((WARNINGS++))
fi

# 7. Sprawdź file permissions
echo ""
echo "🔒 7. CHECKING FILE PERMISSIONS..."
# Znajdź pliki executable (mogą być problematyczne)
EXEC_FILES=$(find "$PUBLIC_DIR/" -type f -executable 2>/dev/null | grep -v ".git" | head -5)
if [ -n "$EXEC_FILES" ]; then
    echo -e "${YELLOW}⚠️  Executable files found:${NC}"
    echo "$EXEC_FILES"
    echo "   Verify these should be executable"
    ((WARNINGS++))
fi

# 8. Sprawdź wielkość plików
echo ""
echo "📏 8. CHECKING FILE SIZES..."
# Znajdź duże pliki (>1MB)
LARGE_FILES=$(find "$PUBLIC_DIR/" -type f -size +1M 2>/dev/null | head -3)
if [ -n "$LARGE_FILES" ]; then
    echo -e "${YELLOW}⚠️  Large files found (>1MB):${NC}"
    echo "$LARGE_FILES"
    echo "   Consider if these should be in public repo"
    ((WARNINGS++))
fi

# SUMMARY
echo ""
echo "📊 SECURITY CHECK SUMMARY"
echo "========================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ PASSED: No security issues found${NC}"
    echo -e "${GREEN}   Safe to publish to PUBLIC repository${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  WARNINGS: $WARNINGS issues found${NC}"
    echo -e "${YELLOW}   Review warnings before publishing${NC}"
    echo ""
    echo "💡 For dual-repo sync, warnings about executable Python files are typically OK"
    echo "   Proceeding with sync (warnings are non-blocking)..."
    exit 0
else
    echo -e "${RED}❌ ERRORS: $ERRORS critical issues found${NC}"
    echo -e "${RED}   Fix all errors before publishing${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}   Also $WARNINGS warnings to review${NC}"
    fi
    exit 2
fi