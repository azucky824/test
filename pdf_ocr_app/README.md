# PDF OCR GUIアプリケーション

PDFファイルからテキストを抽出するOCR（光学文字認識）GUIアプリケーションです。
ドラッグ&ドロップで簡単にPDFファイルを処理できます。

## 特徴

- **直感的なGUI**: シンプルで使いやすいインターフェース
- **ドラッグ&ドロップ対応**: PDFファイルをドロップするだけで読み込み可能
- **多言語対応**: 日本語、英語、または両方の言語でOCR処理が可能
- **複数ページ対応**: PDFの全ページを一括処理
- **テキスト保存機能**: 抽出したテキストをファイルに保存

## 必要要件

### システム要件

- Python 3.8以上
- Tesseract OCR

### Tesseract OCRのインストール

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-eng
```

#### macOS (Homebrew)
```bash
brew install tesseract tesseract-lang
```

#### Windows
1. [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)からインストーラーをダウンロード
2. インストール時に日本語と英語の言語データを選択
3. インストール後、`pdf_ocr_gui.py`の該当箇所でTesseractのパスを設定:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

## インストール

1. リポジトリをクローンまたはダウンロード

2. 必要なPythonパッケージをインストール:
   ```bash
   cd pdf_ocr_app
   pip install -r requirements.txt
   ```

## 使い方

1. アプリケーションを起動:
   ```bash
   python pdf_ocr_gui.py
   ```

2. PDFファイルを読み込む:
   - **方法1**: ドロップゾーンにPDFファイルをドラッグ&ドロップ
   - **方法2**: ドロップゾーンをクリックしてファイル選択ダイアログから選択

3. OCR言語を選択:
   - `jpn`: 日本語
   - `eng`: 英語
   - `jpn+eng`: 日本語と英語の両方

4. 「OCR実行」ボタンをクリック

5. 処理が完了したら、結果が表示されます

6. 必要に応じて「テキストを保存」ボタンで結果をファイルに保存

## 技術スタック

- **GUI**: tkinter (Python標準ライブラリ)
- **ドラッグ&ドロップ**: tkinterdnd2
- **PDF処理**: PyMuPDF (fitz)
- **OCR**: pytesseract (Tesseract OCRのPythonラッパー)
- **画像処理**: Pillow (PIL)

## トラブルシューティング

### Tesseractが見つからないエラー

**症状**: `TesseractNotFoundError`が発生する

**解決方法**:
1. Tesseract OCRがインストールされているか確認
2. `pdf_ocr_gui.py`の`main()`関数内でTesseractのパスを明示的に設定

### 日本語が認識されない

**症状**: 日本語のテキストが正しく抽出されない

**解決方法**:
1. 日本語言語データがインストールされているか確認:
   ```bash
   tesseract --list-langs
   ```
2. `jpn`が表示されない場合は、日本語言語パックを追加インストール

### OCRの精度が低い

**改善方法**:
- 元のPDFの画質を確認（スキャン品質が低い場合は精度も下がります）
- `pdf_ocr_gui.py`の`process_pdf()`関数内の解像度設定を調整:
  ```python
  mat = fitz.Matrix(3.0, 3.0)  # 解像度を上げる（処理時間は増加）
  ```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 注意事項

- 大きなPDFファイルや多ページのPDFは処理に時間がかかる場合があります
- OCRの精度は元のPDFの品質に大きく依存します
- 処理中はアプリケーションが一時的に応答しなくなることがありますが、プログレスバーで進行状況を確認できます
