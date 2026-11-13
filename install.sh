#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
if command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed python python-pyqt6 python-requests python-beautifulsoup4 gcc
elif command -v apt >/dev/null 2>&1; then
    sudo apt update && sudo apt install -y python3 python3-pyqt6 python3-requests python3-bs4 g++
fi
g++ -O3 -shared -fPIC "$DIR/cpp_core/image_cache.cpp" -o "$DIR/cpp_core/libfasi_core.so" 2>/dev/null || true
echo "Готово! Запускайте: python3 main.py"
