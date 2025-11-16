/**
 * Kindle to PDF Converter - Capture Utilities
 * スクリーンショットのキャプチャとトリミング処理
 */

/**
 * スクリーンショットを取得
 * @param {number} tabId - タブID
 * @param {Object} options - キャプチャオプション
 * @returns {Promise<string>} base64エンコードされた画像データ
 */
export async function captureTab(tabId, options = {}) {
  const format = options.format || 'png';
  const quality = options.quality || 100;

  try {
    const dataUrl = await chrome.tabs.captureVisibleTab(null, {
      format: format,
      quality: quality
    });

    return dataUrl;
  } catch (error) {
    throw new Error(`スクリーンショットの取得に失敗: ${error.message}`);
  }
}

/**
 * 画像をトリミング
 * @param {string} dataUrl - 元画像のdata URL
 * @param {Object} rect - トリミング範囲 {x, y, width, height}
 * @returns {Promise<string>} トリミング後の画像data URL
 */
export async function cropImage(dataUrl, rect) {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      try {
        const canvas = new OffscreenCanvas(rect.width, rect.height);
        const ctx = canvas.getContext('2d');

        // 画像の一部を切り出し
        ctx.drawImage(
          img,
          rect.x, rect.y, rect.width, rect.height,
          0, 0, rect.width, rect.height
        );

        // BlobからData URLを生成
        canvas.convertToBlob({ type: 'image/png' }).then(blob => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.onerror = () => reject(new Error('画像の変換に失敗'));
          reader.readAsDataURL(blob);
        }).catch(reject);

      } catch (error) {
        reject(new Error(`画像のトリミングに失敗: ${error.message}`));
      }
    };

    img.onerror = () => reject(new Error('画像の読み込みに失敗'));
    img.src = dataUrl;
  });
}

/**
 * 画像サイズを取得
 * @param {string} dataUrl - 画像のdata URL
 * @returns {Promise<{width: number, height: number}>}
 */
export async function getImageDimensions(dataUrl) {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      resolve({
        width: img.width,
        height: img.height
      });
    };

    img.onerror = () => reject(new Error('画像の読み込みに失敗'));
    img.src = dataUrl;
  });
}

/**
 * 画像を圧縮
 * @param {string} dataUrl - 元画像のdata URL
 * @param {number} quality - 品質 (0-1)
 * @returns {Promise<string>} 圧縮後の画像data URL
 */
export async function compressImage(dataUrl, quality = 0.9) {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      try {
        const canvas = new OffscreenCanvas(img.width, img.height);
        const ctx = canvas.getContext('2d');

        ctx.drawImage(img, 0, 0);

        canvas.convertToBlob({
          type: 'image/jpeg',
          quality: quality
        }).then(blob => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.onerror = () => reject(new Error('画像の変換に失敗'));
          reader.readAsDataURL(blob);
        }).catch(reject);

      } catch (error) {
        reject(new Error(`画像の圧縮に失敗: ${error.message}`));
      }
    };

    img.onerror = () => reject(new Error('画像の読み込みに失敗'));
    img.src = dataUrl;
  });
}
