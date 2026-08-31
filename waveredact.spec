# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import importlib.util

datas_gliner, binaries_gliner, hiddenimports_gliner = collect_all('gliner2')
datas_quest, binaries_quest, hiddenimports_quest = collect_all('questionary')

custom_datas = [
    ('prompts.yaml', '.')
]

core_spec = importlib.util.find_spec('waveredact_core')
if core_spec and core_spec.origin:
    core_binary = [(core_spec.origin, '.')]
    print(f"✅ Found Rust: {core_spec.origin}")
else:
    print("❌ ATTENTION: Module waveredact_core not found!")
    core_binary = []

a = Analysis(
    ['cli/main.py'],
    pathex=[],
    binaries=binaries_gliner + core_binary,
    datas=custom_datas + datas_gliner,
    hiddenimports=hiddenimports_gliner + hiddenimports_quest + ['peft', 'waveredact_core'],
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