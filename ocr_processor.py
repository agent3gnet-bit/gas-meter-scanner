"""
Модуль для распознавания штрихкодов и текста на изображениях
СГД-Г4 счётчик: серийный из штрихкода, показания — 5 цифр

Pipeline:
1. Распознаём штрихкод → серийный номер
2. Если штрихкод найден → вырезаем фиксированный LCD-кроп (y=65-71%, x=15-50%)
3. Если штрихкод НЕ найден → fallback: сканируем 9 полос по Y
4. Распознаём вырезанный фрагмент
"""
import cv2
import numpy as np
import os
import sys
from typing import Optional, List, Tuple, Dict
import re
import logging
import pytesseract
from pyzxing import BarCodeReader

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ocr_debug.log'), encoding='utf-8', mode='w'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

# Устанавливаем путь к Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\PROGRA~1\TESSER~1\TESSER~1.EXE'

# Для PyInstaller onefile режима: путь к папке проекта
if getattr(sys, 'frozen', False):
    _script_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    _script_dir = os.path.dirname(os.path.abspath(__file__))


class OCRProcessor:
    """Обработчик для распознавания штрихкодов и показаний газовых счётчиков СГД-Г4"""

    def __init__(self):
        self.reader = BarCodeReader()
        self.tesseract_config = '--oem 3 --psm 6'
        self.last_reading = None

    def decode_barcodes(self, image: np.ndarray) -> List[Dict]:
        """
        Распознавание штрихкодов из изображения.
        Возвращает список словарей: [{'text': '...', 'bbox': (x,y,w,h)}, ...]
        """
        try:
            temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_temp_barcode.png')
            cv2.imwrite(temp_path, image)

            reader = BarCodeReader()
            results = reader.decode(temp_path)

            os.remove(temp_path)

            barcodes = []
            for result in results:
                text = str(result.get('text', result.get('raw', ''))).strip()
                if text and text != 'None':
                    # Извлекаем bounding box если есть
                    bbox = None
                    if hasattr(result, 'bounding_box'):
                        bb = result.bounding_box
                        if bb and len(bb) >= 4:
                            # bb — list of corners: top-left, top-right, bottom-right, bottom-left
                            xs = [p.x for p in bb]
                            ys = [p.y for p in bb]
                            bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
                    elif 'boundingBox' in result:
                        bb = result['boundingBox']
                        if bb and len(bb) >= 4:
                            xs = [p['x'] for p in bb]
                            ys = [p['y'] for p in bb]
                            bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

                    barcodes.append({'text': text, 'bbox': bbox})
                    logger.info(f"Найден штрихкод: {text}, bbox={bbox}")

            return barcodes

        except Exception as e:
            logger.error(f"Ошибка распознавания штрихкодов: {e}")
            return []

    def recognize_serial_from_barcode(self, image: np.ndarray) -> Optional[str]:
        """Получение серийного номера из штрихкода"""
        barcodes = self.decode_barcodes(image)
        if barcodes:
            serial = barcodes[0]['text'].strip()
            logger.info(f"Серийный номер из штрихкода: {serial}")
            return serial
        return None

    def _find_barcode_position(self, image: np.ndarray) -> Optional[Dict]:
        """
        Найти штрихкод и вернуть его позицию.
        Если barcode в верхней части — LCD внизу (фиксированная область).
        """
        barcodes = self.decode_barcodes(image)
        if not barcodes:
            return None

        bc = barcodes[0]
        if bc['bbox']:
            x, y, w, h = bc['bbox']
            h_img = image.shape[0]
            # barcode в верхней части?
            y_pct = y / h_img
            logger.info(f"Штрихкод найден: pos={y_pct:.1%} от высоты, text={bc['text']}")
            return bc
        return bc  # bbox неизвестен, но barcode есть

    def crop_lcd_strip(self, image: np.ndarray, y_start_pct: float, y_end_pct: float,
                       x_start_pct: float, x_end_pct: float) -> Optional[np.ndarray]:
        """
        Вырезать фиксированную полосу LCD.

        Для СГД-Г4 с известным barcode:
        - LCD всегда в нижней части (65-71% высоты)
        - Цифры слева направо (15-50% ширины)
        """
        h, w = image.shape[:2]
        y1 = int(h * y_start_pct)
        y2 = int(h * y_end_pct)
        x1 = int(w * x_start_pct)
        x2 = int(w * x_end_pct)

        strip = image[y1:y2, x1:x2]

        if strip.size == 0:
            logger.warning(f"❌ Пустой crop: y={y1}-{y2}, x={x1}-{x2}")
            return None

        logger.info(f"✅ LCD-кроп: y={y1}-{y2} ({y2-y1}px), x={x1}-{x2} ({x2-x1}px)")
        return strip

    def recognize_meter_reading_with_barcode(self, image: np.ndarray) -> Optional[int]:
        """
        Распознавание показаний СГД-Г4 с использованием штрихкода.

        Pipeline:
        1. Найти штрихкод → знаем что это счётчик
        2. Вырезать фиксированную область LCD (y=65-71%, x=15-50%)
        3. Распознать 5 цифр
        """
        debug_dir = _script_dir

        # --- Шаг 1: Ищем штрихкод ---
        barcode_info = self._find_barcode_position(image)

        if not barcode_info:
            logger.warning("❌ Штрихкод не найден, fallback на универсальный режим")
            return self._recognize_meter_reading_generic(image)

        # --- Шаг 2: Вырезаем фиксированный LCD-кроп ---
        # СГД-Г4: LCD внизу (ниже "СГД-Г4"), цифры слева направо
        y_start = 0.72  # 72% высоты (ниже "СГД-Г4")
        y_end = 0.78    # 78% высоты
        x_start = 0.15  # 15% ширины (захватываем "0" слева)
        x_end = 0.50    # 50% ширины

        lcd_crop = self.crop_lcd_strip(image, y_start, y_end, x_start, x_end)

        if lcd_crop is None:
            logger.warning("❌ LCD-кроп пустой, fallback на универсальный режим")
            return self._recognize_meter_reading_generic(image)

        # --- Шаг 3: Сохраняем raw crop для отладки ---
        cv2.imwrite(os.path.join(debug_dir, '_debug_lcd_crop.png'), lcd_crop)

        # --- Шаг 4: Распознаём ---
        candidates = self._recognize_from_crop(
            lcd_crop, '_debug_lcd_recognized.png', debug_dir
        )

        if not candidates:
            logger.warning("❌ Ничего не распознано из LCD-кропа, fallback на универсальный режим")
            return self._recognize_meter_reading_generic(image)

        # --- Шаг 5: Выбираем лучшего кандидата ---
        best_reading = None
        best_score = -1
        best_text = ""

        for val, text, digits, extra_score in candidates:
            score = self._calculate_reading_score(val, digits, extra_score)
            logger.info(f"Кандидат: {val} ({digits}зн) score={score} text='{text}'")

            if score > best_score:
                best_score = score
                best_reading = val
                best_text = text

        if best_reading:
            best_reading = self._postprocess_correction(best_reading)
            logger.info(f"✅ Итог из barcode-кропа: {best_reading} ({len(str(best_reading))}зн, text='{best_text}')")
            self.last_reading = best_reading
            return best_reading

        return None

    def _recognize_meter_reading_generic(self, image: np.ndarray) -> Optional[int]:
        """
        Универсальное распознавание (без штрихкода).
        Сканирует 9 Y-позиций в нижней части изображения.
        """
        debug_dir = _script_dir

        if len(image.shape) > 2:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        logger.info(f"[generic] Image: {w}x{h}")

        best_reading = None
        best_text = ""
        best_score = -1

        for y_pct in [0.48, 0.50, 0.52, 0.54, 0.56, 0.60, 0.65, 0.70, 0.75]:
            y_start = int(h * y_pct)
            y_end = y_start + int(h * 0.04)
            x_start = int(w * 0.02)
            x_end = int(w * 0.60)

            crop = image[y_start:y_end, x_start:x_end]
            if crop.size == 0:
                continue

            candidates = self._recognize_from_crop(
                crop, f'_debug_y{y_pct:.2f}.png', debug_dir
            )

            for val, text, digits, extra_score in candidates:
                score = self._calculate_reading_score(val, digits, extra_score)
                logger.info(f"Кандидат y={y_pct:.2f}: {val} ({digits}зн) score={score} text='{text}'")

                if score > best_score:
                    best_score = score
                    best_reading = val
                    best_text = text

        if best_reading:
            best_reading = self._postprocess_correction(best_reading)
            logger.info(f"✅ Итог generic: {best_reading} ({len(str(best_reading))}зн, text='{best_text}')")
            self.last_reading = best_reading
            return best_reading

        logger.warning("❌ Нет подходящих кандидатов в generic режиме")
        return None

    def _calculate_reading_score(self, val: int, digits: int, extra_score: int) -> int:
        """
        Рассчитать приоритет кандидата.
        """
        score = 0
        first_digit = str(val).zfill(digits)[0]

        if digits == 5 and first_digit == '0':
            score += 100
        elif digits == 5 and first_digit != '0':
            score += 50
        elif digits == 4:
            score += 10
        if first_digit not in ('0', '1'):
            score += 5
        score += extra_score

        return score

    def _recognize_from_crop(self, crop: np.ndarray, debug_name: str,
                              debug_dir: str) -> List[Tuple[int, str, int]]:
        """
        Распознать показания из cropped изображения дисплея.

        Pipeline для LCD (белые цифры на чёрном):
        1. Инверсия цветов
        2. CLAHE для усиления
        3. Otsu бинаризация
        4. Обрезка сверху (убираем тех. характеристики)
        5. Morph close (соединяем разрывы в цифре 1)
        6. Dilation (утолщаем вертикальные линии)
        7. Scale 4x NEAREST
        8. Tesseract: 6 конфигураций (ENG + RUS)
        """
        candidates = []

        if len(crop.shape) > 2:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop.copy()

        # Инвертируем: белые цифры на чёрном → тёмные на белом
        gray = 255 - gray

        # Без CLAHE — цифры на LCD уже достаточно контрастные
        # Оставляем gray как есть
        enhanced = gray

        # Otsu
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        white_pixels = np.sum(binary > 0)
        logger.info(f"[recognize_from_crop] binary white pixels: {white_pixels} / {binary.size} ({100*white_pixels/binary.size:.1f}%)")

        # Обрезаем чёрную рамку слева: пропускаем первые 60px
        skip_left = 60
        if binary.shape[1] > skip_left + 50:
            binary = binary[:, skip_left:]
            logger.info(f"[recognize_from_crop] Пропущено {skip_left}px слева (рамка)")

        # Обрезаем: берём только верхние 80% — там цифры
        h2 = binary.shape[0]
        digit_h = int(h2 * 0.80)
        binary = binary[:digit_h, :]
        logger.info(f"[recognize_from_crop] Ограничение по высоте: {digit_h}px из {h2}px")

        # Morph vertical close — соединяем разрывы в вертикальных линиях (цифра 1)
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_v, iterations=1)

        # Дилатация по горизонтали — утолщаем тонкие вертикальные линии
        kernel_thicken = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
        binary = cv2.dilate(binary, kernel_thicken, iterations=1)

        # Масштабируем в 4x NEAREST
        scale = 4
        large = cv2.resize(binary, (binary.shape[1]*scale, binary.shape[0]*scale),
                          interpolation=cv2.INTER_NEAREST)

        cv2.imwrite(os.path.join(debug_dir, debug_name), large)

        # Распознавание: ENG модели приоритетнее для LCD СГД-счётчиков
        # RUS — только как fallback
        configs = [
            ('eng', 1, 7, 15),   # LSTM ENG — высокий приоритет
            ('eng', 1, 6, 15),
            ('eng', 1, 11, 15),
            ('eng', 3, 7, 10),   # Classic ENG
            ('rus', 1, 7, 5),    # LSTM RUS — fallback
            ('rus', 1, 6, 5),
        ]

        for lang, oem, psm, base_score in configs:
            config = f'--oem {oem} --psm {psm} -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(large, config=config, lang=lang).strip()
            logger.info(f"  {lang.upper()} OEM{oem} PSM{psm}: raw='{text}', base_score={base_score}")

            for match in re.finditer(r'\d{4,5}', text):
                val = int(match.group())
                digits = len(match.group())
                first_digit = match.group()[0]
                candidates.append((val, text, digits, base_score))
                logger.info(f"  ✅ Candidate: {val} ({digits}зн, {lang}) from '{text}'")

        # Fallback: без CLAHE
        if not candidates:
            logger.info("[recognize_from_crop] Fallback: trying without CLAHE...")
            _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            large2 = cv2.resize(binary2, (binary2.shape[1]*4, binary2.shape[0]*4),
                               interpolation=cv2.INTER_NEAREST)
            cv2.imwrite(os.path.join(debug_dir, '_debug_lcd_found_noclahe.png'), large2)

            for lang, oem, psm, base_score in [('eng', 1, 7, 15), ('eng', 1, 6, 15), ('rus', 1, 7, 5), ('rus', 1, 6, 5)]:
                config = f'--oem {oem} --psm {psm} -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(large2, config=config, lang=lang).strip()
                logger.info(f"  Fallback {lang.upper()} OEM{oem} PSM{psm}: raw='{text}', score={base_score}")

                for match in re.finditer(r'\d{4,5}', text):
                    val = int(match.group())
                    digits = len(match.group())
                    candidates.append((val, text, digits, base_score))
                    logger.info(f"  ✅ Fallback Candidate: {val} ({digits}зн, {lang})")

        logger.info(f"[recognize_from_crop] Итого кандидатов: {len(candidates)}")
        return candidates

    def _postprocess_correction(self, reading: int) -> int:
        """
        Контекстная коррекция: 7→1 если разница с предыдущим показанием подозрительная.
        """
        if self.last_reading is None:
            return reading

        reading_str = str(reading).zfill(5)
        last_str = str(self.last_reading).zfill(5)
        last_digit = int(reading_str[4])
        last_last_digit = int(last_str[4])

        if last_digit == 7 and last_last_digit <= 5:
            diff = reading - self.last_reading
            if diff > 5:
                corrected = int(reading_str[:4] + '1')
                new_diff = corrected - self.last_reading
                if 1 <= new_diff <= 10:
                    logger.info(f"[postprocess] Коррекция: {reading}→{corrected} (разница {diff}→{new_diff})")
                    return corrected

        return reading

    def process_image(self, image_path: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Полная обработка изображения.

        Pipeline:
        1. Загрузить фото
        2. Распознать штрихкод → серийный номер
        3. Распознать показания (с barcode → fixed crop, без → generic scan)
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Не удалось загрузить изображение: {image_path}")
                return None, None

            serial_number = self.recognize_serial_from_barcode(image)
            meter_reading = self.recognize_meter_reading_with_barcode(image)

            return serial_number, meter_reading

        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            logger.exception("  Полный стек:")
            return None, None

    def process_image_from_array(self, image_array: np.ndarray) -> Tuple[Optional[str], Optional[int]]:
        """
        Обработка изображения из numpy массива (например, с веб-камеры).
        """
        try:
            serial_number = self.recognize_serial_from_barcode(image_array)
            meter_reading = self.recognize_meter_reading_with_barcode(image_array)
            return serial_number, meter_reading
        except Exception as e:
            logger.error(f"Ошибка обработки изображения из массива: {e}")
            return None, None
