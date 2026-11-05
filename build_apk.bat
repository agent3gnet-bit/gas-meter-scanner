@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   GAS METER READER - APK Сборка
echo   Android версия 1.1.0
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.11+ из https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Проверка Python... OK
echo.

REM Установка buildozer
echo [2/5] Установка buildozer...
pip install buildozer Cython == 3.0.11
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить buildozer
    pause
    exit /b 1
)
echo OK
echo.

REM Установка зависимостей
echo [3/5] Установка Android зависимостей...
pip install -r requirements_android.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)
echo OK
echo.

REM Проверка файлов
echo [4/5] Проверка файлов...
if not exist "main_android.py" (
    echo [ОШИБКА] main_android.py не найден!
    pause
    exit /b 1
)
if not exist "ocr_processor.py" (
    echo [ОШИБКА] ocr_processor.py не найден!
    pause
    exit /b 1
)
if not exist "excel_manager.py" (
    echo [ОШИБКА] excel_manager.py не найден!
    pause
    exit /b 1
)
if not exist "reference_db.xlsx" (
    echo [ПРЕДУПРЕЖДЕНИЕ] reference_db.xlsx не найден (будет создан пустой)
)
echo OK
echo.

echo ========================================
echo   ГОТОВО К СБОРКЕ!
echo ========================================
echo.
echo Следующий шаг:
echo   buildozer android debug
echo или для production:
echo   buildozer android release
echo.
echo Сборка займёт 15-30 минут (первый раз).
echo APK будет в папке: bin/GasMeterReader-*.apk
echo.
pause
