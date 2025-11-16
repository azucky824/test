/**
 * Kindle to PDF Converter - Popup Script
 * ポップアップUIの制御とメッセージング
 */

// DOM要素の取得
const endPageInput = document.getElementById('endPage');
const intervalInput = document.getElementById('interval');
const imageQualityInput = document.getElementById('imageQuality');
const qualityValueSpan = document.getElementById('qualityValue');
const enableOCRCheckbox = document.getElementById('enableOCR');
const startButton = document.getElementById('startButton');
const cancelButton = document.getElementById('cancelButton');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const progressCount = document.getElementById('progressCount');
const statusMessage = document.getElementById('statusMessage');

// 状態管理
let isCapturing = false;
let currentTabId = null;

/**
 * ステータスメッセージを表示
 * @param {string} message - 表示するメッセージ
 * @param {string} type - メッセージタイプ (info, success, error, warning)
 */
function showStatus(message, type = 'info') {
  statusMessage.textContent = message;
  statusMessage.className = `status-message show ${type}`;
}

/**
 * ステータスメッセージを非表示
 */
function hideStatus() {
  statusMessage.className = 'status-message';
}

/**
 * 進捗バーを更新
 * @param {number} current - 現在のページ
 * @param {number} total - 総ページ数
 */
function updateProgress(current, total) {
  const percentage = (current / total) * 100;
  progressBar.style.width = `${percentage}%`;
  progressCount.textContent = `${current} / ${total}`;
}

/**
 * UIを初期状態にリセット
 */
function resetUI() {
  isCapturing = false;
  startButton.style.display = 'flex';
  cancelButton.style.display = 'none';
  progressSection.style.display = 'none';
  startButton.disabled = false;
  endPageInput.disabled = false;
  intervalInput.disabled = false;
  imageQualityInput.disabled = false;
  enableOCRCheckbox.disabled = false;
}

/**
 * キャプチャ中のUIに変更
 */
function setCapturingUI() {
  isCapturing = true;
  startButton.style.display = 'none';
  cancelButton.style.display = 'flex';
  progressSection.style.display = 'block';
  progressSection.classList.add('active');
  endPageInput.disabled = true;
  intervalInput.disabled = true;
  imageQualityInput.disabled = true;
  enableOCRCheckbox.disabled = true;
}

/**
 * 現在のタブがKindle Cloud Readerか確認
 * @returns {Promise<boolean>}
 */
async function isKindleCloudReader() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return false;

    currentTabId = tab.id;
    const url = tab.url || '';

    return url.includes('read.amazon.com') || url.includes('read.amazon.co.jp');
  } catch (error) {
    console.error('タブ情報の取得に失敗:', error);
    return false;
  }
}

/**
 * 入力値の検証
 * @returns {Object|null} - 検証済みの設定オブジェクト、またはnull
 */
function validateInputs() {
  const startPage = 1; // 常に1ページ目から開始
  const endPage = parseInt(endPageInput.value);
  const interval = parseFloat(intervalInput.value);

  if (!endPage || endPage < 1) {
    showStatus('終了ページを入力してください（1以上）', 'error');
    return null;
  }

  if (interval < 1 || interval > 10) {
    showStatus('キャプチャ間隔は1〜10秒の範囲で指定してください', 'error');
    return null;
  }

  const imageQuality = parseInt(imageQualityInput.value) / 100; // 0.5-1.0に変換
  const enableOCR = enableOCRCheckbox.checked;

  return {
    startPage,
    endPage,
    interval: interval * 1000, // ミリ秒に変換
    imageQuality,
    enableOCR
  };
}

/**
 * キャプチャ開始ボタンのクリックハンドラ
 */
async function handleStartCapture() {
  hideStatus();

  // Kindle Cloud Readerのチェック
  const isKindle = await isKindleCloudReader();
  if (!isKindle) {
    showStatus(
      'このページはKindle Cloud Readerではありません。' +
      'read.amazon.comまたはread.amazon.co.jpで書籍を開いてください。',
      'error'
    );
    return;
  }

  // 入力値の検証
  const config = validateInputs();
  if (!config) return;

  // UIを変更
  setCapturingUI();
  showStatus('キャプチャを開始しています...', 'info');
  progressText.textContent = '準備中...';

  try {
    // content scriptにメッセージを送信
    const response = await chrome.tabs.sendMessage(currentTabId, {
      action: 'START_CAPTURE',
      config: config
    });

    if (response && response.success) {
      showStatus('キャプチャを開始しました', 'success');
    } else {
      throw new Error(response?.error || 'キャプチャの開始に失敗しました');
    }
  } catch (error) {
    console.error('キャプチャ開始エラー:', error);
    showStatus(
      `エラー: ${error.message || 'キャプチャの開始に失敗しました'}`,
      'error'
    );
    resetUI();
  }
}

/**
 * キャンセルボタンのクリックハンドラ
 */
async function handleCancelCapture() {
  try {
    await chrome.tabs.sendMessage(currentTabId, {
      action: 'CANCEL_CAPTURE'
    });

    showStatus('キャプチャをキャンセルしました', 'warning');
    resetUI();
  } catch (error) {
    console.error('キャンセルエラー:', error);
    showStatus('キャンセルに失敗しました', 'error');
  }
}

/**
 * background scriptからのメッセージを処理
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Popup received message:', message);

  switch (message.action) {
    case 'UPDATE_PROGRESS':
      progressText.textContent = message.status || 'キャプチャ中...';
      updateProgress(message.current, message.total);
      break;

    case 'CAPTURE_COMPLETE':
      progressSection.classList.remove('active');
      showStatus(
        `PDF生成が完了しました！ファイル名: ${message.filename}`,
        'success'
      );
      resetUI();
      break;

    case 'CAPTURE_ERROR':
      showStatus(`エラー: ${message.error}`, 'error');
      resetUI();
      break;
  }

  sendResponse({ received: true });
  return true; // 非同期レスポンスを許可
});

/**
 * 初期化処理
 */
async function init() {
  // イベントリスナーの設定
  startButton.addEventListener('click', handleStartCapture);
  cancelButton.addEventListener('click', handleCancelCapture);

  // 画像品質スライダーのイベントハンドラ
  imageQualityInput.addEventListener('input', (e) => {
    qualityValueSpan.textContent = e.target.value;
  });

  // Kindle Cloud Readerのチェック
  const isKindle = await isKindleCloudReader();
  if (!isKindle) {
    showStatus(
      'このページはKindle Cloud Readerではありません',
      'warning'
    );
    startButton.disabled = true;
    return;
  }
}

// DOM読み込み完了後に初期化
document.addEventListener('DOMContentLoaded', init);
