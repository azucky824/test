"""
PDFレポート生成モジュール
ReportLabを使用してA4サイズのレポートを生成
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from PIL import Image
import io


class PDFReportGenerator:
    """PDFレポート生成クラス"""

    def __init__(self):
        """初期化"""
        self.page_width, self.page_height = A4
        self.margin = 20 * mm

        # 日本語フォントの登録を試みる（システムにある場合）
        self.font_registered = False
        try:
            # よくあるフォントパスを試す
            font_paths = [
                '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                'C:\\Windows\\Fonts\\msgothic.ttc',  # Windows
                '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',  # macOS
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Japanese', font_path))
                    self.font_registered = True
                    break
        except Exception as e:
            print(f"日本語フォント登録エラー: {e}")
            self.font_registered = False

    def generate_report(self, output_path: str, kendall_result: Dict,
                       frontal_eval: Dict, sagittal_eval: Dict,
                       frontal_image_path: str = None,
                       sagittal_image_path: str = None) -> bool:
        """
        評価レポートを生成

        Args:
            output_path: 出力PDFファイルパス
            kendall_result: ケンダル分類結果
            frontal_eval: 正面像評価結果
            sagittal_eval: 矢状面像評価結果
            frontal_image_path: 正面像（ランドマーク付き）のパス
            sagittal_image_path: 矢状面像（ランドマーク付き）のパス

        Returns:
            成功時True、失敗時False
        """
        try:
            c = canvas.Canvas(output_path, pagesize=A4)

            # ページ1: タイトルとケンダル分類
            self._draw_title_page(c, kendall_result)
            c.showPage()

            # ページ2: 正面像評価
            self._draw_frontal_evaluation(c, frontal_eval)
            c.showPage()

            # ページ3: 矢状面像評価
            self._draw_sagittal_evaluation(c, sagittal_eval)
            c.showPage()

            # ページ4: 総合コメントと推奨事項
            self._draw_recommendations(c, kendall_result, frontal_eval, sagittal_eval)
            c.showPage()

            # ページ5: 画像（ある場合）
            if frontal_image_path or sagittal_image_path:
                self._draw_images(c, frontal_image_path, sagittal_image_path)
                c.showPage()

            c.save()
            return True

        except Exception as e:
            print(f"PDF生成エラー: {e}")
            return False

    def _draw_title_page(self, c: canvas.Canvas, kendall_result: Dict):
        """タイトルページを描画"""
        y = self.page_height - self.margin

        # タイトル
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor('#667eea'))
        c.drawCentredString(self.page_width / 2, y, "Posture Evaluation Report")
        y -= 15 * mm

        c.setFont("Helvetica", 16)
        c.drawCentredString(self.page_width / 2, y, "Shisei Hyoka Hokokusho")
        y -= 20 * mm

        # 日付
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.grey)
        date_str = datetime.now().strftime("%Y/%m/%d")
        c.drawCentredString(self.page_width / 2, y, f"Evaluation Date: {date_str}")
        y -= 20 * mm

        # 区切り線
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(1)
        c.line(self.margin, y, self.page_width - self.margin, y)
        y -= 15 * mm

        # ケンダル分類
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#764ba2'))
        c.drawString(self.margin, y, "Kendall Posture Classification")
        y -= 12 * mm

        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#667eea'))
        c.drawString(self.margin, y, f"Type: {kendall_result['type']}")
        y -= 15 * mm

        # 説明
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        desc_text = kendall_result.get('description', '')
        self._draw_wrapped_text(c, desc_text, self.margin, y,
                               self.page_width - 2 * self.margin, 10)
        y -= 30 * mm

        # 特徴
        if 'characteristics' in kendall_result:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(self.margin, y, "Characteristics:")
            y -= 8 * mm

            c.setFont("Helvetica", 9)
            for char in kendall_result['characteristics'][:5]:  # 最大5つ
                c.drawString(self.margin + 5 * mm, y, f"• {char}")
                y -= 6 * mm

        # フッター
        self._draw_footer(c, 1)

    def _draw_frontal_evaluation(self, c: canvas.Canvas, frontal_eval: Dict):
        """正面像評価ページを描画"""
        y = self.page_height - self.margin

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#764ba2'))
        c.drawString(self.margin, y, "Frontal View Evaluation")
        y -= 12 * mm

        # 評価項目
        for item in frontal_eval.get('items', []):
            y = self._draw_evaluation_item(c, item, y)
            if y < 50 * mm:  # ページ下部に近づいたら中断
                break

        self._draw_footer(c, 2)

    def _draw_sagittal_evaluation(self, c: canvas.Canvas, sagittal_eval: Dict):
        """矢状面像評価ページを描画"""
        y = self.page_height - self.margin

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#764ba2'))
        c.drawString(self.margin, y, "Sagittal View Evaluation")
        y -= 12 * mm

        # 評価項目
        for item in sagittal_eval.get('items', []):
            y = self._draw_evaluation_item(c, item, y)
            if y < 50 * mm:
                break

        self._draw_footer(c, 3)

    def _draw_recommendations(self, c: canvas.Canvas, kendall_result: Dict,
                            frontal_eval: Dict, sagittal_eval: Dict):
        """推奨事項ページを描画"""
        y = self.page_height - self.margin

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#764ba2'))
        c.drawString(self.margin, y, "Recommendations")
        y -= 12 * mm

        # すべてのコメントと推奨事項を集める
        all_recommendations = []
        all_recommendations.extend(kendall_result.get('recommendations', []))
        all_recommendations.extend(frontal_eval.get('comments', []))
        all_recommendations.extend(sagittal_eval.get('comments', []))

        # 重複を削除
        all_recommendations = list(dict.fromkeys(all_recommendations))

        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)

        for i, rec in enumerate(all_recommendations[:15], 1):  # 最大15項目
            if y < 50 * mm:
                break

            # 番号付きリスト
            c.drawString(self.margin, y, f"{i}.")

            # テキストを折り返し
            text_width = self.page_width - 2 * self.margin - 10 * mm
            wrapped = self._wrap_text(rec, text_width, 10)

            for line in wrapped:
                c.drawString(self.margin + 10 * mm, y, line)
                y -= 6 * mm

            y -= 2 * mm

        self._draw_footer(c, 4)

    def _draw_images(self, c: canvas.Canvas, frontal_path: str, sagittal_path: str):
        """画像ページを描画"""
        y = self.page_height - self.margin

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor('#764ba2'))
        c.drawString(self.margin, y, "Posture Analysis Images")
        y -= 15 * mm

        image_width = self.page_width - 2 * self.margin
        max_image_height = 100 * mm

        # 正面像
        if frontal_path and os.path.exists(frontal_path):
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.grey)
            c.drawString(self.margin, y, "Frontal View with Landmarks")
            y -= 8 * mm

            try:
                img = Image.open(frontal_path)
                aspect = img.height / img.width
                img_height = min(image_width * aspect, max_image_height)
                img_width = img_height / aspect

                c.drawImage(frontal_path, self.margin, y - img_height,
                          width=img_width, height=img_height)
                y -= img_height + 10 * mm
            except Exception as e:
                print(f"正面像の描画エラー: {e}")

        # 矢状面像
        if sagittal_path and os.path.exists(sagittal_path) and y > 50 * mm:
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.grey)
            c.drawString(self.margin, y, "Sagittal View with Landmarks")
            y -= 8 * mm

            try:
                img = Image.open(sagittal_path)
                aspect = img.height / img.width
                img_height = min(image_width * aspect, max_image_height)
                img_width = img_height / aspect

                c.drawImage(sagittal_path, self.margin, y - img_height,
                          width=img_width, height=img_height)
            except Exception as e:
                print(f"矢状面像の描画エラー: {e}")

        self._draw_footer(c, 5)

    def _draw_evaluation_item(self, c: canvas.Canvas, item: Dict, y: float) -> float:
        """評価項目を描画"""
        severity = item.get('severity', 'good')

        # 背景色
        if severity == 'good':
            bg_color = colors.HexColor('#e8f5e9')
        elif severity == 'warning':
            bg_color = colors.HexColor('#fff3e0')
        else:
            bg_color = colors.HexColor('#ffebee')

        # 背景ボックス
        box_height = 25 * mm
        c.setFillColor(bg_color)
        c.rect(self.margin, y - box_height,
               self.page_width - 2 * self.margin, box_height,
               fill=1, stroke=0)

        # タイトル
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(self.margin + 3 * mm, y - 6 * mm, item['title'])

        # 値
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.grey)
        c.drawString(self.margin + 3 * mm, y - 12 * mm, f"Value: {item['value']}")

        # コメント
        c.setFont("Helvetica", 9)
        comment_text = item.get('comment', '')
        self._draw_wrapped_text(c, comment_text, self.margin + 3 * mm, y - 18 * mm,
                               self.page_width - 2 * self.margin - 6 * mm, 9)

        return y - box_height - 5 * mm

    def _draw_footer(self, c: canvas.Canvas, page_num: int):
        """フッターを描画"""
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.lightgrey)
        footer_text = f"Page {page_num} - Posture Evaluation System"
        c.drawCentredString(self.page_width / 2, 10 * mm, footer_text)

    def _wrap_text(self, text: str, max_width: float, font_size: int) -> list:
        """テキストを指定幅で折り返し"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # 簡易的な幅計算（実際のフォント幅とは異なる場合がある）
            if len(test_line) * font_size * 0.5 < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _draw_wrapped_text(self, c: canvas.Canvas, text: str, x: float, y: float,
                          max_width: float, font_size: int):
        """折り返しテキストを描画"""
        lines = self._wrap_text(text, max_width, font_size)
        for line in lines:
            c.drawString(x, y, line)
            y -= font_size * 1.2


from typing import Dict
