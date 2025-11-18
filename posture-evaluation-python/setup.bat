@echo off
REM 姿勢評価システム - セットアップスクリプト (Windows)
REM 依存パッケージをインストール

echo =====================================
echo 姿勢評価システム - セットアップ
echo =====================================
echo.

REM Pythonがインストールされているか確認
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません
    echo Python 3.8以上をインストールしてください
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Pythonが見つかりました
python --version
echo.

REM 仮想環境の作成（推奨）
echo 仮想環境を作成しますか？ (推奨)
echo Y: 作成する  N: スキップ
choice /c YN /n /m "選択してください: "
if errorlevel 2 goto :install
if errorlevel 1 goto :venv

:venv
echo.
echo 仮想環境を作成中...
python -m venv venv
if errorlevel 1 (
    echo エラー: 仮想環境の作成に失敗しました
    pause
    exit /b 1
)

echo 仮想環境をアクティベート中...
call venv\Scripts\activate.bat
echo.

:install
echo 依存パッケージをインストール中...
echo.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo エラー: パッケージのインストールに失敗しました
    pause
    exit /b 1
)

echo.
echo =====================================
echo ✅ セットアップが完了しました！
echo =====================================
echo.
echo 次のステップ:
echo   1. アプリケーションを起動: python src/main_gui.py
echo   2. EXEファイルを作成: python build_exe.py
echo.
pause
