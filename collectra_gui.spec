# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for collectra_gui.

Builds a single-file executable that bundles:
- Python runtime
- All dependencies (pywebview, typer, pyyaml, rich)
- index.html frontend
"""
import sys
from pathlib import Path

block_cipher = None

# Determine platform-specific settings
if sys.platform == 'darwin':
    icon_file = None  # Add .icns file path if you have one
    console = False
elif sys.platform == 'win32':
    icon_file = None  # Add .ico file path if you have one
    console = False
else:  # Linux
    icon_file = None
    console = False

a = Analysis(
    ['collectra_gui/api.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('collectra_gui/index.html', '.'),
    ],
    hiddenimports=[
        'typer',
        'typer.main',
        'typer.core',
        'click',
        'rich',
        'rich.console',
        'rich.traceback',
        'yaml',
        'webview',
        'webview.platforms',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='collectra_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS app bundle (optional)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='CollectraGUI.app',
        icon=icon_file,
        bundle_identifier='com.collectra.gui',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '0.1.0',
        },
    )
