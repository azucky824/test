"""
GUI アプリケーション - 遅延ビデオ再生のメインインターフェース
"""
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import time
from camera_capture import CameraCapture
from frame_buffer import FrameBuffer


class DelayedVideoApp:
    """遅延ビデオ再生アプリケーションのGUIクラス"""

    def __init__(self, root):
        """
        Args:
            root: tkinterのルートウィンドウ
        """
        self.root = root
        self.root.title("遅延ビデオ再生アプリ")
        self.root.geometry("800x700")

        # カメラとバッファの初期化
        self.camera = CameraCapture(camera_index=0, fps=30)
        self.delay_seconds = 3
        self.buffer = FrameBuffer(delay_seconds=self.delay_seconds, fps=30)

        # 実行状態
        self.running = False
        self.update_job = None

        # GUI構築
        self._create_widgets()

        # ウィンドウクローズ時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        """GUIウィジェットを作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ビデオ表示エリア
        self.canvas = tk.Canvas(main_frame, width=640, height=480, bg="black")
        self.canvas.grid(row=0, column=0, columnspan=3, pady=10)

        # 状態表示ラベル
        self.status_label = ttk.Label(main_frame, text="停止中", font=("Arial", 12))
        self.status_label.grid(row=1, column=0, columnspan=3, pady=5)

        # FPS表示
        self.fps_label = ttk.Label(main_frame, text="FPS: 0.0", font=("Arial", 10))
        self.fps_label.grid(row=2, column=0, columnspan=3)

        # バッファ状態表示
        self.buffer_label = ttk.Label(main_frame, text="バッファ: 0%", font=("Arial", 10))
        self.buffer_label.grid(row=3, column=0, columnspan=3)

        # 遅延秒数設定
        delay_frame = ttk.Frame(main_frame)
        delay_frame.grid(row=4, column=0, columnspan=3, pady=20)

        ttk.Label(delay_frame, text="遅延秒数:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)

        self.delay_var = tk.IntVar(value=self.delay_seconds)
        self.delay_label_value = ttk.Label(delay_frame, text=f"{self.delay_seconds}秒", font=("Arial", 11, "bold"))
        self.delay_label_value.pack(side=tk.LEFT, padx=5)

        self.delay_slider = ttk.Scale(
            delay_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            length=300,
            variable=self.delay_var,
            command=self._on_delay_change
        )
        self.delay_slider.pack(side=tk.LEFT, padx=10)

        # コントロールボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(
            button_frame,
            text="開始",
            command=self.start,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = ttk.Button(
            button_frame,
            text="停止",
            command=self.stop,
            width=15,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def _on_delay_change(self, value):
        """遅延秒数スライダーの変更ハンドラ"""
        delay = int(float(value))
        self.delay_seconds = delay
        self.delay_label_value.config(text=f"{delay}秒")

        # 実行中の場合はバッファを更新
        if self.running:
            self.buffer.update_delay(delay)

    def start(self):
        """カメラと遅延再生を開始"""
        if self.running:
            return

        # カメラ開始
        if not self.camera.start():
            self.status_label.config(text="エラー: カメラを開けません")
            return

        # バッファをリセット
        self.buffer = FrameBuffer(delay_seconds=self.delay_seconds, fps=30)

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="実行中")

        # 更新ループ開始
        self._update_frame()

    def stop(self):
        """カメラと遅延再生を停止"""
        if not self.running:
            return

        self.running = False
        self.camera.stop()

        # 更新ジョブをキャンセル
        if self.update_job:
            self.root.after_cancel(self.update_job)
            self.update_job = None

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="停止中")

        # キャンバスをクリア
        self.canvas.delete("all")

    def _update_frame(self):
        """フレームを更新（定期的に呼び出される）"""
        if not self.running:
            return

        # カメラから最新フレームを取得してバッファに追加
        frame, timestamp = self.camera.get_frame()
        if frame is not None:
            self.buffer.add_frame(frame, timestamp)

        # 遅延したフレームを取得して表示
        delayed_frame, _ = self.buffer.get_delayed_frame()
        if delayed_frame is not None:
            self._display_frame(delayed_frame)

        # FPS表示を更新
        fps = self.camera.get_fps()
        self.fps_label.config(text=f"FPS: {fps:.1f}")

        # バッファ状態を更新
        buffer_pct = self.buffer.get_fill_percentage() * 100
        self.buffer_label.config(text=f"バッファ: {buffer_pct:.0f}%")

        # 次のフレーム更新をスケジュール（約30fps）
        self.update_job = self.root.after(33, self._update_frame)

    def _display_frame(self, frame):
        """フレームをキャンバスに表示

        Args:
            frame: OpenCVフォーマットの画像（BGR）
        """
        # BGRからRGBに変換
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # PIL Imageに変換
        image = Image.fromarray(rgb_frame)

        # キャンバスサイズに合わせてリサイズ
        image = image.resize((640, 480), Image.Resampling.LANCZOS)

        # PhotoImageに変換
        photo = ImageTk.PhotoImage(image=image)

        # キャンバスに表示
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)

        # 参照を保持（ガベージコレクション防止）
        self.canvas.image = photo

    def on_closing(self):
        """ウィンドウクローズ時の処理"""
        self.stop()
        self.root.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    root = tk.Tk()
    app = DelayedVideoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
