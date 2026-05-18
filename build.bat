@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building ClipboardManager.exe...
pyinstaller --noconfirm ^
            --onefile ^
            --windowed ^
            --name "ClipboardManager" ^
            --add-data "cm_constants.py;." ^
            --add-data "cm_widgets.py;." ^
            --add-data "cm_window.py;." ^
            clipboard_manager.py

echo.
if exist dist\ClipboardManager.exe (
    echo SUCCESS! File is at: dist\ClipboardManager.exe
) else (
    echo FAILED. See the output above for errors.
)
pause
