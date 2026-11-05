@echo off
chcp 65001 >nul
cd /d "C:\Users\Igor\GasMeterReader"

echo [1/3] Copying cv2 DLLs to temp...
if not exist cv2_dll mkdir cv2_dll
copy /Y "C:\Users\Igor\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages\cv2\cv2.pyd" cv2_dll\
copy /Y "C:\Users\Igor\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages\cv2\opencv_videoio_ffmpeg500_64.dll" cv2_dll\
echo Done.

echo [2/3] Build EXE...
C:\Users\Igor\AppData\Local\Python\bin\python.exe -m PyInstaller --clean --noconfirm ^
    --onefile --windowed ^
    --name GasMeterReader ^
    --add-data "cv2_dll;cv2_dll" ^
    --add-data "reference_db.xlsx;." ^
    --add-data "history.xlsx;." ^
    --hidden-import cv2 ^
    --hidden-import cv2.cv2 ^
    --hidden-import pytesseract ^
    --hidden-import pyzxing ^
    --hidden-import numpy ^
    --hidden-import pandas ^
    --hidden-import PIL ^
    --hidden-import openpyxl ^
    "main.py"

if errorlevel 1 (
    echo Oshibka sborki!
    pause
    exit /b 1
)

echo [3/3] Done!
dir dist\GasMeterReader.exe
echo.
pause
