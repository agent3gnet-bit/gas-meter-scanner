# 📱 GasMeterReader - Android APK

## 📋 Содержание
- [Быстрый старт](#быстрый-старт)
- [Сборка APK](#сборка-apk)
- [Установка](#установка)
- [Требования](#требования)
- [Структура файлов](#структура-файлов)

---

## 🚀 Быстрый старт

### Для Windows (через WSL2 - Linux внутри Windows):

```bash
# 1. Установите WSL2 (если нет)
wsl --install

# 2. Перейдите в папку проекта
cd /mnt/c/Users/Igor/GasMeterReader

# 3. Запустите сборку
sudo apt update && sudo apt install -y python3 python3-pip build-essential \
    libsqlite3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev \
    libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev \
    libavcodec-dev zlib1g-dev libgstreamer1.0 gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good openjdk-17-jdk-headless git zip unzip \
    autoconf automake libtool libltdl-dev python3-dev

pip3 install buildozer Cython==3.0.11
buildozer android debug
```

### Для Linux (Ubuntu/Debian):

```bash
# 1. Установите зависимости
sudo apt update && sudo apt install -y python3 python3-pip build-essential \
    libsqlite3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev \
    libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev \
    libavcodec-dev zlib1g-dev libgstreamer1.0 gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good openjdk-17-jdk-headless git zip unzip \
    autoconf automake libtool libltdl-dev python3-dev

# 2. Перейдите в папку проекта
cd /path/to/GasMeterReader

# 3. Запустите сборку
pip3 install buildozer Cython==3.0.11
buildozer android debug
```

---

## 📦 Сборка APK

### Debug (для тестирования)
```bash
buildozer android debug
```
- Быстрее (нет оптимизации)
- APK будет в: `bin/GasMeterReader-1.1.0-debug.apk`

### Release (для публикации)
```bash
# 1. Создайте keystore (если нет)
keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-alias

# 2. Отредактируйте buildozer.spec:
# buildozer.android.release = True
# buildozer.android.keystore = my-release-key.jks
# buildozer.android.keystore_alias = my-alias

# 3. Соберите
buildozer android release
```
- APK будет в: `bin/GasMeterReader-1.1.0-release.apk`
- Signed для публикации в Google Play

---

## 📲 Установка

### Через USB:
```bash
# Подключите телефон, включите USB-отладку
adb install bin/GasMeterReader-1.1.0-debug.apk
```

### Через Wi-Fi:
1. Запустите HTTP сервер на ПК:
   ```bash
   python -m http.server 8000
   ```
2. Откройте в браузере телефона: `http://192.168.1.X:8000/bin/`
3. Скачайте APK, установите

---

## ✅ Требования

### Минимальные:
- **Android**: 7.0+ (API 21+)
- **RAM**: 2GB+
- **Хранилище**: 150MB для APK + данные

### ПК для сборки:
- **ОС**: Ubuntu 20.04+ (или WSL2 на Windows 10/11)
- **RAM**: 4GB+ (8GB рекомендуется)
- **Диск**: 5GB свободное место
- **Python**: 3.11+

---

## 📁 Структура файлов

```
GasMeterReader/
├── main_android.py          # Android UI (KivyMD)
├── main.py                  # Desktop UI (Tkinter) - не меняйте!
├── ocr_processor.py         # OCR движок (общий)
├── excel_manager.py         # Excel (общий)
├── config.py                # Конфиг (общий)
├── buildozer.spec           # Конфигурация сборки
├── requirements_android.txt # Python зависимости
├── build_apk.bat            # Скрипт быстрой сборки (Windows)
├── README_ANDROID.md        # Этот файл
├── reference_db.xlsx        # Справочник абонентов
└── history.xlsx             # История показаний
```

---

## ⚙️ Настройка

### Изменение версии:
```ini
# buildozer.spec
version = 1.1.0
```

### Иконка приложения:
```bash
# Создайте icon.png (512x512, RGBA)
# Buildozer автоматически сгенерирует иконки для Android
```

### Разрешения:
```ini
# buildozer.spec - уже настроены:
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
```

### Поддержка других языков:
```python
# ocr_processor.py: configs для Tesseract
langs = ['eng', 'rus']  # Английский + Русский
```

---

## 🐛 Устранение проблем

### Ошибка: `libsdl2 not found`
```bash
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

### Ошибка: `openjdk not found`
```bash
sudo apt install openjdk-17-jdk-headless
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

### Ошибка: `Python 3.11 not available`
```bash
# Buildozer требует Python 3.8-3.11
python --version
# Если 3.12+, установите 3.11:
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 python3.11-dev
```

### Сборка занимает слишком долго
- Первый раз: ~30 минут (скачивание зависимостей)
- Повторно: ~5 минут (используется кэш)

---

## 📊 Размер APK

| Компонент | Размер |
|-----------|--------|
| Python runtime | ~25 MB |
| Kivy + KivyMD | ~8 MB |
| OpenCV + NumPy | ~45 MB |
| Pandas + Openpyxl | ~15 MB |
| Tesseract OCR | ~12 MB |
| Приложение + данные | ~2 MB |
| **Итого** | **~107 MB** |

---

## 📝 Чangelog

### v1.1.0 (2024-11-05)
- ✅ Поддержка 5-значных показаний
- ✅ OCR с LSTM Tesseract (OEM 1)
- ✅ Русские модели Tesseract
- ✅ Контекстная коррекция (7→1)
- ✅ Excel: справочник + история
- ✅ Камера Android
- ✅ Выбор фото из галереи
- ✅ Экспорт в Excel на Android

### v1.0.0
- Первая версия Android приложения

---

## 📞 Поддержка

При проблемах с сборкой:
1. Проверьте: `python --version` (должен быть 3.11)
2. Проверьте: `java -version` (должен быть OpenJDK 17)
3. Очистите кэш: `buildozer clean`
4. Посмотрите логи: `cat .buildozer/android/platform/build-*/dists/GasMeterReader/build/logs/`
