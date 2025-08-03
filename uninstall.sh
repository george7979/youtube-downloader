#!/bin/bash
# YouTube Downloader - Deinstalator
# Autor: george7979

echo "🗑️ YouTube Downloader - Deinstalator"
echo "===================================="

# Sprawdź czy jesteś root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ten skrypt wymaga uprawnień root (sudo)"
    echo "Uruchom: sudo ./uninstall.sh"
    exit 1
fi

echo "🧹 Usuwanie plików aplikacji..."

# Usuń pliki aplikacji (włącznie ze środowiskiem wirtualnym)
rm -rf /usr/share/youtube-downloader
rm -f /usr/bin/youtube-downloader
rm -f /usr/share/applications/youtube-downloader.desktop
rm -f /usr/share/icons/hicolor/256x256/apps/youtube-downloader.png

# Usuń logi użytkownika
echo "🗑️ Usuwanie logów aplikacji..."
rm -rf ~/.youtube-downloader
echo "✅ Logi zostały usunięte"

# Informacja o środowisku wirtualnym
echo ""
echo "🐍 Środowisko wirtualne zostało automatycznie usunięte"
echo "   Zależności były izolowane w /usr/share/youtube-downloader/venv/"
echo "   Nie wpłynęło to na inne aplikacje w systemie"

echo "✅ Deinstalacja zakończona!"
echo "📝 Aplikacja została usunięta z systemu"
