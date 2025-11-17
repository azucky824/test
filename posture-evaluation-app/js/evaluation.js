// 正面像の評価
function evaluateFrontalView(landmarks) {
    const keyLandmarks = getKeyLandmarks(landmarks);

    if (!keyLandmarks.leftShoulder || !keyLandmarks.rightShoulder ||
        !keyLandmarks.leftHip || !keyLandmarks.rightHip) {
        return {
            items: [],
            comments: ['正面像のランドマークを十分に検出できませんでした。']
        };
    }

    const evaluationItems = [];
    const comments = [];

    // 1. 頭部の傾き評価
    const headTilt = evaluateHeadTilt(keyLandmarks);
    evaluationItems.push(headTilt.item);
    if (headTilt.comment) comments.push(headTilt.comment);

    // 2. 肩の高さの評価
    const shoulderLevel = evaluateShoulderLevel(keyLandmarks);
    evaluationItems.push(shoulderLevel.item);
    if (shoulderLevel.comment) comments.push(shoulderLevel.comment);

    // 3. 骨盤の傾き評価
    const pelvicLevel = evaluatePelvicLevel(keyLandmarks);
    evaluationItems.push(pelvicLevel.item);
    if (pelvicLevel.comment) comments.push(pelvicLevel.comment);

    // 4. 身体の左右対称性評価
    const symmetry = evaluateBodySymmetry(keyLandmarks);
    evaluationItems.push(symmetry.item);
    if (symmetry.comment) comments.push(symmetry.comment);

    // 5. 重心線の評価
    const centerLine = evaluateCenterLine(keyLandmarks);
    evaluationItems.push(centerLine.item);
    if (centerLine.comment) comments.push(centerLine.comment);

    return {
        items: evaluationItems,
        comments: comments
    };
}

// 矢状面像の評価
function evaluateSagittalView(landmarks) {
    const keyLandmarks = getKeyLandmarks(landmarks);

    if (!keyLandmarks.nose || !keyLandmarks.leftShoulder ||
        !keyLandmarks.leftHip || !keyLandmarks.leftAnkle) {
        return {
            items: [],
            comments: ['矢状面像のランドマークを十分に検出できませんでした。']
        };
    }

    const evaluationItems = [];
    const comments = [];

    // 1. 頭部前方位評価
    const headForward = evaluateHeadForwardPosture(keyLandmarks);
    evaluationItems.push(headForward.item);
    if (headForward.comment) comments.push(headForward.comment);

    // 2. 肩の位置評価
    const shoulderPosition = evaluateShoulderPosition(keyLandmarks);
    evaluationItems.push(shoulderPosition.item);
    if (shoulderPosition.comment) comments.push(shoulderPosition.comment);

    // 3. 骨盤の前後傾評価
    const pelvicTilt = evaluatePelvicTiltSagittal(keyLandmarks);
    evaluationItems.push(pelvicTilt.item);
    if (pelvicTilt.comment) comments.push(pelvicTilt.comment);

    // 4. 膝の位置評価
    const kneePosition = evaluateKneePosition(keyLandmarks);
    evaluationItems.push(kneePosition.item);
    if (kneePosition.comment) comments.push(kneePosition.comment);

    return {
        items: evaluationItems,
        comments: comments
    };
}

// 頭部の傾き評価
function evaluateHeadTilt(landmarks) {
    const leftEar = landmarks.leftEar;
    const rightEar = landmarks.rightEar;

    if (!leftEar || !rightEar) {
        return {
            item: {
                title: '頭部の傾き',
                value: '評価不可',
                comment: '耳のランドマークを検出できませんでした。',
                severity: 'warning'
            }
        };
    }

    const heightDiff = Math.abs(leftEar.y - rightEar.y);
    const angle = calculateAngleFromHorizontal(leftEar, rightEar);

    let severity = 'good';
    let comment = null;

    if (heightDiff > 0.03) {
        severity = 'warning';
        const higherSide = leftEar.y < rightEar.y ? '左' : '右';
        comment = `頭部が${higherSide}に傾いています。首や肩の筋肉の緊張に注意が必要です。`;
    }

    if (heightDiff > 0.06) {
        severity = 'poor';
        const higherSide = leftEar.y < rightEar.y ? '左' : '右';
        comment = `頭部が${higherSide}に大きく傾いています。専門家による評価をお勧めします。`;
    }

    return {
        item: {
            title: '頭部の傾き',
            value: `${Math.abs(angle).toFixed(1)}° ${heightDiff > 0.03 ? '(傾きあり)' : '(正常範囲)'}`,
            comment: comment || '頭部の位置は適切です。',
            severity: severity
        },
        comment: comment
    };
}

