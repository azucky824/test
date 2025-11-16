/**
 * Kindle to PDF Converter - Background Script (Service Worker)
 * スクリーンショットのキャプチャとPDF生成を管理
 */

// キャプチャ状態の管理
let captureData = {
  images: [],
  isCapturing: false,
  startPage: null,
  endPage: null,
  tabId: null
};

/**
 * スクリーンショットを取得
 * @param {number} tabId - タブID
 * @param {Object} coordinates - トリミング座標 {x, y, width, height}
 * @returns {Promise<string>} base64エンコードされた画像データ
 */
async function captureScreenshot(tabId, coordinates = null) {
  try {
    // アクティブなタブのスクリーンショットを取得
    const dataUrl = await chrome.tabs.captureVisibleTab(null, {
      format: 'png'
    });

    console.log('[Kindle to PDF] スクリーンショット取得成功');

    // トリミングが必要な場合
    if (coordinates && (coordinates.x > 0 || coordinates.y > 0 ||
        coordinates.width < window.screen.width || coordinates.height < window.screen.height)) {
      return await trimImage(dataUrl, coordinates);
    }

    return dataUrl;
  } catch (error) {
    console.error('[Kindle to PDF] スクリーンショット取得エラー:', error);
    throw new Error(`スクリーンショットの取得に失敗しました: ${error.message}`);
  }
}

/**
 * 画像をトリミング
 * @param {string} dataUrl - 元画像のdata URL
 * @param {Object} coordinates - トリミング座標
 * @returns {Promise<string>} トリミング後の画像data URL
 */
async function trimImage(dataUrl, coordinates) {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      try {
        const canvas = new OffscreenCanvas(coordinates.width, coordinates.height);
        const ctx = canvas.getContext('2d');

        // 画像をトリミング
        ctx.drawImage(
          img,
          coordinates.x, coordinates.y, coordinates.width, coordinates.height,
          0, 0, coordinates.width, coordinates.height
        );

        // Canvas を Blob に変換
        canvas.convertToBlob({ type: 'image/png' }).then(blob => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.onerror = () => reject(new Error('トリミング画像の読み込みに失敗'));
          reader.readAsDataURL(blob);
        });
      } catch (error) {
        reject(new Error(`画像のトリミングに失敗: ${error.message}`));
      }
    };

    img.onerror = () => reject(new Error('画像の読み込みに失敗'));
    img.src = dataUrl;
  });
}

/**
 * キャプチャした画像を保存
 * @param {string} imageData - base64画像データ
 * @param {number} pageNumber - ページ番号
 */
function saveImage(imageData, pageNumber) {
  captureData.images.push({
    pageNumber,
    data: imageData,
    timestamp: Date.now()
  });

  console.log(`[Kindle to PDF] ページ ${pageNumber} の画像を保存 (合計: ${captureData.images.length})`);

  // メモリ使用量の監視（警告のみ）
  const estimatedSize = captureData.images.reduce((sum, img) => sum + img.data.length, 0);
  const estimatedMB = (estimatedSize / 1024 / 1024).toFixed(2);
  console.log(`[Kindle to PDF] 推定メモリ使用量: ${estimatedMB} MB`);

  if (estimatedMB > 200) {
    console.warn('[Kindle to PDF] メモリ使用量が200MBを超えています');
  }
}

/**
 * PDFを生成してダウンロード
 * @param {number} startPage - 開始ページ
 * @param {number} endPage - 終了ページ
 */
