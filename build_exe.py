#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXEビルドスクリプト
PyInstallerを使用してWindows用の実行ファイルを作成します
"""

import os
import sys
import subprocess

def build_exe():
    """EXEファイルをビルド"""

    print("=" * 60)
    print("トレーニングメニューアプリ - EXEビルド")
    print("=" * 60)

    # PyInstallerのオプション
    options = [
        'pyinstaller',
        '--onefile',  # 単一の実行ファイルとして作成
        '--windowed',  # コンソールウィンドウを表示しない（GUIアプリ用）
        '--name=TrainingMenuApp',  # 実行ファイル名
        '--add-data=requirements.txt;.',  # 依存関係ファイルを含める（Windowsの場合）
        # '--icon=icon.ico',  # アイコンファイルがあれば指定
        'training_menu_app.py'
    ]

    # Linuxの場合はセパレータを変更
    if sys.platform != 'win32':
        options = [opt.replace(';', ':') if ';' in opt else opt for opt in options]

    print("\nビルドオプション:")
    print(' '.join(options))
    print()

    try:
        # PyInstallerを実行
        result = subprocess.run(options, check=True)

        print("\n" + "=" * 60)
        print("ビルド成功！")
        print("=" * 60)
        print("\n実行ファイルは dist/TrainingMenuApp.exe に作成されました")
        print("※ EXEファイルと同じディレクトリにPDFファイルを配置してください")
        print()

    except subprocess.CalledProcessError as e:
        print(f"\nエラー: ビルドに失敗しました")
        print(f"詳細: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\nエラー: PyInstallerがインストールされていません")
        print("pip install pyinstaller を実行してください")
        sys.exit(1)

if __name__ == "__main__":
    build_exe()
