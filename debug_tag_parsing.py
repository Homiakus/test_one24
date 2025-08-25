"""
Отладочный скрипт для проверки парсинга тегов
"""
import sys
import re
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.tag_types import TagType

def debug_parsing():
    """Отладка парсинга тегов"""
    print("=== Отладка парсинга тегов ===")
    
    # Тестируем регулярное выражение
    tag_pattern = re.compile(r'_([a-zA-Z][a-zA-Z0-9_]*)$')
    
    test_commands = [
        "simple_command",
        "test_command_wanted",
        "command_wanted_another",
        "og_multizone-test_command_wanted"
    ]
    
    for command in test_commands:
        print(f"\nКоманда: {command}")
        
        # Находим все совпадения
        matches = list(tag_pattern.finditer(command))
        print(f"  Найдено совпадений: {len(matches)}")
        
        for i, match in enumerate(matches):
            print(f"  Совпадение {i+1}:")
            print(f"    Полное совпадение: '{match.group(0)}'")
            print(f"    Группа 1: '{match.group(1)}'")
            print(f"    Позиция: {match.start()}-{match.end()}")
            
            # Проверяем, можно ли создать TagType
            tag_type_name = match.group(1)
            try:
                tag_type = TagType(tag_type_name)
                print(f"    TagType: {tag_type}")
            except ValueError as e:
                print(f"    Ошибка создания TagType: {e}")
    
    print("\n=== Тест извлечения базовой команды ===")
    
    command = "test_command_wanted"
    matches = list(tag_pattern.finditer(command))
    
    if matches:
        first_tag_start = matches[0].start()
        base_command = command[:first_tag_start]
        print(f"Команда: {command}")
        print(f"Позиция первого тега: {first_tag_start}")
        print(f"Базовая команда: '{base_command}'")
    else:
        print(f"В команде '{command}' не найдено тегов")

if __name__ == "__main__":
    debug_parsing()
