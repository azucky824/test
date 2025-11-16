# Changelog

All notable changes to the Kindle to PDF Converter extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 計画中の機能 (Future Phases)
- OCR機能（Tesseract.js使用）- テキスト抽出とPDFへの埋め込み
- 複数書籍の一括変換
- カスタムページ範囲指定の改善
- プリセット設定の保存機能

## [1.1.0] - 2025-01-16

### Added - Phase 2

#### Table of Contents Support
- ✅ Kindle Cloud Readerから目次情報を自動取得
  - 目次ボタンの自動検出
  - 目次項目とページ番号の抽出
  - 階層構造の認識
- ✅ PDFに目次ページを自動追加
  - 書籍タイトル表示
  - 目次項目のリスト表示（ページ番号付き）
  - 長い目次の複数ページ対応
  - 日英バイリンガル表示

#### Image Quality Options
- ✅ 画像品質設定（50%-100%）
  - スライダーUIで直感的に設定
  - ファイルサイズと画質のトレードオフ調整
  - リアルタイムプレビュー表示

#### Enhanced Metadata
- ✅ 書籍タイトルの自動取得と PDF メタデータへの設定
- ✅ ファイル名に書籍タイトルを含める機能
- ✅ PDFプロパティ（作成者、キーワード）の設定

#### UI Improvements
- ✅ 設定画面の拡張
  - 画像品質スライダー
  - OCR有効化チェックボックス（UI準備完了）
  - ヒントテキストの追加

### Technical Improvements
- ✅ content.jsに目次取得機能を追加
- ✅ background.jsに目次ページ生成機能を追加
- ✅ PDFメタデータの充実
- ✅ 日本語対応の改善

### Notes
- OCR機能のUIは準備済みだが、実装は次フェーズ
- 目次が取得できない書籍でも正常に動作

## [1.0.0] - 2025-01-16

### Added - Phase 1 (MVP)

#### Core Features
- ✅ Kindle Cloud Readerからの自動スクリーンショット取得
- ✅ 自動ページめくり機能
- ✅ PDF生成とダウンロード
- ✅ Chrome/Firefox両対応（Manifest V3）

#### User Interface
- ✅ ポップアップUI実装
  - 開始/終了ページ指定
  - キャプチャ間隔設定
  - 進捗バー表示
  - ステータスメッセージ
  - キャンセル機能

#### Content Script
- ✅ Kindle Cloud Readerのページ番号取得
  - 複数のセレクタパターンに対応
  - フォールバック機能
- ✅ 次ページボタンの自動検出
- ✅ キーボードイベントによるページめくり
- ✅ コンテンツエリアの座標取得
- ✅ ページ遷移の検出と待機

#### Background Script
- ✅ スクリーンショットキャプチャ
- ✅ 画像のトリミング処理
- ✅ 画像データの一時保存
- ✅ PDF生成機能
- ✅ メモリ使用量の監視

#### Utilities
- ✅ browser-polyfill（Chrome/Firefox互換性）
- ✅ jsPDF統合
- ✅ キャプチャユーティリティ
- ✅ PDF生成ユーティリティ

#### Documentation
- ✅ README.md
- ✅ INSTALL.md（詳細なインストール手順）
- ✅ CHANGELOG.md

#### Assets
- ✅ 拡張機能アイコン（16x16, 48x48, 128x128）
- ✅ manifest.json（Manifest V3）

### Technical Details

#### Browser Support
- Chrome 88+
- Firefox 109+

#### Permissions
- `activeTab` - アクティブなタブのキャプチャ
- `tabs` - タブ情報の取得
- `downloads` - PDFダウンロード
- `storage` - 設定の保存
- `scripting` - コンテンツスクリプトの実行

#### Host Permissions
- `https://read.amazon.com/*`
- `https://read.amazon.co.jp/*`

#### Dependencies
- webextension-polyfill v0.12.0（簡易実装含む）
- jsPDF v2.5.2（CDNまたはローカル）

### Known Issues

#### Limitations
- すべてのKindle書籍がCloud Readerで開けるわけではない
- スクリーンショットは表示画面サイズに依存
- レイアウトが特殊な書籍は完璧に変換できない可能性
- 長時間の処理中はブラウザをアクティブに保つ必要がある

#### Browser-Specific
- **Firefox**: 一時的なアドオンとして読み込んだ場合、再起動時に削除される
- **Chrome**: Service Worker のタイムアウトに注意（長時間処理の場合）

### Security

#### Privacy
- ✅ すべての処理はブラウザ内で完結
- ✅ 外部サーバーへの通信なし
- ✅ ユーザーデータの収集なし
- ✅ Kindleアカウント情報を扱わない

#### Data Handling
- スクリーンショットデータは一時的にメモリに保存
- PDF生成後は自動的に削除
- ユーザー設定のみstorageに保存

### Legal

⚠️ **重要な注意事項**
- この拡張機能は個人の私的使用のみを目的としています
- 著作権法を遵守してください
- 変換したPDFの配布や共有は違法です
- DRM保護されたコンテンツに対してDRM解除は行いません

### Development

#### Project Structure
```
kindle-to-pdf-extension/
├── manifest.json
├── README.md
├── INSTALL.md
├── CHANGELOG.md
├── icons/
├── popup/
├── background/
├── content/
├── lib/
└── utils/
```

#### Code Quality
- ES6+ 構文使用
- async/await パターン
- 詳細なエラーハンドリング
- 日本語コメント
- コンソールログ出力

### Testing

#### Manual Testing Checklist
- [ ] Kindle Cloud Readerで書籍を開いてキャプチャ開始
- [ ] 1ページのみのキャプチャ
- [ ] 10ページのキャプチャ
- [ ] 100ページ以上のキャプチャ
- [ ] キャンセル機能
- [ ] ブラウザの再起動後も動作
- [ ] Chrome での動作確認
- [ ] Firefox での動作確認

## [0.1.0] - 2025-01-15

### Added
- 初期プロジェクトセットアップ
- 基本的なディレクトリ構造
- manifest.json 作成
- プロジェクト要件定義

---

## Version History Summary

| Version | Date       | Description                           |
|---------|------------|---------------------------------------|
| 1.0.0   | 2025-01-16 | Phase 1 (MVP) リリース               |
| 0.1.0   | 2025-01-15 | プロジェクト初期設定                 |

## Contributing

このプロジェクトへの貢献方法:
1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## License

このプロジェクトは教育目的で作成されています。個人の私的使用の範囲内でのみ使用してください。

---

**Note**: このCHANGELOGは開発の進行に伴って更新されます。
