#!/bin/sh
# DeckForge - Presentation Builder
# macOS / Linux launcher (cross-platform equivalent of start.bat)
#
#   ./start.sh          start on the default port 8420
#   ./start.sh 9000     start on port 9000
#
set -e

cd "$(dirname "$0")"

# --- pick a Python interpreter -------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "ERROR: Python 3 was not found on your PATH."
    echo "Install it first:"
    echo "  macOS    brew install python3"
    echo "  Debian   sudo apt install python3"
    echo "  Fedora   sudo dnf install python3"
    echo "  Arch     sudo pacman -S python"
    echo "or download it from https://www.python.org/downloads/"
    exit 1
fi

"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' || {
    echo "ERROR: Python 3.8 or newer is required (found $($PY --version 2>&1))."
    exit 1
}

# --- port -----------------------------------------------------------------
PORT="${1:-${PORT:-8420}}"

# --- open a browser once the server is up (best effort) -------------------
(
    i=0
    while [ "$i" -lt 10 ]; do
        sleep 0.5
        if "$PY" -c "import socket,sys; s=socket.socket(); sys.exit(0 if s.connect_ex(('127.0.0.1',$PORT))==0 else 1)" 2>/dev/null; then
            URL="http://127.0.0.1:${PORT}/"
            if command -v open >/dev/null 2>&1; then open "$URL"; break; fi
            if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; break; fi
            if command -v wslview >/dev/null 2>&1; then wslview "$URL"; break; fi
            break
        fi
        i=$((i + 1))
    done
) >/dev/null 2>&1 &

echo "DeckForge starting on http://127.0.0.1:${PORT}/  (press Ctrl+C to stop)"
exec "$PY" server.py --port "$PORT"
