"""
EXE化ビルドスクリプト
PyInstallerを使用してWindowsの実行可能ファイルを生成
"""

import PyInstaller.__main__
import os
import sys

def build_exe():
    """EXEファイルをビルド"""

    # ビルドオプション
    options = [
        'src/main_gui.py',  # メインスクリプト
        '--name=PostureEvaluation',  # 実行ファイル名
        '--onefile',  # 単一の実行ファイルとして出力
        '--windowed',  # コンソールウィンドウを表示しない（GUIアプリ）
        '--icon=assets/icon.ico',  # アイコン（ある場合）
        '--add-data=src;src',  # srcディレクトリを含める

        # 必要なモジュールを明示的に指定
        '--hidden-import=customtkinter',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=mediapipe',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=reportlab',

        # MediaPipeのデータファイルを含める
        '--collect-data=mediapipe',
        '--collect-binaries=mediapipe',

        # CustomTkinterのデータファイルを含める
        '--collect-data=customtkinter',

        # 一時ファイルを削除
        '--clean',

        # UPXによる圧縮（オプション、サイズ削減）
        # '--upx-dir=path/to/upx',  # UPXがインストールされている場合
    ]

    print("=" * 60)
    print("姿勢評価システム - EXEビルド開始")
    print("=" * 60)
    print()
    print("ビルドオプション:")
    for opt in options:
        print(f"  {opt}")
    print()
    print("ビルドを開始します...")
    print()

    try:
        # PyInstallerを実行
        PyInstaller.__main__.run(options)

        print()
        print("=" * 60)
        print("✅ ビルドが完了しました！")
        print("=" * 60)
        print()
        print("実行ファイルの場所:")
        print(f"  dist/PostureEvaluation.exe")
        print()
        print("注意事項:")
        print("  - 初回起動時は、Windows Defenderの警告が表示される場合があります")
        print("  - MediaPipeの初期化に数秒かかる場合があります")
        print("  - 日本語フォントが必要な場合は、システムにインストールしてください")
        print()

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ビルドエラー")
        print("=" * 60)
        print(f"エラー: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
