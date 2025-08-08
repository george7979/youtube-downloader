#!/bin/bash
set -e

echo "🔄 CONTINUOUS INTEGRATION CHECKS"
echo "================================="

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
    return 1
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo ""
echo -e "${BLUE}1. CODE QUALITY CHECKS${NC}"
echo "======================="

# Python syntax check
echo "Checking Python syntax..."
PYTHON_ERRORS=0
for file in public-src/*.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo "  ✓ $(basename "$file") syntax OK"
        else
            echo -e "  ${RED}✗ $(basename "$file") syntax ERROR${NC}"
            ((PYTHON_ERRORS++))
        fi
    fi
done

if [ $PYTHON_ERRORS -eq 0 ]; then
    check_pass "All Python files have valid syntax"
else
    check_fail "$PYTHON_ERRORS Python syntax errors found"
fi

# Check for common Python issues
echo ""
echo "Checking for common Python issues..."
if grep -r "print(" public-src/*.py | grep -v "# debug" >/dev/null 2>&1; then
    check_warning "Debug print statements found (may be intentional)"
else
    check_pass "No debug print statements found"
fi

echo ""
echo -e "${BLUE}2. SECURITY VALIDATION${NC}"
echo "======================="

# Run full security check
echo "Running comprehensive security scan..."
if ./scripts/security-check.sh >/dev/null 2>&1; then
    check_pass "Security scan completed successfully"
else
    # Security check returns 1 for warnings, 2 for errors
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 1 ]; then
        check_warning "Security scan completed with warnings"
    else
        check_fail "Security scan failed with errors"
    fi
fi

# Check Git configuration
echo ""
echo "Checking Git configuration..."
if git config user.name >/dev/null 2>&1; then
    check_pass "Git user.name configured"
else
    check_warning "Git user.name not configured"
fi

if git config user.email >/dev/null 2>&1; then
    check_pass "Git user.email configured"
else
    check_warning "Git user.email not configured"
fi

echo ""
echo -e "${BLUE}3. BUILD VALIDATION${NC}"
echo "==================="

# Test build system
echo "Testing build system..."
if make -n build >/dev/null 2>&1; then
    check_pass "Makefile build target works"
else
    check_fail "Makefile build target broken"
fi

# Check version consistency
echo ""
echo "Checking version consistency..."
if ./build-tools/version-manager.sh show >/dev/null 2>&1; then
    VERSION=$(./build-tools/version-manager.sh show | grep "Aktualna wersja:" | cut -d: -f2 | xargs)
    check_pass "Version manager works (version: $VERSION)"
else
    check_fail "Version manager broken"
fi

# Check required files
echo ""
echo "Checking required files..."
REQUIRED_FILES=("public-src/main.py" "public-src/gui.py" "public-src/requirements.txt" "public-src/README.md")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Required file $file exists"
    else
        check_fail "Required file $file missing"
    fi
done

echo ""
echo -e "${BLUE}4. DUAL-REPO VALIDATION${NC}"
echo "======================="

# Test dual-repo workflow
echo "Testing dual-repo workflow..."
if ./scripts/test-dual-repo.sh >/dev/null 2>&1; then
    check_pass "Dual-repo workflow tests pass"
else
    check_fail "Dual-repo workflow tests failed"
fi

# Check public-src cleanliness
echo ""
echo "Checking public-src cleanliness..."
PRIVATE_PATTERNS=("cursorrules" "*-dev.*" "private-*" "*.local" ".env.*")
PRIVATE_FOUND=0

for pattern in "${PRIVATE_PATTERNS[@]}"; do
    if find public-src/ -name "$pattern" 2>/dev/null | grep -q .; then
        check_fail "Private files found in public-src: $pattern"
        ((PRIVATE_FOUND++))
    fi
done

if [ $PRIVATE_FOUND -eq 0 ]; then
    check_pass "public-src/ contains no private files"
fi

echo ""
echo -e "${BLUE}5. FINAL VALIDATION${NC}"
echo "==================="

# Overall project health
echo "Checking overall project health..."

# Check .gitignore
if [ -f ".gitignore" ] && grep -q "cursorrules" ".gitignore"; then
    check_pass "gitignore properly configured for dual-repo"
else
    check_warning "gitignore may need dual-repo configuration"
fi

# Check documentation
if [ -f "docs/DUAL-REPO.md" ] && [ -f "docs/ZASADY-DUAL-REPO.md" ]; then
    check_pass "Dual-repo documentation complete"
else
    check_warning "Dual-repo documentation may be incomplete"
fi

echo ""
echo -e "${BLUE}📊 CI CHECK SUMMARY${NC}"
echo "==================="

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED))
echo -e "Total checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🚀 CI CHECKS PASSED!${NC}"
    echo -e "${GREEN}Project is ready for production use.${NC}"
    
    echo ""
    echo -e "${BLUE}📋 RECOMMENDED NEXT STEPS:${NC}"
    echo "• Run full build: make build"
    echo "• Test package: make test"
    echo "• Sync to public: ./scripts/sync-to-public-github.sh"
    exit 0
else
    echo ""
    echo -e "${RED}❌ CI CHECKS FAILED${NC}"
    echo -e "${RED}Fix all issues before proceeding with production.${NC}"
    
    echo ""
    echo -e "${YELLOW}🔧 TROUBLESHOOTING:${NC}"
    echo "• Check individual test results above"
    echo "• Run: ./scripts/test-dual-repo.sh for detailed analysis"
    echo "• Review: docs/DUAL-REPO.md for workflow guidance"
    exit 1
fi