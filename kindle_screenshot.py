"""
Kindle for PC 自動スクリーンショットツール
ページを自動的にキャプチャしてPNG画像として保存し、PDFに変換します
"""

import pyautogui as pag
import os
import os.path as osp
import datetime
import time
from PIL import ImageGrab, Image
from tkinter import messagebox, simpledialog, Tk
import cv2
import numpy as np
from ctypes import *
from ctypes.wintypes import *
import glob
import json

# ========== 設定 ==========
KINDLE_WINDOW_TITLE = 'Kindle'  # Kindle for PCに含まれるウインドウタイトル
PAGE_DIRECTION = 'left'          # ページ送り方向（'left' または 'right'）

KINDLE_FULLSCREEN_KEY = 'f11'   # フルスクリーンにするときのキー
KINDLE_FULLSCREEN_WAIT = 5      # フルスクリーンにした後の待ち時間(秒)
KINDLE_TOC_KEY = 'ctrl+t'        # 目次を開くキー

L_MARGIN = 1                     # サイズ自動設定のときの左側マージン
R_MARGIN = 1                     # サイズ自動設定のときの右側マージン
WAIT_SEC = 0.15                  # キーを押してからスクリーンショットを撮る待ち時間(秒)
PAGE_TIMEOUT = 5.0               # ページ変更を待つ最大時間(秒)

BASE_SAVE_FOLDER = r'C:\Users\azuck\Downloads'   # 保存する場所 タイトルの前に入れられる
KEY_PRESS_DURATION = 0.1         # キー押下の持続時間(秒)

# PDF生成設定
CREATE_PDF = True                # PDF生成を行うかどうか
DELETE_IMAGES = True             # PDF生成後にPNG画像を削除するか
ENABLE_OCR = True                # OCRを実行して検索可能なPDFを生成するか

# 座標設定
USE_SAVED_COORDS = False         # 前回保存した座標を使用するか
# トリミング座標設定（Noneの場合は自動検出、USE_SAVED_COORDS=Trueの場合は保存された座標を優先）
# 例: TRIM_TOP = 100, TRIM_BOTTOM = 1920, TRIM_LEFT = 200, TRIM_RIGHT = 1720
TRIM_TOP = None                  # トリミング上端（px）
TRIM_BOTTOM = None               # トリミング下端（px）
TRIM_LEFT = None                 # トリミング左端（px）
TRIM_RIGHT = None                # トリミング右端（px）

# ========== Windows API 設定 ==========
EnumWindows = windll.user32.EnumWindows
GetWindowText = windll.user32.GetWindowTextW
GetWindowTextLength = windll.user32.GetWindowTextLengthW
GetWindowRect = windll.user32.GetWindowRect
SetForegroundWindow = windll.user32.SetForegroundWindow

WNDENUMPROC = WINFUNCTYPE(c_bool, POINTER(c_int), POINTER(c_int))


def find_kindle_window():
    """Kindleウィンドウを検索する"""
    hwnd_found = None

    def enum_windows_proc(hwnd, lParam):
        nonlocal hwnd_found
        length = GetWindowTextLength(hwnd)
        buff = create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buff, length + 1)

        if buff.value.find(KINDLE_WINDOW_TITLE) != -1:
            hwnd_found = hwnd
            return False
        return True

    EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
    return hwnd_found


def activate_kindle_window(hwnd):
    """Kindleウィンドウをアクティブにする"""
    SetForegroundWindow(hwnd)
    rect = RECT()
    GetWindowRect(hwnd, pointer(rect))
    pag.moveTo(rect.left + 60, rect.top + 10)
    pag.click()
    time.sleep(1)


def detect_content_area(img):
    """画像からコンテンツ領域の左右端を検出する（旧バージョン）"""
    def find_edge(img, rng):
        for i in rng:
            if np.all(img[20][i] != img[19][0]):
                return i
        return None

    left = find_edge(img, range(L_MARGIN, img.shape[1] - R_MARGIN))
    right = find_edge(img, reversed(range(L_MARGIN, img.shape[1] - R_MARGIN)))

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


def get_title():
    """ユーザーにタイトルを入力させる"""
    default_title = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    title = simpledialog.askstring('タイトルを入力', 'タイトルを入力して下さい(空白の場合現在の時刻)')

    if title and title.strip():
        return title.strip()
    return default_title


def create_save_directory(base_folder, title):
    """保存ディレクトリを作成する"""
    save_path = osp.join(base_folder, title)

    try:
        os.makedirs(save_path, exist_ok=True)
        return save_path
    except Exception as e:
        messagebox.showerror("エラー", f"ディレクトリの作成に失敗しました: {e}")
        raise


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


def wait_for_page_change(old_img, left, right, top=None, bottom=None, timeout=PAGE_TIMEOUT):
    """ページが変わるまで待機する"""
    start = time.perf_counter()

    while True:
        time.sleep(WAIT_SEC)
        new_img = capture_page(left, right, top, bottom)

        if not np.array_equal(old_img, new_img):
            return new_img

        if time.perf_counter() - start > timeout:
            return None


