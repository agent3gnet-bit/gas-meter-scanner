"""
Модуль для работы с Excel файлами
Чтение справочника соответствия серийных номеров с лицевыми счетами
Запись истории показаний
"""
import pandas as pd
import os
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExcelManager:
    """Управление Excel файлами для справочника и истории"""
    
    def __init__(self, reference_db_path: str, history_db_path: str):
        self.reference_db_path = reference_db_path
        self.history_db_path = history_db_path
        self._init_reference_db()
        self._init_history_db()
    
    def _init_reference_db(self):
        """Инициализация файла справочника, если не существует"""
        if not os.path.exists(self.reference_db_path):
            logger.info(f"Создаётся справочник: {self.reference_db_path}")
            df = pd.DataFrame(columns=['Серийный_номер', 'Лицевой_счёт', 'Абонент', 'Адрес'])
            df.to_excel(self.reference_db_path, index=False)
            logger.info("Справочник создан. Добавьте данные в файл.")
        else:
            logger.info(f"Справочник найден: {self.reference_db_path}")
    
    def _init_history_db(self):
        """Инициализация файла истории, если не существует"""
        if not os.path.exists(self.history_db_path):
            logger.info(f"Создаётся файл истории: {self.history_db_path}")
            df = pd.DataFrame(columns=[
                'Дата', 
                'Серийный_номер', 
                'Лицевой_счёт', 
                'Абонент', 
                'Адрес', 
                'Показание',
                'Источник_фото'
            ])
            df.to_excel(self.history_db_path, index=False)
            logger.info("Файл истории создан.")
        else:
            logger.info(f"Файл истории найден: {self.history_db_path}")
    
    def lookup_account(self, serial_number: str) -> Optional[Dict]:
        """
        Поиск лицевой счёт по серийному номеру в справочнике
        Возвращает словарь с данными или None
        """
        try:
            df = pd.read_excel(self.reference_db_path)
            # Приводим серийный номер к строке и ищем (без учёта регистра)
            df['SN_clean'] = df['Серийный_номер'].astype(str).str.strip().str.upper()
            sn_clean = serial_number.strip().upper()
            
            # Точное совпадение
            mask = df['SN_clean'] == sn_clean
            if mask.any():
                row = df.loc[mask].iloc[0]
                return {
                    'Лицевой_счёт': str(row['Лицевой_счёт']),
                    'Абонент': str(row.get('Абонент', '')),
                    'Адрес': str(row.get('Адрес', ''))
                }
            
            # Нечёткое совпадение (серийник может быть подстрокой)
            mask = df['SN_clean'].str.contains(sn_clean, na=False)
            if mask.any():
                row = df.loc[mask].iloc[0]
                return {
                    'Лицевой_счёт': str(row['Лицевой_счёт']),
                    'Абонент': str(row.get('Абонент', '')),
                    'Адрес': str(row.get('Адрес', ''))
                }
                
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска лицевой счёта: {e}")
            return None
    
    def add_reading(self, serial_number: str, account_number: str, 
                    subscriber: str, address: str, reading: int, photo_path: str = ""):
        """
        Добавление показания в историю (5 цифр)
        """
        try:
            df = pd.read_excel(self.history_db_path)
            new_row = pd.DataFrame([{
                'Дата': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Серийный_номер': serial_number,
                'Лицевой_счёт': account_number,
                'Абонент': subscriber,
                'Адрес': address,
                'Показание': reading,
                'Источник_фото': os.path.basename(photo_path) if photo_path else ''
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(self.history_db_path, index=False)
            logger.info(f"Показание добавлено: SN={serial_number}, ЛС={account_number}, Показание={reading}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления показания: {e}")
            return False
    
    def get_history(self) -> pd.DataFrame:
        """Получить всю историю показаний"""
        try:
            return pd.read_excel(self.history_db_path)
        except Exception as e:
            logger.error(f"Ошибка чтения истории: {e}")
            return pd.DataFrame()
    
    def add_reference_row(self, serial_number: str, account_number: str, 
                          subscriber: str = "", address: str = "") -> bool:
        """
        Добавить новую запись в справочник (если серийный номер не найден)
        """
        try:
            df = pd.read_excel(self.reference_db_path)
            new_row = pd.DataFrame([{
                'Серийный_номер': serial_number,
                'Лицевой_счёт': account_number,
                'Абонент': subscriber,
                'Адрес': address
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(self.reference_db_path, index=False)
            logger.info(f"Новый серийный номер добавлен в справочник: {serial_number}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления в справочник: {e}")
            return False
