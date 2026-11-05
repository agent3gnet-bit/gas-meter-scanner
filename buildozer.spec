[app]

# Имя приложения
title = Газовый Счётчик

# Имя пакета (package name)
package.name = gasmeterreader

# Домен пакета (обратный DNS)
package.domain = org.rusgas

# Версия приложения
version = 1.1.0

# Имя бинарного файла
source.dir = .

# Включаемые расширения файлов
source.include_exts = py,png,jpg,kv,spec,xlsx

# Исключаемые файлы
source.exclude_exts = spec

# Bootstrap (SDL2 - стандарт для Kivy)
p4a.bootstrap = sdl2

# Зависимости (Python 3 + все библиотеки)
# Важные: kivy, kivyMD, opencv-python, pytesseract, pyzxing, numpy, pandas, pillow, openpyxl, plyer
p4a.requirements = python3,kivy,kivymd,openssl,libav

# Опции для opencv-python (включаем cv2 и его зависимости)
p4a.hooks.cv2 = opencv-python

# Разрешения Android
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

# Целевая версия Android API
android.api = 33

# Минимальная версия Android
android.minapi = 21

# NDK версия (стабильная для Android 13)
android.ndk = 25b

# SDK версия
android.sdk = 20

# Python версии
p4a.python_version = 3.11

# Дополнительные флаги для plyer
p4a.extra_sources = plyer

# Локальные зависимости (если есть)
# p4a.site_packages = /path/to/your/libs

# Список системных пакетов (для исправления ошибок сборки)
[buildozer]

# Уровень логирования (2 = максимум)
log_level = 2

# Предупреждение при запуске от root
warn_on_root = 1

# Версия buildozer
buildozer_version = 1.5.0

# Исправление для ошибок с пакетами в Linux/WSL
system.package_list = libsdl2-ttf-dev, libsdl2-dev, libsdl2-image-dev, libsdl2-mixer-dev, libavformat-dev, libavcodec-dev, libavdevice-dev, libavutil-dev, libswscale-dev, libavfilter-dev, ffmpeg

# Кэш сборки
buildozer.cache_dir = .buildozer

# Папка для APK
bin = ./bin

# Режим сборки (release или debug)
# Для production раскомментируйте:
# buildozer.android.release = True
# buildozer.android.keystore = my.keystore
# buildozer.android.keystore_alias = myalias
# buildozer.android.keystore_alias_password = password
# buildozer.android.keystore_password = password

# Автогенерация иконки
# buildozer.android.new_bootstrap = true
