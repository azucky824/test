# Kindle Screenshot Tool - EXE ビルド手順

## 方法1: バッチファイルを使用（簡単）

1. **build_exe.bat** をダブルクリック
2. 自動的に必要なライブラリがインストールされ、EXEファイルが生成されます
3. `dist\KindleScreenshot.exe` が作成されます

## 方法2: 手動でビルド

### 1. 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

### 2. PyInstallerでビルド

```bash
pyinstaller --onefile --noconsole --name="KindleScreenshot" kindle_screenshot.py
```

### オプション説明

- `--onefile`: 単一のEXEファイルとして出力
- `--noconsole`: コンソールウィンドウを非表示（GUIモード）
- `--name="KindleScreenshot"`: EXEファイル名を指定
- `--icon=icon.ico`: アイコンを指定（オプション）

### 3. 生成されたEXEファイル

`dist\KindleScreenshot.exe` が作成されます。

## コンソール版をビルドする場合

デバッグや進行状況を確認したい場合は、`--noconsole` を削除してください:

```bash
pyinstaller --onefile --name="KindleScreenshot" kindle_screenshot.py
```

## ビルドオプションのカスタマイズ

### specファイルを使用

より詳細な設定が必要な場合は、specファイルを生成して編集します:

```bash
pyinstaller --onefile kindle_screenshot.py
# kindle_screenshot.spec が生成されます
```

specファイルを編集後、以下でビルド:

```bash
pyinstaller kindle_screenshot.spec
```

## トラブルシューティング

### エラー: ModuleNotFoundError

必要なライブラリがインストールされていません:
```bash
pip install pyautogui pillow opencv-python numpy
```

### EXEが大きすぎる

`--onefile` を削除して、複数ファイル構成でビルド:
```bash
pyinstaller --noconsole --name="KindleScreenshot" kindle_screenshot.py
```

### セキュリティソフトに検出される

- コード署名証明書で署名する
- または、`--debug=all` オプションでビルドして原因を調査

## 配布方法

配布する際は以下をまとめてください:

1. `dist\KindleScreenshot.exe`
2. `README_EXE.txt`

ユーザーは EXE ファイルをダブルクリックするだけで実行できます。
