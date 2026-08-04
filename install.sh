#!/usr/bin/env bash
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
BIN="/usr/local/bin"

if [ "$(id -u)" -ne 0 ]; then
    exec sudo "$REPO/install.sh" "$@"
fi

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
chmod 755 "$BIN/uniland"

echo "Готово: $BIN/uniland"
echo "Теперь просто: uniland run script.uni"
echo "Картинки без установки работают для png/gif; для jpg/webp: pip install Pillow (или используй GIF)."
