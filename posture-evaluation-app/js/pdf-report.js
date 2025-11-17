// PDFレポート生成
async function generatePDFReport() {
    try {
        // jsPDFのインスタンスを作成
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = 210; // A4幅 (mm)
        const pageHeight = 297; // A4高さ (mm)
        const margin = 20;
        let currentY = margin;

        // 日本語フォントの設定（デフォルトフォントを使用）
        doc.setFont('helvetica');

        // タイトル
        doc.setFontSize(24);
        doc.setTextColor(102, 126, 234);
        doc.text('Posture Evaluation Report', pageWidth / 2, currentY, { align: 'center' });
        currentY += 10;

        doc.setFontSize(18);
        doc.text('Shisei Hyoka Hokokusho', pageWidth / 2, currentY, { align: 'center' });
        currentY += 15;

        // 日付
        doc.setFontSize(10);
        doc.setTextColor(100, 100, 100);
        const today = new Date();
        const dateStr = `${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}/${String(today.getDate()).padStart(2, '0')}`;
        doc.text(`Evaluation Date: ${dateStr}`, pageWidth / 2, currentY, { align: 'center' });
        currentY += 15;

        // 区切り線
        doc.setDrawColor(200, 200, 200);
        doc.line(margin, currentY, pageWidth - margin, currentY);
        currentY += 10;

        // ケンダル分類セクション
        doc.setFontSize(16);
        doc.setTextColor(118, 75, 162);
        doc.text('Kendall Posture Classification (Sagittal View)', margin, currentY);
        currentY += 10;

        const kendallType = document.getElementById('kendall-type').textContent;
        doc.setFontSize(14);
        doc.setTextColor(102, 126, 234);
        doc.text(`Type: ${kendallType}`, margin, currentY);
        currentY += 10;

        // ケンダル分類の説明を追加
        const kendallDesc = document.getElementById('kendall-description').innerText;
        doc.setFontSize(10);
        doc.setTextColor(80, 80, 80);
        const descLines = doc.splitTextToSize(kendallDesc, pageWidth - 2 * margin);
        doc.text(descLines, margin, currentY);
        currentY += descLines.length * 5 + 10;

        // ページ区切りチェック
        if (currentY > pageHeight - 40) {
            doc.addPage();
            currentY = margin;
        }

        // 正面像評価セクション
        doc.setFontSize(16);
        doc.setTextColor(118, 75, 162);
        doc.text('Frontal View Evaluation', margin, currentY);
        currentY += 8;

        const frontalItems = document.querySelectorAll('#frontal-results .evaluation-item');
        currentY = addEvaluationItems(doc, frontalItems, currentY, margin, pageWidth, pageHeight);

        // ページ区切りチェック
        if (currentY > pageHeight - 60) {
            doc.addPage();
            currentY = margin;
        }

        // 矢状面像評価セクション
        doc.setFontSize(16);
        doc.setTextColor(118, 75, 162);
        doc.text('Sagittal View Evaluation', margin, currentY);
        currentY += 8;

        const sagittalItems = document.querySelectorAll('#sagittal-results .evaluation-item');
        currentY = addEvaluationItems(doc, sagittalItems, currentY, margin, pageWidth, pageHeight);

        // ページ区切りチェック
        if (currentY > pageHeight - 60) {
            doc.addPage();
            currentY = margin;
        }

        // 総合コメントセクション
        doc.setFontSize(16);
        doc.setTextColor(118, 75, 162);
        doc.text('Overall Comments and Recommendations', margin, currentY);
        currentY += 8;

        const comments = document.querySelectorAll('#overall-comments li');
        doc.setFontSize(10);
        doc.setTextColor(60, 60, 60);

        comments.forEach((comment, index) => {
            if (currentY > pageHeight - 30) {
                doc.addPage();
                currentY = margin;
            }

            const text = comment.textContent;
            const lines = doc.splitTextToSize(`${index + 1}. ${text}`, pageWidth - 2 * margin - 5);
            doc.text(lines, margin + 5, currentY);
            currentY += lines.length * 5 + 3;
        });

        // 新しいページを追加して画像を配置
        doc.addPage();
        currentY = margin;

        // タイトル
        doc.setFontSize(16);
        doc.setTextColor(118, 75, 162);
        doc.text('Posture Analysis Images', margin, currentY);
        currentY += 10;

        // 正面像キャンバス
        const frontalCanvas = document.getElementById('frontal-canvas');
        if (frontalCanvas) {
            doc.setFontSize(12);
            doc.setTextColor(100, 100, 100);
            doc.text('Frontal View with Landmarks', margin, currentY);
            currentY += 5;

            const frontalImgData = frontalCanvas.toDataURL('image/jpeg', 0.8);
            const imgWidth = pageWidth - 2 * margin;
            const imgHeight = (frontalCanvas.height / frontalCanvas.width) * imgWidth;

            if (imgHeight < 100) {
                doc.addImage(frontalImgData, 'JPEG', margin, currentY, imgWidth, imgHeight);
                currentY += imgHeight + 10;
            } else {
                const scaledHeight = 100;
                const scaledWidth = (frontalCanvas.width / frontalCanvas.height) * scaledHeight;
                doc.addImage(frontalImgData, 'JPEG', margin, currentY, scaledWidth, scaledHeight);
                currentY += scaledHeight + 10;
            }
        }

        // ページ区切りチェック
        if (currentY > pageHeight - 120) {
            doc.addPage();
            currentY = margin;
        }

        // 矢状面像キャンバス
        const sagittalCanvas = document.getElementById('sagittal-canvas');
        if (sagittalCanvas) {
            doc.setFontSize(12);
            doc.setTextColor(100, 100, 100);
            doc.text('Sagittal View with Landmarks', margin, currentY);
            currentY += 5;

            const sagittalImgData = sagittalCanvas.toDataURL('image/jpeg', 0.8);
            const imgWidth = pageWidth - 2 * margin;
            const imgHeight = (sagittalCanvas.height / sagittalCanvas.width) * imgWidth;

            if (imgHeight < 100) {
                doc.addImage(sagittalImgData, 'JPEG', margin, currentY, imgWidth, imgHeight);
                currentY += imgHeight + 10;
            } else {
                const scaledHeight = 100;
                const scaledWidth = (sagittalCanvas.width / sagittalCanvas.height) * scaledHeight;
                doc.addImage(sagittalImgData, 'JPEG', margin, currentY, scaledWidth, scaledHeight);
                currentY += scaledHeight + 10;
            }
        }

        // フッター（全ページに追加）
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setFontSize(8);
            doc.setTextColor(150, 150, 150);
            doc.text(
                `Page ${i} of ${pageCount} - Posture Evaluation System`,
                pageWidth / 2,
                pageHeight - 10,
                { align: 'center' }
            );
        }

        // PDFを保存
        const filename = `posture_evaluation_${dateStr.replace(/\//g, '')}.pdf`;
        doc.save(filename);

        alert('PDFレポートをダウンロードしました！');

    } catch (error) {
        console.error('PDF生成エラー:', error);
        alert('PDFの生成中にエラーが発生しました。');
    }
}

