# Kindle to PDF Converter

Kindle Cloud Readerで開いている書籍を、自動的にスクリーンショットを取得しながらPDFファイルに変換するブラウザ拡張機能です。

## 特徴

- **自動ページめくり**: 指定したページ範囲を自動的にキャプチャ
- **高品質PDF生成**: スクリーンショットベースで高品質なPDFを作成
- **目次保持**: Kindle Cloud Readerから目次情報を取得してPDFに追加 ✨ NEW
- **画像品質調整**: ファイルサイズと画質のバランスを調整可能 ✨ NEW
- **Chrome/Firefox対応**: Manifest V3で両ブラウザに対応
- **完全ローカル処理**: すべての処理はブラウザ内で完結（外部サーバー不要）

## 注意事項

**重要**: この拡張機能は個人の私的使用のみを目的としています。著作権法を遵守し、変換したPDFの配布や共有は行わないでください。

## 対応サイト

- Kindle Cloud Reader (https://read.amazon.com/*)
- Kindle Cloud Reader JP (https://read.amazon.co.jp/*)

## インストール方法

### Chrome

1. このリポジトリをダウンロードまたはクローン
2. Chromeで `chrome://extensions/` を開く
3. 右上の「デベロッパーモード」を有効化
4. 「パッケージ化されていない拡張機能を読み込む」をクリック
5. このプロジェクトのルートフォルダを選択

### Firefox

1. このリポジトリをダウンロードまたはクローン
2. Firefoxで `about:debugging#/runtime/this-firefox` を開く
3. 「一時的なアドオンを読み込む」をクリック
4. このプロジェクトの `manifest.json` を選択

## 使用方法

1. Kindle Cloud Readerで書籍を開く
2. ブラウザのツールバーにある拡張機能アイコンをクリック
3. 変換設定を入力：
   - **開始ページ**: キャプチャを開始するページ番号（デフォルト: 現在のページ）
   - **終了ページ**: キャプチャを終了するページ番号
   - **キャプチャ間隔**: ページめくりの間隔（秒）（デフォルト: 2秒）
   - **画像品質**: 50%-100%の範囲で調整（デフォルト: 90%） ✨ NEW
   - **OCR機能**: テキスト抽出を有効化（実験的機能、準備中） 🚧
4. 「キャプチャ開始」ボタンをクリック
5. 進捗バーで状況を確認
6. 完了後、PDFファイルが自動的にダウンロードされます
   - **目次がある書籍**: PDFの最初のページに目次が追加されます ✨ NEW
   - **ファイル名**: 書籍タイトルが自動的に含まれます ✨ NEW

## プロジェクト構造

```
kindle-to-pdf-extension/
├── manifest.json                 # 拡張機能の設定ファイル
├── README.md                     # このファイル
├── icons/                        # アイコン画像
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── popup/                        # ポップアップUI
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
├── background/                   # バックグラウンドスクリプト
│   └── background.js
├── content/                      # コンテンツスクリプト
│   └── content.js
├── lib/                         # 外部ライブラリ
│   ├── browser-polyfill.min.js  # ブラウザ互換性
│   └── jspdf.umd.min.js         # PDF生成
└── utils/                       # ユーティリティ関数
    ├── capture.js               # キャプチャ処理
    └── pdf-generator.js         # PDF生成処理
```

## 技術スタック

- **Manifest Version**: 3
- **互換性ライブラリ**: webextension-polyfill
- **PDF生成**: jsPDF
- **画像処理**: Canvas API

## 制限事項

1. すべての書籍がKindle Cloud Readerで開けるわけではありません
2. スクリーンショットは表示画面サイズに依存します（フルスクリーン表示推奨）
3. 長時間の処理中はブラウザをアクティブに保つ必要があります
4. DRM保護されたコンテンツに対してDRM解除は行いません

## トラブルシューティング

### キャプチャが開始されない

- Kindle Cloud Readerのページで拡張機能を実行していることを確認
- ブラウザの開発者ツールでエラーメッセージを確認

### ページ番号が取得できない

- Kindle Cloud Readerの仕様が変更された可能性があります
- GitHubのIssuesで報告してください

### PDFが生成されない

- 大量のページをキャプチャする場合、メモリ不足の可能性があります
- ページ範囲を小さくして再試行してください

## 開発

### 必要な依存関係

このプロジェクトは以下の外部ライブラリを使用します：

- [webextension-polyfill](https://github.com/mozilla/webextension-polyfill) (v0.10.0以上)
- [jsPDF](https://github.com/parallax/jsPDF) (v2.5.0以上)

### セットアップ

```bash
# 外部ライブラリのダウンロード（開発時）
# browser-polyfill
curl -o lib/browser-polyfill.min.js https://unpkg.com/webextension-polyfill@latest/dist/browser-polyfill.min.js

# jsPDF
curl -o lib/jspdf.umd.min.js https://unpkg.com/jspdf@latest/dist/jspdf.umd.min.js
```

## ライセンス

このプロジェクトは個人の学習および私的使用を目的としています。

## 免責事項

- この拡張機能は教育目的で作成されています
- 著作権法を遵守し、個人の私的使用の範囲内でのみ使用してください
- 変換したコンテンツの配布や共有は違法です
- 開発者は本拡張機能の使用によって生じたいかなる損害についても責任を負いません

## Phase 1 (MVP) の実装状況

- [x] プロジェクト初期設定
- [ ] 基本UI実装
- [ ] browser-polyfill導入
- [ ] content.js基本実装
- [ ] background.js基本実装
- [ ] ページめくり自動化
- [ ] PDF生成機能
- [ ] 統合テスト
- [ ] 最適化
- [ ] ブラウザ別テスト

## 今後の予定（Phase 2以降）

- OCR機能（Tesseract.js使用）
- 画像圧縮オプション
- しおり・目次の保持
- 複数書籍の一括変換

## バージョン履歴

### v1.0.0 (開発中)
- 初期リリース
- 基本的なキャプチャ＆PDF生成機能
