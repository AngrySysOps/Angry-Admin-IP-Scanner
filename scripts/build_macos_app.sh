#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/macos"
DIST_DIR="$ROOT_DIR/dist/macos"
VENV_DIR="$BUILD_DIR/.venv"
APP_NAME="Angry Admin IP Scanner"
ZIP_NAME="AngryAdminIPScanner-macos.zip"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd python3
require_cmd ditto

rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt" pyinstaller

PYINSTALLER_ARGS=(
  --clean
  --windowed
  --name "$APP_NAME"
  --add-data "$ROOT_DIR/README.md:."
)

if [[ -f "$ROOT_DIR/icon.icns" ]]; then
  PYINSTALLER_ARGS+=(--icon "$ROOT_DIR/icon.icns")
elif [[ -f "$ROOT_DIR/icon.ico" ]]; then
  PYINSTALLER_ARGS+=(--icon "$ROOT_DIR/icon.ico")
fi

pyinstaller "${PYINSTALLER_ARGS[@]}" "$ROOT_DIR/ipscaner.py"
cp -R "$ROOT_DIR/dist/$APP_NAME.app" "$DIST_DIR/$APP_NAME.app"
ditto -c -k --sequesterRsrc --keepParent "$DIST_DIR/$APP_NAME.app" "$DIST_DIR/$ZIP_NAME"

echo "Created:"
echo "  $DIST_DIR/$APP_NAME.app"
echo "  $DIST_DIR/$ZIP_NAME"
