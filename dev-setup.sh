#!/bin/bash
# YouTube Downloader - Skrypt dla programistów
# Autor: george7979

echo "🔧 YouTube Downloader - Setup dla programistów"
echo "=============================================="

# Sprawdź czy Python 3 jest dostępny
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nie jest zainstalowany"
    exit 1
fi

# Utwórz środowisko wirtualne
echo "🐍 Tworzenie środowiska wirtualnego..."
python3 -m venv .venv

# Aktywuj środowisko wirtualne
echo "🔧 Aktywacja środowiska wirtualnego..."
source .venv/bin/activate

# Zainstaluj zależności
echo "📚 Instalowanie zależności..."
pip install -r requirements.txt

echo "✅ Setup zakończony!"
echo "🚀 Aby uruchomić aplikację:"
echo "   source .venv/bin/activate"
echo "   python main.py"
echo ""
echo "📝 Lub użyj skryptu: ./run-dev.sh" 