@echo off
setlocal

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --clean ipscaner.spec

echo.
echo Build complete. EXE output:
echo   dist\AngryAdminIPScanner\AngryAdminIPScanner.exe
