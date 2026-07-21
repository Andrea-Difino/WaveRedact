# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas_gliner, binaries_gliner, hiddenimports_gliner = collect_all('gliner2')

custom_datas = [
    ('prompts.yaml', '.'),
    ('.env', '.')
]

a = Analysis(
    ['cli\\main.py'],
    pathex=[],
    binaries=binaries_gliner,
    datas=custom_datas + datas_gliner,
    hiddenimports=hiddenimports_gliner, 
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
    [],
    exclude_binaries=True,
    name='waveredact',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='waveredact',
)