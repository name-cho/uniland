#!/usr/bin/env bash
# Устанавливает команду `uniland` без pip (Linux/macOS).
# Создаёт лаунчер в ~/.local/bin, который запускает `python -m uniland`
# с этим репозиторием в PYTHONPATH — работает из любого места.
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"

# найдём подходящий python
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo "Не найден python3. Установи Python 3.10+ и повтори." >&2
    exit 1
fi

cat > "$BIN/uniland" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$REPO:\$PYTHONPATH"
exec "$PY" -m uniland "\$@"
EOF
chmod +x "$BIN/uniland"

echo "Готово: $BIN/uniland"
case ":$PATH:" in
    *":$BIN:"*) echo "Теперь просто: uniland run script.uni" ;;
    *) echo "Добавь ~/.local/bin в PATH, например в ~/.bashrc:"
       echo '  export PATH="$HOME/.local/bin:$PATH"' ;;
esac
echo "Картинки без установки работают для png/gif; для jpg/webp: pip install Pillow (или используй GIF)."
