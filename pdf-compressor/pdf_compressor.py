#!/usr/bin/env python3
"""
PDF Compressor - PDFファイルを圧縮するGUIアプリケーション
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF
import os
import threading
from pathlib import Path
import tempfile


class PDFCompressor:
    """PDF圧縮処理を行うクラス"""

    # 圧縮レベルの定義（画像品質）
    COMPRESSION_LEVELS = {
        '低圧縮（高品質）': 90,
        '中圧縮（標準）': 70,
        '高圧縮（低品質）': 50,
        'カスタム': None
    }

    def __init__(self, input_path, quality=70):
        """
        Args:
            input_path (str): 入力PDFファイルのパス
            quality (int): 画像品質 (1-100)
        """
        self.input_path = input_path
        self.quality = quality

    def get_file_size(self, file_path):
        """ファイルサイズを取得（MB単位）"""
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb

    def compress(self, output_path, progress_callback=None):
        """
        PDFを圧縮

        Args:
            output_path (str): 出力PDFファイルのパス
            progress_callback (callable): 進捗コールバック関数

        Returns:
            tuple: (成功フラグ, メッセージ)
        """
        try:
            doc = fitz.open(self.input_path)
            total_pages = len(doc)

            # 新しいPDFを作成
            output_doc = fitz.open()

            for page_num in range(total_pages):
                if progress_callback:
                    progress_callback(page_num + 1, total_pages)

                page = doc[page_num]

                # ページを画像としてレンダリング
                mat = fitz.Matrix(2.0, 2.0)  # 解像度を2倍に（144 DPI）
                pix = page.get_pixmap(matrix=mat)

                # 画像を圧縮
                img_data = pix.tobytes("jpeg", jpg_quality=self.quality)

                # 新しいページを作成
                new_page = output_doc.new_page(width=page.rect.width, height=page.rect.height)

                # 画像をページに挿入
                img_rect = new_page.rect
                new_page.insert_image(img_rect, stream=img_data)

            # 保存オプション
            output_doc.save(
                output_path,
                garbage=4,  # 最大限のガベージコレクション
                deflate=True,  # 圧縮を有効化
                clean=True  # 不要な情報を削除
            )

            output_doc.close()
            doc.close()

            original_size = self.get_file_size(self.input_path)
            compressed_size = self.get_file_size(output_path)
            reduction = ((original_size - compressed_size) / original_size) * 100

            message = f"圧縮完了！\n"
            message += f"元のサイズ: {original_size:.2f} MB\n"
            message += f"圧縮後: {compressed_size:.2f} MB\n"
            message += f"削減率: {reduction:.1f}%"

            return True, message

        except Exception as e:
            return False, f"エラーが発生しました: {str(e)}"

    def estimate_size(self):
        """
        圧縮後のファイルサイズを推定

        Returns:
            float: 推定サイズ（MB）
        """
        try:
            # 一時ファイルを作成してサイズを推定
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            doc = fitz.open(self.input_path)

            # 最初の3ページまたは全ページの10%をサンプリング
            sample_pages = min(3, max(1, len(doc) // 10))
            total_pages = len(doc)

            # 新しいPDFを作成（サンプル用）
            output_doc = fitz.open()

            for page_num in range(sample_pages):
                page = doc[page_num]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("jpeg", jpg_quality=self.quality)

                new_page = output_doc.new_page(width=page.rect.width, height=page.rect.height)
                img_rect = new_page.rect
                new_page.insert_image(img_rect, stream=img_data)

            output_doc.save(tmp_path, garbage=4, deflate=True, clean=True)
            output_doc.close()
            doc.close()

            # サンプルサイズから全体を推定
            sample_size = self.get_file_size(tmp_path)
            estimated_size = (sample_size / sample_pages) * total_pages

            # 一時ファイルを削除
            os.unlink(tmp_path)

            return estimated_size

        except Exception as e:
            print(f"推定エラー: {e}")
            return 0


class PDFCompressorGUI:
    """PDF圧縮アプリケーションのGUIクラス"""

    def __init__(self, root):
        self.root = root
        self.root.title("PDF圧縮ツール")
        self.root.geometry("700x550")
        self.root.resizable(False, False)

        self.input_file = None
        self.output_file = None
        self.estimated_size = None

        self.setup_ui()

    def setup_ui(self):
        """UIをセットアップ"""

        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(
            main_frame,
            text="PDF圧縮ツール",
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # ファイル選択エリア
        file_frame = ttk.LabelFrame(main_frame, text="ファイル選択", padding="10")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        # ドラッグ&ドロップエリア
        self.drop_label = ttk.Label(
            file_frame,
            text="PDFファイルをここにドラッグ&ドロップ\nまたはクリックしてファイルを選択",
            relief="solid",
            borderwidth=2,
            padding=40,
            anchor="center",
            justify="center"
        )
        self.drop_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        # ドラッグ&ドロップの設定
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_label.bind('<Button-1>', self.browse_file)

        # ファイル情報表示
        self.file_info_label = ttk.Label(file_frame, text="", foreground="blue")
        self.file_info_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))

        # 圧縮設定エリア
        settings_frame = ttk.LabelFrame(main_frame, text="圧縮設定", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        # 圧縮レベル選択
        ttk.Label(settings_frame, text="圧縮レベル:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.compression_var = tk.StringVar(value='中圧縮（標準）')
        compression_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.compression_var,
            values=list(PDFCompressor.COMPRESSION_LEVELS.keys()),
            state='readonly',
            width=25
        )
        compression_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        compression_combo.bind('<<ComboboxSelected>>', self.on_compression_change)

        # カスタム品質スライダー
        self.quality_frame = ttk.Frame(settings_frame)
        self.quality_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.quality_frame, text="画像品質:").grid(row=0, column=0, sticky=tk.W)

        self.quality_var = tk.IntVar(value=70)
        self.quality_scale = ttk.Scale(
            self.quality_frame,
            from_=10,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.quality_var,
            command=self.on_quality_change,
            state='disabled'
        )
        self.quality_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))

        self.quality_label = ttk.Label(self.quality_frame, text="70")
        self.quality_label.grid(row=0, column=2, sticky=tk.W)

        self.quality_frame.columnconfigure(1, weight=1)

        # プレビューエリア
        preview_frame = ttk.LabelFrame(main_frame, text="サイズプレビュー", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.original_size_label = ttk.Label(preview_frame, text="元のサイズ: --")
        self.original_size_label.grid(row=0, column=0, sticky=tk.W, pady=2)

        self.estimated_size_label = ttk.Label(preview_frame, text="推定圧縮後サイズ: --")
        self.estimated_size_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        self.reduction_label = ttk.Label(preview_frame, text="推定削減率: --")
        self.reduction_label.grid(row=2, column=0, sticky=tk.W, pady=2)

        # 進捗バー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))

        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.grid(row=5, column=0, columnspan=2)

        # ボタンエリア
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(15, 0))

        self.compress_button = ttk.Button(
            button_frame,
            text="圧縮開始",
            command=self.start_compression,
            state='disabled'
        )
        self.compress_button.grid(row=0, column=0, padx=5)

        ttk.Button(
            button_frame,
            text="クリア",
            command=self.clear_all
        ).grid(row=0, column=1, padx=5)

        # カラム設定
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def on_drop(self, event):
        """ドラッグ&ドロップ時の処理"""
        file_path = event.data
        # 波括弧を削除（Windows）
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]

        self.load_file(file_path)

    def browse_file(self, event=None):
        """ファイル選択ダイアログを開く"""
        file_path = filedialog.askopenfilename(
            title="PDFファイルを選択",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """ファイルを読み込む"""
        if not file_path.lower().endswith('.pdf'):
            messagebox.showerror("エラー", "PDFファイルを選択してください")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("エラー", "ファイルが存在しません")
            return

        self.input_file = file_path

        # ファイル名を表示
        file_name = os.path.basename(file_path)
        self.file_info_label.config(text=f"選択: {file_name}")

        # 元のサイズを表示
        compressor = PDFCompressor(file_path)
        original_size = compressor.get_file_size(file_path)
        self.original_size_label.config(text=f"元のサイズ: {original_size:.2f} MB")

        # サイズ推定を更新
        self.update_size_estimation()

        # 圧縮ボタンを有効化
        self.compress_button.config(state='normal')

    def on_compression_change(self, event=None):
        """圧縮レベル変更時の処理"""
        level = self.compression_var.get()

        if level == 'カスタム':
            self.quality_scale.config(state='normal')
        else:
            self.quality_scale.config(state='disabled')
            quality = PDFCompressor.COMPRESSION_LEVELS[level]
            self.quality_var.set(quality)
            self.quality_label.config(text=str(quality))

        # サイズ推定を更新
        if self.input_file:
            self.update_size_estimation()

    def on_quality_change(self, event=None):
        """品質スライダー変更時の処理"""
        quality = int(self.quality_var.get())
        self.quality_label.config(text=str(quality))

        # サイズ推定を更新
        if self.input_file:
            self.update_size_estimation()

    def update_size_estimation(self):
        """サイズ推定を更新"""
        if not self.input_file:
            return

        def estimate():
            quality = int(self.quality_var.get())
            compressor = PDFCompressor(self.input_file, quality)

            # 推定サイズを計算
            estimated = compressor.estimate_size()
            original = compressor.get_file_size(self.input_file)
            reduction = ((original - estimated) / original) * 100 if original > 0 else 0

            # UIを更新（メインスレッドで）
            self.root.after(0, lambda: self._update_estimation_labels(estimated, reduction))

        # バックグラウンドスレッドで実行
        thread = threading.Thread(target=estimate, daemon=True)
        thread.start()

    def _update_estimation_labels(self, estimated_size, reduction):
        """推定ラベルを更新"""
        self.estimated_size_label.config(text=f"推定圧縮後サイズ: {estimated_size:.2f} MB")
        self.reduction_label.config(
            text=f"推定削減率: {reduction:.1f}%",
            foreground="green" if reduction > 0 else "red"
        )

    def start_compression(self):
        """圧縮を開始"""
        if not self.input_file:
            return

        # 出力ファイル名を生成
        input_path = Path(self.input_file)
        output_path = input_path.parent / f"{input_path.stem}_compressed.pdf"

        # 既存ファイルがある場合は確認
        if output_path.exists():
            result = messagebox.askyesno(
                "確認",
                f"ファイル '{output_path.name}' は既に存在します。\n上書きしますか？"
            )
            if not result:
                return

        # 圧縮実行
        self.compress_button.config(state='disabled')
        self.progress_label.config(text="圧縮中...")

        quality = int(self.quality_var.get())
        compressor = PDFCompressor(self.input_file, quality)

        def compress_thread():
            def progress_callback(current, total):
                progress = (current / total) * 100
                self.root.after(0, lambda: self.progress_var.set(progress))
                self.root.after(0, lambda: self.progress_label.config(
                    text=f"圧縮中... ({current}/{total} ページ)"
                ))

            success, message = compressor.compress(str(output_path), progress_callback)

            self.root.after(0, lambda: self._compression_complete(success, message, output_path))

        thread = threading.Thread(target=compress_thread, daemon=True)
        thread.start()

    def _compression_complete(self, success, message, output_path):
        """圧縮完了時の処理"""
        self.progress_var.set(0)
        self.progress_label.config(text="")
        self.compress_button.config(state='normal')

        if success:
            messagebox.showinfo("完了", message)

            # 出力フォルダを開くか確認
            result = messagebox.askyesno(
                "完了",
                "圧縮されたファイルのフォルダを開きますか？"
            )
            if result:
                folder = os.path.dirname(output_path)
                if os.name == 'nt':  # Windows
                    os.startfile(folder)
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'xdg-open "{folder}"' if os.uname().sysname != 'Darwin' else f'open "{folder}"')
        else:
            messagebox.showerror("エラー", message)

    def clear_all(self):
        """すべてをクリア"""
        self.input_file = None
        self.file_info_label.config(text="")
        self.original_size_label.config(text="元のサイズ: --")
        self.estimated_size_label.config(text="推定圧縮後サイズ: --")
        self.reduction_label.config(text="推定削減率: --")
        self.progress_var.set(0)
        self.progress_label.config(text="")
        self.compress_button.config(state='disabled')
        self.compression_var.set('中圧縮（標準）')
        self.quality_var.set(70)
        self.quality_label.config(text="70")
        self.quality_scale.config(state='disabled')


def main():
    """メイン関数"""
    root = TkinterDnD.Tk()
    app = PDFCompressorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
