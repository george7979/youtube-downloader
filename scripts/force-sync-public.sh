#!/bin/bash
set -e

echo "🚀 FORCE SYNC TO PUBLIC GITHUB REPOSITORY"
echo "=========================================="

# Konfiguracja
PUBLIC_REPO="george7979/youtube-downloader"
PUBLIC_SRC="public-src"
TEMP_DIR="/tmp/force-sync-$$"

echo "📍 Current directory: $(pwd)"
echo "🌍 Public repo: https://github.com/$PUBLIC_REPO"
echo "📁 Source directory: $PUBLIC_SRC"

# Sprawdź czy public-src istnieje
if [ ! -d "$PUBLIC_SRC" ]; then
    echo "❌ Directory $PUBLIC_SRC not found"
    exit 1
fi

echo ""
echo "🔍 SECURITY CHECK"
echo "=================="
if ! ./scripts/security-check.sh; then
    echo ""
    echo "❌ Security check failed!"
    echo "Fix all issues before continuing"
    exit 1
fi

echo "✅ Security check passed"

echo ""
echo "📋 FILES TO SYNC:"
echo "=================="
echo "Total files: $(find $PUBLIC_SRC -type f | wc -l)"
find "$PUBLIC_SRC" -type f | head -15
echo "... (showing first 15 files)"

echo ""
echo "⚠️  WARNING: This will COMPLETELY REPLACE public repository content!"
echo "Only files from public-src/ will remain in the public repo."
echo ""
read -p "🤔 Continue with FORCE sync? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "📥 CLONE PUBLIC REPOSITORY"
echo "=========================="

# Usuń temp dir jeśli istnieje
rm -rf "$TEMP_DIR"

# Clone public repo
echo "Cloning https://github.com/$PUBLIC_REPO.git..."
git clone "https://github.com/$PUBLIC_REPO.git" "$TEMP_DIR"
cd "$TEMP_DIR"

echo "✅ Public repo cloned to: $TEMP_DIR"

echo ""
echo "🧹 COMPLETE CLEANUP OF PUBLIC REPO"
echo "=================================="

# Usuń WSZYSTKO oprócz .git
echo "Removing all files except .git..."
find . -maxdepth 1 -not -name ".git" -not -name "." -exec rm -rf {} + 2>/dev/null || true

# Sprawdź czy są ukryte pliki do usunięcia
find . -maxdepth 1 -name ".*" -not -name ".git" -not -name "." -exec rm -rf {} + 2>/dev/null || true

echo "✅ Public repo completely cleaned"

echo ""
echo "📋 COPY CLEAN FILES FROM PRIVATE"
echo "================================"

# Skopiuj tylko pliki z public-src (bez ukrytych plików systemowych)
echo "Copying files from $OLDPWD/$PUBLIC_SRC/..."

# Kopiuj visible files
cp -r "$OLDPWD/$PUBLIC_SRC/"* . 2>/dev/null || true

# Kopiuj tylko bezpieczne hidden files (exclude .venv, cursorrules itp.)
for hidden_file in "$OLDPWD/$PUBLIC_SRC/".github "$OLDPWD/$PUBLIC_SRC/".gitignore; do
    if [ -e "$hidden_file" ]; then
        cp -r "$hidden_file" . 2>/dev/null || true
    fi
done

# Sprawdź czy mamy pliki
COPIED_FILES=$(find . -type f | grep -v "^./.git" | wc -l)
if [ "$COPIED_FILES" -eq 0 ]; then
    echo "❌ No files copied!"
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "✅ Copied $COPIED_FILES files from private/$PUBLIC_SRC/"

echo ""
echo "📝 FINAL FILE CHECK"
echo "==================="
echo "Files in public repo after sync:"
find . -type f | grep -v "^./.git" | sort | head -20

echo ""
echo "🔍 CRITICAL SECURITY CHECK"
echo "=========================="

