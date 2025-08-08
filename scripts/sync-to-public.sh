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
