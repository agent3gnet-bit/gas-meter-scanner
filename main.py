"""
Главное приложение для распознавания показаний газовых счётчиков
Python + Tkinter интерфейс
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import threading
import datetime

from ocr_processor import OCRProcessor
from excel_manager import ExcelManager
from config import REFERENCE_DB_PATH, HISTORY_DB_PATH


class GasMeterReaderApp:
    """Главное приложение"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Газовый счётчик - Распознавание показаний")
        self.root.geometry("1200x800")
        
        # Инициализация модулей
        self.ocr = OCRProcessor()
        self.excel = ExcelManager(REFERENCE_DB_PATH, HISTORY_DB_PATH)
        
        # Текущие данные
        self.current_serial = None
        self.current_reading = None
        self.current_account = None
        self.current_subscriber = ""
        self.current_address = ""
        self.current_image = None
        self.current_image_path = None
        
        # Создание интерфейса
        self._create_ui()
        
    def _create_ui(self):
        """Создание пользовательского интерфейса"""
        # Главная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для масштабирования
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === Заголовок ===
        title_label = ttk.Label(
            main_frame, 
            text="Распознавание показаний газовых счётчиков",
            font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # === Область изображения (левая колонка) ===
        image_frame = ttk.LabelFrame(main_frame, text="Изображение", padding="10")
        image_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        image_frame.columnconfigure(0, weight=1)
        image_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Метка для отображения изображения
        self.image_label = ttk.Label(image_frame, text="Нет загруженного изображения")
        self.image_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # === Панель управления ===
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Кнопка загрузки файла
        self.btn_load = ttk.Button(
            control_frame, 
            text="📁 Загрузить файл",
            command=self.load_image_file,
            width=20
        )
        self.btn_load.grid(row=0, column=0, padx=5)
        
        # Кнопка захвата с камеры
        self.btn_capture = ttk.Button(
            control_frame,
            text="📷 Захватить с камеры",
            command=self.capture_from_camera,
            width=20
        )
        self.btn_capture.grid(row=0, column=1, padx=5)
        
        # Кнопка распознавания
        self.btn_ocr = ttk.Button(
            control_frame,
            text="🔍 Распознать",
            command=self.start_ocr,
            width=20,
            state=tk.DISABLED
        )
        self.btn_ocr.grid(row=0, column=2, padx=5)
        
        # === Область результатов (правая колонка) ===
        result_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        result_frame.grid(row=1, column=2, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10, padx=(10, 0))
        result_frame.columnconfigure(1, weight=1)
        
        # Серийный номер
        ttk.Label(result_frame, text="Серийный номер:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.serial_var = tk.StringVar(value="Не распознан")
        ttk.Label(result_frame, textvariable=self.serial_var, font=("Courier", 11)).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Показание (5 цифр)
        ttk.Label(result_frame, text="Показание (м³):").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Рамка для поля ввода
        reading_input_frame = ttk.Frame(result_frame)
        reading_input_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        self.reading_var = tk.StringVar(value="Не распознано")
        ttk.Label(reading_input_frame, textvariable=self.reading_var, font=("Courier", 14, "bold")).pack(side=tk.LEFT)
        
        # Поле ручного ввода
        self.reading_entry = ttk.Entry(reading_input_frame, width=8, font=("Courier", 12))
        self.reading_entry.pack(side=tk.LEFT, padx=(10, 5))
        self.reading_entry.config(state=tk.DISABLED)
        
        ttk.Button(
            reading_input_frame,
            text="✓",
            command=self.confirm_manual_reading,
            width=3
        ).pack(side=tk.LEFT)
        
        # Лицевой счёт
        ttk.Label(result_frame, text="Лицевой счёт:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.account_var = tk.StringVar(value="Не найден")
        ttk.Label(result_frame, textvariable=self.account_var, font=("Courier", 11)).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Абонент
        ttk.Label(result_frame, text="Абонент:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.subscriber_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.subscriber_var).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Адрес
        ttk.Label(result_frame, text="Адрес:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.address_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.address_var).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # === Кнопки действий ===
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.btn_save = ttk.Button(
            action_frame,
            text="💾 Сохранить в Excel",
            command=self.save_to_excel,
            state=tk.DISABLED,
            width=25
        )
        self.btn_save.grid(row=0, column=0, padx=10)
        
        self.btn_add_reference = ttk.Button(
            action_frame,
            text="➕ Добавить в справочник",
            command=self.add_to_reference,
            state=tk.DISABLED,
            width=25
        )
        self.btn_add_reference.grid(row=0, column=1, padx=10)
        
        self.btn_history = ttk.Button(
            action_frame,
            text="📊 История",
            command=self.show_history,
            width=25
        )
        self.btn_history.grid(row=0, column=2, padx=10)
        
        # === Статус бар ===
        self.status_var = tk.StringVar(value="Готово")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def load_image_file(self):
        """Загрузка изображения из файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path: str):
        """Загрузка и отображение изображения"""
        try:
            # Загрузка изображения через OpenCV
            image = cv2.imread(file_path)
            if image is None:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {file_path}")
                return
            
            self.current_image = image
            self.current_image_path = file_path
            
            # Масштабирование для отображения
            max_width = 500
            max_height = 400
            height, width = image.shape[:2]
            scale = min(max_width / width, max_height / height)
            if scale < 1:
                scaled = cv2.resize(image, (int(width * scale), int(height * scale)))
            else:
                scaled = image
            
            # Конвертация для отображения в Tkinter
            rgb = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)
            tk_image = ImageTk.PhotoImage(pil_image)
            
            self.image_label.configure(image=tk_image, text="")
            self.image_label.image = tk_image
            
            # Включаем кнопку распознавания
            self.btn_ocr.configure(state=tk.NORMAL)
            self.status_var.set(f"Изображение загружено: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки изображения: {str(e)}")
    
    def capture_from_camera(self):
        """Захват изображения с веб-камеры"""
        # Открываем модальное окно для захвата
        capture_window = tk.Toplevel(self.root)
        capture_window.title("Захват с камеры")
        capture_window.geometry("640x500")
        
        # Открываем камеру
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            messagebox.showerror("Ошибка", "Не удалось открыть веб-камеру")
            capture_window.destroy()
            return
        
        # Метка для отображения видео
        label = ttk.Label(capture_window)
        label.pack(fill=tk.BOTH, expand=True)
        
        # Флаг для завершения
        capture_done = [False]
        captured_frame = [None]
        
        def update_frame():
            if capture_done[0]:
                return
            
            ret, frame = cap.read()
            if ret:
                # Поворачиваем зеркально
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb)
                tk_image = ImageTk.PhotoImage(pil_image)
                label.configure(image=tk_image)
                label.image = tk_image
            
            capture_window.after(30, update_frame)
        
        def capture():
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                captured_frame[0] = frame
                capture_done[0] = True
                capture_window.destroy()
                cap.release()
                # Загружаем захваченное изображение
                self.current_image = captured_frame[0]
                self.current_image_path = None  # Нет файла, захват с камеры
                
                # Масштабирование для отображения
                max_width = 500
                max_height = 400
                height, width = frame.shape[:2]
                scale = min(max_width / width, max_height / height)
                if scale < 1:
                    scaled = cv2.resize(frame, (int(width * scale), int(height * scale)))
                else:
                    scaled = frame
                
                rgb = cv2.cvtColor(scaled, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb)
                tk_image = ImageTk.PhotoImage(pil_image)
                
                self.image_label.configure(image=tk_image, text="")
                self.image_label.image = tk_image
                
                self.btn_ocr.configure(state=tk.NORMAL)
                self.status_var.set("Изображение захвачено с камеры")
        
        def close_capture():
            capture_done[0] = True
            cap.release()
            capture_window.destroy()
        
        # Кнопки
        button_frame = ttk.Frame(capture_window)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="📷 Захватить",
            command=capture,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="✖ Закрыть",
            command=close_capture,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Запуск обновления кадра
        update_frame()
    
    def start_ocr(self):
        """Запуск распознавания в отдельном потоке"""
        if self.current_image is None:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение")
            return
        
        self.btn_ocr.configure(state=tk.DISABLED)
        self.status_var.set("Распознавание... Пожалуйста, подождите.")
        
        # Запуск в отдельном потоке, чтобы не блокировать UI
        thread = threading.Thread(target=self.run_ocr)
        thread.daemon = True
        thread.start()
    
    def run_ocr(self):
        """Выполнение OCR распознавания"""
        try:
            # Распознавание
            serial, reading = self.ocr.process_image_from_array(self.current_image)
            
            self.current_serial = serial
            self.current_reading = reading
            
            # Обновление UI
            self.root.after(0, self.update_ocr_results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка OCR", str(e)))
            self.root.after(0, lambda: self.btn_ocr.configure(state=tk.NORMAL))
    
    def update_ocr_results(self):
        """Обновление результатов распознавания в UI"""
        # Серийный номер
        if self.current_serial:
            self.serial_var.set(self.current_serial)
            self.root.after(0, lambda: self.btn_ocr.configure(state=tk.NORMAL))
            
            # Поиск лицевой счёта
            self.lookup_account()
        else:
            self.serial_var.set("Не распознан")
            self.status_var.set("Внимание: серийный номер не распознан. Проверьте изображение.")
            self.btn_ocr.configure(state=tk.NORMAL)
        
        # Показание (5 цифр)
        if self.current_reading is not None:
            self.reading_var.set(f"{self.current_reading:05d}")
            self.reading_entry.config(state=tk.DISABLED)
        else:
            self.reading_var.set("Не распознано")
            self.reading_entry.config(state=tk.NORMAL)
            self.reading_entry.delete(0, tk.END)
            self.reading_entry.focus_set()
            self.status_var.set("Внимание: показание не распознано. Введите вручную или проверьте фото.")
        
        # Включаем кнопки сохранения и добавления в справочник
        if self.current_serial:
            self.btn_save.configure(state=tk.NORMAL)
            self.btn_add_reference.configure(state=tk.NORMAL)
    
    def lookup_account(self):
        """Поиск лицевой счёта по серийному номеру"""
        if not self.current_serial:
            return
        
        result = self.excel.lookup_account(self.current_serial)
        
        if result:
            self.current_account = result['Лицевой_счёт']
            self.current_subscriber = result.get('Абонент', '')
            self.current_address = result.get('Адрес', '')
            
            self.account_var.set(self.current_account)
            self.subscriber_var.set(self.current_subscriber)
            self.address_var.set(self.current_address)
            
            self.status_var.set("Лицевой счёт найден в справочнике")
        else:
            self.current_account = "Не найден"
            self.account_var.set("Не найден")
            self.subscriber_var.set("")
            self.address_var.set("")
            self.status_var.set("Серийный номер не найден в справочнике. Добавьте его.")

    def confirm_manual_reading(self):
        """Подтверждение ручного ввода показаний"""
        reading_text = self.reading_entry.get().strip()
        if reading_text and len(reading_text) == 5 and reading_text.isdigit():
            self.current_reading = int(reading_text)
            self.reading_var.set(f"{self.current_reading:05d}")
            self.reading_entry.config(state=tk.DISABLED)
            self.status_var.set(f"Показание введено вручную: {reading_text}")
        else:
            messagebox.showwarning("Предупреждение", "Введите 5 цифр показаний")

    def save_to_excel(self):
        """Сохранение показаний в Excel"""
        if not self.current_serial:
            messagebox.showwarning("Предупреждение", "Сначала распознайте серийный номер")
            return
        
        # Если лицевой счёт не найден, предлагаем ввести
        account = self.current_account
        if account == "Не найден":
            # Открываем диалог для ввода лицевого счёта
            dialog = tk.Toplevel(self.root)
            dialog.title("Введите лицевой счёт")
            dialog.geometry("400x200")

            ttk.Label(dialog, text="Лицевой счёт не найден в справочнике.").pack(pady=10)
            ttk.Label(dialog, text="Введите лицевой счёт:").pack(pady=5)

            account_entry = ttk.Entry(dialog, width=30)
            account_entry.pack(pady=5)
            account_entry.focus_set()

            def save_and_close():
                nonlocal account
                account = account_entry.get().strip()
                if account:
                    dialog.destroy()

            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=20)

            ttk.Button(
                button_frame,
                text="Сохранить",
                command=save_and_close,
                width=15
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                button_frame,
                text="Отмена",
                command=dialog.destroy,
                width=15
            ).pack(side=tk.LEFT, padx=5)
            
            dialog.grab_set()
            self.root.wait_window(dialog)
            
            if not account:
                return
        
        # Если показание не распознано, берём из поля ввода
        reading = self.current_reading
        if reading is None:
            try:
                manual_reading = self.reading_entry.get().strip()
                if manual_reading and len(manual_reading) == 5 and manual_reading.isdigit():
                    reading = int(manual_reading)
                else:
                    messagebox.showwarning("Предупреждение", "Введите 5 цифр показаний в поле ввода")
                    return
            except:
                messagebox.showwarning("Предупреждение", "Введите 5 цифр показаний")
                return
        
        # Сохранение
        photo_path = self.current_image_path if self.current_image_path else "Камера"
        
        success = self.excel.add_reading(
            serial_number=self.current_serial,
            account_number=account,
            subscriber=self.current_subscriber,
            address=self.current_address,
            reading=reading,
            photo_path=photo_path
        )
        
        if success:
            self.status_var.set("Показание сохранено в Excel!")
            messagebox.showinfo("Успех", "Показание успешно сохранено в Excel!")
            
            # Сброс после сохранения
            self.reset_results()
        else:
            messagebox.showerror("Ошибка", "Ошибка сохранения в Excel")
    
    def add_to_reference(self):
        """Добавление серийного номера в справочник"""
        if not self.current_serial:
            messagebox.showwarning("Предупреждение", "Сначала распознajte серийный номер")
            return
        
        if self.current_account != "Не найден":
            messagebox.showinfo("Информация", "Этот серийный номер уже есть в справочнике")
            return
        
        # Открываем диалог для добавления в справочник
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить в справочник")
        dialog.geometry("500x300")
        
        ttk.Label(dialog, text="Добавить серийный номер в справочник").pack(pady=10)
        ttk.Label(dialog, text=f"Серийный номер: {self.current_serial}", font=("Courier", 10)).pack(pady=5)
        
        ttk.Label(dialog, text="Лицевой счёт:").pack(pady=5)
        account_entry = ttk.Entry(dialog, width=40)
        account_entry.pack(pady=5)
        account_entry.focus_set()
        
        ttk.Label(dialog, text="Абонент (ФИО):").pack(pady=5)
        subscriber_entry = ttk.Entry(dialog, width=40)
        subscriber_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Адрес:").pack(pady=5)
        address_entry = ttk.Entry(dialog, width=40)
        address_entry.pack(pady=5)
        
        def save_reference():
            account = account_entry.get().strip()
            if not account:
                messagebox.showwarning("Предупреждение", "Введите лицевой счёт")
                return
            
            success = self.excel.add_reference_row(
                serial_number=self.current_serial,
                account_number=account,
                subscriber=subscriber_entry.get().strip(),
                address=address_entry.get().strip()
            )
            
            if success:
                messagebox.showinfo("Успех", "Серийный номер добавлен в справочник!")
                self.lookup_account()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Ошибка добавления в справочник")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="Добавить",
            command=save_reference,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        dialog.grab_set()
    
    def show_history(self):
        """Отображение истории показаний"""
        # Создаём окно истории
        history_window = tk.Toplevel(self.root)
        history_window.title("История показаний")
        history_window.geometry("1000x600")
        
        # Получаем историю
        df = self.excel.get_history()
        
        if df.empty:
            ttk.Label(
                history_window,
                text="История пуста",
                font=("Helvetica", 12)
            ).pack(pady=50)
            return
        
        # Создаём таблицу
        tree = ttk.Treeview(history_window, columns=list(df.columns), show="headings")
        
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        for _, row in df.iterrows():
            tree.insert("", tk.END, values=list(row))
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
        
        # Кнопка закрытия
        ttk.Button(
            history_window,
            text="Закрыть",
            command=history_window.destroy,
            width=15
        ).pack(pady=10)
    
    def reset_results(self):
        """Сброс результатов"""
        self.current_serial = None
        self.current_reading = None
        self.current_account = None
        self.current_subscriber = ""
        self.current_address = ""
        
        self.serial_var.set("Не распознан")
        self.reading_var.set("Не распознано")
        self.account_var.set("Не найден")
        self.subscriber_var.set("")
        self.address_var.set("")
        
        self.btn_save.configure(state=tk.DISABLED)
        self.btn_add_reference.configure(state=tk.DISABLED)
        self.status_var.set("Готово к новому сканированию")


def main():
    root = tk.Tk()
    app = GasMeterReaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
