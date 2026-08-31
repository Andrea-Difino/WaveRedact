# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas_gliner, binaries_gliner, hiddenimports_gliner = collect_all('gliner2')
datas_quest, binaries_quest, hiddenimports_quest = collect_all('questionary')
datas_core, binaries_core, hiddenimports_core = collect_all('waveredact_core')

custom_datas = [
    ('prompts.yaml', '.')
]

a = Analysis(
    ['cli/main.py'],
    pathex=[],
    binaries=binaries_gliner + binaries_core,
    datas=custom_datas + datas_gliner + datas_core,
    hiddenimports=hiddenimports_gliner + hiddenimports_quest + hiddenimports_core + ['peft'],
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