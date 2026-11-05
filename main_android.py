"""
GasMeterReader - Android версия
Распознавание показаний газовых счётчиков СГД-Г4
Kivy + KivyMD интерфейс
"""
import os
import sys
import threading
import datetime
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.utils import platform
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from jnius import autoclass
from android.permissions import request_permissions, Permission
from android import ActivityCompat
from android.app import Activity
from android.os import Bundle

import cv2
import numpy as np
from PIL import Image
import io

# Импортируем модули OCR из основной папки
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ocr_processor import OCRProcessor
from excel_manager import ExcelManager
from config import REFERENCE_DB_PATH, HISTORY_DB_PATH

# Для Android - ищем файлы в правильных местах
if platform == 'android':
    from android.storage import internal_storage_path
    _android_data_dir = Activity.getInstance().getFilesDir().getAbsolutePath()
else:
    _android_data_dir = os.path.dirname(__file__)

# Пути к Excel файлам (копируем при первом запуске)
_REFERENCE_DB = os.path.join(_android_data_dir, 'reference_db.xlsx')
_HISTORY_DB = os.path.join(_android_data_dir, 'history.xlsx')


def ensure_excel_files():
    """Копируем Excel файлы во внутреннюю память Android при первом запуске"""
    if platform != 'android':
        return
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Пытаемся найти файлы в assets (из APK)
    assets_ref = os.path.join(app_dir, 'reference_db.xlsx')
    assets_hist = os.path.join(app_dir, 'history.xlsx')
    
    if not os.path.exists(_REFERENCE_DB) and os.path.exists(assets_ref):
        import shutil
        shutil.copy2(assets_ref, _REFERENCE_DB)
        print(f"Copied reference_db.xlsx to {_REFERENCE_DB}")
    
    if not os.path.exists(_HISTORY_DB) and os.path.exists(assets_hist):
        import shutil
        shutil.copy2(assets_hist, _HISTORY_DB)
        print(f"Copied history.xlsx to {_HISTORY_DB}")


ensure_excel_files()

# Глобальный OCR процессор
_ocr_processor = None
_excel_manager = None


def get_ocr_processor():
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor


def get_excel_manager():
    global _excel_manager
    if _excel_manager is None:
        _excel_manager = ExcelManager(_REFERENCE_DB, _HISTORY_DB)
    return _excel_manager


class GasMeterActivity:
    """Обработка Android Activity lifecycle"""
    pass


class ImageLoaderThread(threading.Thread):
    """Поток для загрузки и обработки изображения"""
    def __init__(self, image_path, callback):
        super().__init__()
        self.image_path = image_path
        self.callback = callback
        self.image_array = None
        self.kivy_image = None
        self.error = None
    
    def run(self):
        try:
            # Загружаем через OpenCV
            img = cv2.imread(self.image_path)
            if img is None:
                self.error = "Не удалось загрузить изображение"
                return
            
            self.image_array = img
            
            # Масштабируем для отображения
            max_width = Window.width * 0.7
            max_height = Window.height * 0.5
            height, width = img.shape[:2]
            scale = min(max_width / width, max_height / height)
            if scale < 1:
                scaled = cv2.resize(img, (int(width * scale), int(height * scale)))
            else:
                scaled = img
            
            # Конвертируем для Kivy (BGR → RGB → PIL → Kivy)
            rgb = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            pil_img_io = io.BytesIO()
            pil_img.save(pil_img_io, format='png')
            pil_img_io.seek(0)
            
            self.kivy_image = CoreImage(pil_img_io, ext='png').texture
            
        except Exception as e:
            self.error = f"Ошибка: {str(e)}"