def perform_ocr_on_pdf(pdf_path):
    """PDFにOCRを実行して検索可能なPDFを生成する

    Args:
        pdf_path: 入力PDFファイルのパス

    Returns:
        成功時: OCR処理後のPDFパス、失敗時: None
    """
    try:
        import ocrmypdf

        print("\nOCR処理を開始...")
        print("⚠ 初回実行時は時間がかかる場合があります")

        # 出力ファイル名（元のファイルを上書き）
        output_path = pdf_path

        # 一時ファイルを作成
        temp_output = pdf_path.replace('.pdf', '_ocr_temp.pdf')

        # OCR実行（日本語と英語）
        print("OCRエンジンを実行中（日本語+英語）...")

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
            print(f"✓ OCR処理完了")
            print(f"  - 検索可能なPDF: {output_path}")
            print(f"  - ファイルサイズ: {file_size:.2f} MB")
            return output_path
        else:
            print("⚠ OCR処理に失敗しました")
            return None

    except ImportError:
        print("⚠ OCRmyPDFがインストールされていません")
        print("  インストール方法: pip install ocrmypdf")
        print("  Tesseractも必要です: https://github.com/tesseract-ocr/tesseract")
        return None
    except Exception as e:
        print(f"⚠ OCR処理中にエラーが発生: {e}")
        # 一時ファイルをクリーンアップ
        temp_output = pdf_path.replace('.pdf', '_ocr_temp.pdf')
        if osp.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass
        return None


