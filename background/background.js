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
  tabId: null,
  tableOfContents: null,
  bookTitle: null,
  // プログレス情報
  progress: {
    current: 0,
    total: 0,
    status: '',
    error: null,
    completed: false
  }
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
 * @param {Array} tableOfContents - 目次情報
 * @param {string} bookTitle - 書籍タイトル
 * @param {string} readingDirection - 読み方向（rtl/ltr）
 */
async function generatePDF(startPage, endPage, tableOfContents = null, bookTitle = null, readingDirection = 'ltr') {
  try {
    console.log('[Kindle to PDF] PDF生成開始');
    console.log(`[Kindle to PDF] 読み方向: ${readingDirection === 'rtl' ? '右開き（縦書き）' : '左開き（横書き）'}`);

    if (captureData.images.length === 0) {
      throw new Error('キャプチャされた画像がありません');
    }

    // ページ番号順にソート（右開きの場合は逆順）
    if (readingDirection === 'rtl') {
      captureData.images.sort((a, b) => b.pageNumber - a.pageNumber);
      console.log('[Kindle to PDF] 右開き書籍のため、ページ順を逆にします');
    } else {
      captureData.images.sort((a, b) => a.pageNumber - b.pageNumber);
    }

    // PDF生成オプション
    const pdfOptions = {
      tableOfContents: tableOfContents,
      title: bookTitle,
      readingDirection: readingDirection
    };

    // PDF生成ユーティリティを呼び出し
    const pdfBlob = await createPDFFromImages(captureData.images, pdfOptions);

    // ファイル名を生成
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const directionSuffix = readingDirection === 'rtl' ? '_縦書き' : '';
    let filename;
    if (bookTitle) {
      const safeTitle = bookTitle.replace(/[^a-zA-Z0-9-_\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/g, '_').slice(0, 50);
      filename = `${safeTitle}${directionSuffix}_p${startPage}-${endPage}_${timestamp}.pdf`;
    } else {
      filename = `kindle-book${directionSuffix}_p${startPage}-${endPage}-${timestamp}.pdf`;
    }

    // PDFをダウンロード
    const url = URL.createObjectURL(pdfBlob);
    await chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: true
    });

    console.log(`[Kindle to PDF] PDF生成完了: ${filename}`);

    // プログレス情報を更新
    captureData.progress = {
      current: captureData.progress.total,
      total: captureData.progress.total,
      status: `PDF生成完了: ${filename}`,
      error: null,
      completed: true
    };

    // バッジをクリア
    chrome.action.setBadgeText({ text: '' });

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

    // プログレス情報にエラーを記録
    captureData.progress = {
      ...captureData.progress,
      status: `エラー: ${error.message}`,
      error: error.message,
      completed: false
    };
    captureData.isCapturing = false;

    // バッジにエラーを表示
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#ea4335' });

    chrome.runtime.sendMessage({
      action: 'CAPTURE_ERROR',
      error: error.message
    });
  }
}

/**
 * PDFに目次ページを追加
 * @param {Object} pdf - jsPDFインスタンス
 * @param {Array} tableOfContents - 目次データ
 * @param {string} bookTitle - 書籍タイトル
 */
