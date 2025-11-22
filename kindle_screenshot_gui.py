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
import json

# ========== Windows API 設定 ==========
EnumWindows = windll.user32.EnumWindows
GetWindowText = windll.user32.GetWindowTextW
GetWindowTextLength = windll.user32.GetWindowTextLengthW
GetWindowRect = windll.user32.GetWindowRect
SetForegroundWindow = windll.user32.SetForegroundWindow

WNDENUMPROC = WINFUNCTYPE(c_bool, POINTER(c_int), POINTER(c_int))

# グローバル変数
stop_capture = False
selected_area = None  # (top, bottom, left, right)


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
    """Kindleウィンドウタイトルから本のタイトルを抽出する

    例: "鈴木淳さんの  for PC3 - Tarzan(ターザン) 2025年8月28日号 - Kindle"
    → "Tarzan(ターザン) 2025年8月28日号"
    """
    if not window_title:
        return None

    # 「ユーザー名 - 本のタイトル - Kindle」の形式から抽出
    # まず末尾の「Kindle」関連の文字を削除
    title = window_title.strip()
    if title.endswith(' - Kindle'):
        title = title[:-len(' - Kindle')]
    elif title.endswith('- Kindle'):
        title = title[:-len('- Kindle')]
    elif title.endswith('Kindle'):
        title = title[:-len('Kindle')].strip()

    # ユーザー名/デバイス名部分を削除
    # 「鈴木淳さんの  for PC3 - Tarzan...」→「Tarzan...」
    # パターン: 最初の部分に "for PC" や "さんの" が含まれていれば除去
    if ' - ' in title:
        parts = title.split(' - ', 1)  # 最初の " - " で2つに分割
        if len(parts) == 2:
            first_part = parts[0].strip()
            # ユーザー名/デバイス名を示すキーワードをチェック
            if any(keyword in first_part for keyword in ['for PC', 'さんの', 'の  ', 'iPad', 'iPhone', 'Android']):
                title = parts[1].strip()

    return title.strip()


def activate_kindle_window(hwnd):
    """Kindleウィンドウをアクティブにする"""
    SetForegroundWindow(hwnd)
    rect = RECT()
    GetWindowRect(hwnd, pointer(rect))
    pag.moveTo(rect.left + 60, rect.top + 10)
    pag.click()
    time.sleep(1)