// 肩の高さ評価
function evaluateShoulderLevel(landmarks) {
    const leftShoulder = landmarks.leftShoulder;
    const rightShoulder = landmarks.rightShoulder;

    const heightDiff = Math.abs(leftShoulder.y - rightShoulder.y);
    const angle = calculateAngleFromHorizontal(leftShoulder, rightShoulder);

    let severity = 'good';
    let comment = null;

    if (heightDiff > 0.04) {
        severity = 'warning';
        const higherSide = leftShoulder.y < rightShoulder.y ? '左肩' : '右肩';
        const lowerSide = leftShoulder.y < rightShoulder.y ? '右肩' : '左肩';
        comment = `${higherSide}が${lowerSide}より高くなっています。肩の筋肉のバランスを整えるストレッチをお勧めします。`;
    }

    if (heightDiff > 0.08) {
        severity = 'poor';
        comment = '肩の高さに大きな左右差があります。専門家による評価と適切なエクササイズが必要です。';
    }

    return {
        item: {
            title: '肩の高さ',
            value: `${Math.abs(angle).toFixed(1)}° ${heightDiff > 0.04 ? '(左右差あり)' : '(正常範囲)'}`,
            comment: comment || '左右の肩の高さはバランスが取れています。',
            severity: severity
        },
        comment: comment
    };
}

// 骨盤の傾き評価
function evaluatePelvicLevel(landmarks) {
    const leftHip = landmarks.leftHip;
    const rightHip = landmarks.rightHip;

    const heightDiff = Math.abs(leftHip.y - rightHip.y);
    const angle = calculateAngleFromHorizontal(leftHip, rightHip);

    let severity = 'good';
    let comment = null;

    if (heightDiff > 0.03) {
        severity = 'warning';
        const higherSide = leftHip.y < rightHip.y ? '左側' : '右側';
        comment = `骨盤が${higherSide}に傾いています。股関節や腰部の筋肉バランスを改善するエクササイズが有効です。`;
    }

    if (heightDiff > 0.06) {
        severity = 'poor';
        comment = '骨盤に大きな傾きがあります。腰痛や姿勢異常の原因となる可能性があるため、専門家への相談をお勧めします。';
    }

    return {
        item: {
            title: '骨盤の高さ',
            value: `${Math.abs(angle).toFixed(1)}° ${heightDiff > 0.03 ? '(傾きあり)' : '(正常範囲)'}`,
            comment: comment || '骨盤の位置は左右バランスが取れています。',
            severity: severity
        },
        comment: comment
    };
}

// 身体の左右対称性評価
function evaluateBodySymmetry(landmarks) {
    const leftShoulder = landmarks.leftShoulder;
    const rightShoulder = landmarks.rightShoulder;
    const leftHip = landmarks.leftHip;
    const rightHip = landmarks.rightHip;

    // 肩と股関節の中点を計算
    const shoulderMid = getMidpoint(leftShoulder, rightShoulder);
    const hipMid = getMidpoint(leftHip, rightHip);

    // 体幹の中心線の左右偏位
    const lateralDeviation = Math.abs(shoulderMid.x - hipMid.x);

    let severity = 'good';
    let comment = null;

    if (lateralDeviation > 0.05) {
        severity = 'warning';
        const direction = shoulderMid.x > hipMid.x ? '右' : '左';
        comment = `体幹が${direction}に偏っています。コアマッスルのバランスを整えるトレーニングが推奨されます。`;
    }

    if (lateralDeviation > 0.1) {
        severity = 'poor';
        comment = '体幹の左右対称性に大きな問題があります。側弯症の可能性も考慮し、専門家の評価を受けてください。';
    }

    return {
        item: {
            title: '身体の左右対称性',
            value: lateralDeviation > 0.05 ? '非対称' : '対称',
            comment: comment || '身体の左右対称性は良好です。',
            severity: severity
        },
        comment: comment
    };
}

// 重心線の評価
function evaluateCenterLine(landmarks) {
    const nose = landmarks.nose;
    const leftHip = landmarks.leftHip;
    const rightHip = landmarks.rightHip;
    const leftAnkle = landmarks.leftAnkle;
    const rightAnkle = landmarks.rightAnkle;

    if (!nose || !leftHip || !rightHip || !leftAnkle || !rightAnkle) {
        return {
            item: {
                title: '重心線',
                value: '評価不可',
                comment: '必要なランドマークが検出できませんでした。',
                severity: 'warning'
            }
        };
    }

    const hipMid = getMidpoint(leftHip, rightHip);
    const ankleMid = getMidpoint(leftAnkle, rightAnkle);

    // 鼻の位置と足首中点の水平距離
    const deviation = Math.abs(nose.x - ankleMid.x);

    let severity = 'good';
    let comment = null;

    if (deviation > 0.05) {
        severity = 'warning';
        comment = '重心線がやや偏っています。バランストレーニングを取り入れることをお勧めします。';
    }

    if (deviation > 0.1) {
        severity = 'poor';
        comment = '重心線に大きな偏位があります。転倒リスクや筋骨格系への負担が懸念されます。';
    }

    return {
        item: {
            title: '重心線',
            value: deviation > 0.05 ? '偏位あり' : '正常',
            comment: comment || '重心線は適切な位置にあります。',
            severity: severity
        },
        comment: comment
    };
}

