# 姿勢評価システム (Python Desktop Edition)

AIを活用したデスクトップ姿勢評価アプリケーションです。正面像と矢状面像の写真から姿勢を分析し、ケンダルの姿勢分類に基づいた詳細なレポートを生成します。

## 🌟 特徴

- **モダンなデスクトップGUI**: CustomTkinterによる美しいユーザーインターフェース
- **AIによる姿勢検出**: Google MediaPipe Poseを使用した高精度な姿勢ランドマーク検出
- **ケンダルの姿勢分類**: 矢状面像から4つの姿勢タイプを判定
  - 理想姿勢 (Ideal Posture)
  - カイホロードシス姿勢 (Kyphosis-Lordosis Posture)
  - フラットバック姿勢 (Flat-Back Posture)
  - スウェイバック姿勢 (Sway-Back Posture)
- **多面的な評価**: 正面像と矢状面像の両方から詳細な姿勢評価
- **視覚的フィードバック**: ランドマークを表示した画像で評価結果を確認
- **A4レポート生成**: 評価結果をPDFレポートとしてダウンロード可能
- **EXE化対応**: PyInstallerで実行可能ファイル(.exe)を作成可能

## 📋 評価項目

### 正面像評価
- 頭部の傾き
- 左右の肩の高さ
- 骨盤の傾き
- 身体の左右対称性
- 重心線の評価

### 矢状面像評価
- 頭部の前方位（ストレートネック）
- 肩の前後位置
- 骨盤の前後傾
- 膝の位置（過伸展など）
- ケンダルの姿勢分類

## 🔧 システム要件

- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 以上 3.11 以下 (推奨: 3.10)
- **RAM**: 最低 4GB (推奨: 8GB以上)
- **ディスク空き容量**: 2GB以上
- **GPU**: 不要（CPUのみで動作）

## 🚀 インストール方法

### 方法1: セットアップスクリプトを使用（推奨）

#### Windows
```cmd
setup.bat
```

#### Linux/macOS
```bash
chmod +x setup.sh
./setup.sh
```

### 方法2: 手動セットアップ

1. リポジトリをクローン
```bash
git clone [repository-url]
cd posture-evaluation-python
```

2. 仮想環境を作成（推奨）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

## 💻 使用方法

### アプリケーションの起動

```bash
# Windows
python src/main_gui.py

# Linux/macOS
python3 src/main_gui.py
```

### 基本的な使い方

1. **写真の準備**
   - 正面像: 正面から全身が写るように撮影
   - 矢状面像: 真横から全身が写るように撮影
   - 明るい場所で撮影
   - 体のラインがはっきり見える服装（タイトな服やスポーツウェアが最適）

2. **画像のアップロード**
   - 「正面像」エリアで「📁 画像を選択」ボタンをクリック
   - 正面から撮影した写真を選択
   - 「矢状面像」エリアで同様に横から撮影した写真を選択

3. **評価の実行**
   - 両方の画像をアップロードすると「🔍 姿勢を評価する」ボタンが有効になります
   - ボタンをクリックして評価を開始
   - プログレスバーで進捗を確認

4. **結果の確認**
   - ケンダルの姿勢分類結果を確認
   - 正面像・矢状面像の詳細評価を確認
   - 各評価項目の色で重要度を判別
     - 🟢 緑: 良好
     - 🟡 黄: 注意
     - 🔴 赤: 要改善

5. **レポートのダウンロード**
   - 「📄 A4レポートをダウンロード」ボタンをクリック
   - 保存先を選択してPDFを保存

## 📦 EXE化（実行可能ファイルの作成）

アプリケーションをEXEファイルにして、Pythonをインストールしていない環境でも実行できるようにします。

### 方法1: ビルドスクリプトを使用

```bash
python build_exe.py
```

### 方法2: PyInstallerを直接使用

```bash
# 基本的なビルド
pyinstaller PostureEvaluation.spec

# または、詳細オプションを指定
pyinstaller --onefile --windowed --name=PostureEvaluation src/main_gui.py
```

### ビルド後

- 生成されたEXEファイル: `dist/PostureEvaluation.exe`
- ファイルサイズ: 約500MB〜1GB（MediaPipeを含むため）
- このEXEファイルは単体で動作し、Pythonのインストールは不要です

### 注意事項

- 初回ビルドには数分かかります
- Windows Defenderがウイルススキャンを行う場合があります
- 生成されたEXEは配布可能ですが、ファイルサイズが大きいです

## 🗂️ プロジェクト構造