def select_area_interactively():
    """フルスクリーン後に、ユーザーがマウスドラッグで範囲を選択できるようにする

    Returns:
        (top, bottom, left, right): 選択された座標、キャンセルの場合はNone
    """
    global selected_area
    selected_area = None

    # 透明なオーバーレイウィンドウを作成
    overlay = tk.Toplevel()
    overlay.attributes('-fullscreen', True)
    overlay.attributes('-alpha', 0.3)  # 半透明
    overlay.attributes('-topmost', True)
    overlay.config(bg='black')

    # キャンバスを作成
    canvas = tk.Canvas(overlay, bg='black', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    # 説明テキスト
    canvas.create_text(
        overlay.winfo_screenwidth() // 2,
        30,
        text="マウスをドラッグしてキャプチャ範囲を選択してください（ESCキーでキャンセル）",
        fill='white',
        font=('Arial', 16, 'bold'),
        tags='info_text'
    )

    # ルーペウィンドウを作成
    magnifier = tk.Toplevel(overlay)
    magnifier.attributes('-topmost', True)
    magnifier.overrideredirect(True)  # タイトルバーなし
    magnifier.config(bg='white')

    # ルーペのキャンバス（拡大表示用）
    mag_size = 200  # ルーペのサイズ
    zoom_factor = 3  # 拡大率
    mag_canvas = tk.Canvas(magnifier, width=mag_size, height=mag_size,
                          bg='white', highlightthickness=2, highlightbackground='red')
    mag_canvas.pack()

    # 座標表示用のラベル
    coord_label = tk.Label(magnifier, text="", font=('Arial', 10, 'bold'),
                          bg='white', fg='black')
    coord_label.pack()

    # ドラッグ状態
    drag_data = {'start_x': 0, 'start_y': 0, 'rect': None}

    # スクリーンショット用の画像（ルーペ表示用）
    screen_img = ImageGrab.grab()
    screen_array = np.array(screen_img)

    def update_magnifier(x, y):
        """ルーペを更新する"""
        try:
            # ルーペの位置を設定（カーソルの右下に表示）
            mag_x = x + 20
            mag_y = y + 20

            # 画面外に出ないように調整
            screen_w = overlay.winfo_screenwidth()
            screen_h = overlay.winfo_screenheight()
            if mag_x + mag_size > screen_w:
                mag_x = x - mag_size - 20
            if mag_y + mag_size + 30 > screen_h:  # ラベル分も考慮
                mag_y = y - mag_size - 50

            magnifier.geometry(f"+{mag_x}+{mag_y}")

            # 拡大表示する領域を計算（カーソル位置を正確に中央に）
            capture_size = mag_size // zoom_factor  # 66ピクセル
            half_capture = capture_size // 2  # 33ピクセル

            # キャプチャ範囲（境界外になる場合も考慮）
            x1 = x - half_capture
            y1 = y - half_capture
            x2 = x1 + capture_size
            y2 = y1 + capture_size

            # 画面範囲内にクリップしてキャプチャ
            screen_h_max, screen_w_max = screen_array.shape[:2]

            # 実際にキャプチャできる範囲
            cap_x1 = max(0, x1)
            cap_y1 = max(0, y1)
            cap_x2 = min(screen_w_max, x2)
            cap_y2 = min(screen_h_max, y2)

            # 固定サイズの領域を作成（黒で初期化）
            region = np.zeros((capture_size, capture_size, 3), dtype=np.uint8)

            # 実際にキャプチャした部分を配置
            paste_x1 = cap_x1 - x1
            paste_y1 = cap_y1 - y1
            paste_x2 = paste_x1 + (cap_x2 - cap_x1)
            paste_y2 = paste_y1 + (cap_y2 - cap_y1)

            region[paste_y1:paste_y2, paste_x1:paste_x2] = screen_array[cap_y1:cap_y2, cap_x1:cap_x2]

            # PIL Imageに変換して拡大
            from PIL import Image as PILImage
            pil_img = PILImage.fromarray(region)
            zoomed = pil_img.resize((mag_size, mag_size), PILImage.NEAREST)

            # Tkinter PhotoImageに変換
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(zoomed)

            # キャンバスに表示（中央に十字線を描画）
            mag_canvas.delete('all')
            mag_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            mag_canvas.image = photo  # 参照を保持

            # 十字線（中央）- カーソル位置を正確に示す
            center = mag_size // 2
            mag_canvas.create_line(center, 0, center, mag_size, fill='red', width=2)
            mag_canvas.create_line(0, center, mag_size, center, fill='red', width=2)

            # 座標表示
            coord_label.config(text=f"X: {x}, Y: {y}")

        except Exception as e:
            print(f"ルーペ更新エラー: {e}")

    def on_mouse_down(event):
        drag_data['start_x'] = event.x
        drag_data['start_y'] = event.y
        if drag_data['rect']:
            canvas.delete(drag_data['rect'])
        drag_data['rect'] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline='red', width=3
        )
        update_magnifier(event.x, event.y)

    def on_mouse_move(event):
        if drag_data['rect']:
            canvas.coords(
                drag_data['rect'],
                drag_data['start_x'], drag_data['start_y'],
                event.x, event.y
            )
        update_magnifier(event.x, event.y)

    def on_mouse_up(event):
        global selected_area
        if drag_data['rect']:
            x1, y1 = drag_data['start_x'], drag_data['start_y']
            x2, y2 = event.x, event.y

            # 座標を正規化（左上と右下を確定）
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2)
            bottom = max(y1, y2)

            # 最小サイズチェック（100x100ピクセル以上）
            if (right - left) >= 100 and (bottom - top) >= 100:
                selected_area = (top, bottom, left, right)
                magnifier.destroy()
                overlay.destroy()
            else:
                canvas.delete(drag_data['rect'])
                drag_data['rect'] = None

    def on_escape(event):
        global selected_area
        selected_area = None
        magnifier.destroy()
        overlay.destroy()

    # イベントバインド
    canvas.bind('<Button-1>', on_mouse_down)
    canvas.bind('<B1-Motion>', on_mouse_move)
    canvas.bind('<ButtonRelease-1>', on_mouse_up)
    canvas.bind('<Motion>', lambda e: update_magnifier(e.x, e.y))
    overlay.bind('<Escape>', on_escape)

    # 初期ルーペ位置
    magnifier.geometry(f"+100+100")

    # モーダルダイアログとして実行
    overlay.wait_window()

    return selected_area


