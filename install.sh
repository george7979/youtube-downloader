#!/bin/bash
# YouTube Downloader - Instalator
# Autor: george7979

echo "🎬 YouTube Downloader - Instalator"
echo "=================================="

# Sprawdź czy jesteś root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ten skrypt wymaga uprawnień root (sudo)"
    echo "Uruchom: sudo ./install.sh"
    exit 1
fi

# Utwórz katalogi
echo "📁 Tworzenie katalogów..."
mkdir -p /usr/share/youtube-downloader
mkdir -p /usr/bin
mkdir -p /usr/share/applications
mkdir -p /usr/share/icons/hicolor/16x16/apps
mkdir -p /usr/share/icons/hicolor/32x32/apps
mkdir -p /usr/share/icons/hicolor/48x48/apps
mkdir -p /usr/share/icons/hicolor/64x64/apps
mkdir -p /usr/share/icons/hicolor/128x128/apps
mkdir -p /usr/share/icons/hicolor/256x256/apps

# Skopiuj pliki aplikacji
echo "📦 Kopiowanie plików aplikacji..."
cp main.py gui.py downloader.py utils.py requirements.txt /usr/share/youtube-downloader/

# Utwórz skrypt uruchamiający
echo "🔧 Tworzenie skryptu uruchamiającego..."
cat > /usr/bin/youtube-downloader << 'PYTHON_SCRIPT'
#!/bin/bash
# Aktywuj środowisko wirtualne i uruchom aplikację
source /usr/share/youtube-downloader/venv/bin/activate
cd /usr/share/youtube-downloader
python main.py
PYTHON_SCRIPT

chmod +x /usr/bin/youtube-downloader

# Utwórz plik .desktop
echo "🖥️ Tworzenie launcher..."
cat > /usr/share/applications/youtube-downloader.desktop << 'DESKTOP_ENTRY'
[Desktop Entry]
Version=1.0
Type=Application
Name=YouTube Downloader
Comment=Download videos from YouTube with GUI
Exec=youtube-downloader
Icon=youtube-downloader
Terminal=false
Categories=AudioVideo;Video;Network;
DESKTOP_ENTRY

# Skopiuj ikony
echo "🎨 Kopiowanie ikon..."
cp icons/youtube-downloader-16.png /usr/share/icons/hicolor/16x16/apps/youtube-downloader.png
cp icons/youtube-downloader-32.png /usr/share/icons/hicolor/32x32/apps/youtube-downloader.png
cp icons/youtube-downloader-48.png /usr/share/icons/hicolor/48x48/apps/youtube-downloader.png
cp icons/youtube-downloader-64.png /usr/share/icons/hicolor/64x64/apps/youtube-downloader.png
cp icons/youtube-downloader-128.png /usr/share/icons/hicolor/128x128/apps/youtube-downloader.png
cp icons/youtube-downloader-256.png /usr/share/icons/hicolor/256x256/apps/youtube-downloader.png

# Utwórz środowisko wirtualne dla aplikacji
echo "🐍 Tworzenie środowiska wirtualnego..."
python3 -m venv /usr/share/youtube-downloader/venv

# Zainstaluj zależności w środowisku wirtualnym
echo "📚 Instalowanie zależności w środowisku wirtualnym..."
/usr/share/youtube-downloader/venv/bin/pip install yt-dlp

# Usuń stary plik log z katalogu aplikacji (jeśli istnieje)
echo "🧹 Czyszczenie starych plików..."
rm -f /usr/share/youtube-downloader/youtube_downloader.log

echo "✅ Instalacja zakończona!"
echo "🚀 Uruchom aplikację: youtube-downloader"
echo "📱 Lub znajdź w menu aplikacji"
echo "📝 Logi będą zapisywane w: ~/.youtube-downloader/youtube_downloader.log"
