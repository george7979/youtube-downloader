#!/bin/bash

echo "🪝 Installing Git Hooks for Dual-Repo Security"
echo "=============================================="

# Sprawdź czy jesteśmy w git repo
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Utwórz katalog hooks jeśli nie istnieje
mkdir -p .git/hooks

echo "📝 Installing pre-push hook..."

# Utwórz pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash

echo ""
echo "🔍 DUAL-REPO SECURITY CHECK (pre-push hook)"
echo "============================================"

# Sprawdź czy istnieje public-src
if [ ! -d "public-src" ]; then
    echo "💡 No public-src directory found - skipping dual-repo checks"
    exit 0
fi

# Uruchom security check
if [ -x "scripts/security-check.sh" ]; then
    echo "🚀 Running security scan..."
    if ! ./scripts/security-check.sh; then
        echo ""
        echo "❌ PUSH BLOCKED BY SECURITY CHECK"
        echo "=================================="
        echo ""
        echo "🔧 To fix:"
        echo "1. Review and fix all errors shown above"
        echo "2. Run: ./scripts/security-check.sh"
        echo "3. Only push when all checks pass"
        echo ""
        echo "⚠️  Or skip this check with: git push --no-verify"
        echo "   (NOT recommended for production)"
        exit 1
    fi
    echo "✅ Security check passed - proceeding with push"
else
    echo "⚠️  Security check script not found - proceeding without scan"
fi

echo ""
EOF

# Uczyń hook wykonywalny
chmod +x .git/hooks/pre-push

echo "✅ Pre-push hook installed"

echo ""
echo "📝 Installing commit-msg hook..."

# Utwórz commit-msg hook dla better commit messages
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash

# Sprawdź czy commit message nie zawiera sekretów
if grep -q -i "password\|secret\|key\|token" "$1"; then
    echo "❌ COMMIT BLOCKED: Potential secret in commit message"
    echo "   Remove any passwords, keys, or secrets from the commit message"
    exit 1
fi

# Sprawdź czy commit message nie jest za krótki
if [ $(wc -c < "$1") -lt 10 ]; then
    echo "❌ COMMIT BLOCKED: Commit message too short (minimum 10 characters)"
    exit 1
fi

# Sprawdź czy commit message nie zawiera TODO-DEV w public-src commits
if git diff --cached --name-only | grep -q "^public-src/"; then
    if grep -q -i "todo-dev\|fixme-dev\|xxx-dev" "$1"; then
        echo "❌ COMMIT BLOCKED: Dev comments in commit message for public-src changes"
        echo "   Remove TODO-DEV, FIXME-DEV, XXX-DEV from commit message"
        exit 1
    fi
fi
EOF

chmod +x .git/hooks/commit-msg

echo "✅ Commit-msg hook installed"

echo ""
echo "📝 Installing pre-commit hook..."

# Utwórz pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo ""
echo "🔍 PRE-COMMIT CHECKS"
echo "===================="

# Sprawdź czy dodajemy przypadkowo private files do public-src
STAGED_PUBLIC_FILES=$(git diff --cached --name-only | grep "^public-src/" | head -10)

if [ -n "$STAGED_PUBLIC_FILES" ]; then
    echo "📤 Changes to public-src detected:"
    echo "$STAGED_PUBLIC_FILES"
    echo ""
    
    # Sprawdź czy staged files w public-src zawierają sekrety
    for file in $STAGED_PUBLIC_FILES; do
        if [ -f "$file" ]; then
            if grep -q -i "api_key\|secret\|password\|token\|private_key" "$file"; then
                echo "❌ COMMIT BLOCKED: Potential secret found in: $file"
                echo "   Remove secrets before committing public-src changes"
                exit 1
            fi
            
            if grep -q "todo-dev\|fixme-dev\|xxx-dev" "$file"; then
                echo "❌ COMMIT BLOCKED: Dev comment found in: $file"
                echo "   Remove or change TODO-DEV, FIXME-DEV, XXX-DEV comments"
                exit 1
            fi
        fi
    done
    
    echo "✅ Public-src files look safe"
fi

# Sprawdź czy przypadkowo nie commitujemy cursorrules do public-src
if git diff --cached --name-only | grep -q "^public-src/cursorrules"; then
    echo "❌ COMMIT BLOCKED: cursorrules file in public-src"
    echo "   Remove cursorrules from public-src directory"
    exit 1
fi

# Sprawdź czy nie ma very large files (>5MB)
LARGE_FILES=$(git diff --cached --name-only | xargs -I {} find {} -size +5M 2>/dev/null | head -3)
if [ -n "$LARGE_FILES" ]; then
    echo "⚠️  WARNING: Large files detected (>5MB):"
    echo "$LARGE_FILES"
    echo "   Consider using Git LFS for large files"
fi

echo "✅ Pre-commit checks passed"
echo ""
EOF

chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed"

echo ""
echo "🎉 INSTALLATION COMPLETE!"
echo "========================"
echo ""
echo "📋 INSTALLED HOOKS:"
echo ""
echo "🔒 pre-push     - Runs security-check.sh before push"
echo "💬 commit-msg   - Validates commit messages" 
echo "📝 pre-commit   - Checks staged files for secrets"
echo ""
echo "🔧 USAGE:"
echo ""
echo "• Hooks run automatically on git operations"
echo "• Skip with --no-verify flag (not recommended)"
echo "• Test manually: ./scripts/security-check.sh"
echo ""
echo "⚠️  IMPORTANT:"
echo "• Hooks are LOCAL to this repository"
echo "• Share this script with team members"
echo "• Re-run after fresh clone"
echo ""
echo "🚀 Next: Test with 'git commit' or 'git push'"