// ケンダルの姿勢分類
function classifyKendallPosture(landmarks) {
    const keyLandmarks = getKeyLandmarks(landmarks);

    // ランドマークが検出されているかチェック
    if (!keyLandmarks.nose || !keyLandmarks.leftShoulder ||
        !keyLandmarks.leftHip || !keyLandmarks.leftKnee || !keyLandmarks.leftAnkle) {
        return {
            type: '評価不可',
            description: '姿勢のランドマークを十分に検出できませんでした。全身が写った横向きの写真を使用してください。',
            recommendations: []
        };
    }

    // 各部位の角度と位置を計算
    const measurements = calculateSagittalMeasurements(keyLandmarks);

    // 姿勢分類の判定
    const classification = determineKendallType(measurements, keyLandmarks);

    return classification;
}

// 矢状面での測定値を計算
function calculateSagittalMeasurements(landmarks) {
    const ear = landmarks.leftEar || landmarks.nose;
    const shoulder = landmarks.leftShoulder;
    const hip = landmarks.leftHip;
    const knee = landmarks.leftKnee;
    const ankle = landmarks.leftAnkle;

    // 頭部の前方傾斜角度(耳-肩のライン)
    const headForwardAngle = calculateAngleFromVertical(shoulder, ear);

    // 肩の前方位置(肩が股関節より前にあるか)
    const shoulderForward = shoulder.x - hip.x;

    // 骨盤の前後傾(股関節-膝のライン)
    const pelvicTilt = calculateAngleFromVertical(knee, hip);

    // 膝の位置(膝が足首より前か後か)
    const kneePosition = knee.x - ankle.x;

    // 体幹の角度(肩-股関節のライン)
    const trunkAngle = calculateAngleFromVertical(hip, shoulder);

    // 重心線の評価(耳-足首のライン)
    const plumbLineDeviation = Math.abs(ear.x - ankle.x);

    return {
        headForwardAngle,
        shoulderForward,
        pelvicTilt,
        kneePosition,
        trunkAngle,
        plumbLineDeviation
    };
}

