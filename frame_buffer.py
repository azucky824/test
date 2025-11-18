"""
フレームバッファクラス - 遅延再生用のフレーム管理
"""
from collections import deque
import threading
import time


class FrameBuffer:
    """遅延再生のためのフレームバッファを管理するクラス"""

    def __init__(self, delay_seconds=3, fps=30):
        """
        Args:
            delay_seconds (int): 遅延秒数
            fps (int): フレームレート
        """
        self.delay_seconds = delay_seconds
        self.fps = fps
        self.buffer_size = delay_seconds * fps
        self.buffer = deque(maxlen=self.buffer_size)
        self.lock = threading.Lock()

    def add_frame(self, frame, timestamp):
        """バッファにフレームを追加

        Args:
            frame: 画像フレーム（numpy array）
            timestamp (float): タイムスタンプ
        """
        with self.lock:
            self.buffer.append((frame, timestamp))

    def get_delayed_frame(self):
        """遅延したフレームを取得

        Returns:
            tuple: (frame, timestamp) または (None, None)
        """
        with self.lock:
            if len(self.buffer) < self.buffer_size:
                # バッファが満たされていない場合は最初のフレーム
                if len(self.buffer) > 0:
                    return self.buffer[0]
                return None, None
            else:
                # バッファが満たされている場合は最も古いフレーム
                return self.buffer[0]

    def update_delay(self, delay_seconds):
        """遅延秒数を更新

        Args:
            delay_seconds (int): 新しい遅延秒数
        """
        with self.lock:
            self.delay_seconds = delay_seconds
            new_size = delay_seconds * self.fps

            # 新しいサイズでバッファを再構築
            if new_size < len(self.buffer):
                # サイズが小さくなる場合、最新のフレームを保持
                self.buffer = deque(list(self.buffer)[-new_size:], maxlen=new_size)
            else:
                # サイズが大きくなる場合
                self.buffer = deque(self.buffer, maxlen=new_size)

            self.buffer_size = new_size

    def clear(self):
        """バッファをクリア"""
        with self.lock:
            self.buffer.clear()

    def is_ready(self):
        """バッファが準備完了か確認

        Returns:
            bool: バッファが満たされている場合True
        """
        with self.lock:
            return len(self.buffer) >= self.buffer_size

    def get_fill_percentage(self):
        """バッファの充填率を取得

        Returns:
            float: 充填率（0.0-1.0）
        """
        with self.lock:
            if self.buffer_size == 0:
                return 0.0
            return len(self.buffer) / self.buffer_size
