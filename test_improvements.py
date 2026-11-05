"""Тестовый скрипт для проверки улучшений OCR:
- vertical morph close
- dilation для тонких линий
- lang='rus' fallback
- context-aware post-processing
"""
import sys
import os
sys.path.insert(0, r'C:\Users\Igor\GasMeterReader')

from ocr_processor import OCRProcessor
import cv2

def test_image(path, prev_reading=None):
    print(f"\n{'='*60}")
    print(f"Тест: {os.path.basename(path)}")
    print(f"{'='*60}")
    
    proc = OCRProcessor()
    proc.last_reading = prev_reading  # Устанавливаем предыдущее показание
    
    img = cv2.imread(path)
    if img is None:
        print(f"❌ Не удалось загрузить: {path}")
        return None
    
    serial, reading = proc.process_image(path)
    
    print(f"\nРезультат:")
    print(f"  Серийный номер: {serial}")
    print(f"  Показание: {reading}")
    
    return reading

if __name__ == '__main__':
    test_files = [
        r'C:\Users\Igor\test_meter.png',
        r'C:\Users\Igor\test_meter2.png',
    ]
    
    results = {}
    for f in test_files:
        r = test_image(f)
        results[os.path.basename(f)] = r
    
    print(f"\n{'='*60}")
    print(f"ИТОГ:")
    print(f"{'='*60}")
    for name, reading in results.items():
        print(f"  {name}: {reading}")