// 頭部前方位の評価
function evaluateHeadForwardPosture(landmarks) {
    const ear = landmarks.leftEar || landmarks.nose;
    const shoulder = landmarks.leftShoulder;

    const angle = calculateAngleFromVertical(shoulder, ear);

    let severity = 'good';
    let comment = null;

    if (angle > 10) {
        severity = 'warning';
        comment = '頭部が前方に突出しています。首や肩の負担を軽減するため、頭部の位置を意識しましょう。';
    }

    if (angle > 20) {
        severity = 'poor';
        comment = '頭部が大きく前方に突出しています(ストレートネック)。頸部痛や肩こりのリスクが高まります。';
    }

    return {
        item: {
            title: '頭部の前方位',
            value: `${angle.toFixed(1)}° ${angle > 10 ? '(前方突出)' : '(正常範囲)'}`,
            comment: comment || '頭部の位置は適切です。',
            severity: severity
        },
        comment: comment
    };
}

// 肩の位置評価
function evaluateShoulderPosition(landmarks) {
    const shoulder = landmarks.leftShoulder;
    const hip = landmarks.leftHip;

    const horizontalDiff = shoulder.x - hip.x;

    let severity = 'good';
    let comment = null;

    if (horizontalDiff > 0.08) {
        severity = 'warning';
        comment = '肩が前方に位置しています。胸筋のストレッチと背筋の強化をお勧めします。';
    }

    if (horizontalDiff > 0.15) {
        severity = 'poor';
        comment = '肩が大きく前方に位置しています(円背)。姿勢矯正エクササイズが必要です。';
    }

    return {
        item: {
            title: '肩の前後位置',
            value: horizontalDiff > 0.08 ? '前方位' : '正常',
            comment: comment || '肩の位置は適切です。',
            severity: severity
        },
        comment: comment
    };
}

// 骨盤の前後傾評価
function evaluatePelvicTiltSagittal(landmarks) {
    const hip = landmarks.leftHip;
    const knee = landmarks.leftKnee;

    const angle = calculateAngleFromVertical(knee, hip);

    let severity = 'good';
    let tiltType = '正常';
    let comment = null;

    if (angle < -5) {
        severity = 'warning';
        tiltType = '前傾';
        comment = '骨盤が前傾しています。腹筋と臀筋の強化、股関節屈筋のストレッチをお勧めします。';
    }

    if (angle < -10) {
        severity = 'poor';
        tiltType = '過度な前傾';
        comment = '骨盤が過度に前傾しています。腰椎への負担が大きく、腰痛のリスクが高まります。';
    }

    if (angle > 5) {
        severity = 'warning';
        tiltType = '後傾';
        comment = '骨盤が後傾しています。ハムストリングスのストレッチと股関節屈筋の強化が有効です。';
    }

    if (angle > 10) {
        severity = 'poor';
        tiltType = '過度な後傾';
        comment = '骨盤が過度に後傾しています。腰椎の生理的弯曲が減少し、腰部への負担が増加します。';
    }

    return {
        item: {
            title: '骨盤の前後傾',
            value: `${angle.toFixed(1)}° (${tiltType})`,
            comment: comment || '骨盤の傾きは正常範囲です。',
            severity: severity
        },
        comment: comment
    };
}

// 膝の位置評価
function evaluateKneePosition(landmarks) {
    const knee = landmarks.leftKnee;
    const ankle = landmarks.leftAnkle;

    const horizontalDiff = knee.x - ankle.x;

    let severity = 'good';
    let comment = null;

    if (horizontalDiff < -0.03) {
        severity = 'warning';
        comment = '膝が過伸展しています。膝関節への負担に注意し、適切な膝の位置を意識しましょう。';
    }

    if (horizontalDiff < -0.06) {
        severity = 'poor';
        comment = '膝の過伸展が顕著です。関節への過度な負担があり、専門家のアドバイスが必要です。';
    }

    if (horizontalDiff > 0.05) {
        severity = 'warning';
        comment = '膝が前方に位置しています。大腿四頭筋の柔軟性を改善しましょう。';
    }

    return {
        item: {
            title: '膝の位置',
            value: horizontalDiff < -0.03 ? '過伸展' : horizontalDiff > 0.05 ? '前方位' : '正常',
            comment: comment || '膝の位置は適切です。',
            severity: severity
        },
        comment: comment
    };
}
