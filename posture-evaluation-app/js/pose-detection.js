// MediaPipe Poseの接続情報
window.POSE_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 7],
    [0, 4], [4, 5], [5, 6], [6, 8],
    [9, 10],
    [11, 12], [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], [17, 19],
    [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], [18, 20],
    [11, 23], [12, 24], [23, 24],
    [23, 25], [25, 27], [27, 29], [27, 31], [29, 31],
    [24, 26], [26, 28], [28, 30], [28, 32], [30, 32]
];

// ランドマークのインデックス
window.POSE_LANDMARKS = {
    NOSE: 0,
    LEFT_EYE_INNER: 1,
    LEFT_EYE: 2,
    LEFT_EYE_OUTER: 3,
    RIGHT_EYE_INNER: 4,
    RIGHT_EYE: 5,
    RIGHT_EYE_OUTER: 6,
    LEFT_EAR: 7,
    RIGHT_EAR: 8,
    MOUTH_LEFT: 9,
    MOUTH_RIGHT: 10,
    LEFT_SHOULDER: 11,
    RIGHT_SHOULDER: 12,
    LEFT_ELBOW: 13,
    RIGHT_ELBOW: 14,
    LEFT_WRIST: 15,
    RIGHT_WRIST: 16,
    LEFT_PINKY: 17,
    RIGHT_PINKY: 18,
    LEFT_INDEX: 19,
    RIGHT_INDEX: 20,
    LEFT_THUMB: 21,
    RIGHT_THUMB: 22,
    LEFT_HIP: 23,
    RIGHT_HIP: 24,
    LEFT_KNEE: 25,
    RIGHT_KNEE: 26,
    LEFT_ANKLE: 27,
    RIGHT_ANKLE: 28,
    LEFT_HEEL: 29,
    RIGHT_HEEL: 30,
    LEFT_FOOT_INDEX: 31,
    RIGHT_FOOT_INDEX: 32
};

// MediaPipe Poseインスタンス
let pose = null;

// Pose検出の初期化
function initializePose() {
    if (pose) {
        return pose;
    }

    pose = new Pose({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
        }
    });

    pose.setOptions({
        modelComplexity: 1,
        smoothLandmarks: true,
        enableSegmentation: false,
        smoothSegmentation: false,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    });

    return pose;
}

// 画像から姿勢を検出
async function detectPose(image) {
    return new Promise((resolve, reject) => {
        const poseInstance = initializePose();

        // 結果を受け取るコールバック
        poseInstance.onResults((results) => {
            resolve(results);
        });

        // キャンバスに画像を描画
        const canvas = document.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(image, 0, 0);

        // 姿勢検出を実行
        poseInstance.send({ image: canvas })
            .catch(error => {
                console.error('Pose detection error:', error);
                reject(error);
            });

        // タイムアウト処理(10秒)
        setTimeout(() => {
            reject(new Error('Pose detection timeout'));
        }, 10000);
    });
}

// 2点間の距離を計算
function calculateDistance(point1, point2) {
    const dx = point1.x - point2.x;
    const dy = point1.y - point2.y;
    const dz = (point1.z || 0) - (point2.z || 0);
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

// 3点から角度を計算(度数法)
function calculateAngle(point1, point2, point3) {
    const vector1 = {
        x: point1.x - point2.x,
        y: point1.y - point2.y
    };
    const vector2 = {
        x: point3.x - point2.x,
        y: point3.y - point2.y
    };

    const dot = vector1.x * vector2.x + vector1.y * vector2.y;
    const mag1 = Math.sqrt(vector1.x * vector1.x + vector1.y * vector1.y);
    const mag2 = Math.sqrt(vector2.x * vector2.x + vector2.y * vector2.y);

    const cosAngle = dot / (mag1 * mag2);
    const angleRad = Math.acos(Math.max(-1, Math.min(1, cosAngle)));
    const angleDeg = angleRad * (180 / Math.PI);

    return angleDeg;
}

// 垂直線からの角度を計算
function calculateAngleFromVertical(point1, point2) {
    const dx = point2.x - point1.x;
    const dy = point2.y - point1.y;
    const angleRad = Math.atan2(dx, dy);
    const angleDeg = Math.abs(angleRad * (180 / Math.PI));
    return angleDeg;
}

// 水平線からの角度を計算
function calculateAngleFromHorizontal(point1, point2) {
    const dx = point2.x - point1.x;
    const dy = point2.y - point1.y;
    const angleRad = Math.atan2(dy, dx);
    const angleDeg = angleRad * (180 / Math.PI);
    return angleDeg;
}

// 2点の中点を計算
function getMidpoint(point1, point2) {
    return {
        x: (point1.x + point2.x) / 2,
        y: (point1.y + point2.y) / 2,
        z: ((point1.z || 0) + (point2.z || 0)) / 2
    };
}

// ランドマークの可視性をチェック
function isLandmarkVisible(landmark, threshold = 0.5) {
    return landmark && landmark.visibility > threshold;
}

// ランドマークを取得(エラーチェック付き)
function getLandmark(landmarks, index) {
    if (!landmarks || !landmarks.poseLandmarks || !landmarks.poseLandmarks[index]) {
        return null;
    }
    return landmarks.poseLandmarks[index];
}

// 体の主要なランドマークを取得
function getKeyLandmarks(landmarks) {
    const LANDMARKS = window.POSE_LANDMARKS;

    return {
        nose: getLandmark(landmarks, LANDMARKS.NOSE),
        leftShoulder: getLandmark(landmarks, LANDMARKS.LEFT_SHOULDER),
        rightShoulder: getLandmark(landmarks, LANDMARKS.RIGHT_SHOULDER),
        leftHip: getLandmark(landmarks, LANDMARKS.LEFT_HIP),
        rightHip: getLandmark(landmarks, LANDMARKS.RIGHT_HIP),
        leftKnee: getLandmark(landmarks, LANDMARKS.LEFT_KNEE),
        rightKnee: getLandmark(landmarks, LANDMARKS.RIGHT_KNEE),
        leftAnkle: getLandmark(landmarks, LANDMARKS.LEFT_ANKLE),
        rightAnkle: getLandmark(landmarks, LANDMARKS.RIGHT_ANKLE),
        leftEar: getLandmark(landmarks, LANDMARKS.LEFT_EAR),
        rightEar: getLandmark(landmarks, LANDMARKS.RIGHT_EAR)
    };
}
