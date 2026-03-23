@echo off
setlocal

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean ipscaner.spec

echo.
echo Build complete. Use this file:
echo   dist\AngryAdminIPScanner.exe
