@echo off
REM Kindle Screenshot Tool - EXE ビルドスクリプト
echo Kindle Screenshot Tool をEXE形式にビルドします...
echo.

REM PyInstallerがインストールされているか確認
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstallerがインストールされていません。
    echo インストール中...
    pip install pyinstaller
    echo.
)

REM 必要なライブラリを確認
echo 必要なライブラリを確認中...
pip install pillow opencv-python numpy pyautogui

echo.
echo EXEファイルをビルド中...
pyinstaller --onefile ^
    --noconsole ^
    --icon=NONE ^
    --name="KindleScreenshot" ^
    --add-data "README_EXE.txt;." ^
    kindle_screenshot.py

echo.
if %errorlevel% equ 0 (
    echo ビルド成功！
    echo EXEファイルは dist\KindleScreenshot.exe にあります
    echo.
    pause
) else (
    echo ビルドに失敗しました
    pause
)
