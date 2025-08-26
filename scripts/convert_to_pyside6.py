#!/usr/bin/env python3
"""
Скрипт для конвертации PyQt6 импортов на PySide6
Заменяет все импорты PyQt6 на соответствующие PySide6
"""

import os
import re
from pathlib import Path

def convert_file(file_path: Path) -> bool:
    """Конвертирует один файл с PyQt6 на PySide6"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Заменяем импорты PyQt6 на PySide6
        content = re.sub(r'from PyQt6\.', 'from PySide6.', content)
        content = re.sub(r'import PyQt6', 'import PySide6', content)
        
        # Заменяем pyqtSignal на Signal
        content = re.sub(r'pyqtSignal', 'Signal', content)
        
        # Заменяем pyqtSlot на Slot
        content = re.sub(r'pyqtSlot', 'Slot', content)
        
        # Заменяем pyqtProperty на Property
        content = re.sub(r'pyqtProperty', 'Property', content)
        
        # Если содержимое изменилось, записываем файл
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Конвертирован: {file_path}")
            return True
        else:
            print(f"- Без изменений: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка конвертации {file_path}: {e}")
        return False

def main():
    """Основная функция конвертации"""
    project_root = Path(__file__).parent.parent
    
    # Папки для конвертации
    folders_to_convert = [
        'ui',
        'core',
        'utils',
        'tests',
        'main.py',
        'main_modern.py'
    ]
    
    converted_count = 0
    total_files = 0
    
    for folder_name in folders_to_convert:
        folder_path = project_root / folder_name
        
        if folder_path.is_file():
            # Это файл
            if convert_file(folder_path):
                converted_count += 1
            total_files += 1
        elif folder_path.is_dir():
            # Это папка
            for file_path in folder_path.rglob('*.py'):
                if convert_file(file_path):
                    converted_count += 1
                total_files += 1
    
    print(f"\nКонвертация завершена!")
    print(f"Всего файлов: {total_files}")
    print(f"Конвертировано: {converted_count}")
    print(f"Без изменений: {total_files - converted_count}")

if __name__ == "__main__":
    main()
