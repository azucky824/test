# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Posture Evaluation System
より詳細なビルド設定
"""

block_cipher = None

a = Analysis(
    ['src/main_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/*.py', 'src'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'mediapipe',
        'cv2',
        'numpy',
        'reportlab',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.pdfgen',
        'reportlab.platypus',
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

# MediaPipeのデータを収集
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
mediapipe_datas = collect_data_files('mediapipe')
mediapipe_binaries = collect_dynamic_libs('mediapipe')

a.datas += mediapipe_datas
a.binaries += mediapipe_binaries

# CustomTkinterのデータを収集
customtkinter_datas = collect_data_files('customtkinter')
a.datas += customtkinter_datas

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PostureEvaluation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIアプリケーションなのでコンソールは非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

import os
