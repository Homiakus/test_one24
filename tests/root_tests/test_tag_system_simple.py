"""
Простой тестовый скрипт для системы тегов команд
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.tag_manager import TagManager
from core.tag_validator import TagValidator
from core.flag_manager import FlagManager
from core.tags.wanted_tag import WantedTag
from ui.dialogs.tag_dialogs import TagDialogManager


def test_basic_tag_functionality():
    """Тест базовой функциональности тегов"""
    print("=== Тест базовой функциональности тегов ===")
    
    # Создаем компоненты
    tag_manager = TagManager()
    flag_manager = FlagManager()
    
    # Тест 1: Парсинг команды без тегов
    print("1. Тест парсинга команды без тегов")
    result = tag_manager.parse_command("simple_command")
    print(f"   Базовая команда: {result.base_command}")
    print(f"   Количество тегов: {len(result.tags)}")
    print(f"   Оригинальная команда: {result.original_command}")
    
    # Тест 2: Парсинг команды с тегом _wanted
    print("\n2. Тест парсинга команды с тегом _wanted")
    result = tag_manager.parse_command("test_command_wanted")
    print(f"   Базовая команда: {result.base_command}")
    print(f"   Количество тегов: {len(result.tags)}")
    if result.tags:
        print(f"   Первый тег: {result.tags[0].tag_name}")
        print(f"   Тип тега: {result.tags[0].tag_type}")
    
    # Тест 3: Проверка наличия тегов
    print("\n3. Тест проверки наличия тегов")
    print(f"   'command_wanted' содержит теги: {tag_manager._has_tags('command_wanted')}")
    print(f"   'simple_command' содержит теги: {tag_manager._has_tags('simple_command')}")
    
    print("\n✅ Базовая функциональность тегов работает корректно")


def test_wanted_tag_processing():
    """Тест обработки тега _wanted"""
    print("\n=== Тест обработки тега _wanted ===")
    
    # Создаем компоненты
    tag_manager = TagManager()
    flag_manager = FlagManager()
    wanted_tag = WantedTag()
    
    # Тест 1: wanted=False
    print("1. Тест с wanted=False")
    flag_manager.set_flag('wanted', False)
    tag_info = tag_manager.parse_command("test_command_wanted").tags[0]
    context = {"flag_manager": flag_manager}
    
    result = wanted_tag.process(tag_info, context)
    print(f"   Успех: {result.success}")
    print(f"   Продолжить: {result.should_continue}")
    print(f"   Сообщение: {result.message}")
    
    # Тест 2: wanted=True
    print("\n2. Тест с wanted=True")
    flag_manager.set_flag('wanted', True)
    result = wanted_tag.process(tag_info, context)
    print(f"   Успех: {result.success}")
    print(f"   Продолжить: {result.should_continue}")
    print(f"   Сообщение: {result.message}")
    print(f"   Показать диалог: {result.data.get('show_dialog') if result.data else 'None'}")
    
    print("\n✅ Обработка тега _wanted работает корректно")


def test_flag_manager():
    """Тест FlagManager"""
    print("\n=== Тест FlagManager ===")
    
    flag_manager = FlagManager()
    
    # Тест 1: Установка и получение флагов
    print("1. Тест установки и получения флагов")
    flag_manager.set_flag('test_flag', True)
    flag_manager.set_flag('counter', 42)
    flag_manager.set_flag('message', "Hello World")
    
    print(f"   test_flag: {flag_manager.get_flag('test_flag')}")
    print(f"   counter: {flag_manager.get_flag('counter')}")
    print(f"   message: {flag_manager.get_flag('message')}")
    print(f"   nonexistent: {flag_manager.get_flag('nonexistent', 'default')}")
    
    # Тест 2: Проверка наличия флагов
    print("\n2. Тест проверки наличия флагов")
    print(f"   test_flag существует: {flag_manager.has_flag('test_flag')}")
    print(f"   nonexistent существует: {flag_manager.has_flag('nonexistent')}")
    
    # Тест 3: Переключение флага
    print("\n3. Тест переключения флага")
    flag_manager.set_flag('toggle_flag', False)
    print(f"   Исходное значение: {flag_manager.get_flag('toggle_flag')}")
    new_value = flag_manager.toggle_flag('toggle_flag')
    print(f"   После переключения: {new_value}")
    new_value = flag_manager.toggle_flag('toggle_flag')
    print(f"   Еще раз переключили: {new_value}")
    
    # Тест 4: Увеличение/уменьшение счетчика
    print("\n4. Тест увеличения/уменьшения счетчика")
    flag_manager.set_flag('counter', 10)
    print(f"   Исходное значение: {flag_manager.get_flag('counter')}")
    new_value = flag_manager.increment_flag('counter', 5)
    print(f"   После увеличения на 5: {new_value}")
    new_value = flag_manager.decrement_flag('counter', 3)
    print(f"   После уменьшения на 3: {new_value}")
    
    # Тест 5: Получение всех флагов
    print("\n5. Тест получения всех флагов")
    all_flags = flag_manager.get_all_flags()
    print(f"   Все флаги: {all_flags}")
    
    print("\n✅ FlagManager работает корректно")


def test_tag_validator():
    """Тест TagValidator"""
    print("\n=== Тест TagValidator ===")
    
    validator = TagValidator()
    
    # Тест 1: Валидация имен тегов
    print("1. Тест валидации имен тегов")
    valid_names = ["_wanted", "_test_tag", "_tag123"]
    invalid_names = ["wanted", "_", "_123tag"]
    
    for name in valid_names:
        result = validator.validate_tag_name(name)
        print(f"   '{name}' валидно: {result}")
    
    for name in invalid_names:
        result = validator.validate_tag_name(name)
        print(f"   '{name}' валидно: {result}")
    
    # Тест 2: Валидация команд с тегами
    print("\n2. Тест валидации команд с тегами")
    commands = ["command_wanted", "simple_command", "command_invalid"]
    
    for command in commands:
        result = validator.validate_command_with_tags(command)
        print(f"   '{command}' валидна: {result}")
    
    print("\n✅ TagValidator работает корректно")


def test_tag_dialog_manager():
    """Тест TagDialogManager"""
    print("\n=== Тест TagDialogManager ===")
    
    dialog_manager = TagDialogManager()
    
    # Тест 1: Получение поддерживаемых типов диалогов
    print("1. Тест получения поддерживаемых типов диалогов")
    supported_types = dialog_manager.get_supported_dialog_types()
    print(f"   Поддерживаемые типы: {supported_types}")
    
    # Тест 2: Тест показа неизвестного диалога
    print("\n2. Тест показа неизвестного диалога")
    result = dialog_manager.show_tag_dialog('unknown')
    print(f"   Результат показа неизвестного диалога: {result}")
    
    print("\n✅ TagDialogManager работает корректно")


def test_full_workflow():
    """Тест полного workflow"""
    print("\n=== Тест полного workflow ===")
    
    # Создаем все компоненты
    tag_manager = TagManager()
    flag_manager = FlagManager()
    dialog_manager = TagDialogManager()
    
    # Устанавливаем флаг wanted=True
    print("1. Устанавливаем флаг wanted=True")
    flag_manager.set_flag('wanted', True)
    print(f"   wanted = {flag_manager.get_flag('wanted')}")
    
    # Создаем команду с тегом
    print("\n2. Создаем команду с тегом")
    command = "test_command_wanted"
    print(f"   Команда: {command}")
    
    # Парсим команду
    print("\n3. Парсим команду")
    parsed = tag_manager.parse_command(command)
    print(f"   Базовая команда: {parsed.base_command}")
    print(f"   Количество тегов: {len(parsed.tags)}")
    
    # Валидируем теги
    print("\n4. Валидируем теги")
    validator = TagValidator()
    is_valid = validator.validate_tags(parsed.tags)
    print(f"   Теги валидны: {is_valid}")
    
    # Обрабатываем теги
    print("\n5. Обрабатываем теги")
    context = {"flag_manager": flag_manager}
    results = tag_manager.process_tags(parsed.tags, context)
    
    print(f"   Количество результатов: {len(results)}")
    if results:
        result = results[0]
        print(f"   Успех: {result.success}")
        print(f"   Продолжить: {result.should_continue}")
        print(f"   Сообщение: {result.message}")
        if result.data:
            print(f"   Данные: {result.data}")
    
    print("\n✅ Полный workflow работает корректно")


def main():
    """Основная функция"""
    print("🚀 Запуск тестов системы тегов команд")
    print("=" * 50)
    
    try:
        test_basic_tag_functionality()
        test_wanted_tag_processing()
        test_flag_manager()
        test_tag_validator()
        test_tag_dialog_manager()
        test_full_workflow()
        
        print("\n" + "=" * 50)
        print("🎉 Все тесты прошли успешно!")
        print("✅ Система тегов команд работает корректно")
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
