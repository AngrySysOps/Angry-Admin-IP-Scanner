#!/usr/bin/env bash
set -euo pipefail

APP_NAME="angry-admin-ipscanner"
VERSION="1.0"
RELEASE="1"
ARCH="x86_64"
DEB_ARCH="amd64"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/linux"
DIST_DIR="$ROOT_DIR/dist/linux"
APP_DIR="$BUILD_DIR/appdir"
VENV_DIR="$BUILD_DIR/.venv"
PYINSTALLER_NAME="AngryAdminIPScanner"
PYINSTALLER_OUTPUT="$ROOT_DIR/dist/$PYINSTALLER_NAME"
ALT_BIN_PATH="$ROOT_DIR/dist/$PYINSTALLER_NAME/$PYINSTALLER_NAME"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

resolve_binary_path() {
  if [[ -f "$PYINSTALLER_OUTPUT" ]]; then
    printf '%s\n' "$PYINSTALLER_OUTPUT"
    return 0
  fi
  if [[ -f "$ALT_BIN_PATH" ]]; then
    printf '%s\n' "$ALT_BIN_PATH"
    return 0
  fi
  echo "Unable to find packaged executable after PyInstaller build." >&2
  return 1
}

require_cmd python3
require_cmd dpkg-deb
require_cmd rpmbuild

rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p \
  "$BUILD_DIR" \
  "$DIST_DIR" \
  "$APP_DIR/usr/lib/$APP_NAME" \
  "$APP_DIR/usr/bin" \
  "$APP_DIR/usr/share/applications" \
  "$APP_DIR/usr/share/doc/$APP_NAME" \
  "$BUILD_DIR/rpmbuild"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt" pyinstaller
pyinstaller --clean "$ROOT_DIR/ipscaner.spec"

BIN_PATH="$(resolve_binary_path)"
install -m 755 "$BIN_PATH" "$APP_DIR/usr/lib/$APP_NAME/$APP_NAME"
ln -sf "../lib/$APP_NAME/$APP_NAME" "$APP_DIR/usr/bin/$APP_NAME"
install -m 644 "$ROOT_DIR/README.md" "$APP_DIR/usr/share/doc/$APP_NAME/README.md"
install -m 644 "$ROOT_DIR/packaging/linux/angry-admin-ipscanner.desktop" "$APP_DIR/usr/share/applications/angry-admin-ipscanner.desktop"
if [[ -f "$ROOT_DIR/icon.ico" ]]; then
  install -m 644 "$ROOT_DIR/icon.ico" "$APP_DIR/usr/lib/$APP_NAME/icon.ico"
fi

DEBIAN_DIR="$APP_DIR/DEBIAN"
mkdir -p "$DEBIAN_DIR"
INSTALLED_SIZE="$(du -sk "$APP_DIR/usr" | awk '{print $1}')"
cat > "$DEBIAN_DIR/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: net
Priority: optional
Architecture: $DEB_ARCH
Maintainer: AngrySysOps
Depends: libgl1, libx11-6, libxext6, libxrender1, libxi6, libxkbcommon-x11-0, libfontconfig1, libpulse0, libxcb-xkb1, libxcb-render-util0, libxcb-keysyms1, libxcb-icccm4, libxcb-image0, libxcb-xinerama0, libxcb-shape0, libgstreamer1.0-0, libgstreamer-plugins-base1.0-0
Installed-Size: $INSTALLED_SIZE
Description: Desktop IP scanner for subnet, range, and DNS discovery workflows.
EOF

dpkg-deb --build "$APP_DIR" "$DIST_DIR/${APP_NAME}_${VERSION}_${DEB_ARCH}.deb"

tar --exclude="./DEBIAN" -C "$APP_DIR" -czf "$BUILD_DIR/rpmbuild/SOURCES/${APP_NAME}-${VERSION}.tar.gz" .
sed \
  -e "s|@ROOT_DIR@|$ROOT_DIR|g" \
  -e "s|@APP_NAME@|$APP_NAME|g" \
  -e "s|@VERSION@|$VERSION|g" \
  -e "s|@RELEASE@|$RELEASE|g" \
  "$ROOT_DIR/packaging/linux/angry-admin-ipscanner.spec.in" > "$BUILD_DIR/rpmbuild/SPECS/${APP_NAME}.spec"

rpmbuild --define "_topdir $BUILD_DIR/rpmbuild" -bb "$BUILD_DIR/rpmbuild/SPECS/${APP_NAME}.spec"
cp "$BUILD_DIR/rpmbuild/RPMS/$ARCH/${APP_NAME}-${VERSION}-${RELEASE}.$ARCH.rpm" "$DIST_DIR/${APP_NAME}-${VERSION}-${RELEASE}.$ARCH.rpm"

echo "Created:"
echo "  $DIST_DIR/${APP_NAME}_${VERSION}_${DEB_ARCH}.deb"
echo "  $DIST_DIR/${APP_NAME}-${VERSION}-${RELEASE}.$ARCH.rpm"
