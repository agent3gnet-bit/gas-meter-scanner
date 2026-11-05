"""
Модуль конфигурации приложения для чтения показаний газовых счётчиков
"""
import os

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REFERENCE_DB_PATH = os.path.join(BASE_DIR, "reference_db.xlsx")      # Таблица соответствия SN -> лицевой счёт
HISTORY_DB_PATH = os.path.join(BASE_DIR, "history.xlsx")             # Таблица истории показаний

# Параметры OCR — серийник из штрихкода, показания 5 цифр
SN_MAX_LENGTH = 20

# Формат лицевой счёт
ACCOUNT_NUMBER_FORMAT = r'[\d]{8,12}'
