#!/bin/bash
# 音量一括調整ツール起動スクリプト (Linux/macOS用)

cd "$(dirname "$0")"

# 依存関係チェック
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python3がインストールされていません"
    exit 1
fi

# 仮想環境がある場合はアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# アプリケーション起動
python3 volume_adjuster.py
