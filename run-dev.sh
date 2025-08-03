#!/bin/bash
# YouTube Downloader - Uruchamianie w środowisku wirtualnym
# Autor: george7979

echo "🚀 YouTube Downloader - Uruchamianie w trybie deweloperskim"
echo "=========================================================="

# Sprawdź czy .venv istnieje
if [ ! -d ".venv" ]; then
    echo "❌ Środowisko wirtualne nie istnieje"
    echo "Uruchom: ./dev-setup.sh"
    exit 1
fi

# Aktywuj środowisko wirtualne
echo "🔧 Aktywacja środowiska wirtualnego..."
source .venv/bin/activate

# Sprawdź czy zależności są zainstalowane
if ! python -c "import yt_dlp" 2>/dev/null; then
    echo "📚 Instalowanie brakujących zależności..."
    pip install -r requirements.txt
fi

# Uruchom aplikację
echo "🎬 Uruchamianie aplikacji..."
python main.py 