@echo off
chcp 866 >nul
setlocal

echo ========================================
echo  Sbornka GasMeterReader Setup
echo ========================================
echo.

set APP_DIR=C:\Users\Igor\GasMeterReader
set DIST_DIR=%APP_DIR%\dist
set PYTHON=C:\Users\Igor\Python\pythoncore-3.15-64\python.exe
set NSIS_PATH="C:\Program Files (x86)\NSIS\makensis.exe"
set NSIS_ALT="C:\Program Files\NSIS\makensis.exe"

echo [1/3] Sbornka GasMeterReader.exe...
if not exist "%DIST_DIR%\GasMeterReader.exe" (
    cd /d "%APP_DIR%"
    %PYTHON% -m PyInstaller --clean --noconfirm --onefile --windowed ^
        --name GasMeterReader ^
        --add-data "reference_db.xlsx;." ^
        --add-data "history.xlsx;." ^
        --hidden-import pyzxing ^
        --hidden-import cv2 ^
        --hidden-import pandas ^
        --hidden-import openpyxl ^
        --hidden-import numpy ^
        --hidden-import PIL ^
        --hidden-import pytesseract ^
        "main.py"
    cd /d "C:\Users\Igor"
    if errorlevel 1 (
        echo Oshibka sborki!
        pause
        exit /b 1
    )
) else (
    echo GasMeterReader.exe uze sushchestvuet.
)

echo.
echo [2/3] Proverka NSIS...

set NSIS_FOUND=0
if exist %NSIS_PATH% (
    set NSIS_PATH=%NSIS_PATH:"=%
    set NSIS_FOUND=1
) else if exist %NSIS_ALT% (
    set NSIS_PATH=%NSIS_ALT:"=%
    set NSIS_FOUND=1
)

if not "%NSIS_FOUND%"=="1" (
    echo.
    echo !!! NSIS ne ustanovlen !!!
    echo.
    echo Ustanovite NSIS:
    echo https://sourceforge.net/projects/nsis/files/NSIS%203/
    echo.
    echo Lибо skajajte gotovyy exe:
    echo %DIST_DIR%\GasMeterReader.exe
    echo.
    pause
    exit /b 0
)

echo NSIS nayden: %NSIS_PATH%

echo.
echo [3/3] Sozdanie GasMeterReader_Setup.exe...

cd /d "%APP_DIR%"
%NSIS_PATH% -DAPP_DIR="%DIST_DIR%" GasMeterReader.nsi

if errorlevel 1 (
    echo Oshibka sozdaniya ustano4schika!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  GOTOVO!
echo ========================================
echo.
echo Ustano4schik: %APP_DIR%\GasMeterReader_Setup.exe
echo.
echo Gotovyy exe: %DIST_DIR%\GasMeterReader.exe
echo.
pause
