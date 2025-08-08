#!/bin/bash
# Skrypt do automatycznej instalacji FFmpeg po zainstalowaniu YouTube Downloader

echo "🎬 YouTube Downloader - Instalacja FFmpeg"
echo "========================================="

# Czekaj na zwolnienie dpkg
echo "⏳ Oczekiwanie na zwolnienie systemu pakietów..."
for i in {1..60}; do
    if ! (fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 || fuser /var/lib/apt/lists/lock >/dev/null 2>&1); then
        echo "✅ System pakietów jest wolny"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo "❌ Timeout - system pakietów nadal zajęty"
        exit 1
    fi
done

# Instaluj FFmpeg
echo "🔄 Instalowanie FFmpeg..."
export DEBIAN_FRONTEND=noninteractive

if apt-get update -qq && apt-get install -y -qq ffmpeg; then
    echo "✅ FFmpeg został zainstalowany pomyślnie!"
    echo "🎉 YouTube Downloader ma teraz pełną funkcjonalność (konwersja MP3)"
    
    # Poinformuj użytkowników
    wall "✅ FFmpeg zainstalowany! YouTube Downloader ma teraz pełną funkcjonalność" 2>/dev/null || true
    
    # Usuń ten skrypt - już nie jest potrzebny
    rm -f "$0"
else
    echo "❌ Nie udało się zainstalować FFmpeg"
    echo "💡 Spróbuj ręcznie: sudo apt install ffmpeg"
    wall "❌ Instalacja FFmpeg nie powiodła się. Zainstaluj ręcznie: sudo apt install ffmpeg" 2>/dev/null || true
fi