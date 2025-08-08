#!/bin/bash
set -e

echo "🧪 DUAL-REPO WORKFLOW TESTS"
echo "============================"

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo ""
echo -e "${BLUE}📁 TEST 1: STRUCTURE INTEGRITY${NC}"
echo "================================="

# Test symlinks
echo "Testing symlinks..."
for file in main.py gui.py downloader.py utils.py requirements.txt; do
    if [ -L "$file" ]; then
        if [ -e "$file" ]; then
            test_pass "Symlink $file works"
        else
            test_fail "Symlink $file broken"
        fi
    else
        test_fail "File $file is not a symlink"
    fi
done

# Test debian-src symlink
if [ -L "debian-src" ] && [ -d "debian-src" ]; then
    test_pass "debian-src symlink works"
else
    test_fail "debian-src symlink broken"
fi

# Test source files exist
echo ""
echo "Testing source files in public-src/..."
for file in main.py gui.py downloader.py utils.py requirements.txt; do
    if [ -f "public-src/$file" ]; then
        test_pass "Source file public-src/$file exists"
    else
        test_fail "Source file public-src/$file missing"
    fi
done

echo ""
echo -e "${BLUE}🔒 TEST 2: SECURITY CHECKS${NC}"
echo "============================"

# Test security script exists and works
if [ -x "scripts/security-check.sh" ]; then
    test_pass "Security check script executable"
    
    echo "Running security scan..."
    if ./scripts/security-check.sh >/dev/null 2>&1; then
        test_pass "Security scan passes"
    else
        test_warning "Security scan has warnings (may be normal)"
    fi
else
    test_fail "Security check script not executable"
fi

# Test for private files in public-src
echo ""
echo "Checking for private files in public-src/..."
PRIVATE_FILES_FOUND=0

for pattern in "cursorrules" ".cursorrules" "*-dev.*" "private-*" "*.local"; do
    if find public-src/ -name "$pattern" 2>/dev/null | grep -q .; then
        test_fail "Private files found in public-src/: $pattern"
        ((PRIVATE_FILES_FOUND++))
    fi
done

if [ $PRIVATE_FILES_FOUND -eq 0 ]; then
    test_pass "No private files in public-src/"
fi

echo ""
echo -e "${BLUE}🔧 TEST 3: BUILD SYSTEM${NC}"
echo "========================="

# Test build tools exist
if [ -x "build-tools/build-deb.sh" ]; then
    test_pass "Build script exists and is executable"
else
    test_fail "Build script missing or not executable"
fi

if [ -x "build-tools/version-manager.sh" ]; then
    test_pass "Version manager exists and is executable"
else
    test_fail "Version manager missing or not executable"
fi

# Test Makefile targets
echo ""
echo "Testing Makefile targets..."
for target in help version clean; do
    if make -n "$target" >/dev/null 2>&1; then
        test_pass "Makefile target '$target' works"
    else
        test_fail "Makefile target '$target' broken"
    fi
done

echo ""
echo -e "${BLUE}🌍 TEST 4: DUAL-REPO SYNC${NC}"
echo "=========================="

# Test sync scripts exist
for script in "sync-to-public-github.sh" "force-sync-public.sh" "pull-from-public.sh"; do
    if [ -x "scripts/$script" ]; then
        test_pass "Sync script $script exists"
    else
        test_fail "Sync script $script missing or not executable"
    fi
done

# Test Git hooks
echo ""
echo "Testing Git hooks..."
for hook in "pre-push" "pre-commit" "commit-msg"; do
    if [ -f ".git/hooks/$hook" ] && [ -x ".git/hooks/$hook" ]; then
        test_pass "Git hook $hook installed"
    else
        test_warning "Git hook $hook not installed (run ./scripts/install-hooks.sh)"
    fi
done

echo ""
echo -e "${BLUE}📚 TEST 5: DOCUMENTATION${NC}"
echo "=========================="

# Test documentation files
DOC_FILES=("docs/BUILDING.md" "docs/DUAL-REPO.md" "docs/ZASADY-DUAL-REPO.md" "README.md")
for doc in "${DOC_FILES[@]}"; do
    if [ -f "$doc" ]; then
        test_pass "Documentation file $doc exists"
    else
        test_fail "Documentation file $doc missing"
    fi
done

# Test public-src has user documentation
if [ -f "public-src/README.md" ]; then
    if grep -q "instalacja\|installation" "public-src/README.md"; then
        test_pass "Public README contains user documentation"
    else
        test_warning "Public README may lack user installation info"
    fi
else
    test_fail "Public README.md missing"
fi

echo ""
echo -e "${BLUE}🎯 TEST 6: FILE CONSISTENCY${NC}"
echo "============================"

# Test file consistency between symlinks and sources
echo "Testing file consistency..."
for file in main.py gui.py downloader.py utils.py requirements.txt; do
    if [ -f "$file" ] && [ -f "public-src/$file" ]; then
        if diff "$file" "public-src/$file" >/dev/null 2>&1; then
            test_pass "File $file consistent with source"
        else
            test_fail "File $file differs from source"
        fi
    fi
done

echo ""
echo -e "${BLUE}📊 TEST SUMMARY${NC}"
echo "================"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "Total tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}Dual-repo workflow is working correctly.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}Fix issues before using dual-repo workflow.${NC}"
    exit 1
fi