def detect_content_area(img):
    """画像からコンテンツ領域の左右端を検出する（旧バージョン）"""
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


def detect_content_area_full(img, threshold=250, margin=10):
    """画像から上下左右すべての余白を検出する

    Args:
        img: 入力画像（BGR形式）
        threshold: 二値化の閾値（デフォルト250、白背景を想定）
        margin: 余白の最小マージン（ピクセル）

    Returns:
        (top, bottom, left, right): コンテンツ領域の座標
    """
    try:
        # グレースケール化
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 二値化（余白は白=255、コンテンツは黒っぽい）
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

        # ノイズ除去（小さな点を消す）
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # 輪郭検出でコンテンツ領域を見つける
        coords = cv2.findNonZero(binary)

        if coords is None:
            raise ValueError("コンテンツが検出できませんでした")

        # バウンディングボックスを取得
        x, y, w, h = cv2.boundingRect(coords)

        # マージンを適用
        top = max(0, y - margin)
        bottom = min(img.shape[0], y + h + margin)
        left = max(0, x - margin)
        right = min(img.shape[1], x + w + margin)

        return top, bottom, left, right

    except Exception as e:
        raise ValueError(f"コンテンツ領域の検出に失敗: {e}")


def get_coords_file_path():
    """座標保存ファイルのパスを取得する"""
    # アプリケーションのデータディレクトリ
    app_data_dir = osp.join(osp.expanduser('~'), '.kindle_screenshot')
    os.makedirs(app_data_dir, exist_ok=True)
    return osp.join(app_data_dir, 'coords.json')


def save_coordinates(top, bottom, left, right):
    """座標をJSONファイルに保存する"""
    try:
        coords_file = get_coords_file_path()
        coords_data = {
            'top': top,
            'bottom': bottom,
            'left': left,
            'right': right
        }
        with open(coords_file, 'w', encoding='utf-8') as f:
            json.dump(coords_data, f, indent=2)
        return True
    except Exception as e:
        print(f"座標の保存に失敗: {e}")
        return False


def load_coordinates():
    """保存された座標をJSONファイルから読み込む

    Returns:
        (top, bottom, left, right): 座標のタプル、失敗時はNone
    """
    try:
        coords_file = get_coords_file_path()
        if not osp.exists(coords_file):
            return None

        with open(coords_file, 'r', encoding='utf-8') as f:
            coords_data = json.load(f)

        top = coords_data.get('top')
        bottom = coords_data.get('bottom')
        left = coords_data.get('left')
        right = coords_data.get('right')

        if all(v is not None for v in [top, bottom, left, right]):
            return (top, bottom, left, right)
        return None
    except Exception as e:
        print(f"座標の読み込みに失敗: {e}")
        return None


def create_save_directory(base_folder, title):
    """保存ディレクトリを作成する"""
    save_path = osp.join(base_folder, title)
    os.makedirs(save_path, exist_ok=True)
    return save_path