// 評価項目をPDFに追加
function addEvaluationItems(doc, items, startY, margin, pageWidth, pageHeight) {
    let currentY = startY;

    items.forEach((item) => {
        // ページ区切りチェック
        if (currentY > pageHeight - 40) {
            doc.addPage();
            currentY = margin;
        }

        const title = item.querySelector('.evaluation-item-title').textContent;
        const value = item.querySelector('.evaluation-item-value').textContent;
        const comment = item.querySelector('.evaluation-item-comment').textContent;
        const severity = item.classList.contains('good') ? 'good' :
            item.classList.contains('warning') ? 'warning' : 'poor';

        // 背景色
        if (severity === 'good') {
            doc.setFillColor(76, 175, 80, 0.1);
        } else if (severity === 'warning') {
            doc.setFillColor(255, 152, 0, 0.1);
        } else {
            doc.setFillColor(244, 67, 54, 0.1);
        }

        const boxHeight = 20;
        doc.rect(margin, currentY - 5, pageWidth - 2 * margin, boxHeight, 'F');

        // タイトル
        doc.setFontSize(11);
        doc.setTextColor(60, 60, 60);
        doc.setFont('helvetica', 'bold');
        doc.text(title, margin + 3, currentY);
        currentY += 5;

        // 値
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(80, 80, 80);
        doc.text(`Value: ${value}`, margin + 3, currentY);
        currentY += 5;

        // コメント
        doc.setFontSize(9);
        doc.setTextColor(100, 100, 100);
        const commentLines = doc.splitTextToSize(comment, pageWidth - 2 * margin - 6);
        doc.text(commentLines, margin + 3, currentY);
        currentY += commentLines.length * 4 + 5;
    });

    return currentY;
}