function addTableOfContentsPage(pdf, tableOfContents, bookTitle = null) {
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 40;
  let yPosition = margin;

  // タイトル
  if (bookTitle) {
    pdf.setFontSize(20);
    pdf.setFont(undefined, 'bold');
    pdf.text(bookTitle, margin, yPosition);
    yPosition += 30;
  }

  // 「目次」ヘッダー
  pdf.setFontSize(16);
  pdf.setFont(undefined, 'bold');
  pdf.text('Table of Contents / 目次', margin, yPosition);
  yPosition += 25;

  // 区切り線
  pdf.setLineWidth(0.5);
  pdf.line(margin, yPosition, pageWidth - margin, yPosition);
  yPosition += 15;

  // 目次項目
  pdf.setFontSize(12);
  pdf.setFont(undefined, 'normal');

  const lineHeight = 18;
  const maxItemsPerPage = Math.floor((pageHeight - yPosition - margin) / lineHeight);

  tableOfContents.forEach((item, index) => {
    // ページが足りない場合、新しいページを追加
    if (index > 0 && index % maxItemsPerPage === 0) {
      pdf.addPage();
      yPosition = margin;

      pdf.setFontSize(16);
      pdf.setFont(undefined, 'bold');
      pdf.text('Table of Contents / 目次（続き）', margin, yPosition);
      yPosition += 25;

      pdf.setFontSize(12);
      pdf.setFont(undefined, 'normal');
    }

    // インデント（階層レベルに応じて）
    const indent = margin + (item.level || 0) * 15;

    // 項目テキスト
    const itemText = `${index + 1}. ${item.title}`;

    // テキストが長すぎる場合は切り詰め
    const maxWidth = pageWidth - indent - margin - 60;
    const lines = pdf.splitTextToSize(itemText, maxWidth);

    // 最初の行のみ表示（複数行は省略）
    const displayText = lines[0] + (lines.length > 1 ? '...' : '');
    pdf.text(displayText, indent, yPosition);

    // ページ番号（右揃え）
    if (item.pageNumber) {
      const pageNumText = `p.${item.pageNumber}`;
      const pageNumWidth = pdf.getTextWidth(pageNumText);
      pdf.text(pageNumText, pageWidth - margin - pageNumWidth, yPosition);
    }

    yPosition += lineHeight;
  });

  console.log(`[Kindle to PDF] 目次ページを追加 (${tableOfContents.length}項目)`);
}

/**
 * 画像配列からPDFを生成
 * @param {Array} images - 画像データの配列
 * @param {Object} options - PDFオプション
 * @returns {Promise<Blob>} PDF Blob
 */
async function createPDFFromImages(images, options = {}) {
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

      // メタデータを設定
      if (options.title) {
        pdf.setProperties({
          title: options.title,
          subject: 'Kindle Book',
          author: options.author || 'Kindle to PDF Converter',
          creator: 'Kindle to PDF Converter Extension',
          keywords: options.keywords || 'kindle, pdf, ebook'
        });
      }

      let isFirstPage = true;

      // 目次ページを追加（オプション）
      if (options.tableOfContents && options.tableOfContents.length > 0) {
        addTableOfContentsPage(pdf, options.tableOfContents, options.title);
        isFirstPage = false;
      }

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
          captureData.tableOfContents = message.tableOfContents || null;
          captureData.bookTitle = message.bookTitle || null;
          captureData.readingDirection = message.readingDirection || 'ltr';

          await generatePDF(
            message.startPage,
            message.endPage,
            message.tableOfContents,
            message.bookTitle,
            message.readingDirection || 'ltr'
          );
          sendResponse({ success: true });
          break;
        }

        case 'UPDATE_PROGRESS': {
          // プログレス情報を保存
          captureData.progress = {
            current: message.current,
            total: message.total,
            status: message.status,
            error: null,
            completed: false
          };
          captureData.isCapturing = true;

          console.log('[Kindle to PDF Background] プログレス更新:', captureData.progress);

          // バッジにプログレスを表示
          const percentage = Math.round((message.current / message.total) * 100);
          chrome.action.setBadgeText({ text: `${percentage}%` });
          chrome.action.setBadgeBackgroundColor({ color: '#4285f4' });

          sendResponse({ success: true });
          break;
        }

        case 'GET_PROGRESS': {
          // popupからのプログレス問い合わせ
          sendResponse({
            success: true,
            progress: captureData.progress
          });
          break;
        }

        case 'CAPTURE_CANCELLED': {
          captureData.images = [];
          captureData.isCapturing = false;

          // プログレス情報をリセット
          captureData.progress = {
            current: 0,
            total: 0,
            status: 'キャンセルされました',
            error: null,
            completed: false
          };

          // バッジをクリア
          chrome.action.setBadgeText({ text: '' });

          console.log('[Kindle to PDF Background] キャプチャをキャンセルしました');

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
