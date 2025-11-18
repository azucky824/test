"""
姿勢評価モジュール
正面像と矢状面像の詳細な評価を実行
"""

from typing import Dict, List
from pose_detector import PoseDetector
import numpy as np


class PostureEvaluator:
    """姿勢評価クラス"""

    def __init__(self):
        """初期化"""
        pass

    def evaluate_frontal_view(self, detection_result: Dict) -> Dict:
        """
        正面像の評価

        Args:
            detection_result: PoseDetectorのdetect()結果

        Returns:
            評価結果の辞書
        """
        landmarks = self._get_key_landmarks(detection_result)

        if not self._validate_frontal_landmarks(landmarks):
            return {
                'items': [],
                'comments': ['正面像のランドマークを十分に検出できませんでした。']
            }

        evaluation_items = []
        comments = []

        # 1. 頭部の傾き評価
        result = self._evaluate_head_tilt(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 2. 肩の高さの評価
        result = self._evaluate_shoulder_level(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 3. 骨盤の傾き評価
        result = self._evaluate_pelvic_level(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 4. 身体の左右対称性評価
        result = self._evaluate_body_symmetry(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 5. 重心線の評価
        result = self._evaluate_center_line(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        return {
            'items': evaluation_items,
            'comments': comments
        }

    def evaluate_sagittal_view(self, detection_result: Dict) -> Dict:
        """
        矢状面像の評価

        Args:
            detection_result: PoseDetectorのdetect()結果

        Returns:
            評価結果の辞書
        """
        landmarks = self._get_key_landmarks(detection_result)

        if not self._validate_sagittal_landmarks(landmarks):
            return {
                'items': [],
                'comments': ['矢状面像のランドマークを十分に検出できませんでした。']
            }

        evaluation_items = []
        comments = []

        # 1. 頭部前方位評価
        result = self._evaluate_head_forward_posture(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 2. 肩の位置評価
        result = self._evaluate_shoulder_position(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 3. 骨盤の前後傾評価
        result = self._evaluate_pelvic_tilt_sagittal(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        # 4. 膝の位置評価
        result = self._evaluate_knee_position(landmarks)
        evaluation_items.append(result['item'])
        if result.get('comment'):
            comments.append(result['comment'])

        return {
            'items': evaluation_items,
            'comments': comments
        }

    def _get_key_landmarks(self, detection_result: Dict) -> Dict:
        """主要なランドマークを取得"""
        landmarks = detection_result['landmarks']

        return {
            'nose': landmarks[0] if len(landmarks) > 0 else None,
            'left_ear': landmarks[7] if len(landmarks) > 7 else None,
            'right_ear': landmarks[8] if len(landmarks) > 8 else None,
            'left_shoulder': landmarks[11] if len(landmarks) > 11 else None,
            'right_shoulder': landmarks[12] if len(landmarks) > 12 else None,
            'left_hip': landmarks[23] if len(landmarks) > 23 else None,
            'right_hip': landmarks[24] if len(landmarks) > 24 else None,
            'left_knee': landmarks[25] if len(landmarks) > 25 else None,
            'right_knee': landmarks[26] if len(landmarks) > 26 else None,
            'left_ankle': landmarks[27] if len(landmarks) > 27 else None,
            'right_ankle': landmarks[28] if len(landmarks) > 28 else None,
        }

    def _validate_frontal_landmarks(self, landmarks: Dict) -> bool:
        """正面像のランドマーク妥当性を確認"""
        required = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
        return all(landmarks.get(key) is not None for key in required)

    def _validate_sagittal_landmarks(self, landmarks: Dict) -> bool:
        """矢状面像のランドマーク妥当性を確認"""
        required = ['left_shoulder', 'left_hip', 'left_ankle']
        return all(landmarks.get(key) is not None for key in required)

    def _evaluate_head_tilt(self, landmarks: Dict) -> Dict:
        """頭部の傾き評価"""
        left_ear = landmarks.get('left_ear')
        right_ear = landmarks.get('right_ear')

        if not left_ear or not right_ear:
            return {
                'item': {
                    'title': '頭部の傾き',
                    'value': '評価不可',
                    'comment': '耳のランドマークを検出できませんでした。',
                    'severity': 'warning'
                }
            }

        height_diff = abs(left_ear['y'] - right_ear['y'])
        angle = PoseDetector.calculate_angle_from_horizontal(left_ear, right_ear)

        severity = 'good'
        comment = None

        if height_diff > 0.03:
            severity = 'warning'
            higher_side = '左' if left_ear['y'] < right_ear['y'] else '右'
            comment = f'頭部が{higher_side}に傾いています。首や肩の筋肉の緊張に注意が必要です。'

        if height_diff > 0.06:
            severity = 'poor'
            higher_side = '左' if left_ear['y'] < right_ear['y'] else '右'
            comment = f'頭部が{higher_side}に大きく傾いています。専門家による評価をお勧めします。'

        value_text = f'{abs(angle):.1f}° {"(傾きあり)" if height_diff > 0.03 else "(正常範囲)"}'

        return {
            'item': {
                'title': '頭部の傾き',
                'value': value_text,
                'comment': comment or '頭部の位置は適切です。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_shoulder_level(self, landmarks: Dict) -> Dict:
        """肩の高さ評価"""
        left_shoulder = landmarks['left_shoulder']
        right_shoulder = landmarks['right_shoulder']

        height_diff = abs(left_shoulder['y'] - right_shoulder['y'])
        angle = PoseDetector.calculate_angle_from_horizontal(left_shoulder, right_shoulder)

        severity = 'good'
        comment = None

        if height_diff > 0.04:
            severity = 'warning'
            higher_side = '左肩' if left_shoulder['y'] < right_shoulder['y'] else '右肩'
            lower_side = '右肩' if left_shoulder['y'] < right_shoulder['y'] else '左肩'
            comment = f'{higher_side}が{lower_side}より高くなっています。肩の筋肉のバランスを整えるストレッチをお勧めします。'

        if height_diff > 0.08:
            severity = 'poor'
            comment = '肩の高さに大きな左右差があります。専門家による評価と適切なエクササイズが必要です。'

        value_text = f'{abs(angle):.1f}° {"(左右差あり)" if height_diff > 0.04 else "(正常範囲)"}'

        return {
            'item': {
                'title': '肩の高さ',
                'value': value_text,
                'comment': comment or '左右の肩の高さはバランスが取れています。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_pelvic_level(self, landmarks: Dict) -> Dict:
        """骨盤の傾き評価"""
        left_hip = landmarks['left_hip']
        right_hip = landmarks['right_hip']

        height_diff = abs(left_hip['y'] - right_hip['y'])
        angle = PoseDetector.calculate_angle_from_horizontal(left_hip, right_hip)

        severity = 'good'
        comment = None

        if height_diff > 0.03:
            severity = 'warning'
            higher_side = '左側' if left_hip['y'] < right_hip['y'] else '右側'
            comment = f'骨盤が{higher_side}に傾いています。股関節や腰部の筋肉バランスを改善するエクササイズが有効です。'

        if height_diff > 0.06:
            severity = 'poor'
            comment = '骨盤に大きな傾きがあります。腰痛や姿勢異常の原因となる可能性があるため、専門家への相談をお勧めします。'

        value_text = f'{abs(angle):.1f}° {"(傾きあり)" if height_diff > 0.03 else "(正常範囲)"}'

        return {
            'item': {
                'title': '骨盤の高さ',
                'value': value_text,
                'comment': comment or '骨盤の位置は左右バランスが取れています。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_body_symmetry(self, landmarks: Dict) -> Dict:
        """身体の左右対称性評価"""
        left_shoulder = landmarks['left_shoulder']
        right_shoulder = landmarks['right_shoulder']
        left_hip = landmarks['left_hip']
        right_hip = landmarks['right_hip']

        shoulder_mid = PoseDetector.get_midpoint(left_shoulder, right_shoulder)
        hip_mid = PoseDetector.get_midpoint(left_hip, right_hip)

        lateral_deviation = abs(shoulder_mid['x'] - hip_mid['x'])

        severity = 'good'
        comment = None

        if lateral_deviation > 0.05:
            severity = 'warning'
            direction = '右' if shoulder_mid['x'] > hip_mid['x'] else '左'
            comment = f'体幹が{direction}に偏っています。コアマッスルのバランスを整えるトレーニングが推奨されます。'

        if lateral_deviation > 0.1:
            severity = 'poor'
            comment = '体幹の左右対称性に大きな問題があります。側弯症の可能性も考慮し、専門家の評価を受けてください。'

        value_text = '非対称' if lateral_deviation > 0.05 else '対称'

        return {
            'item': {
                'title': '身体の左右対称性',
                'value': value_text,
                'comment': comment or '身体の左右対称性は良好です。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_center_line(self, landmarks: Dict) -> Dict:
        """重心線の評価"""
        nose = landmarks.get('nose')
        left_hip = landmarks.get('left_hip')
        right_hip = landmarks.get('right_hip')
        left_ankle = landmarks.get('left_ankle')
        right_ankle = landmarks.get('right_ankle')

        if not all([nose, left_hip, right_hip, left_ankle, right_ankle]):
            return {
                'item': {
                    'title': '重心線',
                    'value': '評価不可',
                    'comment': '必要なランドマークが検出できませんでした。',
                    'severity': 'warning'
                }
            }

        ankle_mid = PoseDetector.get_midpoint(left_ankle, right_ankle)
        deviation = abs(nose['x'] - ankle_mid['x'])

        severity = 'good'
        comment = None

        if deviation > 0.05:
            severity = 'warning'
            comment = '重心線がやや偏っています。バランストレーニングを取り入れることをお勧めします。'

        if deviation > 0.1:
            severity = 'poor'
            comment = '重心線に大きな偏位があります。転倒リスクや筋骨格系への負担が懸念されます。'

        value_text = '偏位あり' if deviation > 0.05 else '正常'

        return {
            'item': {
                'title': '重心線',
                'value': value_text,
                'comment': comment or '重心線は適切な位置にあります。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_head_forward_posture(self, landmarks: Dict) -> Dict:
        """頭部前方位の評価"""
        ear = landmarks.get('left_ear') or landmarks.get('nose')
        shoulder = landmarks['left_shoulder']

        if not ear:
            return {
                'item': {
                    'title': '頭部の前方位',
                    'value': '評価不可',
                    'comment': '必要なランドマークを検出できませんでした。',
                    'severity': 'warning'
                }
            }

        angle = PoseDetector.calculate_angle_from_vertical(shoulder, ear)

        severity = 'good'
        comment = None

        if angle > 10:
            severity = 'warning'
            comment = '頭部が前方に突出しています。首や肩の負担を軽減するため、頭部の位置を意識しましょう。'

        if angle > 20:
            severity = 'poor'
            comment = '頭部が大きく前方に突出しています(ストレートネック)。頸部痛や肩こりのリスクが高まります。'

        value_text = f'{angle:.1f}° {"(前方突出)" if angle > 10 else "(正常範囲)"}'

        return {
            'item': {
                'title': '頭部の前方位',
                'value': value_text,
                'comment': comment or '頭部の位置は適切です。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_shoulder_position(self, landmarks: Dict) -> Dict:
        """肩の位置評価"""
        shoulder = landmarks['left_shoulder']
        hip = landmarks['left_hip']

        horizontal_diff = shoulder['x'] - hip['x']

        severity = 'good'
        comment = None

        if horizontal_diff > 0.08:
            severity = 'warning'
            comment = '肩が前方に位置しています。胸筋のストレッチと背筋の強化をお勧めします。'

        if horizontal_diff > 0.15:
            severity = 'poor'
            comment = '肩が大きく前方に位置しています(円背)。姿勢矯正エクササイズが必要です。'

        value_text = '前方位' if horizontal_diff > 0.08 else '正常'

        return {
            'item': {
                'title': '肩の前後位置',
                'value': value_text,
                'comment': comment or '肩の位置は適切です。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_pelvic_tilt_sagittal(self, landmarks: Dict) -> Dict:
        """骨盤の前後傾評価"""
        hip = landmarks['left_hip']
        knee = landmarks['left_knee']

        angle = PoseDetector.calculate_angle_from_vertical(knee, hip)

        severity = 'good'
        tilt_type = '正常'
        comment = None

        if angle < -5:
            severity = 'warning'
            tilt_type = '前傾'
            comment = '骨盤が前傾しています。腹筋と臀筋の強化、股関節屈筋のストレッチをお勧めします。'

        if angle < -10:
            severity = 'poor'
            tilt_type = '過度な前傾'
            comment = '骨盤が過度に前傾しています。腰椎への負担が大きく、腰痛のリスクが高まります。'

        if angle > 5:
            severity = 'warning'
            tilt_type = '後傾'
            comment = '骨盤が後傾しています。ハムストリングスのストレッチと股関節屈筋の強化が有効です。'

        if angle > 10:
            severity = 'poor'
            tilt_type = '過度な後傾'
            comment = '骨盤が過度に後傾しています。腰椎の生理的弯曲が減少し、腰部への負担が増加します。'

        value_text = f'{angle:.1f}° ({tilt_type})'

        return {
            'item': {
                'title': '骨盤の前後傾',
                'value': value_text,
                'comment': comment or '骨盤の傾きは正常範囲です。',
                'severity': severity
            },
            'comment': comment
        }

    def _evaluate_knee_position(self, landmarks: Dict) -> Dict:
        """膝の位置評価"""
        knee = landmarks['left_knee']
        ankle = landmarks['left_ankle']

        horizontal_diff = knee['x'] - ankle['x']

        severity = 'good'
        comment = None

        if horizontal_diff < -0.03:
            severity = 'warning'
            comment = '膝が過伸展しています。膝関節への負担に注意し、適切な膝の位置を意識しましょう。'

        if horizontal_diff < -0.06:
            severity = 'poor'
            comment = '膝の過伸展が顕著です。関節への過度な負担があり、専門家のアドバイスが必要です。'

        if horizontal_diff > 0.05:
            severity = 'warning'
            comment = '膝が前方に位置しています。大腿四頭筋の柔軟性を改善しましょう。'

        if horizontal_diff < -0.03:
            value_text = '過伸展'
        elif horizontal_diff > 0.05:
            value_text = '前方位'
        else:
            value_text = '正常'

        return {
            'item': {
                'title': '膝の位置',
                'value': value_text,
                'comment': comment or '膝の位置は適切です。',
                'severity': severity
            },
            'comment': comment
        }
