"""
姿勢検出モジュール
MediaPipe Poseを使用して画像から姿勢のランドマークを検出
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Dict, Tuple, List


class PoseDetector:
    """姿勢検出クラス"""

    # MediaPipe Poseランドマークインデックス
    LANDMARKS = {
        'NOSE': 0,
        'LEFT_EYE_INNER': 1,
        'LEFT_EYE': 2,
        'LEFT_EYE_OUTER': 3,
        'RIGHT_EYE_INNER': 4,
        'RIGHT_EYE': 5,
        'RIGHT_EYE_OUTER': 6,
        'LEFT_EAR': 7,
        'RIGHT_EAR': 8,
        'MOUTH_LEFT': 9,
        'MOUTH_RIGHT': 10,
        'LEFT_SHOULDER': 11,
        'RIGHT_SHOULDER': 12,
        'LEFT_ELBOW': 13,
        'RIGHT_ELBOW': 14,
        'LEFT_WRIST': 15,
        'RIGHT_WRIST': 16,
        'LEFT_PINKY': 17,
        'RIGHT_PINKY': 18,
        'LEFT_INDEX': 19,
        'RIGHT_INDEX': 20,
        'LEFT_THUMB': 21,
        'RIGHT_THUMB': 22,
        'LEFT_HIP': 23,
        'RIGHT_HIP': 24,
        'LEFT_KNEE': 25,
        'RIGHT_KNEE': 26,
        'LEFT_ANKLE': 27,
        'RIGHT_ANKLE': 28,
        'LEFT_HEEL': 29,
        'RIGHT_HEEL': 30,
        'LEFT_FOOT_INDEX': 31,
        'RIGHT_FOOT_INDEX': 32
    }

    def __init__(self):
        """初期化"""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )

    def detect(self, image_path: str) -> Optional[Dict]:
        """
        画像から姿勢を検出

        Args:
            image_path: 画像ファイルのパス

        Returns:
            検出結果の辞書（landmarks, image_shape等）
            検出失敗時はNone
        """
        # 画像を読み込み
        image = cv2.imread(image_path)
        if image is None:
            return None

        # BGRからRGBに変換
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 姿勢検出
        results = self.pose.process(image_rgb)

        if not results.pose_landmarks:
            return None

        # ランドマークを辞書形式で保存
        landmarks = []
        for landmark in results.pose_landmarks.landmark:
            landmarks.append({
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            })

        return {
            'landmarks': landmarks,
            'image_shape': image.shape,
            'image_path': image_path
        }

    def draw_landmarks(self, image_path: str, detection_result: Dict) -> np.ndarray:
        """
        画像にランドマークを描画

        Args:
            image_path: 元画像のパス
            detection_result: detect()の結果

        Returns:
            ランドマークが描画された画像
        """
        # 画像を読み込み
        image = cv2.imread(image_path)
        if image is None:
            return None

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # ランドマークを再構築
        landmark_list = []
        for lm in detection_result['landmarks']:
            landmark = self.mp_pose.PoseLandmark.__new__(self.mp_pose.PoseLandmark)
            landmark.x = lm['x']
            landmark.y = lm['y']
            landmark.z = lm['z']
            landmark.visibility = lm['visibility']
            landmark_list.append(landmark)

        # MediaPipeのランドマークリスト形式に変換
        pose_landmarks = type('obj', (object,), {
            'landmark': landmark_list
        })()

        # ランドマークを描画
        self.mp_drawing.draw_landmarks(
            image_rgb,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )

        return image_rgb

    def get_landmark(self, detection_result: Dict, landmark_name: str) -> Optional[Dict]:
        """
        特定のランドマークを取得

        Args:
            detection_result: detect()の結果
            landmark_name: ランドマーク名（例: 'LEFT_SHOULDER'）

        Returns:
            ランドマーク情報の辞書
        """
        if landmark_name not in self.LANDMARKS:
            return None

        index = self.LANDMARKS[landmark_name]
        if index >= len(detection_result['landmarks']):
            return None

        return detection_result['landmarks'][index]

    def get_key_landmarks(self, detection_result: Dict) -> Dict:
        """
        主要なランドマークを取得

        Args:
            detection_result: detect()の結果

        Returns:
            主要ランドマークの辞書
        """
        key_names = [
            'NOSE', 'LEFT_EAR', 'RIGHT_EAR',
            'LEFT_SHOULDER', 'RIGHT_SHOULDER',
            'LEFT_HIP', 'RIGHT_HIP',
            'LEFT_KNEE', 'RIGHT_KNEE',
            'LEFT_ANKLE', 'RIGHT_ANKLE'
        ]

        key_landmarks = {}
        for name in key_names:
            landmark = self.get_landmark(detection_result, name)
            if landmark:
                key_landmarks[name.lower()] = landmark

        return key_landmarks

    @staticmethod
    def calculate_distance(point1: Dict, point2: Dict) -> float:
        """2点間の距離を計算"""
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        dz = point1.get('z', 0) - point2.get('z', 0)
        return np.sqrt(dx*dx + dy*dy + dz*dz)

    @staticmethod
    def calculate_angle(point1: Dict, point2: Dict, point3: Dict) -> float:
        """
        3点から角度を計算（度数法）
        point2が頂点
        """
        v1 = np.array([point1['x'] - point2['x'], point1['y'] - point2['y']])
        v2 = np.array([point3['x'] - point2['x'], point3['y'] - point2['y']])

        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)

        return np.degrees(angle_rad)

    @staticmethod
    def calculate_angle_from_vertical(point1: Dict, point2: Dict) -> float:
        """垂直線からの角度を計算"""
        dx = point2['x'] - point1['x']
        dy = point2['y'] - point1['y']
        angle_rad = np.arctan2(dx, dy)
        return abs(np.degrees(angle_rad))

    @staticmethod
    def calculate_angle_from_horizontal(point1: Dict, point2: Dict) -> float:
        """水平線からの角度を計算"""
        dx = point2['x'] - point1['x']
        dy = point2['y'] - point1['y']
        angle_rad = np.arctan2(dy, dx)
        return np.degrees(angle_rad)

    @staticmethod
    def get_midpoint(point1: Dict, point2: Dict) -> Dict:
        """2点の中点を計算"""
        return {
            'x': (point1['x'] + point2['x']) / 2,
            'y': (point1['y'] + point2['y']) / 2,
            'z': (point1.get('z', 0) + point2.get('z', 0)) / 2
        }

    def __del__(self):
        """クリーンアップ"""
        if hasattr(self, 'pose'):
            self.pose.close()
