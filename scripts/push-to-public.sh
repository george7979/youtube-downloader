#!/bin/bash
set -e

echo "🚀 Publishing to PUBLIC repository"

# Sprawdź czy mamy zmiany w public-src
if [ -z "$(git status --porcelain public-src/)" ]; then
    echo "📍 No changes in public-src/ to publish"
    exit 0
fi

echo "📋 Changes detected in public-src/:"
git status --porcelain public-src/

echo ""
read -p "🤔 Proceed with publishing? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Commit changes in private repo
git add public-src/
git commit -m "Update public-src for release $(date +%Y%m%d-%H%M)"

echo "✅ Changes committed to private repo"
echo "💡 TODO: Setup git-subrepo or manual sync to public repository"

# TODO: Implement git-subrepo push when public repo is setup
# git subrepo push public-src -r https://github.com/user/youtube-downloader.git
