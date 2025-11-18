#!/bin/bash
# 姿勢評価システム - セットアップスクリプト (Linux/macOS)
# 依存パッケージをインストール

echo "====================================="
echo "姿勢評価システム - セットアップ"
echo "====================================="
echo ""

# Pythonがインストールされているか確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python 3がインストールされていません"
    echo "Python 3.8以上をインストールしてください"
    exit 1
fi

echo "Pythonが見つかりました"
python3 --version
echo ""

# 仮想環境の作成（推奨）
read -p "仮想環境を作成しますか？ (推奨) [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv

    if [ $? -ne 0 ]; then
        echo "エラー: 仮想環境の作成に失敗しました"
        exit 1
    fi

    echo "仮想環境をアクティベート中..."
    source venv/bin/activate
    echo ""
fi

# 依存パッケージのインストール
echo "依存パッケージをインストール中..."
echo ""
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "エラー: パッケージのインストールに失敗しました"
    exit 1
fi

echo ""
echo "====================================="
echo "✅ セットアップが完了しました！"
echo "====================================="
echo ""
echo "次のステップ:"
echo "  1. アプリケーションを起動: python3 src/main_gui.py"
echo "  2. EXEファイルを作成 (Linux/macOS): python3 build_exe.py"
echo ""