// ケンダルの姿勢タイプを判定
function determineKendallType(measurements, landmarks) {
    const {
        headForwardAngle,
        shoulderForward,
        pelvicTilt,
        kneePosition,
        trunkAngle,
        plumbLineDeviation
    } = measurements;

    // 判定基準
    const isHeadForward = headForwardAngle > 15;
    const isShoulderForward = shoulderForward > 0.05;
    const isPelvicAnteriorTilt = pelvicTilt < -5;
    const isPelvicPosteriorTilt = pelvicTilt > 5;
    const isKneeHyperextended = kneePosition < -0.03;
    const isTrunkFlexed = trunkAngle > 10;
    const isPlumbLineDeviated = plumbLineDeviation > 0.08;

    // スウェイバック姿勢の判定
    if (isShoulderForward && isPelvicPosteriorTilt && isKneeHyperextended) {
        return {
            type: 'スウェイバック姿勢 (Sway-Back Posture)',
            description: `
                <p><strong>特徴:</strong></p>
                <ul>
                    <li>骨盤が前方に移動し、後傾している</li>
                    <li>胸椎が後方に傾斜</li>
                    <li>膝が過伸展(反り返っている)</li>
                    <li>頭部が前方に突出</li>
                </ul>
                <p><strong>考えられる影響:</strong></p>
                <ul>
                    <li>腰椎への負担軽減だが、胸椎・股関節への負担増加</li>
                    <li>膝関節への過度なストレス</li>
                    <li>バランス能力の低下</li>
                </ul>
            `,
            score: {
                headForwardAngle: headForwardAngle.toFixed(1),
                shoulderPosition: shoulderForward > 0 ? '前方' : '正常',
                pelvicTilt: '後傾',
                kneePosition: '過伸展'
            },
            recommendations: [
                '股関節屈筋群(腸腰筋、大腿直筋)のストレッチ',
                '腹筋群の強化トレーニング',
                '膝関節の適切なアライメント意識',
                '胸椎の伸展エクササイズ',
                '頭部の位置を意識した姿勢改善'
            ]
        };
    }

    // カイホロードシス姿勢の判定
    if (isHeadForward && isShoulderForward && isPelvicAnteriorTilt) {
        return {
            type: 'カイホロードシス姿勢 (Kyphosis-Lordosis Posture)',
            description: `
                <p><strong>特徴:</strong></p>
                <ul>
                    <li>頭部が前方に突出</li>
                    <li>胸椎の後弯が増強(猫背)</li>
                    <li>腰椎の前弯が増強(反り腰)</li>
                    <li>骨盤が前傾</li>
                </ul>
                <p><strong>考えられる影響:</strong></p>
                <ul>
                    <li>頸部・腰部への過度な負担</li>
                    <li>肩こり、首こりのリスク増加</li>
                    <li>腰痛のリスク増加</li>
                    <li>呼吸機能の低下</li>
                </ul>
            `,
            score: {
                headForwardAngle: headForwardAngle.toFixed(1),
                shoulderPosition: '前方',
                pelvicTilt: '前傾',
                spinalCurvature: '増強'
            },
            recommendations: [
                '胸筋・股関節屈筋群のストレッチ',
                '背筋群(僧帽筋中部・下部)の強化',
                '腹筋・臀筋の強化トレーニング',
                '胸椎の可動性改善エクササイズ',
                'デスクワーク時の姿勢改善',
                '定期的な姿勢チェックと休憩'
            ]
        };
    }

    // フラットバック姿勢の判定
    if (!isPelvicAnteriorTilt && !isPlumbLineDeviated && trunkAngle < 5) {
        return {
            type: 'フラットバック姿勢 (Flat-Back Posture)',
            description: `
                <p><strong>特徴:</strong></p>
                <ul>
                    <li>腰椎の前弯が減少または消失</li>
                    <li>胸椎の後弯も減少</li>
                    <li>骨盤が後傾</li>
                    <li>脊椎全体が平坦化</li>
                </ul>
                <p><strong>考えられる影響:</strong></p>
                <ul>
                    <li>衝撃吸収機能の低下</li>
                    <li>腰部への負担増加</li>
                    <li>股関節の可動域制限</li>
                    <li>バランス能力の低下</li>
                </ul>
            `,
            score: {
                headForwardAngle: headForwardAngle.toFixed(1),
                pelvicTilt: '後傾',
                spinalCurvature: '減少',
                trunkAngle: trunkAngle.toFixed(1)
            },
            recommendations: [
                'ハムストリングスのストレッチ',
                '股関節屈筋群の強化',
                '腰椎の可動性改善エクササイズ',
                '骨盤前傾を促すエクササイズ',
                '体幹の柔軟性向上トレーニング'
            ]
        };
    }

    // 理想姿勢
    if (!isHeadForward && !isShoulderForward && !isPelvicAnteriorTilt &&
        !isPelvicPosteriorTilt && !isPlumbLineDeviated) {
        return {
            type: '理想姿勢 (Ideal Posture)',
            description: `
                <p><strong>特徴:</strong></p>
                <ul>
                    <li>頭部、肩、股関節、膝、足首が一直線上に配列</li>
                    <li>適切な脊椎の生理的弯曲</li>
                    <li>バランスの取れた筋活動</li>
                    <li>効率的な身体アライメント</li>
                </ul>
                <p><strong>メリット:</strong></p>
                <ul>
                    <li>関節への負担が最小限</li>
                    <li>筋肉の効率的な使用</li>
                    <li>良好な呼吸機能</li>
                    <li>疲労の軽減</li>
                </ul>
            `,
            score: {
                headForwardAngle: headForwardAngle.toFixed(1),
                shoulderPosition: '正常',
                pelvicTilt: '正常',
                overall: '良好'
            },
            recommendations: [
                '現在の良好な姿勢を維持',
                '定期的な運動習慣の継続',
                'バランストレーニングの実施',
                '姿勢意識の継続',
                '予防的なストレッチとエクササイズ'
            ]
        };
    }

    // その他の姿勢異常
    return {
        type: '姿勢異常あり',
        description: `
            <p><strong>検出された特徴:</strong></p>
            <ul>
                ${isHeadForward ? '<li>頭部の前方突出</li>' : ''}
                ${isShoulderForward ? '<li>肩の前方位置</li>' : ''}
                ${isPelvicAnteriorTilt ? '<li>骨盤の前傾</li>' : ''}
                ${isPelvicPosteriorTilt ? '<li>骨盤の後傾</li>' : ''}
                ${isPlumbLineDeviated ? '<li>重心線の偏位</li>' : ''}
            </ul>
            <p>複数の姿勢異常が見られます。専門家による詳細な評価をお勧めします。</p>
        `,
        score: {
            headForwardAngle: headForwardAngle.toFixed(1),
            shoulderPosition: shoulderForward > 0 ? '前方' : '正常',
            pelvicTilt: isPelvicAnteriorTilt ? '前傾' : isPelvicPosteriorTilt ? '後傾' : '正常',
            deviation: '複数の異常'
        },
        recommendations: [
            '理学療法士など専門家への相談',
            '全身的なストレッチプログラム',
            'コアマッスル強化トレーニング',
            '姿勢教育プログラムへの参加',
            '定期的な姿勢評価の実施'
        ]
    };
}
