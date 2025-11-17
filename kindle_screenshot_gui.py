"""
Kindle for PC 自動スクリーンショットツール (GUI版)
ページを自動的にキャプチャしてPNG画像として保存し、PDFに変換します
"""

import pyautogui as pag
import os
import os.path as osp
import datetime
import time
import threading
from PIL import ImageGrab, Image
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import cv2
import numpy as np
from ctypes import *
from ctypes.wintypes import *
import glob

# ========== Windows API 設定 ==========
EnumWindows = windll.user32.EnumWindows
GetWindowText = windll.user32.GetWindowTextW
GetWindowTextLength = windll.user32.GetWindowTextLengthW
GetWindowRect = windll.user32.GetWindowRect
SetForegroundWindow = windll.user32.SetForegroundWindow

WNDENUMPROC = WINFUNCTYPE(c_bool, POINTER(c_int), POINTER(c_int))

# グローバル変数
stop_capture = False


def find_kindle_window_with_title():
    """Kindleウィンドウを検索し、ウィンドウハンドルとタイトルを返す"""
    hwnd_found = None
    title_found = None

    def enum_windows_proc(hwnd, lParam):
        nonlocal hwnd_found, title_found
        length = GetWindowTextLength(hwnd)
        buff = create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buff, length + 1)

        if buff.value.find('Kindle') != -1 and len(buff.value) > len('Kindle'):
            hwnd_found = hwnd
            title_found = buff.value
            return False
        return True

    EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
    return hwnd_found, title_found


def extract_book_title(window_title):
    """Kindleウィンドウタイトルから本のタイトルを抽出する"""
    if not window_title:
        return None

    # 「本のタイトル - Kindle」の形式から本のタイトルを抽出
    if ' - Kindle' in window_title:
        return window_title.replace(' - Kindle', '').strip()
    elif 'Kindle' in window_title:
        # その他の形式に対応
        return window_title.replace('Kindle', '').strip(' -')

    return window_title


def activate_kindle_window(hwnd):
    """Kindleウィンドウをアクティブにする"""
    SetForegroundWindow(hwnd)
    rect = RECT()
    GetWindowRect(hwnd, pointer(rect))
    pag.moveTo(rect.left + 60, rect.top + 10)
    pag.click()
    time.sleep(1)


def detect_content_area(img):
    """画像からコンテンツ領域の左右端を検出する"""
    def find_edge(img, rng, margin=1):
        for i in rng:
            if np.all(img[20][i] != img[19][0]):
                return i
        return None

    left = find_edge(img, range(1, img.shape[1] - 1))
    right = find_edge(img, reversed(range(1, img.shape[1] - 1)))

    if left is None or right is None:
        raise ValueError("コンテンツ領域の検出に失敗しました")

    return left, right


def create_save_directory(base_folder, title):
    """保存ディレクトリを作成する"""
    save_path = osp.join(base_folder, title)
    os.makedirs(save_path, exist_ok=True)
    return save_path


def capture_page(left, right):
    """現在のページをキャプチャする"""
    img = ImageGrab.grab()
    img = np.array(img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img_bgr[:, left:right]


def wait_for_page_change(old_img, left, right, timeout=5.0, wait_sec=0.15):
    """ページが変わるまで待機する"""
    global stop_capture
    start = time.perf_counter()

    while True:
        if stop_capture:
            return None

        time.sleep(wait_sec)
        new_img = capture_page(left, right)

        if not np.array_equal(old_img, new_img):
            return new_img

        if time.perf_counter() - start > timeout:
            return None


def capture_table_of_contents(save_dir, log_callback):
    """Kindleの目次をキャプチャする"""
    try:
        log_callback("目次をキャプチャ中...")

        pag.hotkey('ctrl', 't')
        time.sleep(2)

        toc_img = ImageGrab.grab()
        toc_path = osp.join(save_dir, 'table_of_contents.png')
        toc_img.save(toc_path)
        log_callback(f"✓ 目次を保存: table_of_contents.png")

        pag.press('esc')
        time.sleep(1)

        return toc_path
    except Exception as e:
        log_callback(f"⚠ 目次のキャプチャに失敗: {e}")
        return None


def convert_images_to_pdf(save_dir, title, log_callback):
    """PNG画像をPDFに変換する"""
    try:
        log_callback("\nPDFを生成中...")

        png_files = sorted(glob.glob(osp.join(save_dir, '*.png')))
        png_files = [f for f in png_files if not f.endswith('table_of_contents.png')]

        if not png_files:
            log_callback("⚠ PNG画像が見つかりませんでした")
            return None

        images = []
        for png_file in png_files:
            img = Image.open(png_file)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)

        pdf_path = osp.join(save_dir, f'{title}.pdf')

        if images:
            images[0].save(
                pdf_path,
                save_all=True,
                append_images=images[1:],
                resolution=100.0,
                quality=95,
                optimize=False
            )
            file_size = osp.getsize(pdf_path) / (1024 * 1024)
            log_callback(f"✓ PDF生成完了: {title}.pdf")
            log_callback(f"  - ページ数: {len(images)}")
            log_callback(f"  - ファイルサイズ: {file_size:.2f} MB")

            return pdf_path

    except Exception as e:
        log_callback(f"⚠ PDF生成に失敗: {e}")
        return None


class KindleScreenshotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kindle Screenshot Tool")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        self.is_capturing = False
        self.capture_thread = None

        self.setup_ui()
        self.auto_detect_kindle()

    def setup_ui(self):
        """UIを構築する"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(main_frame, text="Kindle Screenshot Tool", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # 設定セクション
        settings_frame = ttk.LabelFrame(main_frame, text="設定", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # 本のタイトル
        ttk.Label(settings_frame, text="本のタイトル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(settings_frame, textvariable=self.title_var, width=50)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)

        # 保存先フォルダ
        ttk.Label(settings_frame, text="保存先:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.save_folder_var = tk.StringVar(value=r'C:\Users\azuck\Downloads')
        self.folder_entry = ttk.Entry(settings_frame, textvariable=self.save_folder_var, width=40)
        self.folder_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(settings_frame, text="参照", command=self.browse_folder).grid(row=1, column=2, pady=5, padx=5)

        # オプション
        options_frame = ttk.Frame(settings_frame)
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.create_pdf_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="PDF生成", variable=self.create_pdf_var).grid(row=0, column=0, padx=5)

        self.capture_toc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="目次キャプチャ", variable=self.capture_toc_var).grid(row=0, column=1, padx=5)

        # 待機時間
        ttk.Label(options_frame, text="待機時間(秒):").grid(row=0, column=2, padx=5)
        self.wait_sec_var = tk.DoubleVar(value=0.15)
        wait_spin = ttk.Spinbox(options_frame, from_=0.1, to=2.0, increment=0.05,
                                textvariable=self.wait_sec_var, width=8)
        wait_spin.grid(row=0, column=3, padx=5)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(button_frame, text="▶ キャプチャ開始", command=self.start_capture, width=20)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="⏹ 停止", command=self.stop_capture,
                                      width=20, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        # ステータス
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(status_frame, text="ステータス:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="待機中", foreground="blue")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate', length=400)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # ログエリア
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.log_text.config(state=tk.DISABLED)

    def log(self, message):
        """ログにメッセージを追加"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def browse_folder(self):
        """保存先フォルダを選択"""
        folder = filedialog.askdirectory()
        if folder:
            self.save_folder_var.set(folder)

    def auto_detect_kindle(self):
        """Kindleウィンドウを自動検出してタイトルを設定"""
        hwnd, window_title = find_kindle_window_with_title()
        if hwnd and window_title:
            book_title = extract_book_title(window_title)
            if book_title:
                self.title_var.set(book_title)
                self.log(f"✓ Kindleを検出: {book_title}")
            else:
                self.log("⚠ Kindleを検出しましたが、タイトルを取得できませんでした")
                self.title_var.set(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        else:
            self.log("⚠ Kindleが起動していません")
            self.title_var.set(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

    def start_capture(self):
        """キャプチャを開始"""
        if self.is_capturing:
            return

        # 入力チェック
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("エラー", "タイトルを入力してください")
            return

        save_folder = self.save_folder_var.get().strip()
        if not save_folder or not osp.exists(save_folder):
            messagebox.showerror("エラー", "有効な保存先フォルダを指定してください")
            return

        # UIを更新
        self.is_capturing = True
        global stop_capture
        stop_capture = False

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="キャプチャ中...", foreground="green")
        self.progress_bar.start()

        # 別スレッドでキャプチャを実行
        self.capture_thread = threading.Thread(target=self.capture_process, daemon=True)
        self.capture_thread.start()

    def stop_capture(self):
        """キャプチャを停止"""
        global stop_capture
        stop_capture = True
        self.log("\n⏹ 停止を要求しました...")
        self.status_label.config(text="停止中...", foreground="orange")

    def capture_process(self):
        """キャプチャ処理のメイン"""
        global stop_capture

        try:
            title = self.title_var.get().strip()
            save_folder = self.save_folder_var.get().strip()
            create_pdf = self.create_pdf_var.get()
            capture_toc = self.capture_toc_var.get()
            wait_sec = self.wait_sec_var.get()

            self.log(f"\n{'='*60}")
            self.log(f"キャプチャ開始: {title}")
            self.log(f"{'='*60}\n")

            # Kindleウィンドウを検索
            hwnd, _ = find_kindle_window_with_title()
            if hwnd is None:
                self.log("❌ エラー: Kindleが見つかりません")
                messagebox.showerror("エラー", "Kindleが見つかりません")
                return

            activate_kindle_window(hwnd)

            # 保存ディレクトリを作成
            save_dir = create_save_directory(save_folder, title)
            self.log(f"保存先: {save_dir}")

            # 目次をキャプチャ
            if capture_toc:
                capture_table_of_contents(save_dir, self.log)
                activate_kindle_window(hwnd)

            # フルスクリーンにする
            self.log("\nフルスクリーンモードに切り替え中...")
            pag.press('f11')
            sc_w, sc_h = pag.size()
            pag.moveTo(sc_w - 200, sc_h - 1)
            time.sleep(5)

            # コンテンツ領域を検出
            self.log("コンテンツ領域を検出中...")
            img = ImageGrab.grab()
            img = np.array(img)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            try:
                left, right = detect_content_area(img_bgr)
                self.log(f"✓ 検出完了 (左: {left}px, 右: {right}px, 幅: {right-left}px)")
            except ValueError as e:
                self.log(f"❌ {e}")
                pag.press('f11')
                return

            # ページキャプチャ開始
            original_dir = os.getcwd()
            os.chdir(save_dir)

            old_img = np.zeros((sc_h, right - left, 3), np.uint8)
            page = 1

            self.log(f"\n{'='*60}")
            self.log(f"ページキャプチャ開始")
            self.log(f"{'='*60}\n")

            while not stop_capture:
                filename = str(page).zfill(3) + '.png'

                new_img = wait_for_page_change(old_img, left, right, timeout=5.0, wait_sec=wait_sec)

                if new_img is None:
                    if stop_capture:
                        self.log("\n⏹ ユーザーによって停止されました")
                    else:
                        self.log("\n✓ 最終ページに到達しました")
                    pag.press('f11')
                    break

                cv2.imwrite(filename, new_img)
                self.log(f"Page {page:3d}: {filename}")

                old_img = new_img
                page += 1

                pag.press('left')

            os.chdir(original_dir)

            # PDF生成
            if create_pdf and page > 1 and not stop_capture:
                convert_images_to_pdf(save_dir, title, self.log)

            if not stop_capture:
                self.log(f"\n{'='*60}")
                self.log(f"✓ 処理完了!")
                self.log(f"  合計ページ数: {page - 1}")
                self.log(f"  保存先: {save_dir}")
                self.log(f"{'='*60}\n")
                messagebox.showinfo("完了", f"キャプチャが完了しました！\n\n合計ページ数: {page - 1}\n保存先: {save_dir}")

        except Exception as e:
            self.log(f"\n❌ エラーが発生しました: {e}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("エラー", f"エラーが発生しました:\n{e}")

        finally:
            # UIをリセット
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        """UIを初期状態に戻す"""
        self.is_capturing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="待機中", foreground="blue")
        self.progress_bar.stop()


def main():
    """メイン処理"""
    root = tk.Tk()
    app = KindleScreenshotGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
