#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
if command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed python python-pyqt6 python-requests python-beautifulsoup4 gcc
elif command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y python3 python3-pyqt6 python3-requests python3-bs4 g++
fi
g++ -O3 -shared -fPIC "$DIR/cpp_core/image_cache.cpp" -o "$DIR/cpp_core/libfasi_core.so" 2>/dev/null || true
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"
ln -sf "$DIR/run.sh" "$HOME/.local/bin/fasi"
if [ -f "$DIR/assets/fasi.svg" ]; then
    cp -f "$DIR/assets/fasi.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/fasi.svg"
fi
cat << DESKTOP > "$HOME/.local/share/applications/fasi.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=FaSI (Fast Search Images)
GenericName=Desktop Image Search Overlay
Comment=Fast Desktop Image Search Overlay (Alt+Space)
Exec=$DIR/run.sh
Icon=fasi
Terminal=false
Categories=Utility;Graphics;Network;
DESKTOP
chmod +x "$HOME/.local/share/applications/fasi.desktop"
echo "Готово! Запускайте: ./run.sh или fasi"