def convert_images_to_pdf(save_dir, title, delete_images=False):
    """PNG画像をPDFに変換する

    Args:
        save_dir: 保存ディレクトリ
        title: PDFのタイトル
        delete_images: PDF生成後にPNG画像を削除するか
    """
    try:
        print("\nPDFを生成中...")
        print(f"検索ディレクトリ: {save_dir}")

        # PNG画像を取得（os.listdirを使用してglobの特殊文字問題を回避）
        all_files = os.listdir(save_dir)
        png_files = [f for f in all_files if f.endswith('.png')]

        # 番号順にソート（001.png, 002.png, ...）
        png_files = sorted(png_files)

        print(f"見つかったPNGファイル: {len(png_files)}個")

        if png_files:
            print(f"最初のファイル: {png_files[0]}")
            print(f"最後のファイル: {png_files[-1]}")

        # 絶対パスに変換
        png_files = [osp.join(save_dir, f) for f in png_files]

        if not png_files:
            print("⚠ PNG画像が見つかりませんでした")
            print(f"確認: ディレクトリ '{save_dir}' にファイルが存在するか確認してください")
            # ディレクトリの内容を確認
            if osp.exists(save_dir):
                all_files = os.listdir(save_dir)
                print(f"ディレクトリ内の全ファイル ({len(all_files)}個):")
                for i, f in enumerate(all_files[:10]):  # 最初の10個だけ表示
                    print(f"  {i+1}. {f}")
                if len(all_files) > 10:
                    print(f"  ... 他 {len(all_files) - 10}個")
            else:
                print(f"⚠ ディレクトリが存在しません: {save_dir}")
            return None

        # 画像をPILで読み込み
        images = []
        for png_file in png_files:
            img = Image.open(png_file)
            # RGBモードに変換（PDFはRGBAをサポートしない場合がある）
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)

        # PDFを一時的にsave_dir内に保存
        temp_pdf_path = osp.join(save_dir, f'{title}.pdf')

        if images:
            # 最初の画像を基準に、残りを追加
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

            print(f"✓ PDFを生成しました: {final_pdf_path}")
            print(f"  - ページ数: {len(images)}")

            # ファイルサイズを表示
            file_size = osp.getsize(final_pdf_path) / (1024 * 1024)
            print(f"  - ファイルサイズ: {file_size:.2f} MB")

            # PNG画像の削除
            if delete_images:
                print("\nPNG画像を削除中...")
                deleted_count = 0
                for png_file in png_files:
                    try:
                        os.remove(png_file)
                        deleted_count += 1
                    except Exception as e:
                        print(f"  ⚠ 削除失敗: {osp.basename(png_file)} - {e}")
                print(f"✓ {deleted_count}/{len(png_files)} 個のPNG画像を削除しました")

            return final_pdf_path

    except Exception as e:
        print(f"⚠ PDF生成に失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """メイン処理"""
    # Kindleウィンドウを検索
    hwnd = find_kindle_window()
    if hwnd is None:
        messagebox.showerror("エラー", "Kindleが見つかりません")
        return 1

    # Kindleウィンドウをアクティブにする
    activate_kindle_window(hwnd)

    # タイトルを取得（フルスクリーン前に取得）
    title = get_title()

    # 保存ディレクトリを作成
    original_dir = os.getcwd()
    try:
        save_dir = create_save_directory(BASE_SAVE_FOLDER, title)
        print(f"保存先: {save_dir}")
    except Exception:
        return 1

    # フルスクリーンにする
    pag.press(KINDLE_FULLSCREEN_KEY)
    sc_w, sc_h = pag.size()

    # マウスを画面外に移動
    pag.moveTo(sc_w - 200, sc_h - 1)

    # フルスクリーン化の待機
    time.sleep(KINDLE_FULLSCREEN_WAIT)

    # トリミング座標を設定
    coords_set = False

    # 1. 保存された座標を使用する設定の場合
    if USE_SAVED_COORDS:
        print("\n前回保存した座標を読み込み中...")
        saved_coords = load_coordinates()
        if saved_coords:
            top, bottom, left, right = saved_coords
            print(f"✓ 保存された座標を使用:")
            print(f"  上: {top}px, 下: {bottom}px, 左: {left}px, 右: {right}px")
            print(f"  サイズ: {right-left}x{bottom-top}px")
            coords_set = True
        else:
            print("⚠ 保存された座標が見つかりません。自動検出を行います。")

    # 2. 固定座標が設定されている場合
    if not coords_set and all(coord is not None for coord in [TRIM_TOP, TRIM_BOTTOM, TRIM_LEFT, TRIM_RIGHT]):
        top, bottom, left, right = TRIM_TOP, TRIM_BOTTOM, TRIM_LEFT, TRIM_RIGHT
        print("\n固定座標でトリミング:")
        print(f"  上: {top}px, 下: {bottom}px, 左: {left}px, 右: {right}px")
        print(f"  サイズ: {right-left}x{bottom-top}px")
        coords_set = True

    # 3. 自動検出
    if not coords_set:
        print("\nコンテンツ領域を自動検出中...")
        start = time.perf_counter()
        img = ImageGrab.grab()
        img = np.array(img)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        print(f"初期キャプチャ完了: {time.perf_counter() - start:.3f}秒")

        try:
            # 4方向の余白を検出
            top, bottom, left, right = detect_content_area_full(img_bgr, threshold=250, margin=10)
            print(f"✓ 余白検出完了")
            print(f"  上: {top}px, 下: {bottom}px, 左: {left}px, 右: {right}px")
            print(f"  サイズ: {right-left}x{bottom-top}px")

            # 自動検出した座標を保存
            if save_coordinates(top, bottom, left, right):
                print("✓ 座標を保存しました（次回USE_SAVED_COORDS=Trueで使用可能）")
        except ValueError as e:
            print(f"⚠ 余白検出に失敗、代替方法を使用: {e}")
            # フォールバック: 左右のみ検出
            left, right = detect_content_area(img_bgr)
            top, bottom = 0, sc_h
            print(f"✓ 左右の端のみ検出 (左: {left}px, 右: {right}px)")

    # 作業ディレクトリを変更
    os.chdir(save_dir)

    # 初期画像の準備（固定サイズでキャプチャ）
    old_img = np.zeros((bottom - top, right - left, 3), np.uint8)
    page = 1

    print(f"\n画像サイズ: {old_img.shape}")
    print(f"ページ送り方向: {PAGE_DIRECTION}")
    print("キャプチャ開始...\n")

    try:
        while True:
            filename = str(page).zfill(3) + '.png'
            start = time.perf_counter()

            # 固定座標でキャプチャ
            new_img = wait_for_page_change(old_img, left, right, top, bottom)

            if new_img is None:
                # タイムアウト（最終ページと判断）
                print("ページ変更を検出できませんでした。終了します。")
                pag.press(KINDLE_FULLSCREEN_KEY)
                break

            old_img = new_img

            # 画像を保存
            try:
                cv2.imwrite(filename, new_img)
                elapsed = time.perf_counter() - start
                print(f'Page: {page:3d} | サイズ: {new_img.shape[1]}x{new_img.shape[0]}px | 時間: {elapsed:.3f}秒')
            except Exception as e:
                print(f"ページ {page} の保存に失敗: {e}")

            page += 1

            # 次のページへ（ページ送り方向を使用）
            pag.press(PAGE_DIRECTION)

    except KeyboardInterrupt:
        print("\n\nユーザーによって中断されました")
        pag.press(KINDLE_FULLSCREEN_KEY)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        pag.press(KINDLE_FULLSCREEN_KEY)
    finally:
        os.chdir(original_dir)
        print(f"\n合計 {page - 1} ページをキャプチャしました")

        # PDFを生成
        if CREATE_PDF and page > 1:
            pdf_path = convert_images_to_pdf(save_dir, title, delete_images=DELETE_IMAGES)
            if pdf_path:
                # OCR処理
                if ENABLE_OCR:
                    ocr_path = perform_ocr_on_pdf(pdf_path)
                    if ocr_path:
                        print(f"\n✓ 処理が完了しました")
                        print(f"  検索可能なPDF: {ocr_path}")
                    else:
                        print(f"\n⚠ PDFは生成されましたが、OCR処理に失敗しました")
                        print(f"  PDF: {pdf_path}")
                else:
                    print(f"\n✓ 処理が完了しました")
                    print(f"  PDF: {pdf_path}")
            else:
                print("\n⚠ PNG画像は保存されましたが、PDF生成に失敗しました")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
