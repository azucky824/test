#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用サンプルPDFファイル作成スクリプト
動作確認用のシンプルなPDFファイルを生成します
"""

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("reportlabがインストールされていません")
    print("pip install reportlab を実行してください")
    exit(1)

import os


def create_sample_pdf(filename: str, num_pages: int, title: str):
    """サンプルPDFを作成"""
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    for i in range(num_pages):
        # ページ番号とタイトルを描画
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 100, title)

        c.setFont("Helvetica", 18)
        c.drawCentredString(width / 2, height / 2, f"Page {i + 1} / {num_pages}")

        # ページ固有の内容
        c.setFont("Helvetica", 12)
        y_position = height / 2 - 50

        # サンプルテキスト
        texts = [
            f"This is page {i + 1}",
            f"Document: {title}",
            "Sample training content",
            "Exercise descriptions go here",
        ]

        for text in texts:
            c.drawString(100, y_position, text)
            y_position -= 20

        # 枠線を描画
        c.rect(50, 50, width - 100, height - 100, stroke=1, fill=0)

        c.showPage()

    c.save()
    print(f"作成完了: {filename}")


def main():
    """メイン処理"""
    print("サンプルPDFファイルを作成します...")

    # 複数のサンプルPDFを作成
    samples = [
        ("sample_workout_1.pdf", 5, "Workout Plan 1"),
        ("sample_workout_2.pdf", 4, "Workout Plan 2"),
        ("sample_exercises.pdf", 6, "Exercise Guide"),
    ]

    for filename, pages, title in samples:
        create_sample_pdf(filename, pages, title)

    print("\nすべてのサンプルPDFを作成しました")
    print("training_menu_app.py を実行して動作確認してください")


if __name__ == "__main__":
    main()
