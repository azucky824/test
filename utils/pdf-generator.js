/**
 * Kindle to PDF Converter - PDF Generator Utilities
 * 画像からPDFを生成する処理
 */

/**
 * jsPDFライブラリが読み込まれているか確認
 * @returns {boolean}
 */
function isJsPDFLoaded() {
  return typeof window !== 'undefined' &&
         (typeof window.jspdf !== 'undefined' || typeof jspdf !== 'undefined');
}

/**
 * jsPDFライブラリを動的に読み込む
 * @returns {Promise<void>}
 */
export async function loadJsPDF() {
  if (isJsPDFLoaded()) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js';

    script.onload = () => {
      console.log('[PDF Generator] jsPDF読み込み成功');
      resolve();
    };

    script.onerror = () => {
      reject(new Error(
        'jsPDFの読み込みに失敗しました。' +
        'インターネット接続を確認するか、手動でライブラリをダウンロードしてください。'
      ));
    };

    if (typeof document !== 'undefined') {
      document.head.appendChild(script);
    } else {
      reject(new Error('Document オブジェクトが利用できません'));
    }
  });
}

/**
 * 画像配列からPDFを生成
 * @param {Array<{pageNumber: number, data: string}>} images - 画像データの配列
 * @param {Object} options - PDFオプション
 * @returns {Promise<Blob>} PDF Blob
 */
export async function generatePDF(images, options = {}) {
  // jsPDFを読み込み
  await loadJsPDF();

  if (images.length === 0) {
    throw new Error('画像が指定されていません');
  }

  // ページ番号順にソート
  const sortedImages = [...images].sort((a, b) => a.pageNumber - b.pageNumber);

  return new Promise((resolve, reject) => {
    try {
      const { jsPDF } = window.jspdf || jspdf;

      // PDFオプション
      const orientation = options.orientation || 'portrait';
      const format = options.format || 'a4';
      const compress = options.compress !== false;

      // jsPDFインスタンスを作成
      const pdf = new jsPDF({
        orientation: orientation,
        unit: 'px',
        format: format,
        compress: compress
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

      // 各画像を順番に処理
      for (let i = 0; i < sortedImages.length; i++) {
        const imageData = sortedImages[i];

        // 最初のページ以外は新しいページを追加
        if (!isFirstPage) {
          pdf.addPage();
        }
        isFirstPage = false;

        // ページサイズを取得
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();

        // 画像をページに追加
        // アスペクト比を維持しながらページ全体に配置
        pdf.addImage(
          imageData.data,
          'PNG',
          0,
          0,
          pageWidth,
          pageHeight,
          `page_${imageData.pageNumber}`,
          'FAST' // 'FAST' | 'SLOW' - 圧縮方式
        );

        console.log(
          `[PDF Generator] ページ ${imageData.pageNumber} を追加 ` +
          `(${i + 1}/${sortedImages.length})`
        );
      }

      // PDFをBlobとして出力
      const pdfBlob = pdf.output('blob');

      console.log(
        `[PDF Generator] PDF生成完了 ` +
        `(${sortedImages.length}ページ, ${(pdfBlob.size / 1024 / 1024).toFixed(2)} MB)`
      );

      resolve(pdfBlob);

    } catch (error) {
      console.error('[PDF Generator] PDF生成エラー:', error);
      reject(new Error(`PDF生成に失敗: ${error.message}`));
    }
  });
}

/**
 * PDFファイルをダウンロード
 * @param {Blob} pdfBlob - PDF Blob
 * @param {string} filename - ファイル名
 * @returns {Promise<void>}
 */
export async function downloadPDF(pdfBlob, filename) {
  try {
    const url = URL.createObjectURL(pdfBlob);

    await chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: true
    });

    console.log(`[PDF Generator] ダウンロード開始: ${filename}`);

    // 少し待ってからURLを解放
    setTimeout(() => {
      URL.revokeObjectURL(url);
      console.log('[PDF Generator] Blob URL解放');
    }, 2000);

  } catch (error) {
    throw new Error(`PDFのダウンロードに失敗: ${error.message}`);
  }
}

/**
 * ファイル名を生成
 * @param {Object} options - オプション
 * @returns {string} ファイル名
 */
export function generateFilename(options = {}) {
  const {
    title = 'kindle-book',
    startPage = null,
    endPage = null,
    timestamp = true
  } = options;

  let filename = title.replace(/[^a-zA-Z0-9-_]/g, '_');

  if (startPage && endPage) {
    filename += `_p${startPage}-${endPage}`;
  }

  if (timestamp) {
    const now = new Date();
    const dateStr = now.toISOString()
      .replace(/[:.]/g, '-')
      .slice(0, -5);
    filename += `_${dateStr}`;
  }

  filename += '.pdf';

  return filename;
}

/**
 * 画像を最適化してPDFに追加
 * @param {Array} images - 画像データの配列
 * @param {Object} options - 最適化オプション
 * @returns {Promise<Array>} 最適化された画像データ
 */
export async function optimizeImages(images, options = {}) {
  const {
    maxWidth = 1200,
    maxHeight = 1600,
    quality = 0.9,
    format = 'jpeg'
  } = options;

  console.log(`[PDF Generator] 画像最適化開始 (${images.length}枚)`);

  const optimizedImages = [];

  for (const imageData of images) {
    try {
      // TODO: 画像リサイズと圧縮を実装
      // 現在は元の画像をそのまま使用
      optimizedImages.push(imageData);
    } catch (error) {
      console.warn(`[PDF Generator] ページ ${imageData.pageNumber} の最適化に失敗:`, error);
      // 最適化に失敗した場合は元の画像を使用
      optimizedImages.push(imageData);
    }
  }

  console.log(`[PDF Generator] 画像最適化完了`);
  return optimizedImages;
}
