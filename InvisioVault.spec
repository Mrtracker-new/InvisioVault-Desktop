# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\rolan\\Desktop\\RNR\\InvisioVault-v2\\invisiovault.py'],
    pathex=['C:\\Users\\rolan\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\\Lib\\site-packages', 'C:\\Users\\rolan/.local/lib/python3.12/site-packages'],
    binaries=[],
    datas=[('C:\\Users\\rolan\\Desktop\\RNR\\InvisioVault-v2\\history.json', '.')],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'sip'],
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
    name='InvisioVault',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\rolan\\Desktop\\RNR\\InvisioVault-v2\\InvisioVault.ico'],
)
