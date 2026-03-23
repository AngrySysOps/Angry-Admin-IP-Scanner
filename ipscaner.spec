# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_dir = Path(SPECPATH)
icon_path = project_dir / 'icon.ico'
datas = []
exe_icon = None
if icon_path.exists():
    datas.append((str(icon_path), '.'))
    exe_icon = str(icon_path)

hiddenimports = [
    'dns',
    'dns.resolver',
    'dns.reversename',
]


a = Analysis(
    ['ipscaner.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AngryAdminIPScanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    icon=exe_icon,
)