```
posture-evaluation-python/
├── src/                          # ソースコード
│   ├── main_gui.py              # メインGUIアプリケーション
│   ├── pose_detector.py         # 姿勢検出モジュール
│   ├── kendall_classifier.py    # ケンダル分類モジュール
│   ├── evaluator.py             # 評価ロジック
│   └── pdf_generator.py         # PDFレポート生成
├── assets/                      # アセット（アイコン等）
├── reports/                     # 生成されたレポートの保存先
├── docs/                        # ドキュメント
├── requirements.txt             # 依存パッケージリスト
├── build_exe.py                 # EXEビルドスクリプト
├── PostureEvaluation.spec       # PyInstallerの設定ファイル
├── setup.bat                    # Windowsセットアップスクリプト
├── setup.sh                     # Linux/macOSセットアップスクリプト
└── README.md                    # このファイル
```

## 🧪 技術スタック

### GUI Framework
- **CustomTkinter**: モダンなUIライブラリ
- **Pillow**: 画像処理

### Computer Vision & AI
- **MediaPipe Pose**: Googleの姿勢検出ライブラリ
- **OpenCV**: 画像処理
- **NumPy**: 数値計算

### PDF Generation
- **ReportLab**: PDFレポート生成

### Distribution
- **PyInstaller**: EXE化ツール

## 🔒 医療免責事項

- このアプリケーションは教育・参考目的で作成されています
- 医療診断の代替として使用しないでください
- 姿勢に関する問題や痛みがある場合は、必ず医療専門家（医師、理学療法士等）にご相談ください
- 評価結果は参考値であり、個人の状態によって異なる場合があります

## 🔐 プライバシー

- アップロードされた画像はローカルでのみ処理され、外部サーバーに送信されません
- すべての処理はデバイス内で完結します
- アプリケーションを閉じると一時ファイルは削除されます

## 🐛 トラブルシューティング

### 姿勢が検出されない場合

**原因と対処法:**
- 全身が写っているか確認
- 明るい場所で撮影された画像か確認
- 背景と人物のコントラストが十分か確認
- 画像サイズが大きすぎないか確認（推奨: 2000x3000px以下）

### GUIが起動しない場合

**Windows:**
```cmd
# 依存関係を再インストール
pip uninstall customtkinter
pip install customtkinter --upgrade
```

**Linux:**
```bash
# tkinterをインストール
sudo apt-get install python3-tk

# 依存関係を再インストール
pip3 install -r requirements.txt --force-reinstall
```

### MediaPipeエラー

```bash
# MediaPipeを再インストール
pip uninstall mediapipe
pip install mediapipe==0.10.9
```

### PDFが生成されない場合

```bash
# ReportLabを再インストール
pip uninstall reportlab
pip install reportlab
```

### EXEビルドエラー

```bash
# キャッシュをクリア
pyinstaller --clean PostureEvaluation.spec

# または build/ と dist/ を手動削除してから再ビルド
```

## 📚 ケンダルの姿勢分類について

ケンダルの姿勢分類は、理学療法の分野で広く使用されている姿勢評価法です。

### 1. 理想姿勢 (Ideal Posture)
- 頭部、肩、股関節、膝、足首が一直線上に配列
- 適切な脊椎の生理的弯曲
- 関節への負担が最小限

### 2. カイホロードシス姿勢 (Kyphosis-Lordosis)
- 頭部の前方突出
- 胸椎の後弯増強（猫背）
- 腰椎の前弯増強（反り腰）
- 骨盤の前傾

### 3. フラットバック姿勢 (Flat-Back)
- 腰椎の前弯減少または消失
- 胸椎の後弯も減少
- 骨盤の後傾
- 脊椎全体が平坦化

### 4. スウェイバック姿勢 (Sway-Back)
- 骨盤が前方に移動し後傾
- 胸椎が後方に傾斜
- 膝の過伸展
- 頭部の前方突出

## 🤝 コントリビューション

バグレポートや機能リクエストは、GitHubのIssuesでお知らせください。

## 📝 参考文献

- Kendall, F. P., McCreary, E. K., & Provance, P. G. (2005). Muscles: Testing and Function with Posture and Pain.
- MediaPipe Pose: https://google.github.io/mediapipe/solutions/pose.html
- CustomTkinter: https://github.com/TomSchimansky/CustomTkinter

## 📄 ライセンス

このプロジェクトは教育目的で作成されています。

## 🆕 更新履歴

### v1.0.0 (2025-01-XX)
- 初回リリース
- CustomTkinterによるモダンGUI実装
- MediaPipe Pose統合
- ケンダル姿勢分類実装
- PDFレポート生成機能
- EXE化対応

---

**開発者向け情報**

### 開発環境のセットアップ

```bash
# 開発用の追加パッケージをインストール
pip install -r requirements-dev.txt

# または
pip install pytest black flake8 mypy
```

### コードフォーマット

```bash
# Blackでフォーマット
black src/

# Flake8でリント
flake8 src/

# MyPyで型チェック
mypy src/
```

### テストの実行

```bash
# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=src
```

---

© 2025 Posture Evaluation System | 教育目的での使用に限ります
