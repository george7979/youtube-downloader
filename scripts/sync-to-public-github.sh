#!/bin/bash
set -e

echo "🚀 SYNC TO PUBLIC GITHUB REPOSITORY"
echo "===================================="

# Konfiguracja
PUBLIC_REMOTE="public"
PUBLIC_REPO="george7979/youtube-downloader"
PUBLIC_SRC="public-src"
TEMP_DIR="/tmp/public-sync-$$"

echo "📍 Current directory: $(pwd)"
echo "🔒 Private repo: $(git remote get-url origin)"
echo "🌍 Public repo: $(git remote get-url $PUBLIC_REMOTE)"
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
find "$PUBLIC_SRC" -type f | head -20
echo "... (showing first 20 files)"

echo ""
read -p "🤔 Continue with sync? (y/N): " -n 1 -r
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
git clone "https://github.com/$PUBLIC_REPO.git" "$TEMP_DIR"
cd "$TEMP_DIR"

echo "✅ Public repo cloned to: $TEMP_DIR"

echo ""
echo "🧹 CLEAR PUBLIC REPO CONTENT"
echo "============================"

# Usuń wszystko oprócz .git
find . -maxdepth 1 -not -name ".git" -not -name "." -exec rm -rf {} +

echo "✅ Public repo cleaned"

echo ""
echo "📋 COPY FILES FROM PRIVATE"
echo "=========================="

# Skopiuj wszystkie pliki z public-src
cp -r "$OLDPWD/$PUBLIC_SRC/"* .

# Sprawdź czy mamy pliki
if [ -z "$(ls -A)" ]; then
    echo "❌ No files copied!"
    exit 1
fi

echo "✅ Files copied from private/$PUBLIC_SRC/"

echo ""
echo "📝 CHECK COPIED FILES"
echo "====================="
echo "Total files: $(find . -type f | wc -l)"
echo "Python files: $(find . -name "*.py" | wc -l)"
echo "Config files: $(ls *.md *.txt LICENSE 2>/dev/null | wc -l)"

echo ""
echo "🔍 FINAL SECURITY CHECK"
echo "======================="

# Sprawdź czy nie ma przypadkowych sekretów
if grep -r -i "password\|secret\|api_key\|token" . --exclude-dir=.git >/dev/null 2>&1; then
    echo "⚠️  WARNING: Potential secrets found:"
    grep -r -i "password\|secret\|api_key\|token" . --exclude-dir=.git | head -3
    echo ""
    read -p "🤔 Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled due to security concerns"
        cd "$OLDPWD"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Sprawdź czy nie ma cursorrules
if find . -name "cursorrules" -o -name ".cursorrules" | grep -q .; then
    echo "❌ CRITICAL: cursorrules found in public files!"
    find . -name "cursorrules" -o -name ".cursorrules"
    cd "$OLDPWD"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "✅ Final security check passed"

echo ""
echo "📤 COMMIT AND PUSH TO PUBLIC"
echo "============================"

# Git config dla public repo
git config user.name "Jerzy Maczewski"
git config user.email "jerzy.maczewski@example.com"

# Add wszystkie pliki
git add .

# Sprawdź status
if [ -z "$(git status --porcelain)" ]; then
    echo "📍 No changes to commit - public repo is up to date"
else
    echo "📋 Changes to commit:"
    git status --short | head -10
    
    # Commit ze standardową wiadomością
    COMMIT_MSG="Sync from private repo ($(date '+%Y-%m-%d %H:%M'))

🔄 Synchronized from youtube-downloader-private
📁 Source: public-src/ directory
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    git commit -m "$COMMIT_MSG"
    echo "✅ Changes committed"
    
    # Push do public repo
    echo ""
    echo "🚀 Pushing to public repository..."
    git push origin main
    echo "✅ Successfully pushed to public repo"
fi

echo ""
echo "🧹 CLEANUP"
echo "==========="
cd "$OLDPWD"
rm -rf "$TEMP_DIR"
echo "✅ Temp directory cleaned"

echo ""
echo "🎉 SYNC COMPLETE!"
echo "================="
echo ""
echo "📋 RESULTS:"
echo "🔒 Private repo: https://github.com/george7979/youtube-downloader-private"
echo "🌍 Public repo: https://github.com/$PUBLIC_REPO"
echo ""
echo "✅ Public repository has been updated with clean, user-ready code"
echo "✅ All sensitive files remain in private repository only"
echo ""
echo "🔄 NEXT STEPS:"
echo "• Check public repo: https://github.com/$PUBLIC_REPO"
echo "• Verify files look correct for end users"
echo "• Update any links/documentation as needed"