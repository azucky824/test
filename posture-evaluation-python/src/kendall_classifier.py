"""
ケンダルの姿勢分類モジュール
矢状面像から姿勢タイプを判定
"""

from typing import Dict, List
from pose_detector import PoseDetector


class KendallClassifier:
    """ケンダル姿勢分類クラス"""

    POSTURE_TYPES = {
        'IDEAL': '理想姿勢',
        'KYPHOSIS_LORDOSIS': 'カイホロードシス姿勢',
        'FLAT_BACK': 'フラットバック姿勢',
        'SWAY_BACK': 'スウェイバック姿勢',
        'ABNORMAL': '姿勢異常あり'
    }

    def __init__(self):
        """初期化"""
        pass

    def classify(self, detection_result: Dict) -> Dict:
        """
        姿勢分類を実行

        Args:
            detection_result: PoseDetectorのdetect()結果

        Returns:
            分類結果の辞書
        """
        key_landmarks = self._get_key_landmarks(detection_result)

        # ランドマークが不足している場合
        if not self._validate_landmarks(key_landmarks):
            return {
                'type': '評価不可',
                'type_en': 'UNABLE_TO_EVALUATE',
                'description': '姿勢のランドマークを十分に検出できませんでした。全身が写った横向きの写真を使用してください。',
                'recommendations': [],
                'measurements': {}
            }

        # 測定値を計算
        measurements = self._calculate_measurements(key_landmarks)

        # 姿勢タイプを判定
        result = self._determine_posture_type(measurements, key_landmarks)

        return result

    def _get_key_landmarks(self, detection_result: Dict) -> Dict:
        """主要なランドマークを取得"""
        landmarks = detection_result['landmarks']

        return {
            'nose': landmarks[0] if len(landmarks) > 0 else None,
            'left_ear': landmarks[7] if len(landmarks) > 7 else None,
            'left_shoulder': landmarks[11] if len(landmarks) > 11 else None,
            'left_hip': landmarks[23] if len(landmarks) > 23 else None,
            'left_knee': landmarks[25] if len(landmarks) > 25 else None,
            'left_ankle': landmarks[27] if len(landmarks) > 27 else None,
        }

    def _validate_landmarks(self, landmarks: Dict) -> bool:
        """ランドマークの妥当性を確認"""
        required = ['left_shoulder', 'left_hip', 'left_knee', 'left_ankle']
        return all(landmarks.get(key) is not None for key in required)

    def _calculate_measurements(self, landmarks: Dict) -> Dict:
        """測定値を計算"""
        ear = landmarks.get('left_ear') or landmarks.get('nose')
        shoulder = landmarks['left_shoulder']
        hip = landmarks['left_hip']
        knee = landmarks['left_knee']
        ankle = landmarks['left_ankle']

        # 頭部の前方傾斜角度
        head_forward_angle = PoseDetector.calculate_angle_from_vertical(shoulder, ear)

        # 肩の前方位置
        shoulder_forward = shoulder['x'] - hip['x']

        # 骨盤の前後傾
        pelvic_tilt = self._calculate_pelvic_tilt(hip, knee)

        # 膝の位置
        knee_position = knee['x'] - ankle['x']

        # 体幹の角度
        trunk_angle = PoseDetector.calculate_angle_from_vertical(hip, shoulder)

        # 重心線の偏位
        plumb_line_deviation = abs(ear['x'] - ankle['x']) if ear else 0

        return {
            'head_forward_angle': head_forward_angle,
            'shoulder_forward': shoulder_forward,
            'pelvic_tilt': pelvic_tilt,
            'knee_position': knee_position,
            'trunk_angle': trunk_angle,
            'plumb_line_deviation': plumb_line_deviation
        }

    def _calculate_pelvic_tilt(self, hip: Dict, knee: Dict) -> float:
        """骨盤の前後傾を計算"""
        dx = hip['x'] - knee['x']
        dy = hip['y'] - knee['y']
        angle_rad = np.arctan2(dx, dy)
        return np.degrees(angle_rad)

    def _determine_posture_type(self, measurements: Dict, landmarks: Dict) -> Dict:
        """姿勢タイプを判定"""
        m = measurements

        # 判定基準
        is_head_forward = m['head_forward_angle'] > 15
        is_shoulder_forward = m['shoulder_forward'] > 0.05
        is_pelvic_anterior_tilt = m['pelvic_tilt'] < -5
        is_pelvic_posterior_tilt = m['pelvic_tilt'] > 5
        is_knee_hyperextended = m['knee_position'] < -0.03
        is_trunk_flexed = m['trunk_angle'] > 10
        is_plumb_line_deviated = m['plumb_line_deviation'] > 0.08

        # スウェイバック姿勢
        if is_shoulder_forward and is_pelvic_posterior_tilt and is_knee_hyperextended:
            return self._create_sway_back_result(measurements)

        # カイホロードシス姿勢
        if is_head_forward and is_shoulder_forward and is_pelvic_anterior_tilt:
            return self._create_kyphosis_lordosis_result(measurements)

        # フラットバック姿勢
        if not is_pelvic_anterior_tilt and not is_plumb_line_deviated and m['trunk_angle'] < 5:
            return self._create_flat_back_result(measurements)

        # 理想姿勢
        if (not is_head_forward and not is_shoulder_forward and
            not is_pelvic_anterior_tilt and not is_pelvic_posterior_tilt and
            not is_plumb_line_deviated):
            return self._create_ideal_posture_result(measurements)

        # その他の姿勢異常
        return self._create_abnormal_result(measurements, {
            'is_head_forward': is_head_forward,
            'is_shoulder_forward': is_shoulder_forward,
            'is_pelvic_anterior_tilt': is_pelvic_anterior_tilt,
            'is_pelvic_posterior_tilt': is_pelvic_posterior_tilt,
            'is_plumb_line_deviated': is_plumb_line_deviated
        })

    def _create_ideal_posture_result(self, measurements: Dict) -> Dict:
        """理想姿勢の結果を作成"""
        return {
            'type': self.POSTURE_TYPES['IDEAL'],
            'type_en': 'IDEAL',
            'description': '頭部、肩、股関節、膝、足首が一直線上に配列されており、適切な脊椎の生理的弯曲が保たれています。バランスの取れた筋活動により、関節への負担が最小限に抑えられています。',
            'characteristics': [
                '頭部、肩、股関節、膝、足首が一直線上に配列',
                '適切な脊椎の生理的弯曲',
                'バランスの取れた筋活動',
                '効率的な身体アライメント'
            ],
            'benefits': [
                '関節への負担が最小限',
                '筋肉の効率的な使用',
                '良好な呼吸機能',
                '疲労の軽減'
            ],
            'recommendations': [
                '現在の良好な姿勢を維持',
                '定期的な運動習慣の継続',
                'バランストレーニングの実施',
                '姿勢意識の継続',
                '予防的なストレッチとエクササイズ'
            ],
            'measurements': measurements
        }

    def _create_kyphosis_lordosis_result(self, measurements: Dict) -> Dict:
        """カイホロードシス姿勢の結果を作成"""
        return {
            'type': self.POSTURE_TYPES['KYPHOSIS_LORDOSIS'],
            'type_en': 'KYPHOSIS_LORDOSIS',
            'description': '頭部が前方に突出し、胸椎の後弯が増強（猫背）、腰椎の前弯が増強（反り腰）しています。骨盤が前傾している状態です。',
            'characteristics': [
                '頭部が前方に突出',
                '胸椎の後弯が増強（猫背）',
                '腰椎の前弯が増強（反り腰）',
                '骨盤が前傾'
            ],
            'risks': [
                '頸部・腰部への過度な負担',
                '肩こり、首こりのリスク増加',
                '腰痛のリスク増加',
                '呼吸機能の低下'
            ],
            'recommendations': [
                '胸筋・股関節屈筋群のストレッチ',
                '背筋群（僧帽筋中部・下部）の強化',
                '腹筋・臀筋の強化トレーニング',
                '胸椎の可動性改善エクササイズ',
                'デスクワーク時の姿勢改善',
                '定期的な姿勢チェックと休憩'
            ],
            'measurements': measurements
        }

    def _create_flat_back_result(self, measurements: Dict) -> Dict:
        """フラットバック姿勢の結果を作成"""
        return {
            'type': self.POSTURE_TYPES['FLAT_BACK'],
            'type_en': 'FLAT_BACK',
            'description': '腰椎の前弯が減少または消失し、胸椎の後弯も減少しています。骨盤が後傾し、脊椎全体が平坦化している状態です。',
            'characteristics': [
                '腰椎の前弯が減少または消失',
                '胸椎の後弯も減少',
                '骨盤が後傾',
                '脊椎全体が平坦化'
            ],
            'risks': [
                '衝撃吸収機能の低下',
                '腰部への負担増加',
                '股関節の可動域制限',
                'バランス能力の低下'
            ],
            'recommendations': [
                'ハムストリングスのストレッチ',
                '股関節屈筋群の強化',
                '腰椎の可動性改善エクササイズ',
                '骨盤前傾を促すエクササイズ',
                '体幹の柔軟性向上トレーニング'
            ],
            'measurements': measurements
        }

    def _create_sway_back_result(self, measurements: Dict) -> Dict:
        """スウェイバック姿勢の結果を作成"""
        return {
            'type': self.POSTURE_TYPES['SWAY_BACK'],
            'type_en': 'SWAY_BACK',
            'description': '骨盤が前方に移動し後傾しています。胸椎が後方に傾斜し、膝が過伸展（反り返っている）状態で、頭部が前方に突出しています。',
            'characteristics': [
                '骨盤が前方に移動し、後傾している',
                '胸椎が後方に傾斜',
                '膝が過伸展（反り返っている）',
                '頭部が前方に突出'
            ],
            'risks': [
                '腰椎への負担軽減だが、胸椎・股関節への負担増加',
                '膝関節への過度なストレス',
                'バランス能力の低下'
            ],
            'recommendations': [
                '股関節屈筋群（腸腰筋、大腿直筋）のストレッチ',
                '腹筋群の強化トレーニング',
                '膝関節の適切なアライメント意識',
                '胸椎の伸展エクササイズ',
                '頭部の位置を意識した姿勢改善'
            ],
            'measurements': measurements
        }

    def _create_abnormal_result(self, measurements: Dict, flags: Dict) -> Dict:
        """その他の姿勢異常の結果を作成"""
        characteristics = []
        if flags['is_head_forward']:
            characteristics.append('頭部の前方突出')
        if flags['is_shoulder_forward']:
            characteristics.append('肩の前方位置')
        if flags['is_pelvic_anterior_tilt']:
            characteristics.append('骨盤の前傾')
        if flags['is_pelvic_posterior_tilt']:
            characteristics.append('骨盤の後傾')
        if flags['is_plumb_line_deviated']:
            characteristics.append('重心線の偏位')

        return {
            'type': self.POSTURE_TYPES['ABNORMAL'],
            'type_en': 'ABNORMAL',
            'description': '複数の姿勢異常が見られます。専門家による詳細な評価をお勧めします。',
            'characteristics': characteristics,
            'recommendations': [
                '理学療法士など専門家への相談',
                '全身的なストレッチプログラム',
                'コアマッスル強化トレーニング',
                '姿勢教育プログラムへの参加',
                '定期的な姿勢評価の実施'
            ],
            'measurements': measurements
        }


# NumPyのインポート追加
import numpy as np
