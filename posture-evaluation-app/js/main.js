// グローバル変数
let frontalImage = null;
let sagittalImage = null;
let frontalLandmarks = null;
let sagittalLandmarks = null;

// DOM要素
const frontalInput = document.getElementById('frontal-input');
const sagittalInput = document.getElementById('sagittal-input');
const frontalPreview = document.getElementById('frontal-preview');
const sagittalPreview = document.getElementById('sagittal-preview');
const evaluateBtn = document.getElementById('evaluate-btn');
const loadingDiv = document.getElementById('loading');
const resultsSection = document.getElementById('results-section');
const downloadPdfBtn = document.getElementById('download-pdf-btn');

// 初期化
document.addEventListener('DOMContentLoaded', function() {
    setupFileInputs();
    setupDragAndDrop();

    evaluateBtn.addEventListener('click', evaluatePosture);
    downloadPdfBtn.addEventListener('click', generatePDFReport);
});

// ファイル入力の設定
function setupFileInputs() {
    frontalInput.addEventListener('change', (e) => handleFileSelect(e, 'frontal'));
    sagittalInput.addEventListener('change', (e) => handleFileSelect(e, 'sagittal'));
}

// ドラッグ&ドロップの設定
function setupDragAndDrop() {
    const uploadBoxes = document.querySelectorAll('.upload-box');

    uploadBoxes.forEach(box => {
        box.addEventListener('dragover', (e) => {
            e.preventDefault();
            box.classList.add('drag-over');
        });

        box.addEventListener('dragleave', () => {
            box.classList.remove('drag-over');
        });

        box.addEventListener('drop', (e) => {
            e.preventDefault();
            box.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const viewType = box.id.includes('frontal') ? 'frontal' : 'sagittal';
                handleFile(files[0], viewType);
            }
        });
    });
}

// ファイル選択処理
function handleFileSelect(event, viewType) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file, viewType);
    }
}

// ファイル処理
function handleFile(file, viewType) {
    if (!file.type.startsWith('image/')) {
        alert('画像ファイルを選択してください');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            if (viewType === 'frontal') {
                frontalImage = img;
                displayPreview(img, frontalPreview);
            } else {
                sagittalImage = img;
                displayPreview(img, sagittalPreview);
            }
            checkIfReadyToEvaluate();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

// プレビュー表示
function displayPreview(img, previewContainer) {
    // プレースホルダーを非表示
    const uploadBox = previewContainer.parentElement;
    const placeholder = uploadBox.querySelector('.upload-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }

    // プレビューを表示
    previewContainer.innerHTML = '';
    const previewImg = document.createElement('img');
    previewImg.src = img.src;
    previewContainer.appendChild(previewImg);
    previewContainer.classList.add('active');
}

// 評価ボタンの有効化チェック
function checkIfReadyToEvaluate() {
    if (frontalImage && sagittalImage) {
        evaluateBtn.disabled = false;
    }
}

// 姿勢評価の実行
async function evaluatePosture() {
    // ローディング表示
    loadingDiv.style.display = 'flex';
    resultsSection.style.display = 'none';
    evaluateBtn.disabled = true;

    try {
        // 姿勢検出の実行
        console.log('正面像の姿勢検出を開始...');
        frontalLandmarks = await detectPose(frontalImage);

        console.log('矢状面像の姿勢検出を開始...');
        sagittalLandmarks = await detectPose(sagittalImage);

        // ランドマークの描画
        drawLandmarks(frontalImage, frontalLandmarks, 'frontal-canvas');
        drawLandmarks(sagittalImage, sagittalLandmarks, 'sagittal-canvas');

        // 評価の実行
        const frontalEvaluation = evaluateFrontalView(frontalLandmarks);
        const sagittalEvaluation = evaluateSagittalView(sagittalLandmarks);
        const kendallClassification = classifyKendallPosture(sagittalLandmarks);

        // 結果の表示
        displayResults(frontalEvaluation, sagittalEvaluation, kendallClassification);

        // 結果セクションを表示
        resultsSection.style.display = 'block';

        // 結果セクションまでスクロール
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('評価エラー:', error);
        alert('姿勢評価中にエラーが発生しました。画像を確認して再度お試しください。');
    } finally {
        loadingDiv.style.display = 'none';
        evaluateBtn.disabled = false;
    }
}

// 結果の表示
function displayResults(frontalEval, sagittalEval, kendall) {
    // ケンダル分類の表示
    document.getElementById('kendall-type').textContent = kendall.type;
    document.getElementById('kendall-description').innerHTML = kendall.description;

    // 正面像評価の表示
    const frontalResults = document.getElementById('frontal-results');
    frontalResults.innerHTML = '';
    frontalEval.items.forEach(item => {
        const div = createEvaluationItem(item);
        frontalResults.appendChild(div);
    });

    // 矢状面像評価の表示
    const sagittalResults = document.getElementById('sagittal-results');
    sagittalResults.innerHTML = '';
    sagittalEval.items.forEach(item => {
        const div = createEvaluationItem(item);
        sagittalResults.appendChild(div);
    });

    // 総合コメントの表示
    const overallComments = document.getElementById('overall-comments');
    const allComments = [
        ...frontalEval.comments,
        ...sagittalEval.comments,
        ...kendall.recommendations
    ];

    overallComments.innerHTML = '<ul>' +
        allComments.map(comment => `<li>${comment}</li>`).join('') +
        '</ul>';
}

// 評価項目の作成
function createEvaluationItem(item) {
    const div = document.createElement('div');
    div.className = `evaluation-item ${item.severity}`;

    div.innerHTML = `
        <div class="evaluation-item-title">${item.title}</div>
        <div class="evaluation-item-value">${item.value}</div>
        <div class="evaluation-item-comment">${item.comment}</div>
    `;

    return div;
}

// ランドマークの描画
function drawLandmarks(image, landmarks, canvasId) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');

    // キャンバスサイズを画像に合わせる
    canvas.width = image.width;
    canvas.height = image.height;

    // 画像を描画
    ctx.drawImage(image, 0, 0);

    if (!landmarks || !landmarks.poseLandmarks) {
        return;
    }

    const poseLandmarks = landmarks.poseLandmarks;

    // 接続線を描画
    const connections = window.POSE_CONNECTIONS;
    if (connections) {
        ctx.strokeStyle = '#00FF00';
        ctx.lineWidth = 2;

        connections.forEach(([start, end]) => {
            const startPoint = poseLandmarks[start];
            const endPoint = poseLandmarks[end];

            if (startPoint && endPoint) {
                ctx.beginPath();
                ctx.moveTo(startPoint.x * canvas.width, startPoint.y * canvas.height);
                ctx.lineTo(endPoint.x * canvas.width, endPoint.y * canvas.height);
                ctx.stroke();
            }
        });
    }

    // ランドマークポイントを描画
    ctx.fillStyle = '#FF0000';
    poseLandmarks.forEach(landmark => {
        if (landmark) {
            ctx.beginPath();
            ctx.arc(
                landmark.x * canvas.width,
                landmark.y * canvas.height,
                5,
                0,
                2 * Math.PI
            );
            ctx.fill();
        }
    });
}

// エラーハンドリング
window.addEventListener('error', function(e) {
    console.error('エラーが発生しました:', e.error);
});
