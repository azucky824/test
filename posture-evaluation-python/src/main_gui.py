"""
姿勢評価アプリケーション - メインGUI
CustomTkinterを使用したモダンなデスクトップアプリケーション
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import sys
import threading
from datetime import datetime

# モジュールのインポート
from pose_detector import PoseDetector
from kendall_classifier import KendallClassifier
from evaluator import PostureEvaluator
from pdf_generator import PDFReportGenerator


class PostureEvaluationApp(ctk.CTk):
    """姿勢評価アプリケーションのメインクラス"""

    def __init__(self):
        super().__init__()

        # ウィンドウ設定
        self.title("姿勢評価システム - Posture Evaluation System")
        self.geometry("1400x900")

        # カラーテーマ設定
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 状態変数
        self.frontal_image_path = None
        self.sagittal_image_path = None
        self.frontal_detection = None
        self.sagittal_detection = None
        self.frontal_annotated_image = None
        self.sagittal_annotated_image = None
        self.kendall_result = None
        self.frontal_eval = None
        self.sagittal_eval = None

        # モジュールの初期化
        self.pose_detector = PoseDetector()
        self.kendall_classifier = KendallClassifier()
        self.evaluator = PostureEvaluator()
        self.pdf_generator = PDFReportGenerator()

        # GUI構築
        self._create_header()
        self._create_main_content()
        self._create_footer()

    def _create_header(self):
        """ヘッダーセクションを作成"""
        header_frame = ctk.CTkFrame(self, fg_color=("#667eea", "#764ba2"),
                                    corner_radius=0, height=120)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header_frame,
            text="姿勢評価システム",
            font=("Helvetica", 32, "bold"),
            text_color="white"
        )
        title_label.pack(pady=15)

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Posture Evaluation System - AI-Powered Analysis",
            font=("Helvetica", 14),
            text_color="white"
        )
        subtitle_label.pack()

    def _create_main_content(self):
        """メインコンテンツエリアを作成"""
        # スクロール可能なフレーム
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 画像アップロードセクション
        self._create_upload_section()

        # 評価ボタンセクション
        self._create_action_section()

        # 結果表示セクション
        self._create_results_section()

    def _create_upload_section(self):
        """画像アップロードセクションを作成"""
        upload_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        upload_frame.pack(fill="x", pady=(0, 20))

        # 2カラムレイアウト
        upload_frame.grid_columnconfigure(0, weight=1)
        upload_frame.grid_columnconfigure(1, weight=1)

        # 正面像アップロード
        frontal_frame = self._create_image_upload_card(
            upload_frame, "正面像 (Frontal View)", "frontal"
        )
        frontal_frame.grid(row=0, column=0, padx=10, sticky="nsew")

        # 矢状面像アップロード
        sagittal_frame = self._create_image_upload_card(
            upload_frame, "矢状面像 (Sagittal View)", "sagittal"
        )
        sagittal_frame.grid(row=0, column=1, padx=10, sticky="nsew")

    def _create_image_upload_card(self, parent, title, view_type):
        """画像アップロードカードを作成"""
        card = ctk.CTkFrame(parent, fg_color=("#f8f9ff", "#2b2b2b"),
                           corner_radius=15)

        # タイトル
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Helvetica", 18, "bold"),
            text_color=("#667eea", "#667eea")
        )
        title_label.pack(pady=(20, 10))

        # 画像表示エリア
        image_frame = ctk.CTkFrame(card, width=400, height=300,
                                  fg_color=("#ffffff", "#1e1e1e"),
                                  border_width=2,
                                  border_color=("#ddd", "#444"))
        image_frame.pack(padx=20, pady=10)
        image_frame.pack_propagate(False)

        # プレースホルダー
        placeholder_label = ctk.CTkLabel(
            image_frame,
            text="📷\n\nクリックして画像を選択\nまたは\nドラッグ&ドロップ",
            font=("Helvetica", 14),
            text_color=("#999", "#666")
        )
        placeholder_label.pack(expand=True)

        # 画像ラベル（後で使用）
        image_label = ctk.CTkLabel(image_frame, text="")

        # アップロードボタン
        upload_btn = ctk.CTkButton(
            card,
            text="📁 画像を選択",
            command=lambda: self._select_image(view_type, image_label, placeholder_label),
            fg_color=("#667eea", "#667eea"),
            hover_color=("#5568d3", "#5568d3"),
            corner_radius=25,
            height=40,
            font=("Helvetica", 14, "bold")
        )
        upload_btn.pack(pady=(10, 20), padx=20, fill="x")

        # カードにラベルを保存
        card.image_label = image_label
        card.placeholder_label = placeholder_label

        return card

    def _select_image(self, view_type, image_label, placeholder_label):
        """画像を選択"""
        file_path = filedialog.askopenfilename(
            title=f"{'正面像' if view_type == 'frontal' else '矢状面像'}を選択",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.bmp"),
                ("すべてのファイル", "*.*")
            ]
        )

        if file_path:
            try:
                # 画像を読み込み
                image = Image.open(file_path)

                # サムネイルサイズに縮小
                image.thumbnail((380, 280), Image.Resampling.LANCZOS)

                # PhotoImageに変換
                photo = ImageTk.PhotoImage(image)

                # 画像を表示
                placeholder_label.pack_forget()
                image_label.configure(image=photo, text="")
                image_label.image = photo  # 参照を保持
                image_label.pack(expand=True)

                # パスを保存
                if view_type == "frontal":
                    self.frontal_image_path = file_path
                else:
                    self.sagittal_image_path = file_path

                # 評価ボタンの状態を更新
                self._update_evaluate_button()

            except Exception as e:
                messagebox.showerror("エラー", f"画像の読み込みに失敗しました: {e}")

    def _create_action_section(self):
        """アクションセクションを作成"""
        action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=20)

        # 評価ボタン
        self.evaluate_btn = ctk.CTkButton(
            action_frame,
            text="🔍 姿勢を評価する",
            command=self._start_evaluation,
            fg_color=("#667eea", "#667eea"),
            hover_color=("#5568d3", "#5568d3"),
            corner_radius=30,
            height=50,
            font=("Helvetica", 16, "bold"),
            state="disabled"
        )
        self.evaluate_btn.pack(pady=10)

        # プログレスバー
        self.progress_bar = ctk.CTkProgressBar(
            action_frame,
            width=400,
            height=8,
            corner_radius=4,
            progress_color=("#667eea", "#667eea")
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget()  # 初期は非表示

        # ステータスラベル
        self.status_label = ctk.CTkLabel(
            action_frame,
            text="",
            font=("Helvetica", 12),
            text_color=("#666", "#999")
        )
        self.status_label.pack()

    def _create_results_section(self):
        """結果表示セクションを作成"""
        self.results_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, pady=20)
        self.results_frame.pack_forget()  # 初期は非表示

    def _update_evaluate_button(self):
        """評価ボタンの状態を更新"""
        if self.frontal_image_path and self.sagittal_image_path:
            self.evaluate_btn.configure(state="normal")
        else:
            self.evaluate_btn.configure(state="disabled")

    def _start_evaluation(self):
        """評価を開始（別スレッドで実行）"""
        self.evaluate_btn.configure(state="disabled")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.status_label.configure(text="評価を開始します...")

        # 別スレッドで実行
        thread = threading.Thread(target=self._run_evaluation)
        thread.daemon = True
        thread.start()

    def _run_evaluation(self):
        """評価を実行"""
        try:
            # 正面像の検出
            self.status_label.configure(text="正面像を解析中...")
            self.progress_bar.set(0.2)
            self.frontal_detection = self.pose_detector.detect(self.frontal_image_path)

            if not self.frontal_detection:
                self._show_error("正面像から姿勢を検出できませんでした。")
                return

            # 矢状面像の検出
            self.status_label.configure(text="矢状面像を解析中...")
            self.progress_bar.set(0.4)
            self.sagittal_detection = self.pose_detector.detect(self.sagittal_image_path)

            if not self.sagittal_detection:
                self._show_error("矢状面像から姿勢を検出できませんでした。")
                return

            # ケンダル分類
            self.status_label.configure(text="ケンダル分類を実行中...")
            self.progress_bar.set(0.6)
            self.kendall_result = self.kendall_classifier.classify(self.sagittal_detection)

            # 評価実行
            self.status_label.configure(text="詳細評価を実行中...")
            self.progress_bar.set(0.8)
            self.frontal_eval = self.evaluator.evaluate_frontal_view(self.frontal_detection)
            self.sagittal_eval = self.evaluator.evaluate_sagittal_view(self.sagittal_detection)

            # ランドマーク付き画像を生成
            self.frontal_annotated_image = self.pose_detector.draw_landmarks(
                self.frontal_image_path, self.frontal_detection
            )
            self.sagittal_annotated_image = self.pose_detector.draw_landmarks(
                self.sagittal_image_path, self.sagittal_detection
            )

            # 完了
            self.progress_bar.set(1.0)
            self.status_label.configure(text="✅ 評価が完了しました！")

            # 結果を表示
            self.after(100, self._display_results)

        except Exception as e:
            self._show_error(f"評価中にエラーが発生しました: {e}")

        finally:
            self.after(2000, lambda: self.progress_bar.pack_forget())
            self.after(100, lambda: self.evaluate_btn.configure(state="normal"))

    def _show_error(self, message):
        """エラーメッセージを表示"""
        self.after(0, lambda: messagebox.showerror("エラー", message))
        self.after(0, lambda: self.status_label.configure(text="❌ エラーが発生しました"))
        self.after(0, lambda: self.progress_bar.pack_forget())

    def _display_results(self):
        """評価結果を表示"""
        # 既存の結果をクリア
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.results_frame.pack(fill="both", expand=True, pady=20)

        # タイトル
        title = ctk.CTkLabel(
            self.results_frame,
            text="📊 評価結果",
            font=("Helvetica", 24, "bold"),
            text_color=("#667eea", "#667eea")
        )
        title.pack(pady=(0, 20))

        # ケンダル分類結果
        self._display_kendall_result()

        # 正面像・矢状面像評価
        eval_container = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        eval_container.pack(fill="x", pady=20)
        eval_container.grid_columnconfigure(0, weight=1)
        eval_container.grid_columnconfigure(1, weight=1)

        # 正面像評価
        frontal_card = self._create_evaluation_card(
            eval_container, "正面像評価", self.frontal_eval
        )
        frontal_card.grid(row=0, column=0, padx=10, sticky="nsew")

        # 矢状面像評価
        sagittal_card = self._create_evaluation_card(
            eval_container, "矢状面像評価", self.sagittal_eval
        )
        sagittal_card.grid(row=0, column=1, padx=10, sticky="nsew")

        # PDFダウンロードボタン
        pdf_btn = ctk.CTkButton(
            self.results_frame,
            text="📄 A4レポートをダウンロード",
            command=self._generate_pdf_report,
            fg_color=("#764ba2", "#764ba2"),
            hover_color=("#5f3a82", "#5f3a82"),
            corner_radius=30,
            height=50,
            font=("Helvetica", 16, "bold")
        )
        pdf_btn.pack(pady=20)

    def _display_kendall_result(self):
        """ケンダル分類結果を表示"""
        card = ctk.CTkFrame(self.results_frame, fg_color=("#f8f9ff", "#2b2b2b"),
                           corner_radius=15)
        card.pack(fill="x", padx=10, pady=10)

        # タイトル
        title = ctk.CTkLabel(
            card,
            text="ケンダルの姿勢分類（矢状面）",
            font=("Helvetica", 18, "bold"),
            text_color=("#764ba2", "#764ba2")
        )
        title.pack(pady=(20, 10), padx=20, anchor="w")

        # 分類タイプ
        type_frame = ctk.CTkFrame(card, fg_color=("#e8eaf6", "#3a3a5a"),
                                 corner_radius=10)
        type_frame.pack(fill="x", padx=20, pady=10)

        type_label = ctk.CTkLabel(
            type_frame,
            text=self.kendall_result['type'],
            font=("Helvetica", 20, "bold"),
            text_color=("#667eea", "#667eea")
        )
        type_label.pack(pady=15)

        # 説明
        desc_label = ctk.CTkLabel(
            card,
            text=self.kendall_result.get('description', ''),
            font=("Helvetica", 12),
            wraplength=1200,
            justify="left"
        )
        desc_label.pack(pady=10, padx=20, anchor="w")

        # 特徴
        if 'characteristics' in self.kendall_result:
            char_label = ctk.CTkLabel(
                card,
                text="特徴:",
                font=("Helvetica", 14, "bold")
            )
            char_label.pack(pady=(10, 5), padx=20, anchor="w")

            for char in self.kendall_result['characteristics']:
                bullet = ctk.CTkLabel(
                    card,
                    text=f"  • {char}",
                    font=("Helvetica", 11)
                )
                bullet.pack(pady=2, padx=30, anchor="w")

        card.pack_configure(pady=10)

    def _create_evaluation_card(self, parent, title, eval_result):
        """評価カードを作成"""
        card = ctk.CTkFrame(parent, fg_color=("#f8f9ff", "#2b2b2b"),
                           corner_radius=15)

        # タイトル
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Helvetica", 16, "bold"),
            text_color=("#764ba2", "#764ba2")
        )
        title_label.pack(pady=(15, 10), padx=15, anchor="w")

        # 評価項目
        for item in eval_result.get('items', []):
            self._create_evaluation_item(card, item)

        return card

    def _create_evaluation_item(self, parent, item):
        """評価項目を作成"""
        severity = item.get('severity', 'good')

        # 色設定
        if severity == 'good':
            bg_color = ("#e8f5e9", "#2d4a2e")
            border_color = "#4caf50"
        elif severity == 'warning':
            bg_color = ("#fff3e0", "#4a3d2d")
            border_color = "#ff9800"
        else:
            bg_color = ("#ffebee", "#4a2d2e")
            border_color = "#f44336"

        item_frame = ctk.CTkFrame(parent, fg_color=bg_color,
                                 corner_radius=8, border_width=2,
                                 border_color=border_color)
        item_frame.pack(fill="x", padx=15, pady=5)

        # タイトル
        title_label = ctk.CTkLabel(
            item_frame,
            text=item['title'],
            font=("Helvetica", 13, "bold"),
            anchor="w"
        )
        title_label.pack(pady=(8, 2), padx=10, anchor="w")

        # 値
        value_label = ctk.CTkLabel(
            item_frame,
            text=f"値: {item['value']}",
            font=("Helvetica", 11),
            anchor="w"
        )
        value_label.pack(pady=2, padx=10, anchor="w")

        # コメント
        comment_label = ctk.CTkLabel(
            item_frame,
            text=item.get('comment', ''),
            font=("Helvetica", 10),
            wraplength=500,
            anchor="w",
            justify="left"
        )
        comment_label.pack(pady=(2, 8), padx=10, anchor="w")

    def _generate_pdf_report(self):
        """PDFレポートを生成"""
        # 保存先を選択
        file_path = filedialog.asksaveasfilename(
            title="PDFレポートを保存",
            defaultextension=".pdf",
            initialfile=f"posture_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            filetypes=[("PDFファイル", "*.pdf"), ("すべてのファイル", "*.*")]
        )

        if not file_path:
            return

        try:
            self.status_label.configure(text="PDFレポートを生成中...")

            # 一時的にランドマーク付き画像を保存
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)

            frontal_temp = os.path.join(temp_dir, "frontal_annotated.jpg")
            sagittal_temp = os.path.join(temp_dir, "sagittal_annotated.jpg")

            cv2.imwrite(frontal_temp, cv2.cvtColor(self.frontal_annotated_image, cv2.COLOR_RGB2BGR))
            cv2.imwrite(sagittal_temp, cv2.cvtColor(self.sagittal_annotated_image, cv2.COLOR_RGB2BGR))

            # PDFを生成
            success = self.pdf_generator.generate_report(
                file_path,
                self.kendall_result,
                self.frontal_eval,
                self.sagittal_eval,
                frontal_temp,
                sagittal_temp
            )

            # 一時ファイルを削除
            try:
                os.remove(frontal_temp)
                os.remove(sagittal_temp)
                os.rmdir(temp_dir)
            except:
                pass

            if success:
                messagebox.showinfo("成功", "PDFレポートを生成しました！")
                self.status_label.configure(text="✅ PDFレポートを生成しました")
            else:
                messagebox.showerror("エラー", "PDFレポートの生成に失敗しました。")
                self.status_label.configure(text="❌ PDF生成エラー")

        except Exception as e:
            messagebox.showerror("エラー", f"PDF生成中にエラーが発生しました: {e}")
            self.status_label.configure(text="❌ PDF生成エラー")

    def _create_footer(self):
        """フッターセクションを作成"""
        footer_frame = ctk.CTkFrame(self, fg_color=("#f8f9ff", "#2b2b2b"),
                                   corner_radius=0, height=50)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)

        footer_label = ctk.CTkLabel(
            footer_frame,
            text="© 2025 Posture Evaluation System | 教育目的での使用に限ります",
            font=("Helvetica", 10),
            text_color=("#666", "#999")
        )
        footer_label.pack(pady=15)


def main():
    """メイン関数"""
    app = PostureEvaluationApp()
    app.mainloop()


if __name__ == "__main__":
    main()
