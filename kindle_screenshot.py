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

# ========== 設定 ==========
KINDLE_WINDOW_TITLE = 'Kindle'  # Kindle for PCに含まれるウインドウタイトル
PAGE_CHANGE_KEY = 'left'         # 次ページに移動するときのキー

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
CAPTURE_TOC = True               # 目次をキャプチャするかどうか

# 余白トリミング設定
TRIM_MARGINS = True              # 余白を自動トリミングするかどうか
TRIM_EACH_PAGE = True            # ページごとに余白検出を行うかどうか

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


def capture_table_of_contents(save_dir):
    """Kindleの目次をキャプチャする"""
    try:
        print("\n目次をキャプチャ中...")

        # 目次を開く
        pag.hotkey('ctrl', 't')
        time.sleep(2)  # 目次が表示されるまで待機

        # 目次のスクリーンショットを撮る
        toc_img = ImageGrab.grab()
        toc_path = osp.join(save_dir, 'table_of_contents.png')
        toc_img.save(toc_path)
        print(f"目次を保存しました: {toc_path}")

        # 目次を閉じる（ESCキー）
        pag.press('esc')
        time.sleep(1)

        return toc_path
    except Exception as e:
        print(f"目次のキャプチャに失敗: {e}")
        return None


def convert_images_to_pdf(save_dir, title):
    """PNG画像をPDFに変換する"""
    try:
        print("\nPDFを生成中...")

        # PNG画像を取得（番号順にソート）
        png_files = sorted(glob.glob(osp.join(save_dir, '*.png')))

        # table_of_contents.pngを除外
        png_files = [f for f in png_files if not f.endswith('table_of_contents.png')]

        if not png_files:
            print("PNG画像が見つかりませんでした")
            return None

        # 画像をPILで読み込み
        images = []
        for png_file in png_files:
            img = Image.open(png_file)
            # RGBモードに変換（PDFはRGBAをサポートしない場合がある）
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)

        # PDFとして保存
        pdf_path = osp.join(save_dir, f'{title}.pdf')

        if images:
            # 最初の画像を基準に、残りを追加
            images[0].save(
                pdf_path,
                save_all=True,
                append_images=images[1:],
                resolution=100.0,
                quality=95,
                optimize=False
            )
            print(f"PDFを生成しました: {pdf_path}")
            print(f"  - ページ数: {len(images)}")

            # ファイルサイズを表示
            file_size = osp.getsize(pdf_path) / (1024 * 1024)
            print(f"  - ファイルサイズ: {file_size:.2f} MB")

            return pdf_path

    except Exception as e:
        print(f"PDF生成に失敗: {e}")
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

    # 目次をキャプチャ（フルスクリーン前）
    if CAPTURE_TOC:
        capture_table_of_contents(save_dir)
        # Kindleウィンドウを再度アクティブにする
        activate_kindle_window(hwnd)

    # フルスクリーンにする
    pag.press(KINDLE_FULLSCREEN_KEY)
    sc_w, sc_h = pag.size()

    # マウスを画面外に移動
    pag.moveTo(sc_w - 200, sc_h - 1)

    # フルスクリーン化の待機
    time.sleep(KINDLE_FULLSCREEN_WAIT)

    # 初期画面をキャプチャしてコンテンツ領域を検出
    print("コンテンツ領域を検出中...")
    start = time.perf_counter()
    img = ImageGrab.grab()
    img = np.array(img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    print(f"初期キャプチャ完了: {time.perf_counter() - start:.3f}秒")

    # 余白トリミングの設定
    top, bottom, left, right = None, None, None, None

    if TRIM_MARGINS:
        try:
            # 4方向の余白を検出
            top, bottom, left, right = detect_content_area_full(img_bgr, threshold=250, margin=10)
            print(f"✓ 余白検出完了")
            print(f"  上: {top}px, 下: {bottom}px, 左: {left}px, 右: {right}px")
            print(f"  サイズ: {right-left}x{bottom-top}px")
        except ValueError as e:
            print(f"⚠ 余白検出に失敗、代替方法を使用: {e}")
            # フォールバック: 左右のみ検出
            left, right = detect_content_area(img_bgr)
            top, bottom = 0, sc_h
            print(f"✓ 左右の端のみ検出 (左: {left}px, 右: {right}px)")
    else:
        # 余白トリミングなし（旧方式）
        left, right = detect_content_area(img_bgr)
        top, bottom = 0, sc_h
        print(f"✓ 左右の端のみ検出 (左: {left}px, 右: {right}px)")

    # 作業ディレクトリを変更
    os.chdir(save_dir)

    # 初期画像の準備
    if TRIM_MARGINS and TRIM_EACH_PAGE:
        # ページごとに余白検出する場合、サイズ不定なのでNoneにする
        old_img = None
        print("\n💡 ページごとに余白を検出します")
    else:
        # 固定サイズでキャプチャ
        old_img = np.zeros((bottom - top, right - left, 3), np.uint8)

    page = 1

    if not (TRIM_MARGINS and TRIM_EACH_PAGE):
        print(f"画像サイズ: {old_img.shape}")
    print("キャプチャ開始...")

    try:
        while True:
            filename = str(page).zfill(3) + '.png'
            start = time.perf_counter()

            if TRIM_MARGINS and TRIM_EACH_PAGE:
                # ページごとに余白検出
                time.sleep(WAIT_SEC)

                # 前のページと比較するための一時画像
                temp_img = ImageGrab.grab()
                temp_img = np.array(temp_img)
                temp_img_bgr = cv2.cvtColor(temp_img, cv2.COLOR_RGB2BGR)

                # 最初のページまたはページが変わるまで待機
                if old_img is not None and np.array_equal(old_img, temp_img_bgr):
                    # ページが変わるまで待機
                    start_time = time.perf_counter()
                    while time.perf_counter() - start_time < PAGE_TIMEOUT:
                        time.sleep(WAIT_SEC)
                        temp_img = ImageGrab.grab()
                        temp_img = np.array(temp_img)
                        temp_img_bgr = cv2.cvtColor(temp_img, cv2.COLOR_RGB2BGR)
                        if not np.array_equal(old_img, temp_img_bgr):
                            break

                    if time.perf_counter() - start_time >= PAGE_TIMEOUT:
                        print("ページ変更を検出できませんでした。終了します。")
                        pag.press(KINDLE_FULLSCREEN_KEY)
                        break

                # ページごとに余白を検出してトリミング
                try:
                    page_top, page_bottom, page_left, page_right = detect_content_area_full(temp_img_bgr, threshold=250, margin=10)
                    new_img = temp_img_bgr[page_top:page_bottom, page_left:page_right]
                except Exception as e:
                    print(f"⚠ Page {page}: 余白検出失敗、画像全体を保存: {e}")
                    new_img = temp_img_bgr

                old_img = temp_img_bgr  # 次の比較用
            else:
                # 固定サイズでキャプチャ
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

            # 次のページへ（修正: keyDownのリークを防ぐ）
            pag.press(PAGE_CHANGE_KEY)

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
            pdf_path = convert_images_to_pdf(save_dir, title)
            if pdf_path:
                print(f"\n✓ 処理が完了しました")
                print(f"  PDF: {pdf_path}")
            else:
                print("\n⚠ PNG画像は保存されましたが、PDF生成に失敗しました")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