# Sprawdź cursorrules
if find . -name "cursorrules" -o -name ".cursorrules" | grep -q .; then
    echo "❌ CRITICAL ERROR: cursorrules found!"
    find . -name "cursorrules" -o -name ".cursorrules"
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Sprawdź dev scripts
if find . -name "dev-setup.sh" -o -name "run-dev.sh" -o -name "*-dev.*" | grep -q .; then
    echo "❌ CRITICAL ERROR: Dev scripts found!"
    find . -name "dev-setup.sh" -o -name "run-dev.sh" -o -name "*-dev.*"
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Sprawdź sekrety (z wyjątkiem standardowych GitHub Actions secrets)
if grep -r -i "password\|api_key" . --exclude-dir=.git >/dev/null 2>&1; then
    echo "❌ CRITICAL ERROR: Potential secrets found!"
    grep -r -i "password\|api_key" . --exclude-dir=.git | head -3
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Sprawdź czy nie ma custom secrets (nie GitHub Actions)
SUSPICIOUS_SECRETS=$(grep -r -i "secret\|token" . --exclude-dir=.git | grep -v "secrets.GITHUB_TOKEN\|secrets.github_token" | head -3)
if [ -n "$SUSPICIOUS_SECRETS" ]; then
    echo "❌ CRITICAL ERROR: Custom secrets found!"
    echo "$SUSPICIOUS_SECRETS"
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "✅ Critical security check PASSED"

echo ""
echo "📤 COMMIT AND FORCE PUSH TO PUBLIC"
echo "=================================="

# Git config
git config user.name "Jerzy Maczewski"
git config user.email "jerzy.maczewski@example.com"

# Add wszystkie pliki
git add -A

# Sprawdź status
echo "📋 Git status after add:"
git status --short | head -10

# Commit ze szczegółową wiadomością
COMMIT_MSG="MAJOR: Clean dual-repo implementation

🧹 COMPLETE REPOSITORY CLEANUP
✅ Removed all dev files (cursorrules, dev-setup.sh, etc.)
✅ Removed old build artifacts and scripts  
✅ Removed legacy debian/ structure
🔄 Synchronized ONLY from private/public-src/

📁 NEW CLEAN STRUCTURE:
• Application code (main.py, gui.py, downloader.py, utils.py)
• User documentation (README.md, LICENSE)
• Debian packaging (debian-src/)
• Application assets (icons/, pics/)
• GitHub workflow (.github/)

🛡️ SECURITY VERIFIED:
• No private files (cursorrules, etc.)
• No dev scripts or tools
• No secrets or sensitive data
• Only user-ready code and documentation

🎯 This is now a CLEAN public repository for end users.

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"

git commit -m "$COMMIT_MSG"
echo "✅ Changes committed with detailed message"

# Force push (zastąpi całą historię)
echo ""
echo "🚀 FORCE PUSHING to public repository..."
echo "⚠️  This will replace the entire public repo history!"

git push --force-with-lease origin main 2>/dev/null || git push --force-with-lease origin master 2>/dev/null || git push origin main --force

echo "✅ Successfully FORCE PUSHED to public repo"

echo ""
echo "🧹 CLEANUP"
echo "==========="
cd "$OLDPWD"
rm -rf "$TEMP_DIR"
echo "✅ Temp directory cleaned"

echo ""
echo "🎉 FORCE SYNC COMPLETE!"
echo "======================="
echo ""
echo "📊 RESULTS:"
echo "🔒 Private repo: https://github.com/george7979/youtube-downloader-private"
echo "🌍 Public repo: https://github.com/$PUBLIC_REPO"
echo ""
echo "✅ Public repository now contains ONLY clean, user-ready files"
echo "✅ All sensitive dev files removed from public repo"
echo "✅ Perfect dual-repo implementation achieved"
echo ""
echo "🔄 VERIFICATION:"
echo "• Check public repo: https://github.com/$PUBLIC_REPO"
echo "• Verify no cursorrules or dev files visible"
echo "• Confirm only user documentation and code present"