# 遅延ビデオ再生アプリケーション

カメラからの映像をリアルタイムで取得し、指定した秒数遅れて再生するPythonアプリケーションです。

## 機能

- リアルタイムカメラキャプチャ
- 1〜10秒の遅延再生（スライダーで調整可能）
- 直感的なGUIインターフェース
- FPS表示
- バッファ充填率表示

## 必要な環境

- Python 3.8以上
- Webカメラ

## インストール

1. リポジトリをクローンまたはダウンロード

```bash
git clone <repository-url>
cd test
```

2. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

## 使い方

### アプリケーションの起動

```bash
python main.py
```

または

```bash
python gui_app.py
```

### 操作方法

1. **開始ボタン**: カメラを起動し、遅延再生を開始します
2. **停止ボタン**: カメラを停止し、再生を終了します
3. **遅延秒数スライダー**: 1〜10秒の範囲で遅延時間を調整できます
   - リアルタイムで変更可能
   - 実行中でも調整できます

### 画面の見方

- **映像表示エリア**: 遅延された映像が表示されます（640x480px）
- **ステータス**: 「実行中」または「停止中」を表示
- **FPS**: 現在のフレームレートを表示
- **バッファ**: フレームバッファの充填率を表示（100%で完全に遅延した映像が表示されます）

## プロジェクト構造

```
.
├── main.py              # アプリケーションのエントリーポイント
├── gui_app.py          # GUIアプリケーションのメインロジック
├── camera_capture.py    # カメラキャプチャクラス
├── frame_buffer.py      # フレームバッファ管理クラス
├── requirements.txt     # 依存パッケージリスト
└── README_delayed_video.md  # このファイル
```

## 技術仕様

### アーキテクチャ

- **マルチスレッド設計**: カメラキャプチャは別スレッドで実行され、GUIの応答性を維持
- **循環バッファ**: `collections.deque`を使用した効率的なフレーム管理
- **スレッドセーフ**: ロック機構により安全な並行処理を実現

### 主要コンポーネント

#### FrameBuffer (`frame_buffer.py`)
- 遅延秒数×FPS分のフレームを保持
- スレッドセーフな実装
- 動的なバッファサイズ変更に対応

#### CameraCapture (`camera_capture.py`)
- OpenCVを使用したカメラキャプチャ
- 30FPSでの連続撮影
- FPS計測機能

#### DelayedVideoApp (`gui_app.py`)
- tkinterベースのGUI
- リアルタイムフレーム更新（約30fps）
- PIL/Pillowによる画像表示

## トラブルシューティング

### カメラが開けない場合

- カメラが他のアプリケーションで使用されていないか確認してください
- カメラのアクセス許可を確認してください
- `camera_capture.py`の`camera_index`を変更してみてください（0, 1, 2など）

### 映像が遅い・カクつく場合

- 他のアプリケーションを閉じてCPU使用率を下げてください
- 遅延秒数を短くしてみてください

## 依存パッケージ

- `opencv-python>=4.8.0`: カメラキャプチャと画像処理
- `Pillow>=10.0.0`: tkinterでの画像表示
- `numpy>=1.24.0`: 画像データ処理

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 開発者向け情報

### カスタマイズ

#### 解像度の変更

`camera_capture.py`の以下の部分を編集:

```python
self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

#### FPSの変更

各クラスの初期化時に`fps`パラメータを変更:

```python
self.camera = CameraCapture(camera_index=0, fps=60)  # 60fpsに変更
self.buffer = FrameBuffer(delay_seconds=3, fps=60)
```

#### 最大遅延秒数の変更

`gui_app.py`のスライダー設定を編集:

```python
self.delay_slider = ttk.Scale(
    delay_frame,
    from_=1,
    to=20,  # 20秒に変更
    ...
)
```
