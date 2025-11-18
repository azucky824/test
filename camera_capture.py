"""
カメラキャプチャクラス - リアルタイムでカメラから映像を取得
"""
import cv2
import threading
import time


class CameraCapture:
    """カメラからのフレーム取得を管理するクラス"""

    def __init__(self, camera_index=0, fps=30):
        """
        Args:
            camera_index (int): カメラデバイスインデックス
            fps (int): 目標フレームレート
        """
        self.camera_index = camera_index
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.capture = None
        self.running = False
        self.thread = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0

    def start(self):
        """カメラキャプチャを開始"""
        if self.running:
            return False

        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            return False

        # カメラの解像度を設定（オプション）
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        """カメラキャプチャを停止"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.capture:
            self.capture.release()
            self.capture = None

    def _capture_loop(self):
        """カメラからフレームを取得するループ（別スレッド）"""
        while self.running:
            loop_start = time.time()

            ret, frame = self.capture.read()
            if ret:
                timestamp = time.time()
                with self.frame_lock:
                    self.current_frame = (frame.copy(), timestamp)
                    self.frame_count += 1

                # FPS計算
                if self.frame_count % 30 == 0:
                    current_time = time.time()
                    elapsed = current_time - self.last_fps_time
                    if elapsed > 0:
                        self.current_fps = 30 / elapsed
                    self.last_fps_time = current_time

            # フレームレート制御
            elapsed = time.time() - loop_start
            sleep_time = self.frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_frame(self):
        """最新のフレームを取得

        Returns:
            tuple: (frame, timestamp) または (None, None)
        """
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame
            return None, None

    def get_fps(self):
        """現在のFPSを取得

        Returns:
            float: FPS値
        """
        return self.current_fps

    def is_opened(self):
        """カメラが開かれているか確認

        Returns:
            bool: カメラが開かれている場合True
        """
        return self.capture is not None and self.capture.isOpened()
