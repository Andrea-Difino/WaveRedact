# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sysconfig
import os
import glob

datas_gliner, binaries_gliner, hiddenimports_gliner = collect_all('gliner2')
datas_quest, binaries_quest, hiddenimports_quest = collect_all('questionary')

custom_datas = [
    ('prompts.yaml', '.')
]

search_paths = [sysconfig.get_path('platlib'), sysconfig.get_path('purelib')]
core_binaries = []

for spath in set(search_paths):
    if spath and os.path.exists(spath):
        for ext in ['*.pyd', '*.so']:
            pattern = os.path.join(spath, f'waveredact_core*{ext}')
            matches = glob.glob(pattern)
            for match in matches:
                core_binaries.append((match, '.'))

a = Analysis(
    ['cli/main.py'],
    pathex=[],
    binaries=binaries_gliner + core_binaries,
    datas=custom_datas + datas_gliner,
    hiddenimports=hiddenimports_gliner + hiddenimports_quest + ['peft'],
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