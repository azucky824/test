/**
 * Kindle to PDF Converter - Content Script
 * Kindle Cloud Readerのページを操作し、キャプチャを制御
 */

// 状態管理
let captureState = {
  isCapturing: false,
  startPage: null,
  endPage: null,
  currentPage: null,
  interval: 2000,
  timeoutId: null
};

/**
 * 現在のページ番号を取得
 * @returns {number|null} ページ番号、取得できない場合はnull
 */
function getCurrentPage() {
  // 複数のセレクタ候補を試行
  const selectors = [
    // よく使われるKindle Cloud Readerのページ番号表示要素
    '[data-location-number]',
    '.kp-notebook-annotation-location',
    '#kindleReader_pageTurn_text',
    '.pageNumber',
    '[class*="pageNum"]',
    '[class*="page-number"]',
    '[id*="page"]',
    // ARIAラベルを持つ要素
    '[aria-label*="Page"]',
    '[aria-label*="ページ"]'
  ];

  for (const selector of selectors) {
    try {
      const element = document.querySelector(selector);
      if (element) {
        // テキストから数値を抽出
        const text = element.textContent || element.getAttribute('data-location-number') || '';
        const match = text.match(/\d+/);
        if (match) {
          const pageNum = parseInt(match[0], 10);
          console.log(`[Kindle to PDF] ページ番号を取得: ${pageNum} (セレクタ: ${selector})`);
          return pageNum;
        }
      }
    } catch (error) {
      console.debug(`[Kindle to PDF] セレクタ ${selector} での取得に失敗:`, error);
    }
  }

  // DOMから"Page X of Y"パターンを検索
  const bodyText = document.body.textContent;
  const pagePatterns = [
    /Page\s+(\d+)\s+of\s+\d+/i,
    /ページ\s+(\d+)\s+\/\s+\d+/,
    /(\d+)\s*\/\s*\d+\s*ページ/
  ];

  for (const pattern of pagePatterns) {
    const match = bodyText.match(pattern);
    if (match) {
      const pageNum = parseInt(match[1], 10);
      console.log(`[Kindle to PDF] ページ番号を取得（パターンマッチ）: ${pageNum}`);
      return pageNum;
    }
  }

  console.warn('[Kindle to PDF] ページ番号を取得できませんでした');
  return null;
}

/**
 * 次ページボタンを取得
 * @returns {HTMLElement|null}
 */
function getNextButton() {
  const selectors = [
    // 一般的な次ページボタンのセレクタ
    '[aria-label="Next Page"]',
    '[aria-label="次のページ"]',
    'button[class*="next"]',
    'button[class*="forward"]',
    'button[id*="next"]',
    '.nextButton',
    '#kindleReader_pageTurn_next',
    '[data-action="next-page"]'
  ];

  for (const selector of selectors) {
    const button = document.querySelector(selector);
    if (button && button.offsetParent !== null) { // 表示されている要素のみ
      console.log(`[Kindle to PDF] 次ページボタンを検出: ${selector}`);
      return button;
    }
  }

  console.warn('[Kindle to PDF] 次ページボタンが見つかりませんでした');
  return null;
}

/**
 * ページを次に進める
 * @returns {Promise<boolean>} 成功した場合true
 */
async function goToNextPage() {
  // まず、次ページボタンをクリック
  const nextButton = getNextButton();
  if (nextButton) {
    nextButton.click();
    console.log('[Kindle to PDF] 次ページボタンをクリック');
    return true;
  }

  // ボタンが見つからない場合、キーボードイベントを送信
  console.log('[Kindle to PDF] キーボードイベントで次ページへ移動');

  // 右矢印キーを押下
  const keyEvent = new KeyboardEvent('keydown', {
    key: 'ArrowRight',
    code: 'ArrowRight',
    keyCode: 39,
    which: 39,
    bubbles: true,
    cancelable: true
  });

  document.body.dispatchEvent(keyEvent);

  // keyupイベントも送信
  const keyUpEvent = new KeyboardEvent('keyup', {
    key: 'ArrowRight',
    code: 'ArrowRight',
    keyCode: 39,
    which: 39,
    bubbles: true,
    cancelable: true
  });

  document.body.dispatchEvent(keyUpEvent);

  return true;
}

/**
 * コンテンツエリアの座標を取得
 * @returns {Object} {x, y, width, height}
 */
function getContentArea() {
  const selectors = [
    '#kindleReader_book_inner',
    '#kindleReader_book',
    '.readingContent',
    '[class*="reader-content"]',
    '[id*="reader"]',
    'main',
    '[role="main"]'
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) {
      const rect = element.getBoundingClientRect();
      console.log(`[Kindle to PDF] コンテンツエリアを検出: ${selector}`, rect);
      return {
        x: Math.round(rect.left),
        y: Math.round(rect.top),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      };
    }
  }

  // デフォルト: ビューポート全体
  console.warn('[Kindle to PDF] コンテンツエリアが特定できませんでした。ビューポート全体を使用します。');
  return {
    x: 0,
    y: 0,
    width: window.innerWidth,
    height: window.innerHeight
  };
}