async function generatePDF(startPage, endPage) {
  try {
    console.log('[Kindle to PDF] PDF生成開始');

    if (captureData.images.length === 0) {
      throw new Error('キャプチャされた画像がありません');
    }

    // ページ番号順にソート
    captureData.images.sort((a, b) => a.pageNumber - b.pageNumber);

    // PDF生成ユーティリティを呼び出し
    const pdfBlob = await createPDFFromImages(captureData.images);

    // ファイル名を生成
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `kindle-book-p${startPage}-${endPage}-${timestamp}.pdf`;

    // PDFをダウンロード
    const url = URL.createObjectURL(pdfBlob);
    await chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: true
    });

    console.log(`[Kindle to PDF] PDF生成完了: ${filename}`);

    // Popup に完了通知
    chrome.runtime.sendMessage({
      action: 'CAPTURE_COMPLETE',
      filename: filename
    });

    // データをクリア
    captureData.images = [];
    captureData.isCapturing = false;

    // Blob URLを解放
    setTimeout(() => URL.revokeObjectURL(url), 1000);

  } catch (error) {
    console.error('[Kindle to PDF] PDF生成エラー:', error);

    chrome.runtime.sendMessage({
      action: 'CAPTURE_ERROR',
      error: error.message
    });
  }
}

/**
 * 画像配列からPDFを生成
 * @param {Array} images - 画像データの配列
 * @returns {Promise<Blob>} PDF Blob
 */
async function createPDFFromImages(images) {
  // jsPDFが利用可能か確認
  if (typeof jspdf === 'undefined' && typeof window !== 'undefined' && !window.jspdf) {
    // jsPDFが読み込まれていない場合、動的に読み込む
    await loadJsPDF();
  }

  return new Promise((resolve, reject) => {
    try {
      // jsPDFインスタンスを作成
      const { jsPDF } = window.jspdf || jspdf;
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'px',
        format: 'a4',
        compress: true
      });

      let isFirstPage = true;

      // 各画像をPDFに追加
      for (const imageData of images) {
        const img = new Image();
        img.src = imageData.data;

        // 画像のサイズに合わせてPDFページを設定
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();

        if (!isFirstPage) {
          pdf.addPage();
        }
        isFirstPage = false;

        // 画像をページに追加（アスペクト比を維持）
        pdf.addImage(
          imageData.data,
          'PNG',
          0,
          0,
          pageWidth,
          pageHeight,
          undefined,
          'FAST'
        );

        console.log(`[Kindle to PDF] PDF にページ ${imageData.pageNumber} を追加`);
      }

      // PDFをBlobとして出力
      const pdfBlob = pdf.output('blob');
      resolve(pdfBlob);

    } catch (error) {
      reject(new Error(`PDF生成に失敗: ${error.message}`));
    }
  });
}

/**
 * jsPDFライブラリを動的に読み込む
 * @returns {Promise<void>}
 */
async function loadJsPDF() {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js';
    script.onload = () => {
      console.log('[Kindle to PDF] jsPDF読み込み成功');
      resolve();
    };
    script.onerror = () => {
      reject(new Error('jsPDFの読み込みに失敗しました。インターネット接続を確認してください。'));
    };
    document.head.appendChild(script);
  });
}

/**
 * メッセージリスナー
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Kindle to PDF] Background メッセージ受信:', message);

  (async () => {
    try {
      switch (message.action) {
        case 'CAPTURE_PAGE': {
          const imageData = await captureScreenshot(sender.tab.id, message.coordinates);
          saveImage(imageData, message.pageNumber);

          captureData.tabId = sender.tab.id;

          sendResponse({ success: true });
          break;
        }

        case 'GENERATE_PDF': {
          captureData.startPage = message.startPage;
          captureData.endPage = message.endPage;

          await generatePDF(message.startPage, message.endPage);
          sendResponse({ success: true });
          break;
        }

        case 'UPDATE_PROGRESS': {
          // Popup に進捗を転送
          chrome.runtime.sendMessage({
            action: 'UPDATE_PROGRESS',
            current: message.current,
            total: message.total,
            status: message.status
          });
          sendResponse({ success: true });
          break;
        }

        case 'CAPTURE_CANCELLED': {
          captureData.images = [];
          captureData.isCapturing = false;
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

// Service Worker起動時のログ
console.log('[Kindle to PDF] Background script (Service Worker) loaded');
