#!/usr/bin/env python3
"""
遅延ビデオ再生アプリケーション - メインエントリーポイント

カメラからの映像をリアルタイムで取得し、指定した秒数遅れて再生するアプリケーション
"""
import sys
import tkinter as tk
from gui_app import DelayedVideoApp


def main():
    """アプリケーションのメインエントリーポイント"""
    try:
        root = tk.Tk()
        app = DelayedVideoApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nアプリケーションを終了します...")
        sys.exit(0)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