class GasMeterApp(MDApp):
    """Главное приложение для Android"""
    
    serial_text = StringProperty("Не распознан")
    reading_text = StringProperty("Не распознано")
    account_text = StringProperty("Не найден")
    subscriber_text = StringProperty("")
    address_text = StringProperty("")
    status_text = StringProperty("Готово")
    
    image_source = StringProperty("")
    has_image = NumericProperty(0)  # 0 - нет, 1 - загрузка, 2 - готово
    
    serial = None
    reading = None
    account = None
    subscriber = ""
    address = ""
    current_image_path = None
    current_image_array = None
    
    def build(self):
        # Настройка окна
        Window.size = (400, 800)
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        # Запрашиваем разрешения
        if platform == 'android':
            request_permissions([
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
        
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'Teal'
        
        # Создаём UI
        self.root = self._create_ui()
        
        # Копируем Excel файлы
        ensure_excel_files()
        
        return self.root
    
    def _create_ui(self):
        """Создание интерфейса"""
        return Builder.load_string('''
<GasMeterScreen>:
    BoxLayout:
        orientation: 'vertical'
        
        # Заголовок
        MDToolbar:
            title: 'Газовый счётчик'
            elevation: 10
            MDLabel:
                hbox_margins: [10, 0]
                text: 'СГД-Г4'
                theme_text_color: 'Primary'
        
        ScrollView:
            MDLayout:
                layout: 'GridLayout'
                cols: 1
                padding: [10, 10, 10, 20]
                spacing: [10, 10]
                adaptive_height: True
                
                # Область изображения
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: [10, 10]
                    spacing: [10, 10]
                    elevation: 3
                    radius: [10]
                    
                    MDLabel:
                        text: 'ФОТО СЧЁТЧИКА'
                        theme_text_color: 'Secondary'
                        font_style: 'Subtitle1'
                    
                    GridLayout:
                        cols: 2
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: 10
                        
                        MDRoundFlatIconButton:
                            text: '📁 Выбрать фото'
                            on_press: root.select_image()
                            icon: 'image'
                        
                        MDRoundFlatIconButton:
                            text: '📷 Камера'
                            on_press: root.open_camera()
                            icon: 'camera'
                    
                    FloatLayout:
                        id: image_container
                        size_hint_y: None
                        height: 250 if root.app.has_image == 2 else 150
                        
                        Image:
                            id: image_display
                            source: root.app.image_source
                            allow_stretch: True
                            keep_ratio: True
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                        
                        Label:
                            text: '[b]Загрузка...[/b]'
                            markup: True
                            color: app.theme_cls.primary_color
                            size: self.texture_size
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            canvas.before:
                                Color:
                                    rgba: 1, 1, 1, 0.8
                                Rectangle:
                                    pos: self.pos
                                    size: self.size
                            opacity: 0.5
                            visible: root.app.has_image == 1
                        
                        Label:
                            text: '[b]Нет фото[/b]'
                            markup: True
                            color: [0.5, 0.5, 0.5, 1]
                            size: self.texture_size
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            canvas.before:
                                Color:
                                    rgba: 1, 1, 1, 0.6
                                Rectangle:
                                    pos: self.pos
                                    size: self.texture_size
                            opacity: 0.7
                            visible: root.app.has_image == 0
                    
                    BoxLayout:
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: 10
                        padding: [5, 0]
                        
                        MDRoundFlatIconButton:
                            text: 'Распознать'
                            on_press: root.start_ocr()
                            icon: 'magnify'
                            disabled: root.app.has_image != 2
                            pos_hint: {'center_x': 0.5}
                        
                        MDRoundFlatIconButton:
                            text: 'Очистить'
                            on_press: root.clear_image()
                            icon: 'delete'
                    
                # Результаты
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: [10, 10]
                    spacing: [10, 10]
                    elevation: 3
                    radius: [10]
                    
                    MDLabel:
                        text: 'РЕЗУЛЬТАТЫ'
                        theme_text_color: 'Secondary'
                        font_style: 'Subtitle1'
                    
                    # Серийный номер
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: 10
                        padding: [5, 0]
                        
                        MDLabel:
                            text: 'Серийный номер:'
                            theme_text_color: 'Secondary'
                            font_style: 'Body1'
                        
                        MDLabel:
                            text: root.app.serial_text
                            theme_text_color: 'Custom'
                            text_color: app.theme_cls.primary_color
                            font_style: 'Body1'
                            bold: True
                    
                    # Показание
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: 10
                        padding: [5, 0]
                        
                        MDLabel:
                            text: 'Показание (м³):'
                            theme_text_color: 'Secondary'
                            font_style: 'Body1'
                        
                        MDTextField:
                            id: reading_field
                            text: root.app.reading_text
                            mode: 'meta'
                            size_hint_x: 0.4
                            on_text: root.on_reading_changed(self.text)
                    
                    # Лицевой счёт
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: 10
                        padding: [5, 0]
                        
                        MDLabel:
                            text: 'Лицевой счёт:'
                            theme_text_color: 'Secondary'
                            font_style: 'Body1'
                        
                        MDLabel:
                            text: root.app.account_text
                            theme_text_color: 'Custom'
                            text_color: app.theme_cls.primary_color
                            font_style: 'Body1'
                            bold: True
                    
                    # Абонент
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: 10
                        padding: [5, 0]
                        
                        MDLabel:
                            text: 'Абонент:'
                            theme_text_color: 'Secondary'
                            font_style: 'Body1'
                        
                        MDLabel:
                            text: root.app.subscriber_text
                            font_style: 'Body1'
                    
                    # Адрес
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        spacing: 10
                        padding: [5, 0]
                        
                        MDLabel:
                            text: 'Адрес:'
                            theme_text_color: 'Secondary'
                            font_style: 'Body1'
                        
                        MDLabel:
                            text: root.app.address_text
                            font_style: 'Body1'
                    
                # Кнопки действий
                MDBoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: 10
                    padding: [10, 10]
                    
                    MDRoundFlatButton:
                        text: '💾 Сохранить в Excel'
                        on_press: root.save_to_excel()
                        pos_hint: {'center_x': 0.5}
                        size_hint_x: 0.8
                    
                    MDRoundFlatButton:
                        text: '➕ Добавить в справочник'
                        on_press: root.add_to_reference()
                        pos_hint: {'center_x': 0.5}
                        size_hint_x: 0.8
                    
                    MDRoundFlatButton:
                        text: '📊 История показаний'
                        on_press: root.show_history()
                        pos_hint: {'center_x': 0.5}
                        size_hint_x: 0.8
                
        # Статус бар
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            MDLabel:
                text: root.app.status_text
                theme_text_color: 'Secondary'
                font_style: 'Caption'
                halign: 'center'
        ''')
    
    def select_image(self):
        """Выбор изображения из файловой системы"""
        if platform == 'android':
            from kivy.utils import platform
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            mPythonActivity = PythonActivity.mActivity
            
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            MainActivity = autoclass('org.kivy.android.PythonActivity')
            
            intent = Intent()
            intent.setAction(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            
            # Используем startActivityForResult для выбора файла
            activity = autoclass('org.kivy.android.PythonActivity').activity
            self.current_image_callback = self.on_image_selected
            activity.startActivityForResult(
                Intent.createChooser(intent, 'Выберите фото'),
                1
            )
        else:
            from kivy.garden.filebrowser import FileBrowser
            from kivy.uix.popup import Popup
            
            fb = FileBrowser()
            fb.bind(success=self._on_file_browser_success)
            Popup(title='Выберите фото', content=fb, size_hint=(0.9, 0.9)).open()
    
    def on_image_selected(self, uri):
        """Обработчик выбора изображения"""
        self.current_image_path = uri
        self.load_image_from_path(uri)
    
    def _on_file_browser_success(self, instance):
        """Полный рабочий пример"""
        self.current_image_path = instance.selection[0]
        self.load_image_from_path(self.current_image_path)
    
    def load_image_from_path(self, path):
        """Загрузка изображения"""
        if not os.path.exists(path):
            self.status_text = "Файл не найден"
            return
        
        self.app.status_text = f"Загрузка: {os.path.basename(path)}"
        self.app.has_image = 1
        self.current_image_path = path
        
        # Загружаем в отдельном потоке
        thread = ImageLoaderThread(path, self.on_image_loaded)
        thread.start()
    
    def on_image_loaded(self, loader):
        """Полная обработка загруженного изображения"""
        if loader.error:
            Clock.schedule_once(lambda dt: setattr(self.app, 'status_text', loader.error))
            Clock.schedule_once(lambda dt: setattr(self.app, 'has_image', 0))
            return
        
        self.app.current_image_array = loader.image_array
        self.app.image_source = loader.image_source
        self.app.has_image = 2
        self.app.status_text = f"Фото загружено: {os.path.basename(self.current_image_path)}"
    
    def open_camera(self):
        """Открытие камеры для съёмки"""
        if platform == 'android':
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # Создаём камеру
            Intent = autoclass('android.content.Intent')
            intent = Intent(autoclass('android.provider.MediaStore').ACTION_IMAGE_CAPTURE)
            
            # Сохраняем в временный файл
            import tempfile
            self.temp_photo_file = tempfile.NamedTemporaryFile(
                suffix='.jpg', prefix='gas_meter_', delete=False
            )
            self.temp_photo_file.close()
            
            # Передаём путь в камеру
            from jnius import cast
            Uri = autoclass('android.net.Uri')
            File = autoclass('java.io.File')
            file = File(self.temp_photo_file.name)
            uri = Uri.fromFile(file)
            
            # Используем startActivityForResult
            activity.startActivityForResult(intent, 2)
        else:
            self.app.status_text = "Камера доступна только на Android"
    
    def on_camera_result(self, result_code, intent):
        """Обработчик результата камеры"""
        if result_code == Activity.RESULT_OK and hasattr(self, 'temp_photo_file'):
            self.load_image_from_path(self.temp_photo_file.name)
    
    def start_ocr(self):
        """Запуск распознавания"""
        if self.app.has_image != 2:
            self.app.status_text = "Сначала загрузите фото"
            return
        
        self.app.status_text = "Распознавание..."
        self.app.root.ids['image_container'].children[-1].text = "⏳ Обработка..."
        
        # Запускаем OCR в отдельном потоке
        thread = threading.Thread(target=self._run_ocr_thread)
        thread.daemon = True
        thread.start()
    
    def _run_ocr_thread(self):
        """Окончательный код OCR"""
        try:
            import time
            
            ocr = get_ocr_processor()
            image = self.app.current_image_array
            
            # Вызываем процессирование
            start_time = time.time()
            serial, reading = ocr.process_image_from_array(image)
            elapsed = time.time() - start_time
            
            print(f"OCR за {elapsed:.1f}с: serial={serial}, reading={reading}")
            
            # Обновляем UI в главном потоке
            def update_results(dt):
                self.app.serial = serial
                self.app.reading = reading
                self.app.serial_text = serial if serial else "Не распознан"
                
                if reading is not None:
                    self.app.reading_text = f"{reading:05d}"
                    # Обновляем поле ввода
                    self.app.root.ids['reading_field'].text = f"{reading:05d}"
                else:
                    self.app.reading_text = "Не распознано"
                    self.app.root.ids['reading_field'].text = ""
                
                # Если серийник найден - ищем лицевой счёт
                if serial:
                    self._lookup_account()
                
                self.app.status_text = (
                    f"Готово за {elapsed:.1f}с" + 
                    (f" → {reading:05d}" if reading is not None else " (не распознано)")
                )
                
                # Убираем индикатор загрузки
                if len(self.app.root.ids['image_container'].children) > 1:
                    self.app.root.ids['image_container'].remove_widget(
                        self.app.root.ids['image_container'].children[-1]
                    )
            
            Clock.schedule_once(update_results, 0)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            Clock.schedule_once(lambda dt: setattr(
                self.app, 'status_text', f"Ошибка OCR: {str(e)}"
            ))
    
    def _lookup_account(self):
        """Поиск лицевой счёта"""
        if not self.app.serial:
            return
        
        try:
            excel = get_excel_manager()
            result = excel.lookup_account(self.app.serial)
            
            def update(dt):
                if result:
                    self.app.account = result.get('Лицевой_счёт', 'Не найден')
                    self.app.subscriber = result.get('Абонент', '')
                    self.app.address = result.get('Адрес', '')
                    self.app.account_text = self.app.account
                    self.app.subscriber_text = self.app.subscriber
                    self.app.address_text = self.app.address
                    self.app.status_text += " | Счёт найден"
                else:
                    self.app.account_text = "Не найден"
                    self.app.subscriber_text = ""
                    self.app.address_text = ""
                    self.app.status_text += " | Счёт не найден"
            
            Clock.schedule_once(update, 0)
            
        except Exception as e:
            print(f"Ошибка поиска счёта: {e}")
    
    def save_to_excel(self):
        """Сохранение в Excel"""
        if not self.app.serial:
            self.app.status_text = "Сначала распознайте счётчик"
            return
        
        reading_text = self.app.root.ids['reading_field'].text.strip()
        reading = None
        if reading_text and len(reading_text) == 5 and reading_text.isdigit():
            reading = int(reading_text)
        elif self.app.reading is not None:
            reading = self.app.reading
        
        if reading is None:
            self.app.status_text = "Введите 5 цифр показаний"
            return
        
        # Если лицевой счёт не найден - запрашиваем
        account = self.app.account
        if account == "Не найден" or account is None:
            # Показываем диалог для ввода
            dialog = MDDialog(
                title='Введите лицевой счёт',
                auto_dismiss=False,
                content=MDTextField(
                    hint_text='Лицевой счёт (8-12 цифр)',
                    id='account_input',
                    mode='line'
                ),
                button_layout=[
                    MDButton(
                        content_container_type='HBoxLayout',
                        MDRoundFlatButton(text='Отмена', on_press=self._cancel_save),
                        MDRoundFlatButton(text='Сохранить', on_press=self._confirm_save)
                    )
                ]
            )
            dialog.open()
            self._save_dialog = dialog
        else:
            self._do_save(account, reading)
    
    def _do_save(self, account, reading):
        """Сохранение показаний"""
        try:
            excel = get_excel_manager()
            success = excel.add_reading(
                serial_number=self.app.serial,
                account_number=account,
                subscriber=self.app.subscriber,
                address=self.app.address,
                reading=reading,
                photo_path=self.current_image_path or "Камера"
            )
            
            if success:
                self.app.status_text = "✅ Сохранено в Excel!"
            else:
                self.app.status_text = "Ошибка сохранения в Excel"
        except Exception as e:
            self.app.status_text = f"Ошибка: {str(e)}"
    
    def _cancel_save(self, instance):
        """Отмена сохранения"""
        if hasattr(self, '_save_dialog'):
            self._save_dialog.dismiss()
    
    def _confirm_save(self, instance):
        """Подтверждение сохранения"""
        content = self._save_dialog.content
        account = content.text.strip() if content else ""
        
        if not account or len(account) < 8:
            self.app.status_text = "Введите корректный лицевой счёт"
            return
        
        if hasattr(self, '_save_dialog'):
            self._save_dialog.dismiss()
        
        reading_text = self.app.root.ids['reading_field'].text.strip()
        reading = int(reading_text) if reading_text.isdigit() else self.app.reading
        self._do_save(account, reading)
    
    def add_to_reference(self):
        """Добавление в справочник"""
        if not self.app.serial:
            self.app.status_text = "Сначала распознайте счётчик"
            return
        
        dialog = MDDialog(
            title='Добавить в справочник',
            auto_dismiss=False,
            content=BoxLayout(
                orientation='vertical',
                padding=10,
                spacing=10,
                MDTextField(hint_text='Лицевой счёт', id='ref_account', mode='line'),
                MDTextField(hint_text='Абонент (ФИО)', id='ref_subscriber', mode='line'),
                MDTextField(hint_text='Адрес', id='ref_address', mode='line'),
                padding=[10, 10]
            ),
            button_layout=[
                MDButton(
                    content_container_type='HBoxLayout',
                    MDRoundFlatButton(text='Отмена', on_press=lambda x: dialog.dismiss()),
                    MDRoundFlatButton(text='Добавить', on_press=self._confirm_add_reference)
                )
            ]
        )
        dialog.open()
        self._reference_dialog = dialog
    
    def _confirm_add_reference(self, instance):
        """Подтверждение добавления в справочник"""
        dialog = self._reference_dialog
        content = dialog.content
        
        account = content.children[0].text
        subscriber = content.children[1].text
        address = content.children[2].text
        
        if not account:
            self.app.status_text = "Введите лицевой счёт"
            return
        
        try:
            excel = get_excel_manager()
            success = excel.add_reference_row(
                serial_number=self.app.serial,
                account_number=account,
                subscriber=subscriber,
                address=address
            )
            
            if success:
                self.app.status_text = "✅ Добавлено в справочник!"
                self._lookup_account()
            else:
                self.app.status_text = "Ошибка добавления в справочник"
        except Exception as e:
            self.app.status_text = f"Ошибка: {str(e)}"
        
        dialog.dismiss()
    
    def show_history(self):
        """Показание истории"""
        self.app.status_text = "Загрузка истории..."
        
        def load_history(dt):
            try:
                excel = get_excel_manager()
                df = excel.get_history()
                
                if df.empty:
                    self.app.status_text = "История пуста"
                    return
                
                # Создаём таблицу
                from kivy.uix.table import TableLayout
                from kivy.uix.scrollview import ScrollView
                
                # Создаём простой список записей
                table_items = []
                for _, row in df.iterrows():
                    line = f"{row.get('Дата', '')} | {row.get('Серийный', '')} | {row.get('Показание', '')}"
                    table_items.append(line)
                
                # Создаём ScrollView с ListAdapter (упрощённый вариант)
                from kivy.uix.label import Label
                from kivy.uix.boxlayout import BoxLayout
                
                history_text = "\n".join(table_items[:50])  # Макс 50 записей
                
                history_window = Screen(name='history')
                history_box = BoxLayout(orientation='vertical', padding=10, spacing=10)
                
                history_label = Label(
                    text=history_text,
                    text_size=(Window.width - 40, None),
                    size_hint_y=None,
                    bold=True,
                    font_size='12sp'
                )
                history_label.bind(texture_size=history_label.setter('size'))
                
                history_box.add_widget(
                    Label(text='ИСТОРИЯ ПОКАЗАНИЙ', font_size='18sp', bold=True)
                )
                history_box.add_widget(ScrollView(size_hint=(1, 0.85), content=history_label))
                
                history_box.add_widget(
                    MDRaisedButton(
                        text='Закрыть',
                        size_hint=(1, 0.1),
                        on_press=lambda x: self.root.remove_widget(history_window)
                    )
                )
                
                history_window.add_widget(history_box)
                self.root.add_widget(history_window)
                
                self.app.status_text = f"Загружено {len(table_items)} записей"
                
            except Exception as e:
                self.app.status_text = f"Ошибка истории: {str(e)}"
        
        Clock.schedule_once(load_history, 0)
    
    def clear_image(self):
        """Очистка изображения"""
        self.app.has_image = 0
        self.app.image_source = ""
        self.app.serial = None
        self.app.reading = None
        self.app.serial_text = "Не распознан"
        self.app.reading_text = "Не распознано"
        self.app.account_text = "Не найден"
        self.app.subscriber_text = ""
        self.app.address_text = ""
        self.app.status_text = "Готово"
        self.current_image_path = None
        self.app.current_image_array = None
        
        if hasattr(self, 'temp_photo_file') and os.path.exists(self.temp_photo_file.name):
            os.unlink(self.temp_photo_file.name)


class GasMeterScreen(Screen):
    """Экран главного приложения"""
    pass


if __name__ == '__main__':
    GasMeterApp().run()
