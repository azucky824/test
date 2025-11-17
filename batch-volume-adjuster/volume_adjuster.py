#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音量一括調整アプリケーション
複数の動画・音声ファイルの音量を一括で調整します
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from typing import List

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("Warning: tkinterdnd2 is not installed. Drag and drop will not work.")

try:
    from pydub import AudioSegment
    from pydub.utils import mediainfo
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False
    print("Warning: pydub is not installed. Audio processing will not work.")


class VolumeAdjusterApp:
    """音量調整アプリケーションのメインクラス"""

    def __init__(self, root):
        self.root = root
        self.root.title("音量一括調整ツール")
        self.root.geometry("800x600")

        self.files = []
        self.output_dir = None
        self.processing = False

        self.setup_ui()

    def setup_ui(self):
        """UIのセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # タイトル
        title_label = ttk.Label(
            main_frame,
            text="音量一括調整ツール",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=10)

        # ファイル選択エリア
        file_frame = ttk.LabelFrame(main_frame, text="ファイル選択", padding="10")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)

        # ドラッグアンドドロップエリア
        if HAS_DND:
            drop_label = ttk.Label(
                file_frame,
                text="ここにファイルをドラッグ&ドロップ\nまたは下のボタンでファイルを選択",
                background="#e0e0e0",
                relief="groove",
                padding=20,
                justify="center"
            )
            drop_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
            drop_label.drop_target_register(DND_FILES)
            drop_label.dnd_bind('<<Drop>>', self.on_drop)
        else:
            drop_label = ttk.Label(
                file_frame,
                text="下のボタンでファイルを選択してください\n(ドラッグ&ドロップ機能は利用できません)",
                background="#e0e0e0",
                relief="groove",
                padding=20,
                justify="center"
            )
            drop_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # ファイル選択ボタン
        btn_frame = ttk.Frame(file_frame)
        btn_frame.grid(row=1, column=0, pady=5)

        ttk.Button(
            btn_frame,
            text="ファイルを追加",
            command=self.add_files
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="すべてクリア",
            command=self.clear_files
        ).pack(side=tk.LEFT, padx=5)

        # ファイルリスト
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # スクロールバー付きリストボックス
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED
        )
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.file_listbox.yview)

        # 設定エリア
        settings_frame = ttk.LabelFrame(main_frame, text="音量調整設定", padding="10")
        settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        settings_frame.columnconfigure(1, weight=1)

        # 音量調整スライダー
        ttk.Label(settings_frame, text="音量調整 (dB):").grid(row=0, column=0, sticky=tk.W)

        slider_frame = ttk.Frame(settings_frame)
        slider_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10)
        slider_frame.columnconfigure(0, weight=1)

        self.volume_var = tk.DoubleVar(value=0)
        self.volume_slider = ttk.Scale(
            slider_frame,
            from_=-20,
            to=20,
            variable=self.volume_var,
            orient=tk.HORIZONTAL,
            command=self.on_volume_change
        )
        self.volume_slider.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.volume_label = ttk.Label(slider_frame, text="0.0 dB")
        self.volume_label.grid(row=0, column=1, padx=5)

        # 出力ディレクトリ選択
        ttk.Label(settings_frame, text="出力先:").grid(row=1, column=0, sticky=tk.W, pady=5)

        output_frame = ttk.Frame(settings_frame)
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        output_frame.columnconfigure(0, weight=1)

        self.output_var = tk.StringVar(value="元のファイルと同じ場所")
        ttk.Entry(
            output_frame,
            textvariable=self.output_var,
            state="readonly"
        ).grid(row=0, column=0, sticky=(tk.W, tk.E))

        ttk.Button(
            output_frame,
            text="選択",
            command=self.select_output_dir
        ).grid(row=0, column=1, padx=5)

        # 出力形式
        ttk.Label(settings_frame, text="出力形式:").grid(row=2, column=0, sticky=tk.W, pady=5)

        format_frame = ttk.Frame(settings_frame)
        format_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

        self.format_var = tk.StringVar(value="same")
        ttk.Radiobutton(
            format_frame,
            text="元と同じ",
            variable=self.format_var,
            value="same"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            format_frame,
            text="MP3",
            variable=self.format_var,
            value="mp3"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            format_frame,
            text="WAV",
            variable=self.format_var,
            value="wav"
        ).pack(side=tk.LEFT, padx=5)

        # 実行ボタンエリア
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, pady=10)

        self.process_btn = ttk.Button(
            action_frame,
            text="音量調整を実行",
            command=self.process_files,
            state=tk.DISABLED
        )
        self.process_btn.pack()

        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)

        # ステータスラベル
        self.status_var = tk.StringVar(value="ファイルを追加してください")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=6, column=0, pady=5)

    def on_volume_change(self, value):
        """音量スライダーの変更イベント"""
        self.volume_label.config(text=f"{float(value):.1f} dB")

    def on_drop(self, event):
        """ドラッグ&ドロップイベント"""
        files = self.root.tk.splitlist(event.data)
        self.add_files_from_list(files)

    def add_files(self):
        """ファイル選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="音声・動画ファイルを選択",
            filetypes=[
                ("対応ファイル", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac *.mp4 *.avi *.mkv *.mov"),
                ("音声ファイル", "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"),
                ("動画ファイル", "*.mp4 *.avi *.mkv *.mov"),
                ("すべてのファイル", "*.*")
            ]
        )
        if files:
            self.add_files_from_list(files)

    def add_files_from_list(self, files: List[str]):
        """ファイルリストに追加"""
        for file_path in files:
            # 中括弧を含むパスの処理（tkinterのバグ回避）
            file_path = file_path.strip('{}')
            if os.path.isfile(file_path) and file_path not in self.files:
                self.files.append(file_path)
                self.file_listbox.insert(tk.END, os.path.basename(file_path))

        # ファイルが追加されたらボタンを有効化
        if self.files:
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set(f"{len(self.files)}個のファイルが選択されています")

    def clear_files(self):
        """ファイルリストをクリア"""
        self.files = []
        self.file_listbox.delete(0, tk.END)
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set("ファイルを追加してください")
        self.progress_var.set(0)

    def select_output_dir(self):
        """出力ディレクトリ選択"""
        directory = filedialog.askdirectory(title="出力先ディレクトリを選択")
        if directory:
            self.output_dir = directory
            self.output_var.set(directory)

    def process_files(self):
        """ファイルの一括処理"""
        if not HAS_PYDUB:
            messagebox.showerror(
                "エラー",
                "pydubがインストールされていません。\nrequirements.txtを使用してインストールしてください。"
            )
            return

        if not self.files:
            messagebox.showwarning("警告", "処理するファイルがありません")
            return

        # 別スレッドで処理を実行
        self.processing = True
        self.process_btn.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._process_files_thread)
        thread.daemon = True
        thread.start()

    def _process_files_thread(self):
        """ファイル処理のスレッド"""
        total = len(self.files)
        successful = 0
        failed = []

        volume_change = self.volume_var.get()
        output_format = self.format_var.get()

        for i, file_path in enumerate(self.files):
            try:
                # ステータス更新
                self.status_var.set(f"処理中: {os.path.basename(file_path)} ({i+1}/{total})")

                # 音声/動画ファイルを読み込み
                audio = AudioSegment.from_file(file_path)

                # 音量を調整
                adjusted_audio = audio + volume_change

                # 出力ファイル名を決定
                file_name = Path(file_path).stem

                # 出力形式を決定
                if output_format == "same":
                    ext = Path(file_path).suffix
                    output_ext = ext if ext else ".mp3"
                else:
                    output_ext = f".{output_format}"

                # 出力先ディレクトリを決定
                if self.output_dir:
                    output_path = os.path.join(
                        self.output_dir,
                        f"{file_name}_adjusted{output_ext}"
                    )
                else:
                    output_path = os.path.join(
                        os.path.dirname(file_path),
                        f"{file_name}_adjusted{output_ext}"
                    )

                # ファイルを保存
                adjusted_audio.export(
                    output_path,
                    format=output_ext.lstrip('.')
                )

                successful += 1

            except Exception as e:
                failed.append((os.path.basename(file_path), str(e)))
                print(f"Error processing {file_path}: {e}")

            # プログレスバー更新
            progress = ((i + 1) / total) * 100
            self.progress_var.set(progress)

        # 処理完了
        self.processing = False
        self.process_btn.config(state=tk.NORMAL)

        # 結果表示
        if failed:
            error_msg = f"処理完了: {successful}/{total}個成功\n\n失敗したファイル:\n"
            for fname, error in failed:
                error_msg += f"- {fname}: {error}\n"
            messagebox.showwarning("処理完了（一部エラー）", error_msg)
        else:
            messagebox.showinfo("処理完了", f"{successful}個のファイルを正常に処理しました")

        self.status_var.set(f"処理完了: {successful}/{total}個成功")


def check_dependencies():
    """依存関係のチェック"""
    errors = []

    if not HAS_DND:
        errors.append("- tkinterdnd2 (ドラッグ&ドロップ機能に必要)")

    if not HAS_PYDUB:
        errors.append("- pydub (音声処理に必要)")

    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode != 0:
            errors.append("- ffmpeg (音声・動画処理に必要)")
    except FileNotFoundError:
        errors.append("- ffmpeg (音声・動画処理に必要)")

    if errors:
        print("=" * 50)
        print("警告: 以下の依存関係が不足しています:")
        for error in errors:
            print(error)
        print("\nインストール方法:")
        print("pip install -r requirements.txt")
        print("ffmpegのインストール:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: https://ffmpeg.org/download.html")
        print("=" * 50)


def main():
    """メイン関数"""
    check_dependencies()

    # ウィンドウ作成
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = VolumeAdjusterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
