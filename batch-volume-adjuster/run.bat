@echo off
REM 音量一括調整ツール起動スクリプト (Windows用)

cd /d "%~dp0"

REM 依存関係チェック
python --version >nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)

REM 仮想環境がある場合はアクティベート
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM アプリケーション起動
python volume_adjuster.py

pause