/**
 * ページ遷移の完了を待機
 * @param {number} expectedPage - 期待するページ番号
 * @param {number} timeout - タイムアウト時間（ミリ秒）
 * @returns {Promise<boolean>} 遷移が完了した場合true
 */
async function waitForPageTransition(expectedPage, timeout = 5000) {
  const startTime = Date.now();

  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      const currentPage = getCurrentPage();

      if (currentPage === expectedPage) {
        clearInterval(checkInterval);
        console.log(`[Kindle to PDF] ページ ${expectedPage} への遷移完了`);
        resolve(true);
      } else if (Date.now() - startTime > timeout) {
        clearInterval(checkInterval);
        console.warn(`[Kindle to PDF] ページ遷移のタイムアウト（期待: ${expectedPage}）`);
        resolve(false);
      }
    }, 100);
  });
}

/**
 * キャプチャ処理を実行
 */
async function performCapture() {
  if (!captureState.isCapturing) {
    return;
  }

  try {
    const currentPage = getCurrentPage();
    if (!currentPage) {
      throw new Error('現在のページ番号を取得できませんでした');
    }

    captureState.currentPage = currentPage;

    // 進捗を通知
    chrome.runtime.sendMessage({
      action: 'UPDATE_PROGRESS',
      current: currentPage - captureState.startPage + 1,
      total: captureState.endPage - captureState.startPage + 1,
      status: `ページ ${currentPage} をキャプチャ中...`
    });

    // コンテンツエリアの座標を取得
    const contentArea = getContentArea();

    // background scriptにキャプチャを要求
    const response = await chrome.runtime.sendMessage({
      action: 'CAPTURE_PAGE',
      pageNumber: currentPage,
      coordinates: contentArea
    });

    if (!response || !response.success) {
      throw new Error('ページのキャプチャに失敗しました');
    }

    // 最後のページに到達したか確認
    if (currentPage >= captureState.endPage) {
      console.log('[Kindle to PDF] すべてのページのキャプチャが完了');
      captureState.isCapturing = false;

      // PDF生成を要求
      chrome.runtime.sendMessage({
        action: 'GENERATE_PDF',
        startPage: captureState.startPage,
        endPage: captureState.endPage
      });

      return;
    }

    // 次のページへ移動
    await goToNextPage();

    // ページ遷移の完了を待機
    const transitioned = await waitForPageTransition(currentPage + 1);

    if (!transitioned) {
      console.warn('[Kindle to PDF] ページ遷移に失敗しました。続行します...');
    }

    // 指定間隔後に次のキャプチャを実行
    captureState.timeoutId = setTimeout(performCapture, captureState.interval);

  } catch (error) {
    console.error('[Kindle to PDF] キャプチャエラー:', error);
    captureState.isCapturing = false;

    chrome.runtime.sendMessage({
      action: 'CAPTURE_ERROR',
      error: error.message
    });
  }
}

/**
 * キャプチャを開始
 * @param {Object} config - 設定オブジェクト
 */
async function startCapture(config) {
  console.log('[Kindle to PDF] キャプチャ開始:', config);

  // 現在のページ番号を取得
  const currentPage = getCurrentPage();
  if (!currentPage && !config.startPage) {
    throw new Error('現在のページ番号を取得できませんでした。開始ページを指定してください。');
  }

  // 設定を保存
  captureState.startPage = config.startPage || currentPage;
  captureState.endPage = config.endPage;
  captureState.interval = config.interval;
  captureState.isCapturing = true;

  // 開始ページが現在のページと異なる場合は警告
  if (config.startPage && config.startPage !== currentPage) {
    console.warn(`[Kindle to PDF] 開始ページ（${config.startPage}）と現在のページ（${currentPage}）が異なります`);
    // TODO: 開始ページに移動する機能を実装
  }

  // キャプチャを開始
  performCapture();
}

/**
 * キャプチャをキャンセル
 */
function cancelCapture() {
  console.log('[Kindle to PDF] キャプチャをキャンセル');

  if (captureState.timeoutId) {
    clearTimeout(captureState.timeoutId);
    captureState.timeoutId = null;
  }

  captureState.isCapturing = false;

  chrome.runtime.sendMessage({
    action: 'CAPTURE_CANCELLED'
  });
}

/**
 * メッセージリスナー
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Kindle to PDF] メッセージ受信:', message);

  (async () => {
    try {
      switch (message.action) {
        case 'GET_CURRENT_PAGE': {
          const page = getCurrentPage();
          chrome.runtime.sendMessage({
            action: 'SET_CURRENT_PAGE',
            page: page
          });
          sendResponse({ success: true, page });
          break;
        }

        case 'START_CAPTURE': {
          await startCapture(message.config);
          sendResponse({ success: true });
          break;
        }

        case 'CANCEL_CAPTURE': {
          cancelCapture();
          sendResponse({ success: true });
          break;
        }

        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('[Kindle to PDF] メッセージ処理エラー:', error);
      sendResponse({ success: false, error: error.message });
    }
  })();

  return true; // 非同期レスポンスを許可
});

console.log('[Kindle to PDF] Content script loaded');
