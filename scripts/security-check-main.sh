#!/bin/bash
# Security Check for Main Branch Merge
# Sprawdza czy branch jest bezpieczny do merge na main

set -e

BRANCH=${1:-HEAD}
STRICT_MODE=${2:-false}

echo "🔍 SECURITY CHECK - Main Branch Protection"
echo "=========================================="
echo "Checking branch: $BRANCH"
echo "Strict mode: $STRICT_MODE"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERROR_COUNT=0
WARNING_COUNT=0

# Function to report error
report_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERROR_COUNT++))
}

# Function to report warning  
report_warning() {
    echo -e "${YELLOW}⚠️ WARNING: $1${NC}"
    ((WARNING_COUNT++))
}

# Function to report success
report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "📋 Checking for sensitive files..."

# Check for cursorrules files
if git ls-tree -r --name-only $BRANCH | grep -E "(^|/)cursorrules$" > /dev/null; then
    report_error "cursorrules file found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "(^|/)cursorrules$"
else
    report_success "No cursorrules files found"
fi

# Check for .cursorrules files
if git ls-tree -r --name-only $BRANCH | grep -E "(^|/)\.cursorrules$" > /dev/null; then
    report_error ".cursorrules file found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "(^|/)\.cursorrules$"
else
    report_success "No .cursorrules files found"
fi

# Check for developer documentation files
if git ls-tree -r --name-only $BRANCH | grep -E "^(CLAUDE\.md|PRD\.md|TODO.*\.md|NOTES.*\.md)$" > /dev/null; then
    report_error "Developer documentation found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "^(CLAUDE\.md|PRD\.md|TODO.*\.md|NOTES.*\.md)$"
else
    report_success "No developer documentation files found"
fi

# Check for temporary files
if git ls-tree -r --name-only $BRANCH | grep -E "\.version-backup$" > /dev/null; then
    report_error "Temporary backup files found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "\.version-backup$"
else
    report_success "No temporary backup files found"
fi

# Check for environment files
if git ls-tree -r --name-only $BRANCH | grep -E "\.(env|local)$" > /dev/null; then
    report_error "Environment files found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "\.(env|local)$"
else
    report_success "No environment files found"
fi

# Check for development .deb files
if git ls-tree -r --name-only $BRANCH | grep -E "_dev.*\.deb$|_alpha.*\.deb$|_beta.*\.deb$" > /dev/null; then
    report_error "Development .deb files found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "_dev.*\.deb$|_alpha.*\.deb$|_beta.*\.deb$"
else
    report_success "No development .deb files found"
fi

# Check for backup directories
if git ls-tree -r --name-only $BRANCH | grep -E "^backup/" > /dev/null; then
    report_error "Backup directories found - MUST NOT be in main branch"
    git ls-tree -r --name-only $BRANCH | grep -E "^backup/" | head -5
else
    report_success "No backup directories found"
fi

# Check for private scripts
PRIVATE_SCRIPTS=(
    "scripts/push-to-private.sh"
    "scripts/force-sync-public.sh"
    "scripts/setup-dual-repo.sh"
)

for script in "${PRIVATE_SCRIPTS[@]}"; do
    if git ls-tree -r --name-only $BRANCH | grep -E "^$script$" > /dev/null; then
        report_error "Private script found: $script"
    fi
done

# Check for potential secrets in file contents
echo ""
echo "🔐 Checking file contents for potential secrets..."

# Get list of text files to scan
TEXT_FILES=$(git ls-tree -r --name-only $BRANCH | grep -E '\.(py|sh|yml|yaml|md|txt|json)$' | grep -v -E '^(backup/|tests/)')

if [ -n "$TEXT_FILES" ]; then
    # Check for potential API keys, passwords, etc.
    SECRET_PATTERNS=(
        "password[[:space:]]*="
        "api[_-]?key[[:space:]]*="
        "secret[[:space:]]*="
        "token[[:space:]]*="
        "GITHUB_TOKEN"
        "API_SECRET"
    )
    
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if echo "$TEXT_FILES" | xargs git show $BRANCH:{} 2>/dev/null | grep -i "$pattern" > /dev/null; then
            if [ "$STRICT_MODE" = "true" ]; then
                report_error "Potential secret pattern found: $pattern"
            else
                report_warning "Potential secret pattern found: $pattern (review manually)"
            fi
        fi
    done
else
    report_success "No text files to scan"
fi

# Check version.py for development versions
echo ""
echo "🏷️ Checking version number..."

VERSION_FILE=$(git show $BRANCH:version.py 2>/dev/null || echo "")
if [ -n "$VERSION_FILE" ]; then
    if echo "$VERSION_FILE" | grep -E "(dev|alpha|beta|rc)" > /dev/null; then
        report_warning "Development version detected in version.py"
        echo "   Current: $(echo "$VERSION_FILE" | grep __version__)"
        echo "   Should be stable version for main branch"
    else
        report_success "Stable version detected"
    fi
else
    report_warning "version.py not found"
fi

# Check for large .deb files
echo ""
echo "📦 Checking .deb files..."

DEB_FILES=$(git ls-tree -r --name-only $BRANCH | grep -E '\.deb$')
if [ -n "$DEB_FILES" ]; then
    for deb in $DEB_FILES; do
        # Get file size from git
        SIZE=$(git cat-file -s $(git ls-tree $BRANCH $deb | awk '{print $3}'))
        SIZE_MB=$((SIZE / 1024 / 1024))
        
        if [ $SIZE_MB -gt 100 ]; then
            report_warning ".deb file is large: $deb ($SIZE_MB MB)"
        else
            echo "   📦 $deb ($SIZE_MB MB) - OK"
        fi
    done
else
    report_warning "No .deb files found - is this intentional?"
fi

# Summary
echo ""
echo "📊 SECURITY SCAN SUMMARY"
echo "========================"

if [ $ERROR_COUNT -eq 0 ] && [ $WARNING_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED - Safe to merge to main${NC}"
    exit 0
elif [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠️ WARNINGS FOUND: $WARNING_COUNT${NC}"
    echo "   Review warnings before merging to main"
    exit 0
else
    echo -e "${RED}❌ CRITICAL ERRORS: $ERROR_COUNT${NC}"
    echo -e "${YELLOW}   Warnings: $WARNING_COUNT${NC}"
    echo ""
    echo "🚫 MERGE BLOCKED - Fix errors before proceeding"
    exit 1
fi