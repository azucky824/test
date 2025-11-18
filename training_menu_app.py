#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トレーニングメニュー作成アプリケーション
PDFファイルからページを選択して印刷メニューを作成
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import List, Tuple, Optional
import io
import tempfile
import subprocess
import platform

try:
    from PyPDF2 import PdfReader, PdfWriter
    from pdf2image import convert_from_path
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"必要なライブラリがインストールされていません: {e}")
    print("pip install -r requirements.txt を実行してください")
    sys.exit(1)


class TrainingMenuApp:
    """トレーニングメニュー作成アプリケーション"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("トレーニングメニュー作成アプリ")
        self.root.geometry("1400x800")

        # PDFディレクトリの設定（開発時はカレントディレクトリ、EXE時は実行ファイルの場所）
        if getattr(sys, 'frozen', False):
            # EXE化されている場合
            self.pdf_directory = os.path.dirname(sys.executable)
        else:
            # 開発時
            self.pdf_directory = os.getcwd()

        # データ保持用
        self.pdf_files: List[str] = []
        self.current_pdf: Optional[str] = None
        self.current_pdf_pages: List[Image.Image] = []
        self.print_queue: List[Tuple[str, int, Image.Image]] = []  # (pdf_name, page_num, image)
        self.thumbnail_refs: List[ImageTk.PhotoImage] = []  # サムネイル画像の参照を保持
        self.preview_image_ref: Optional[ImageTk.PhotoImage] = None
        self.print_queue_refs: List[ImageTk.PhotoImage] = []

        self.setup_ui()
        self.load_pdf_list()

    def setup_ui(self):
        """UIのセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左側：PDFファイル一覧
        left_frame = ttk.LabelFrame(main_frame, text="PDFファイル一覧", width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        left_frame.pack_propagate(False)

        # PDFリストボックス
        pdf_scrollbar = ttk.Scrollbar(left_frame)
        pdf_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.pdf_listbox = tk.Listbox(left_frame, yscrollcommand=pdf_scrollbar.set)
        self.pdf_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.pdf_listbox.bind('<<ListboxSelect>>', self.on_pdf_select)
        pdf_scrollbar.config(command=self.pdf_listbox.yview)

        # 真ん中：プレビューとページ一覧
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 上段：PDFプレビューと送信ボタン
        preview_frame = ttk.LabelFrame(middle_frame, text="プレビュー")
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        # プレビューキャンバス
        preview_canvas_frame = ttk.Frame(preview_frame)
        preview_canvas_frame.pack(fill=tk.BOTH, expand=True)

        preview_scrollbar_y = ttk.Scrollbar(preview_canvas_frame, orient=tk.VERTICAL)
        preview_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        preview_scrollbar_x = ttk.Scrollbar(preview_canvas_frame, orient=tk.HORIZONTAL)
        preview_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_canvas = tk.Canvas(
            preview_canvas_frame,
            bg='gray',
            yscrollcommand=preview_scrollbar_y.set,
            xscrollcommand=preview_scrollbar_x.set
        )
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar_y.config(command=self.preview_canvas.yview)
        preview_scrollbar_x.config(command=self.preview_canvas.xview)

        # 下段：ページサムネイル一覧
        thumbnail_frame = ttk.LabelFrame(middle_frame, text="ページ一覧")
        thumbnail_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # サムネイル用キャンバス（横スクロール）
        thumbnail_canvas_frame = ttk.Frame(thumbnail_frame)
        thumbnail_canvas_frame.pack(fill=tk.BOTH, expand=True)

        thumbnail_scrollbar = ttk.Scrollbar(thumbnail_canvas_frame, orient=tk.HORIZONTAL)
        thumbnail_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.thumbnail_canvas = tk.Canvas(
            thumbnail_canvas_frame,
            height=200,
            bg='white',
            xscrollcommand=thumbnail_scrollbar.set
        )
        self.thumbnail_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        thumbnail_scrollbar.config(command=self.thumbnail_canvas.xview)

        # サムネイル内フレーム
        self.thumbnail_inner_frame = ttk.Frame(self.thumbnail_canvas)
        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_inner_frame, anchor='nw')

        # 右側：印刷エリア
        right_frame = ttk.LabelFrame(main_frame, text="印刷エリア", width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        right_frame.pack_propagate(False)

        # 印刷キュー用キャンバス
        print_canvas_frame = ttk.Frame(right_frame)
        print_canvas_frame.pack(fill=tk.BOTH, expand=True)

        print_scrollbar = ttk.Scrollbar(print_canvas_frame)
        print_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.print_canvas = tk.Canvas(print_canvas_frame, yscrollcommand=print_scrollbar.set, bg='white')
        self.print_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        print_scrollbar.config(command=self.print_canvas.yview)

        # 印刷キュー内フレーム
        self.print_inner_frame = ttk.Frame(self.print_canvas)
        self.print_canvas.create_window((0, 0), window=self.print_inner_frame, anchor='nw')

        # ボタンフレーム
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        ttk.Button(button_frame, text="クリア", command=self.clear_print_queue).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="PDF保存", command=self.save_as_pdf).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="印刷", command=self.print_pages).pack(side=tk.RIGHT, padx=2)

    def load_pdf_list(self):
        """PDFファイル一覧を読み込む"""
        try:
            # カレントディレクトリのPDFファイルを取得
            pdf_path = Path(self.pdf_directory)
            self.pdf_files = sorted([f.name for f in pdf_path.glob("*.pdf")])

            # リストボックスに追加
            self.pdf_listbox.delete(0, tk.END)
            for pdf_file in self.pdf_files:
                self.pdf_listbox.insert(tk.END, pdf_file)

            if not self.pdf_files:
                messagebox.showinfo("情報", f"PDFファイルが見つかりません。\n場所: {self.pdf_directory}")
        except Exception as e:
            messagebox.showerror("エラー", f"PDFファイル一覧の読み込みに失敗しました:\n{e}")

    def on_pdf_select(self, event):
        """PDFファイルが選択されたときの処理"""
        selection = self.pdf_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.current_pdf = self.pdf_files[index]
        self.load_pdf_preview()

    def load_pdf_preview(self):
        """選択されたPDFのプレビューとサムネイルを読み込む"""
        if not self.current_pdf:
            return

        try:
            pdf_path = os.path.join(self.pdf_directory, self.current_pdf)

            # PDFを画像に変換
            self.current_pdf_pages = convert_from_path(pdf_path, dpi=150)

            # 最初のページをプレビュー表示
            if self.current_pdf_pages:
                self.show_preview(self.current_pdf_pages[0])

            # サムネイル一覧を表示
            self.show_thumbnails()

        except Exception as e:
            messagebox.showerror("エラー", f"PDFの読み込みに失敗しました:\n{e}")

    def show_preview(self, image: Image.Image):
        """プレビュー画像を表示"""
        # 画像をリサイズ（アスペクト比維持）
        display_image = image.copy()
        max_width = 600
        max_height = 800

        width, height = display_image.size
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        display_image = display_image.resize(new_size, Image.Resampling.LANCZOS)

        # Canvas に表示
        self.preview_image_ref = ImageTk.PhotoImage(display_image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, anchor='nw', image=self.preview_image_ref)
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

    def show_thumbnails(self):
        """ページサムネイル一覧を表示"""
        # 既存のサムネイルをクリア
        for widget in self.thumbnail_inner_frame.winfo_children():
            widget.destroy()
        self.thumbnail_refs.clear()

        # サムネイルを作成
        for i, page_image in enumerate(self.current_pdf_pages):
            # サムネイルサイズにリサイズ
            thumb = page_image.copy()
            thumb.thumbnail((150, 200), Image.Resampling.LANCZOS)

            # PhotoImage に変換
            thumb_photo = ImageTk.PhotoImage(thumb)
            self.thumbnail_refs.append(thumb_photo)

            # フレームを作成
            thumb_frame = ttk.Frame(self.thumbnail_inner_frame, relief=tk.RAISED, borderwidth=2)
            thumb_frame.pack(side=tk.LEFT, padx=5, pady=5)

            # サムネイル画像
            label = tk.Label(thumb_frame, image=thumb_photo, cursor="hand2")
            label.pack()
            label.bind("<Button-1>", lambda e, idx=i: self.on_thumbnail_click(idx))

            # ページ番号
            page_label = ttk.Label(thumb_frame, text=f"ページ {i+1}")
            page_label.pack()

            # 印刷エリアに追加ボタン
            add_btn = ttk.Button(
                thumb_frame,
                text="印刷エリアに追加",
                command=lambda idx=i: self.add_to_print_queue(idx)
            )
            add_btn.pack(pady=2)

        # スクロール領域を更新
        self.thumbnail_inner_frame.update_idletasks()
        self.thumbnail_canvas.config(scrollregion=self.thumbnail_canvas.bbox("all"))

    def on_thumbnail_click(self, page_index: int):
        """サムネイルクリック時の処理（プレビュー更新）"""
        if 0 <= page_index < len(self.current_pdf_pages):
            self.show_preview(self.current_pdf_pages[page_index])

    def add_to_print_queue(self, page_index: int):
        """ページを印刷キューに追加"""
        if not self.current_pdf or page_index >= len(self.current_pdf_pages):
            return

        page_image = self.current_pdf_pages[page_index]
        self.print_queue.append((self.current_pdf, page_index, page_image))
        self.update_print_queue_display()

        messagebox.showinfo("追加完了", f"{self.current_pdf} のページ {page_index + 1} を追加しました")

    def update_print_queue_display(self):
        """印刷キューの表示を更新"""
        # 既存の表示をクリア
        for widget in self.print_inner_frame.winfo_children():
            widget.destroy()
        self.print_queue_refs.clear()

        # 印刷キューの各項目を表示
        for i, (pdf_name, page_num, page_image) in enumerate(self.print_queue):
            # サムネイルサイズにリサイズ
            thumb = page_image.copy()
            thumb.thumbnail((200, 280), Image.Resampling.LANCZOS)

            # PhotoImage に変換
            thumb_photo = ImageTk.PhotoImage(thumb)
            self.print_queue_refs.append(thumb_photo)

            # フレームを作成
            item_frame = ttk.Frame(self.print_inner_frame, relief=tk.GROOVE, borderwidth=2)
            item_frame.pack(fill=tk.X, padx=5, pady=5)

            # 情報ラベル
            info_label = ttk.Label(
                item_frame,
                text=f"{i+1}. {pdf_name}\nページ {page_num + 1}",
                font=('', 9, 'bold')
            )
            info_label.pack(pady=2)

            # サムネイル画像
            img_label = tk.Label(item_frame, image=thumb_photo)
            img_label.pack(pady=2)

            # 削除ボタン
            remove_btn = ttk.Button(
                item_frame,
                text="削除",
                command=lambda idx=i: self.remove_from_print_queue(idx)
            )
            remove_btn.pack(pady=2)

        # スクロール領域を更新
        self.print_inner_frame.update_idletasks()
        self.print_canvas.config(scrollregion=self.print_canvas.bbox("all"))

    def remove_from_print_queue(self, index: int):
        """印刷キューから削除"""
        if 0 <= index < len(self.print_queue):
            self.print_queue.pop(index)
            self.update_print_queue_display()

    def clear_print_queue(self):
        """印刷キューをクリア"""
        if messagebox.askyesno("確認", "印刷エリアをクリアしますか？"):
            self.print_queue.clear()
            self.update_print_queue_display()

    def create_temp_pdf(self) -> str:
        """一時PDFファイルを作成して返す"""
        # 一時ファイルを作成
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        # 新しいPDFを作成
        pdf_writer = PdfWriter()

        for pdf_name, page_num, _ in self.print_queue:
            pdf_path = os.path.join(self.pdf_directory, pdf_name)
            pdf_reader = PdfReader(pdf_path)

            if page_num < len(pdf_reader.pages):
                pdf_writer.add_page(pdf_reader.pages[page_num])

        # PDFを保存
        with open(temp_path, 'wb') as output_file:
            pdf_writer.write(output_file)

        return temp_path

    def print_pages(self):
        """プリンターで印刷を実行"""
        if not self.print_queue:
            messagebox.showwarning("警告", "印刷するページが選択されていません")
            return

        temp_path = None
        try:
            # 一時PDFを作成
            temp_path = self.create_temp_pdf()

            # OSに応じて印刷
            system = platform.system()

            if system == "Windows":
                # Windowsの場合
                os.startfile(temp_path, "print")
                messagebox.showinfo("印刷", "印刷ジョブを送信しました")

            elif system == "Darwin":
                # macOSの場合
                subprocess.run(["lpr", temp_path], check=True)
                messagebox.showinfo("印刷", "印刷ジョブを送信しました")

            elif system == "Linux":
                # Linuxの場合
                subprocess.run(["lpr", temp_path], check=True)
                messagebox.showinfo("印刷", "印刷ジョブを送信しました")

            else:
                messagebox.showerror("エラー", f"お使いのOS（{system}）での印刷はサポートされていません")
                return

        except subprocess.CalledProcessError as e:
            messagebox.showerror("エラー", f"印刷コマンドの実行に失敗しました:\n{e}")
        except Exception as e:
            messagebox.showerror("エラー", f"印刷に失敗しました:\n{e}")
        finally:
            # 一時ファイルを削除（Windowsの場合は少し待つ）
            if temp_path and os.path.exists(temp_path):
                if system == "Windows":
                    # Windowsでは印刷スプーラーがファイルを使用中の可能性があるため、
                    # 遅延削除を試みる
                    self.root.after(5000, lambda: self._safe_delete_file(temp_path))
                else:
                    # Linux/Macでは即座に削除可能
                    self._safe_delete_file(temp_path)

    def _safe_delete_file(self, file_path: str):
        """ファイルを安全に削除"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # 削除失敗は無視

    def save_as_pdf(self):
        """PDFファイルとして保存"""
        if not self.print_queue:
            messagebox.showwarning("警告", "保存するページが選択されていません")
            return

        try:
            # 保存先を選択
            output_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile="training_menu.pdf"
            )

            if not output_path:
                return

            # 新しいPDFを作成
            pdf_writer = PdfWriter()

            for pdf_name, page_num, _ in self.print_queue:
                pdf_path = os.path.join(self.pdf_directory, pdf_name)
                pdf_reader = PdfReader(pdf_path)

                if page_num < len(pdf_reader.pages):
                    pdf_writer.add_page(pdf_reader.pages[page_num])

            # PDFを保存
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)

            messagebox.showinfo("完了", f"PDFを作成しました:\n{output_path}")

        except Exception as e:
            messagebox.showerror("エラー", f"PDF作成に失敗しました:\n{e}")


def main():
    """メイン関数"""
    root = tk.Tk()
    app = TrainingMenuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
