#!/bin/bash
# Build .deb from PyInstaller binary — self-contained, no Python dependency
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}  $1${NC}"; }
log_success() { echo -e "${GREEN}OK $1${NC}"; }
log_error()   { echo -e "${RED}!! $1${NC}"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BINARY="$PROJECT_ROOT/dist/youtube-downloader"
VERSION="${1:-$(python3 -c "from version import __version__; print(__version__)" 2>/dev/null || echo "1.2.0")}"
PACKAGE_NAME="youtube-downloader"
BUILD_DIR="$(mktemp -d -p /tmp ytdl-deb-XXXXXX)"
PKG_DIR="$BUILD_DIR/$PACKAGE_NAME"

trap "rm -rf $BUILD_DIR" EXIT

log_info "Building .deb v$VERSION from PyInstaller binary"
[ -f "$BINARY" ] || log_error "Binary not found at $BINARY — run 'pyinstaller youtube-downloader.spec --clean' first"

mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/doc/$PACKAGE_NAME"
for size in 16 32 48 64 128 256; do
    mkdir -p "$PKG_DIR/usr/share/icons/hicolor/${size}x${size}/apps"
done

cp "$BINARY" "$PKG_DIR/usr/bin/$PACKAGE_NAME"
chmod +x "$PKG_DIR/usr/bin/$PACKAGE_NAME"

if [ -d "$PROJECT_ROOT/icons" ]; then
    for size in 16 32 48 64 128 256; do
        src="$PROJECT_ROOT/icons/youtube-downloader-${size}.png"
        [ -f "$src" ] && cp "$src" "$PKG_DIR/usr/share/icons/hicolor/${size}x${size}/apps/youtube-downloader.png"
    done
fi

cat > "$PKG_DIR/usr/share/applications/$PACKAGE_NAME.desktop" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=YouTube Downloader
Comment=Download videos from YouTube
Comment[pl]=Pobieraj filmy z YouTube
Exec=youtube-downloader
Icon=youtube-downloader
Terminal=false
Categories=Network;Video;AudioVideo;
Keywords=youtube;download;video;mp4;mp3;
StartupNotify=true
DESKTOP

printf "youtube-downloader ($VERSION) stable; urgency=medium\n\n  * Release $VERSION\n\n -- Jerzy Maczewski <jerzymaczewski@gmail.com>  $(date -R)\n" \
  | gzip -9 > "$PKG_DIR/usr/share/doc/$PACKAGE_NAME/changelog.gz"

INSTALLED_SIZE=$(du -sk "$PKG_DIR/usr" | cut -f1)
cat > "$PKG_DIR/DEBIAN/control" <<CTRL
Package: $PACKAGE_NAME
Version: $VERSION
Architecture: amd64
Maintainer: Jerzy Maczewski <jerzymaczewski@gmail.com>
Installed-Size: $INSTALLED_SIZE
Recommends: ffmpeg
Section: utils
Priority: optional
Homepage: https://github.com/george7979/youtube-downloader
Description: YouTube Downloader - download videos from YouTube
 Self-contained binary. No Python or other runtime required.
CTRL

cd "$PKG_DIR"
find . -path './DEBIAN' -prune -o -type f -print0 | xargs -0 md5sum > DEBIAN/md5sums
cd "$PROJECT_ROOT"

fakeroot dpkg-deb --build "$PKG_DIR"
OUTPUT="${PACKAGE_NAME}_${VERSION}_amd64.deb"
mv "$BUILD_DIR/${PACKAGE_NAME}.deb" "$PROJECT_ROOT/$OUTPUT"

log_success "Built: $OUTPUT ($(ls -lh "$PROJECT_ROOT/$OUTPUT" | awk '{print $5}'))"
log_info "Install: sudo dpkg -i $OUTPUT"
