#!/usr/bin/env python3
"""
PDF OCR GUI Application
PDFファイルをドラッグ&ドロップでOCR処理するGUIアプリケーション
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import threading
from pathlib import Path


class PDFOCRApp:
    """PDF OCR GUIアプリケーション"""

    def __init__(self, root):
        self.root = root
        self.root.title("PDF OCR アプリケーション")
        self.root.geometry("900x700")

        # 処理中フラグ
        self.processing = False

        # UI構築
        self.setup_ui()

    def setup_ui(self):
        """UIコンポーネントのセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ドロップゾーン
        self.drop_zone = tk.Label(
            main_frame,
            text="PDFファイルをここにドラッグ&ドロップ\n\nまたはクリックしてファイルを選択",
            relief=tk.GROOVE,
            bg="#f0f0f0",
            font=("Arial", 14),
            height=5,
            cursor="hand2"
        )
        self.drop_zone.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        # ドラッグ&ドロップ設定
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_zone.bind('<Button-1>', self.on_click)

        # ファイルパス表示
        ttk.Label(main_frame, text="選択されたファイル:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar(value="なし")
        ttk.Label(main_frame, textvariable=self.file_path_var, foreground="blue").grid(
            row=1, column=1, sticky=tk.W, pady=5
        )

        # 言語選択
        lang_frame = ttk.Frame(main_frame)
        lang_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(lang_frame, text="OCR言語:").pack(side=tk.LEFT, padx=(0, 5))
        self.lang_var = tk.StringVar(value="jpn")
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["jpn", "eng", "jpn+eng"],
            state="readonly",
            width=15
        )
        lang_combo.pack(side=tk.LEFT)

        # OCR実行ボタン
        self.ocr_button = ttk.Button(
            main_frame,
            text="OCR実行",
            command=self.run_ocr,
            state=tk.DISABLED
        )
        self.ocr_button.grid(row=3, column=0, pady=10, sticky=tk.W)

        # 保存ボタン
        self.save_button = ttk.Button(
            main_frame,
            text="テキストを保存",
            command=self.save_text,
            state=tk.DISABLED
        )
        self.save_button.grid(row=3, column=1, pady=10, sticky=tk.W, padx=(10, 0))

        # プログレスバー
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # ステータスラベル
        self.status_var = tk.StringVar(value="PDFファイルをドロップしてください")
        ttk.Label(main_frame, textvariable=self.status_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        # 結果表示エリア
        ttk.Label(main_frame, text="OCR結果:").grid(row=6, column=0, sticky=tk.W, pady=(10, 5))

        self.result_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=("Arial", 10)
        )
        self.result_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # グリッドの重み設定（リサイズ対応）
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def on_click(self, event):
        """クリックでファイル選択ダイアログを開く"""
        if not self.processing:
            file_path = filedialog.askopenfilename(
                title="PDFファイルを選択",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if file_path:
                self.load_file(file_path)

    def on_drop(self, event):
        """ドロップイベントハンドラ"""
        if self.processing:
            messagebox.showwarning("処理中", "現在処理中です。完了までお待ちください。")
            return

        # ドロップされたファイルパスを取得（波括弧を除去）
        file_path = event.data.strip('{}')

        # 複数ファイルがドロップされた場合は最初のファイルのみ
        if ' ' in file_path:
            file_path = file_path.split()[0].strip('{}')

        self.load_file(file_path)

    def load_file(self, file_path):
        """ファイルを読み込む"""
        # PDFファイルかチェック
        if not file_path.lower().endswith('.pdf'):
            messagebox.showerror("エラー", "PDFファイルを選択してください。")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("エラー", "ファイルが見つかりません。")
            return

        self.current_file = file_path
        self.file_path_var.set(os.path.basename(file_path))
        self.status_var.set(f"ファイルを読み込みました: {os.path.basename(file_path)}")
        self.ocr_button.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.save_button.config(state=tk.DISABLED)

    def run_ocr(self):
        """OCR処理を実行（別スレッドで）"""
        if self.processing:
            return

        # 別スレッドでOCR処理を実行
        thread = threading.Thread(target=self.process_pdf, daemon=True)
        thread.start()

    def process_pdf(self):
        """PDF OCR処理のメイン処理"""
        self.processing = True
        self.ocr_button.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("OCR処理中...")
        self.result_text.delete(1.0, tk.END)

        try:
            # PDFを開く
            pdf_document = fitz.open(self.current_file)
            total_pages = len(pdf_document)

            all_text = []

            # 各ページを処理
            for page_num in range(total_pages):
                self.status_var.set(f"処理中: {page_num + 1}/{total_pages} ページ")

                # ページを取得
                page = pdf_document[page_num]

                # ページを画像に変換（解像度を上げてOCR精度向上）
                mat = fitz.Matrix(2.0, 2.0)  # 2倍の解像度
                pix = page.get_pixmap(matrix=mat)

                # PILイメージに変換
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # OCR実行
                text = pytesseract.image_to_string(
                    img,
                    lang=self.lang_var.get(),
                    config='--psm 6'  # ページセグメンテーションモード
                )

                # 結果に追加
                all_text.append(f"========== ページ {page_num + 1} ==========\n")
                all_text.append(text)
                all_text.append("\n\n")

            pdf_document.close()

            # 結果を表示
            final_text = "".join(all_text)
            self.result_text.insert(1.0, final_text)
            self.status_var.set(f"OCR完了: {total_pages}ページ処理しました")
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("エラー", f"OCR処理中にエラーが発生しました:\n{str(e)}")
            self.status_var.set("エラーが発生しました")

        finally:
            self.processing = False
            self.progress.stop()
            self.ocr_button.config(state=tk.NORMAL)

    def save_text(self):
        """抽出したテキストをファイルに保存"""
        text = self.result_text.get(1.0, tk.END).strip()

        if not text:
            messagebox.showwarning("警告", "保存するテキストがありません。")
            return

        # 保存先を選択
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=Path(self.current_file).stem + "_ocr.txt"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("成功", f"テキストを保存しました:\n{file_path}")
                self.status_var.set(f"保存完了: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("エラー", f"保存中にエラーが発生しました:\n{str(e)}")


# io モジュールのインポートを追加
import io


def main():
    """メイン関数"""
    # Tesseractのパスを設定（必要に応じて）
    # Windows の場合:
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    # macOS の場合（Homebrewでインストールした場合）:
    # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
    # または
    # pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

    root = TkinterDnD.Tk()
    app = PDFOCRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