def capture_page(left, right, top=None, bottom=None):
    """現在のページをキャプチャする

    Args:
        left: 左端の座標
        right: 右端の座標
        top: 上端の座標（Noneの場合は全体）
        bottom: 下端の座標（Noneの場合は全体）

    Returns:
        クロップされた画像
    """
    img = ImageGrab.grab()
    img = np.array(img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # 上下左右でクロップ
    if top is not None and bottom is not None:
        return img_bgr[top:bottom, left:right]
    else:
        return img_bgr[:, left:right]


def capture_page_with_crop_detection(trim_each_page=False, threshold=250, margin=10):
    """ページをキャプチャして余白を検出・削除する

    Args:
        trim_each_page: ページごとに余白検出を行うか
        threshold: 二値化の閾値
        margin: 余白のマージン

    Returns:
        (cropped_img, crop_coords): クロップされた画像と座標
    """
    img = ImageGrab.grab()
    img = np.array(img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if trim_each_page:
        # ページごとに余白検出
        top, bottom, left, right = detect_content_area_full(img_bgr, threshold, margin)
        cropped = img_bgr[top:bottom, left:right]
        return cropped, (top, bottom, left, right)
    else:
        # 余白検出しない（全体）
        return img_bgr, None


def wait_for_page_change(old_img, left, right, top=None, bottom=None, timeout=5.0, wait_sec=0.15):
    """ページが変わるまで待機する"""
    global stop_capture
    start = time.perf_counter()

    while True:
        if stop_capture:
            return None

        time.sleep(wait_sec)
        new_img = capture_page(left, right, top, bottom)

        if not np.array_equal(old_img, new_img):
            return new_img

        if time.perf_counter() - start > timeout:
            return None


def perform_ocr_on_pdf(pdf_path, log_callback):
    """PDFにOCRを実行して検索可能なPDFを生成する

    Args:
        pdf_path: 入力PDFファイルのパス
        log_callback: ログ出力用のコールバック関数

    Returns:
        成功時: OCR処理後のPDFパス、失敗時: None
    """
    try:
        import ocrmypdf

        log_callback("\nOCR処理を開始...")
        log_callback("⚠ 初回実行時は時間がかかる場合があります")

        # 出力ファイル名（元のファイルを上書き）
        output_path = pdf_path

        # 一時ファイルを作成
        temp_output = pdf_path.replace('.pdf', '_ocr_temp.pdf')

        # OCR実行（日本語と英語）
        log_callback("OCRエンジンを実行中（日本語+英語）...")

        result = ocrmypdf.ocr(
            pdf_path,
            temp_output,
            language='jpn+eng',  # 日本語と英語
            deskew=True,         # 傾き補正
            force_ocr=True,      # 既存のテキストを無視してOCR実行
            optimize=1,          # 軽度の最適化
            output_type='pdf',   # PDF出力
            progress_bar=False,  # プログレスバーを無効化
        )

        # 一時ファイルを元のファイルに置き換え
        if osp.exists(temp_output):
            if osp.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output, output_path)

            file_size = osp.getsize(output_path) / (1024 * 1024)
            log_callback(f"✓ OCR処理完了")
            log_callback(f"  - 検索可能なPDF: {output_path}")
            log_callback(f"  - ファイルサイズ: {file_size:.2f} MB")
            return output_path
        else:
            log_callback("⚠ OCR処理に失敗しました")
            return None

    except ImportError:
        log_callback("⚠ OCRmyPDFがインストールされていません")
        log_callback("  インストール方法: pip install ocrmypdf")
        log_callback("  Tesseractも必要です: https://github.com/tesseract-ocr/tesseract")
        return None
    except Exception as e:
        error_msg = str(e)
        log_callback(f"⚠ OCR処理中にエラーが発生: {error_msg}")

        # Tesseractが見つからない場合の詳細案内
        if "tesseract" in error_msg.lower() and "path" in error_msg.lower():
            log_callback("\n【Tesseract OCRのインストールが必要です】")
            log_callback("1. Tesseractをダウンロード:")
            log_callback("   https://github.com/UB-Mannheim/tesseract/wiki")
            log_callback("   → 最新版のインストーラー (.exe) をダウンロード")
            log_callback("")
            log_callback("2. インストール時の注意:")
            log_callback("   ✓ 'Additional language data' で日本語(jpn)を選択")
            log_callback("   ✓ デフォルトのインストール先でOK")
            log_callback("   ✓ インストール後、PCを再起動してください")
            log_callback("")
            log_callback("3. インストール確認:")
            log_callback("   コマンドプロンプトで: tesseract --version")
            log_callback("")
            log_callback("参考: https://tesseract-ocr.github.io/tessdoc/Installation.html")

        # 一時ファイルをクリーンアップ
        temp_output = pdf_path.replace('.pdf', '_ocr_temp.pdf')
        if osp.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass
        return None


def convert_images_to_pdf(save_dir, title, log_callback, delete_images=False):
    """PNG画像をPDFに変換する

    Args:
        save_dir: 保存ディレクトリ
        title: PDFのタイトル
        log_callback: ログ出力用のコールバック関数
        delete_images: PDF生成後にPNG画像を削除するか
    """
    try:
        log_callback("\nPDFを生成中...")
        log_callback(f"検索ディレクトリ: {save_dir}")

        # PNG画像を取得（os.listdirを使用してglobの特殊文字問題を回避）
        all_files = os.listdir(save_dir)
        png_files = [f for f in all_files if f.endswith('.png')]

        # 番号順にソート（001.png, 002.png, ...）
        png_files = sorted(png_files)

        log_callback(f"見つかったPNGファイル: {len(png_files)}個")

        if png_files:
            log_callback(f"最初のファイル: {png_files[0]}")
            log_callback(f"最後のファイル: {png_files[-1]}")

        # 絶対パスに変換
        png_files = [osp.join(save_dir, f) for f in png_files]

        if not png_files:
            log_callback("⚠ PNG画像が見つかりませんでした")
            log_callback(f"確認: ディレクトリ '{save_dir}' にファイルが存在するか確認してください")
            # ディレクトリの内容を確認
            if osp.exists(save_dir):
                all_files = os.listdir(save_dir)
                log_callback(f"ディレクトリ内の全ファイル ({len(all_files)}個):")
                for i, f in enumerate(all_files[:10]):  # 最初の10個だけ表示
                    log_callback(f"  {i+1}. {f}")
                if len(all_files) > 10:
                    log_callback(f"  ... 他 {len(all_files) - 10}個")
            else:
                log_callback(f"⚠ ディレクトリが存在しません: {save_dir}")
            return None

        images = []
        for png_file in png_files:
            img = Image.open(png_file)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)

        # PDFを一時的にsave_dir内に保存
        temp_pdf_path = osp.join(save_dir, f'{title}.pdf')

        if images:
            images[0].save(
                temp_pdf_path,
                save_all=True,
                append_images=images[1:],
                resolution=100.0,
                quality=95,
                optimize=False
            )

            # PDFを親ディレクトリ（保存先フォルダ直下）に移動
            parent_dir = osp.dirname(save_dir)
            final_pdf_path = osp.join(parent_dir, f'{title}.pdf')

            # 既存のPDFがあれば削除
            if osp.exists(final_pdf_path):
                os.remove(final_pdf_path)

            # PDFを移動
            import shutil
            shutil.move(temp_pdf_path, final_pdf_path)

            file_size = osp.getsize(final_pdf_path) / (1024 * 1024)
            log_callback(f"✓ PDF生成完了: {title}.pdf")
            log_callback(f"  - 保存先: {final_pdf_path}")
            log_callback(f"  - ページ数: {len(images)}")
            log_callback(f"  - ファイルサイズ: {file_size:.2f} MB")

            # 画像フォルダの削除
            if delete_images:
                log_callback("\n画像フォルダを削除中...")
                try:
                    import shutil
                    shutil.rmtree(save_dir)
                    log_callback(f"✓ フォルダを削除しました: {save_dir}")
                except Exception as e:
                    log_callback(f"  ⚠ フォルダ削除失敗: {e}")

            return final_pdf_path

    except Exception as e:
        log_callback(f"⚠ PDF生成に失敗: {e}")
        import traceback
        log_callback(traceback.format_exc())
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

        # 1行目のオプション
        self.create_pdf_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="PDF生成", variable=self.create_pdf_var).grid(row=0, column=0, padx=5, sticky=tk.W)

        self.delete_images_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="画像削除", variable=self.delete_images_var).grid(row=0, column=1, padx=5, sticky=tk.W)

        self.enable_ocr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="OCR実行", variable=self.enable_ocr_var).grid(row=0, column=2, padx=5, sticky=tk.W)

        # ページ送り方向
        ttk.Label(options_frame, text="ページ送り:").grid(row=0, column=3, padx=(15, 5), sticky=tk.W)
        self.page_direction_var = tk.StringVar(value="left")
        direction_combo = ttk.Combobox(options_frame, textvariable=self.page_direction_var,
                                      values=["left", "right"], width=8, state="readonly")
        direction_combo.grid(row=0, column=4, padx=5, sticky=tk.W)

        # 2行目のオプション
        ttk.Label(options_frame, text="待機時間(秒):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.wait_sec_var = tk.DoubleVar(value=0.15)
        wait_spin = ttk.Spinbox(options_frame, from_=0.1, to=2.0, increment=0.05,
                                textvariable=self.wait_sec_var, width=8)
        wait_spin.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # 範囲選択の説明と前回座標使用オプション
        info_frame = ttk.Frame(settings_frame)
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        info_label = ttk.Label(info_frame, text="💡 フルスクリーン後、マウスドラッグで範囲を選択できます",
                              foreground="blue", font=('Arial', 9))
        info_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.use_saved_coords_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(info_frame, text="前回の座標を使用", variable=self.use_saved_coords_var).grid(row=0, column=1, padx=15, sticky=tk.W)

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
            wait_sec = self.wait_sec_var.get()
            delete_images = self.delete_images_var.get()
            enable_ocr = self.enable_ocr_var.get()

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

            # フルスクリーンにする
            self.log("\nフルスクリーンモードに切り替え中...")
            pag.press('f11')
            sc_w, sc_h = pag.size()
            pag.moveTo(sc_w - 200, sc_h - 1)
            time.sleep(2)

            # 座標の取得（保存された座標を使用するか、新たに選択するか）
            use_saved = self.use_saved_coords_var.get()
            selected_coords = None

            if use_saved:
                self.log("\n前回の座標を読み込み中...")
                selected_coords = load_coordinates()
                if selected_coords:
                    top, bottom, left, right = selected_coords
                    self.log(f"✓ 保存された座標を使用:")
                    self.log(f"  上: {top}px, 下: {bottom}px, 左: {left}px, 右: {right}px")
                    self.log(f"  サイズ: {right-left}x{bottom-top}px")
                else:
                    self.log("⚠ 保存された座標が見つかりません。範囲選択を行います。")

            if selected_coords is None:
                # 範囲選択を実行
                self.log("\n範囲選択モードを開始します...")
                self.log("マウスドラッグで範囲を選択してください（ESCでキャンセル）")

                selected_coords = select_area_interactively()

                if stop_capture or selected_coords is None:
                    self.log("\n⏹ 範囲選択がキャンセルされました")
                    pag.press('f11')
                    return

                top, bottom, left, right = selected_coords
                self.log(f"✓ 範囲選択完了:")
                self.log(f"  上: {top}px, 下: {bottom}px, 左: {left}px, 右: {right}px")
                self.log(f"  サイズ: {right-left}x{bottom-top}px")

                # 座標を保存
                if save_coordinates(top, bottom, left, right):
                    self.log("✓ 座標を保存しました（次回使用可能）")

            # ページキャプチャ開始
            original_dir = os.getcwd()
            os.chdir(save_dir)

            # 初期画像の準備（固定サイズでキャプチャ）
            old_img = np.zeros((bottom - top, right - left, 3), np.uint8)
            page = 1

            # ページ送り方向を取得
            page_direction = self.page_direction_var.get()

            self.log(f"\n{'='*60}")
            self.log(f"ページキャプチャ開始")
            self.log(f"  ページ送り方向: {page_direction}")
            self.log(f"{'='*60}\n")

            while not stop_capture:
                filename = str(page).zfill(3) + '.png'

                # 固定座標でキャプチャ
                new_img = wait_for_page_change(old_img, left, right, top, bottom, timeout=5.0, wait_sec=wait_sec)

                if new_img is None:
                    if stop_capture:
                        self.log("\n⏹ ユーザーによって停止されました")
                    else:
                        self.log("\n✓ 最終ページに到達しました")
                    pag.press('f11')
                    break

                old_img = new_img

                # 画像を保存
                cv2.imwrite(filename, new_img)
                self.log(f"Page {page:3d}: {filename} ({new_img.shape[1]}x{new_img.shape[0]}px)")

                page += 1
                pag.press(page_direction)

            os.chdir(original_dir)

            # PDF生成
            if create_pdf and page > 1 and not stop_capture:
                pdf_path = convert_images_to_pdf(save_dir, title, self.log, delete_images=delete_images)

                # OCR処理
                if pdf_path and self.enable_ocr_var.get():
                    perform_ocr_on_pdf(pdf_path, self.log)

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
