#!/usr/bin/env bash
# Install codex-switch into a directory on PATH (default ~/.local/bin).
set -euo pipefail

DEST="${1:-$HOME/.local/bin}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/codex-switch"

mkdir -p "$DEST"
cp "$SRC" "$DEST/codex-switch"
chmod +x "$DEST/codex-switch"

echo "Installed codex-switch -> $DEST/codex-switch"
if ! command -v codex-switch >/dev/null 2>&1; then
  echo "NOTE: $DEST is not on your PATH. Add it, e.g.:"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
