# 音量一括調整ツール

複数の動画・音声ファイルの音量を一括で調整するPythonアプリケーションです。

## 特徴

- 🎵 **複数ファイル対応**: 動画・音声ファイルを一括で処理
- 🖱️ **ドラッグ&ドロップ**: 簡単にファイルを追加
- 🎚️ **音量調整**: -20dB ~ +20dBの範囲で調整可能
- 📁 **柔軟な出力**: 元の場所または指定したディレクトリに保存
- 🔄 **フォーマット変換**: MP3、WAV、または元のフォーマットで出力

## 対応フォーマット

### 音声ファイル
- MP3
- WAV
- M4A
- AAC
- OGG
- FLAC

### 動画ファイル
- MP4
- AVI
- MKV
- MOV

## 必要な環境

- Python 3.7以上
- FFmpeg

## インストール

### 1. FFmpegのインストール

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Windows
[FFmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロードしてインストールし、PATHに追加してください。

### 2. Pythonパッケージのインストール

```bash
cd batch-volume-adjuster
pip install -r requirements.txt
```

## 使い方

### 起動

```bash
python volume_adjuster.py
```

または、実行権限を付与して直接実行:

```bash
chmod +x volume_adjuster.py
./volume_adjuster.py
```

### 基本的な使い方

1. **ファイルの追加**
   - ドラッグ&ドロップでファイルを追加
   - または「ファイルを追加」ボタンから選択

2. **音量の調整**
   - スライダーで音量を調整（-20dB ~ +20dB）
   - プラス値で音量を上げ、マイナス値で音量を下げる

3. **出力設定**
   - 出力先: デフォルトは元のファイルと同じ場所
   - 出力形式: 元と同じ、MP3、WAVから選択

4. **実行**
   - 「音量調整を実行」ボタンをクリック
   - 処理完了まで待つ

### 出力ファイル

処理されたファイルは元のファイル名に `_adjusted` が付加されます。

例: `music.mp3` → `music_adjusted.mp3`

## トラブルシューティング

### "pydubがインストールされていません"というエラー

```bash
pip install pydub
```

### "ffmpegが見つかりません"というエラー

FFmpegがインストールされていないか、PATHに追加されていません。上記のインストール手順を参照してください。

### ドラッグ&ドロップが動作しない

tkinterdnd2がインストールされていない可能性があります:

```bash
pip install tkinterdnd2
```

### 音質が劣化する

- WAV形式で出力すると音質の劣化を最小限に抑えられます
- 元の形式で出力する場合、再エンコードによる若干の劣化が発生する可能性があります

## 技術仕様

- **GUI**: tkinter (Python標準ライブラリ)
- **ドラッグ&ドロップ**: tkinterdnd2
- **音声処理**: pydub + FFmpeg
- **マルチスレッド**: 処理中もGUIが応答性を保つ

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 作者

Created with Claude

## 貢献

バグ報告や機能要望は、GitHubのIssuesでお願いします。
