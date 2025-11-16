"""
Kindle for PC 自動スクリーンショットツール
ページを自動的にキャプチャしてPNG画像として保存します
"""

import pyautogui as pag
import os
import os.path as osp
import datetime
import time
from PIL import ImageGrab
from tkinter import messagebox, simpledialog
import cv2
import numpy as np
from ctypes import *
from ctypes.wintypes import *

# ========== 設定 ==========
KINDLE_WINDOW_TITLE = 'Kindle'  # Kindle for PCに含まれるウインドウタイトル
PAGE_CHANGE_KEY = 'left'         # 次ページに移動するときのキー

KINDLE_FULLSCREEN_KEY = 'f11'   # フルスクリーンにするときのキー
KINDLE_FULLSCREEN_WAIT = 5      # フルスクリーンにした後の待ち時間(秒)

L_MARGIN = 1                     # サイズ自動設定のときの左側マージン
R_MARGIN = 1                     # サイズ自動設定のときの右側マージン
WAIT_SEC = 0.15                  # キーを押してからスクリーンショットを撮る待ち時間(秒)
PAGE_TIMEOUT = 5.0               # ページ変更を待つ最大時間(秒)

BASE_SAVE_FOLDER = 'e:\\kss\\'   # 保存する場所 タイトルの前に入れられる
KEY_PRESS_DURATION = 0.1         # キー押下の持続時間(秒)

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
    """画像からコンテンツ領域の左右端を検出する"""
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


def capture_page(left, right):
    """現在のページをキャプチャする"""
    img = ImageGrab.grab()
    img = np.array(img)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img_bgr[:, left:right]


def wait_for_page_change(old_img, left, right, timeout=PAGE_TIMEOUT):
    """ページが変わるまで待機する"""
    start = time.perf_counter()

    while True:
        time.sleep(WAIT_SEC)
        new_img = capture_page(left, right)

        if not np.array_equal(old_img, new_img):
            return new_img

        if time.perf_counter() - start > timeout:
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

    # フルスクリーンにする
    pag.press(KINDLE_FULLSCREEN_KEY)
    sc_w, sc_h = pag.size()

    # タイトルを取得
    title = get_title()

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

    # コンテンツ領域を検出
    start = time.perf_counter()
    try:
        left, right = detect_content_area(img_bgr)
        print(f"コンテンツ領域検出完了: {time.perf_counter() - start:.3f}秒")
        print(f"左端: {left}, 右端: {right}, 幅: {right - left}px")
    except ValueError as e:
        messagebox.showerror("エラー", str(e))
        return 1

    # 保存ディレクトリを作成
    original_dir = os.getcwd()
    try:
        save_dir = create_save_directory(BASE_SAVE_FOLDER, title)
        os.chdir(save_dir)
        print(f"保存先: {save_dir}")
    except Exception:
        return 1

    # 初期ページをキャプチャ
    img_cropped = img_bgr[:, left:right]
    old_img = np.zeros((sc_h, right - left, 3), np.uint8)
    page = 1

    print(f"画像サイズ: {old_img.shape}")
    print("キャプチャ開始...")

    try:
        while True:
            filename = str(page).zfill(3) + '.png'
            start = time.perf_counter()

            # ページが変わるまで待機
            new_img = wait_for_page_change(old_img, left, right)

            if new_img is None:
                # タイムアウト（最終ページと判断）
                print("ページ変更を検出できませんでした。終了します。")
                pag.press(KINDLE_FULLSCREEN_KEY)
                break

            # 画像を保存
            try:
                cv2.imwrite(filename, new_img)
                elapsed = time.perf_counter() - start
                print(f'Page: {page:3d} | サイズ: {new_img.shape} | 時間: {elapsed:.3f}秒')
            except Exception as e:
                print(f"ページ {page} の保存に失敗: {e}")

            old_img = new_img
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

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
