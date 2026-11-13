#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$DIR"

# 1. Проверяем системный /usr/bin/python3 первым (обход mise / pyenv / asdf)
for PY in /usr/bin/python3 "$DIR/.venv/bin/python" "$DIR/venv/bin/python" python3; do
    if command -v "$PY" >/dev/null 2>&1 && "$PY" -c "import PyQt6, bs4, requests" >/dev/null 2>&1; then
        exec "$PY" "$DIR/main.py" "$@"
    fi
done

echo "Зависимости PyQt6/bs4 не найдены! Запустите ./install.sh или установите:"
echo "  Arch Linux:    sudo pacman -S python python-pyqt6 python-requests python-beautifulsoup4"
echo "  Ubuntu/Debian: sudo apt install python3-pyqt6 python3-requests python3-bs4"
exit 1
