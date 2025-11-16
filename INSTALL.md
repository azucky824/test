# インストール手順

Kindle to PDF Converterブラウザ拡張機能の詳細なインストール手順です。

## 事前準備

### 1. jsPDFライブラリのダウンロード

この拡張機能はjsPDFライブラリを使用してPDFを生成します。以下の手順でダウンロードしてください。

**オプションA: 手動ダウンロード（推奨）**

1. ブラウザで以下のURLを開く:
   ```
   https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js
   ```

2. ページ全体を選択（Ctrl+A / Cmd+A）してコピー

3. テキストエディタで`lib/jspdf.umd.min.js`を開く

4. 内容を貼り付けて保存

**オプションB: curlコマンド（Mac/Linux）**

```bash
curl -o lib/jspdf.umd.min.js https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js
```

**オプションC: wgetコマンド（Linux）**

```bash
wget -O lib/jspdf.umd.min.js https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js
```

**注意**: lib/jspdf.umd.min.jsが正しくダウンロードされていない場合、拡張機能はCDNから自動的に読み込みを試みます（インターネット接続が必要）。

### 2. ファイル構造の確認

以下のようなディレクトリ構造になっていることを確認してください:

```
kindle-to-pdf-extension/
├── manifest.json
├── README.md
├── INSTALL.md
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── popup/
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
├── background/
│   └── background.js
├── content/
│   └── content.js
├── lib/
│   ├── browser-polyfill.min.js
│   └── jspdf.umd.min.js  ← この��ァイルが重要
└── utils/
    ├── capture.js
    └── pdf-generator.js
```

## Google Chromeへのインストール

### ステップ 1: 拡張機能ページを開く

1. Chromeブラウザを開く
2. アドレスバーに `chrome://extensions/` と入力してEnter
3. または、メニュー（⋮）→「拡張機能」→「拡張機能を管理」

### ステップ 2: デベロッパーモードを有効化

1. ページ右上の「デベロッパーモード」トグルをONにする

### ステップ 3: 拡張機能を読み込む

1. 「パッケージ化されていない拡張機能を読み込む」ボタンをクリック
2. ダウンロードしたプロジェクトの**ルートフォルダ**（manifest.jsonがあるフォルダ）を選択
3. 「フォルダの選択」をクリック

### ステップ 4: インストール確認

1. 拡張機能一覧に「Kindle to PDF Converter」が表示されることを確認
2. エラーがないことを確認
3. ブラウザのツールバーに拡張機能アイコンが表示される

### トラブルシューティング（Chrome）

**エラー: "Manifest version 3 is required"**
- Chromeのバージョンが古い可能性があります
- Chrome 88以降にアップデートしてください

**エラー: "Could not load icon"**
- iconsフォルダ内の画像ファイルが存在するか確認
- ファイル名が正しいか確認（icon16.png, icon48.png, icon128.png）

**エラー: "background.service_worker"関連**
- background/background.jsファイルが存在するか確認
- ファイルに構文エラーがないか確認

## Mozilla Firefoxへのインストール

### ステップ 1: デバッグページを開く

1. Firefoxブラウザを開く
2. アドレスバーに `about:debugging#/runtime/this-firefox` と入力してEnter

### ステップ 2: 一時的なアドオンを読み込む

1. 「一時的なアドオンを読み込む...」ボタンをクリック
2. プロジェクトフォルダ内の **manifest.json** ファイルを選択
3. 「開く」をクリック

### ステップ 3: インストール確認

1. アドオン一覧に「Kindle to PDF Converter」が表示されることを確認
2. ブラウザのツールバーに拡張機能アイコンが表示される

### 注意事項（Firefox）

- 「一時的なアドオン」として読み込んだ場合、Firefoxを再起動すると削除されます
- 恒久的にインストールするには、アドオンに署名が必要です
- 開発中は毎回読み込み直す必要があります

### トラブルシューティング（Firefox）

**エラー: "This add-on is not compatible"**
- manifest.jsonの`browser_specific_settings`セクションを確認
- Firefoxのバージョンが109.0以降であることを確認

**警告が表示される**
- 一部の警告は開発中のアドオンでは正常です
- エラーでなければ動作に問題ありません

## インストール後の設定

### 1. 拡張機能のピン留め（推奨）

**Chrome:**
1. ツールバーの拡張機能アイコン（パズルピース）をクリック
2. 「Kindle to PDF Converter」の横のピンアイコンをクリック

**Firefox:**
1. ツールバーを右クリック
2. 「ツールバーをカスタマイズ」を選択
3. 拡張機能アイコンをツールバーにドラッグ

### 2. 権限の確認

初回使用時に以下の権限を求められる場合があります:
- ✅ アクティブなタブのスクリーンショット取得
- ✅ read.amazon.comおよびread.amazon.co.jpへのアクセス
- ✅ ダウンロード機能の使用
- ✅ ストレージへのアクセス

これらはすべて拡張機能の動作に必要な権限です。

## 動作確認

### 1. Kindle Cloud Readerを開く

1. ブラウザで[Kindle Cloud Reader](https://read.amazon.com/)にアクセス
2. Amazonアカウントでログイン
3. 任意の書籍を開く

### 2. 拡張機能のテスト

1. ツールバーの「Kindle to PDF Converter」アイコンをクリック
2. ポップアップが表示されることを確認
3. 「開始ページ」に現在のページ番号が自動入力されることを確認
4. 「終了ページ」に小さな数値（例: 開始+2）を入力
5. 「キャプチャ開始」ボタンをクリック
6. 自動的にページがめくられることを確認
7. 完了後、PDFがダウンロードされることを確認

### トラブルシューティング

**ポップアップが表示されない**
- 拡張機能が正しくインストールされているか確認
- ブラウザのコンソールでエラーを確認（F12キー）

**「このページはKindle Cloud Readerではありません」と表示される**
- read.amazon.comまたはread.amazon.co.jpで書籍を開いているか確認
- URLを確認

**キャプチャが開始されない**
- ブラウザの開発者ツール（F12）でエラーメッセージを確認
- content scriptが正しく読み込まれているか確認

**PDFが生成されない**
- jsPDFライブラリが正しくダウンロードされているか確認
- ブラウザのコンソールで"jsPDF library not loaded"警告が出ていないか確認
- インターネット接続を確認（CDNからの自動読み込み用）

## アンインストール

### Chrome
1. `chrome://extensions/` を開く
2. 「Kindle to PDF Converter」の「削除」ボタンをクリック

### Firefox
1. `about:addons` を開く
2. 「Kindle to PDF Converter」の「削除」をクリック
3. または、Firefoxを再起動（一時的なアドオンの場合）

## アップデート

1. プロジェクトフォルダ内のファイルを更新
2. Chrome: 拡張機能ページで「更新」ボタンをクリック
3. Firefox: アドオンを再読み込み

## サポート

問題が発生した場合:
1. README.mdの「トラブルシューティング」セクションを確認
2. ブラウザの開発者コンソール（F12）でエラーメッセージを確認
3. GitHubリポジトリでIssueを作成

---

**重要**: この拡張機能は個人の私的使用のみを目的としています。著作権法を遵守し、変換したPDFの配布や共有は行わないでください。
