#!/bin/bash
set -e

echo "🔧 Setup Dual Repository System"
echo "================================"

# Konfiguracja
PRIVATE_REPO_NAME="youtube-downloader-dev"
PUBLIC_REPO_NAME="youtube-downloader"
CURRENT_DIR=$(pwd)

echo "📍 Current directory: $CURRENT_DIR"
echo "🔒 Private repo: $PRIVATE_REPO_NAME"
echo "🌍 Public repo: $PUBLIC_REPO_NAME"

# Sprawdź czy jesteśmy w repozytorium
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

echo ""
echo "🔄 Step 1: Prepare current repo as PRIVATE"
echo "==========================================="

# Dodaj pliki do .gitignore które nie powinny być w public
cat >> .gitignore << 'EOF'

# Private development files
cursorrules
.cursorrules
*.local
build-scripts/
internal-docs/
dev-setup.sh
private-*
.env.dev
TODO-dev.md
EOF

echo "✅ Updated .gitignore for private repo"

# Commit current state
git add .gitignore
git commit -m "Setup: Prepare private repo structure" || echo "Nothing to commit"

echo ""
echo "📂 Step 2: Create public-ready subdirectory"
echo "============================================"

# Utwórz katalog public z oczyszczonymi plikami
mkdir -p public-src

# Skopiuj pliki które mają być publiczne
PUBLIC_FILES=(
    "main.py"
    "gui.py" 
    "downloader.py"
    "utils.py"
    "requirements.txt"
    "README.md"
    "LICENSE"
    "plan.md"
    "debian-src/"
    "icons/"
    "pics/"
    ".github/"
)

for file in "${PUBLIC_FILES[@]}"; do
    if [ -e "$file" ]; then
        cp -r "$file" public-src/
        echo "✅ Copied: $file"
    else
        echo "⚠️  Not found: $file"
    fi
done

# Utwórz dedykowany .gitignore dla public repo
cat > public-src/.gitignore << 'EOF'
# Build artifacts
build/
*.deb
*.md5
*.sha256

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
debug.log

# Temporary
tmp/
temp/
EOF

# Utwórz publiczny README jeśli nie istnieje
if [ ! -f "public-src/README.md" ]; then
    cat > public-src/README.md << 'EOF'
# YouTube Downloader

Prosta aplikacja w Python do pobierania filmów z YouTube z interfejsem graficznym.

## Instalacja

Pobierz najnowszy pakiet .deb z [Releases](https://github.com/user/youtube-downloader/releases) i zainstaluj:

```bash
sudo dpkg -i youtube-downloader_*.deb
```

## Użycie

Po instalacji uruchom aplikację:

```bash
youtube-downloader
```

Lub znajdź "YouTube Downloader" w menu aplikacji.

## Wymagania systemowe

- Ubuntu/Debian Linux
- Python 3.8+
- python3-tk
- python3-venv

## Licencja

MIT License
EOF
fi

echo "✅ Created public-src directory"

echo ""
echo "🎯 Step 3: Initialize git-subrepo"
echo "=================================="

# Commit public-src
git add public-src/
git commit -m "Setup: Add public-src directory with filtered files"

echo ""
echo "📝 Step 4: Create sync scripts"
echo "==============================="

# Skrypt do synchronizacji PRIVATE -> PUBLIC
cat > scripts/sync-to-public.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Synchronizing PRIVATE -> PUBLIC"

# Pliki do synchronizacji
PUBLIC_FILES=(
    "main.py"
    "gui.py" 
    "downloader.py"
    "utils.py"
    "requirements.txt"
    "README.md"
    "LICENSE"
    "plan.md"
    "debian-src/"
    "icons/"
    "pics/"
    ".github/"
)

echo "📋 Updating files in public-src/..."
for file in "${PUBLIC_FILES[@]}"; do
    if [ -e "$file" ]; then
        cp -r "$file" public-src/
        echo "✅ Updated: $file"
    fi
done

echo "🔄 Creating sanitized README for public..."
# Sanitize README - usuń sekcje deweloperskie
if [ -f "README.md" ]; then
    # Usuń sekcje z deweloperskimi detalami
    sed '/## Development/,$d' README.md > public-src/README.md
    
    # Dodaj sekcję instalacji dla użytkowników
    cat >> public-src/README.md << 'ENDREADME'

## Instalacja

Pobierz najnowszy pakiet .deb z [Releases](https://github.com/user/youtube-downloader/releases):

```bash
sudo dpkg -i youtube-downloader_*.deb
sudo apt-get install -f  # Napraw ewentualne zależności
```

## Wymagania systemowe

- Ubuntu/Debian Linux  
- Python 3.8 lub nowszy
- python3-tk (interface graficzny)
- python3-venv (środowisko wirtualne)
- Opcjonalnie: ffmpeg (konwersja MP3)

## Wsparcie

Jeśli masz problemy, sprawdź [Issues](https://github.com/user/youtube-downloader/issues).
ENDREADME
fi

echo "✅ Files synchronized to public-src/"
echo "💡 Next: Review public-src/, then run push-to-public.sh"
EOF

# Skrypt do pushowania PUBLIC
cat > scripts/push-to-public.sh << 'EOF'
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
EOF

# Utwórz skrypt do pullowania zmian z PUBLIC
cat > scripts/pull-from-public.sh << 'EOF'
#!/bin/bash
set -e

echo "⬇️  Pulling changes from PUBLIC repository"

# TODO: Implement git-subrepo pull when public repo is setup
# git subrepo pull public-src

echo "💡 Manual method: Check public repository for external contributions"
echo "     Then manually copy files to private repo and commit"
EOF

chmod +x scripts/*.sh

echo "✅ Created sync scripts in scripts/"

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. 🔒 PRIVATE REPO (current):"
echo "   - This repo stays as your main development environment"
echo "   - Keep all sensitive files (cursorrules, dev scripts, etc.)"
echo "   - Use scripts/sync-to-public.sh to update public-src/"
echo ""
echo "2. 🌍 PUBLIC REPO (to create):"
echo "   - Create new GitHub repo: $PUBLIC_REPO_NAME"
echo "   - Initialize from public-src/ directory"
echo "   - OR use git-subrepo to link public-src/ as subrepo"
echo ""
echo "3. 🔄 WORKFLOW:"
echo "   - Work in private repo as usual"
echo "   - Run: scripts/sync-to-public.sh"  
echo "   - Run: scripts/push-to-public.sh"
echo "   - Public users see only clean, production-ready code"
echo ""
echo "💡 RECOMMENDATION: Use git-subrepo for seamless sync"
EOF