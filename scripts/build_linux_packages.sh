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
BIN_PATH="$ROOT_DIR/dist/$PYINSTALLER_NAME/$PYINSTALLER_NAME"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd python3
require_cmd dpkg-deb
require_cmd rpmbuild

rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR" "$APP_DIR/usr/lib/$APP_NAME" "$APP_DIR/usr/bin" "$APP_DIR/usr/share/applications" "$APP_DIR/usr/share/doc/$APP_NAME" "$BUILD_DIR/rpmbuild"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements.txt" pyinstaller
pyinstaller --clean "$ROOT_DIR/ipscaner.spec"

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
Depends: libgl1, libx11-6, libxext6, libxrender1, libxi6, libxkbcommon-x11-0, libfontconfig1
Installed-Size: $INSTALLED_SIZE
Description: Desktop IP scanner for subnet, range, and DNS discovery workflows.
EOF

dpkg-deb --build "$APP_DIR" "$DIST_DIR/${APP_NAME}_${VERSION}_${DEB_ARCH}.deb"

tar -C "$APP_DIR" -czf "$BUILD_DIR/rpmbuild/SOURCES/${APP_NAME}-${VERSION}.tar.gz" .
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
