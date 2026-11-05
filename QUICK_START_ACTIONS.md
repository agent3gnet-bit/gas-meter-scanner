# 🚀 Быстрый старт: Сборка APK через GitHub Actions

## 📋 Что нужно

1. **Аккаунт GitHub** (бесплатный)
2. **Репо с проектом** (можно публичный)
3. **Ничего не нужно устанавливать!**

---

## 📝 Шаг 1: Создайте репозиторий

1. Зайдите на https://github.com/new
2. Создайте новый репозиторий (назовите, например, `GasMeterReader`)
3. Скопируйте URL репозитория

---

## 📝 Шаг 2: Загрузите код

```bash
cd C:\Users\Igor\GasMeterReader

# Инициализируйте Git
git init
git add .
git commit -m "Initial commit: GasMeterReader Android"

# Добавьте репозиторий
git branch -M main
git remote add origin https://github.com/ВАШ_НИК/GasMeterReader.git
git push -u origin main
```

---

## 📝 Шаг 3: Запустите сборку

1. Зайдите в свой репозиторий на GitHub
2. Перейдите на вкладку **Actions**
3. Нажмите **"I understand my workflows, go ahead and enable them"**
4. Нажмите **"Run workflow"** → **"Build Android APK"**
5. Подождите **15-30 минут**

---

## 📝 Шаг 4: Скачайте APK

После завершения:
1. Откройте последний Run в Actions
2. Прокрутите вниз до **"Artifacts"**
3. Скачайте `GasMeterReader-APK.zip`
4. Извлеките APK и скопируйте на телефон

---

## 🔄 Автоматическая сборка

Теперь при каждом push в main/master будет автоматически собираться APK.

Также можно запустить вручную:
- Actions → GasMeterReader APK → **"Run workflow"**

---

## ⚙️ Настройка

### Изменить версию:
В `buildozer.spec`:
```ini
version = 1.1.0
```

### Включить release-подпись:
```bash
# Создайте keystore
keytool -genkey -v -keystore release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias gasmeter

# В buildozer.spec раскомментируйте:
buildozer.android.release = True
buildozer.android.keystore = release-key.jks
buildozer.android.keystore_alias = gasmeter
```

---

## 🐛 Устранение проблем

### Ошибка: "buildozer not found"
```bash
# Обновите workflow
pip install buildozer==1.5.0
```

### Ошибка: "tesseract not found"
```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus
```

### Ссылка на репозиторий не работает:
```bash
git remote set-url origin https://github.com/ВАШ_НИК/GasMeterReader.git
git push -u origin main
```

---

## 📊 Что будет в APK

- ✅ Tesseract OCR (ENG + RUS)
- ✅ OpenCV (computer vision)
- ✅ KivyMD (UI)
- ✅ Pandas + Openpyxl (Excel)
- ✅ Plyer (камера, файлы)
- ✅ Размер: ~110 МБ

---

## 📱 Установка на телефон

1. Скачайте APK
2. Скопируйте на телефон (USB, Telegram, облако)
3. Разрешите установку из неизвестных источников:
   - Настройки → Безопасность → Неизвестные источники
4. Установите APK
5. Готово!
