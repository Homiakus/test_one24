#!/usr/bin/env python3
"""
Скрипт миграции config.toml в MOTTO формат

Автоматически конвертирует существующий config.toml в MOTTO v1.1 формат
с сохранением всей функциональности и добавлением новых возможностей.
"""

import sys
import tomli
import tomli_w
from pathlib import Path
from core.motto import CompatibilityAdapter


def migrate_config(input_file: str, output_file: str = None) -> bool:
    """
    Миграция конфигурации из v1.0 в v1.1
    
    Args:
        input_file: Путь к входному файлу config.toml
        output_file: Путь к выходному файлу (если None, создаётся автоматически)
        
    Returns:
        True при успешной миграции
    """
    try:
        # Загружаем исходную конфигурацию
        print(f"Загрузка конфигурации из {input_file}...")
        with open(input_file, 'rb') as f:
            v1_config = tomli.load(f)
        
        print("✓ Конфигурация v1.0 загружена успешно")
        
        # Создаём адаптер и конвертируем
        adapter = CompatibilityAdapter()
        print("Конвертация в MOTTO v1.1...")
        
        config = adapter.convert_v1_to_v1_1(v1_config)
        
        print("✓ Конфигурация конвертирована в MOTTO v1.1")
        
        # Определяем имя выходного файла
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_motto.toml"
        
        # Создаём словарь для сохранения
        config_dict = {
            'version': config.version,
            'vars': config.vars,
            'profiles': {name: profile for name, profile in config.profiles.items()},
            'conditions': {name: cond for name, cond in config.conditions.items()},
            'guards': {name: guard for name, guard in config.guards.items()},
            'policies': {name: policy for name, policy in config.policies.items()},
            'resources': {name: resource for name, resource in config.resources.items()},
            'events': {name: event for name, event in config.events.items()},
            'handlers': {name: handler for name, handler in config.handlers.items()},
            'units': config.units or {},
            'validators': {name: validator for name, validator in config.validators.items()},
            'runtime': config.runtime or {},
            'audit': config.audit or {}
        }
        
        # Добавляем команды
        commands = {}
        for button_name, command in v1_config.get('buttons', {}).items():
            command_name = adapter._normalize_command_name(button_name)
            commands[command_name] = command
        
        config_dict['commands'] = commands
        
        # Добавляем последовательности
        sequences_dict = {}
        for name, seq in config.sequences.items():
            sequences_dict[name] = {
                'name': seq.name,
                'description': seq.description,
                'type': str(seq.type),
                'steps': seq.steps,
                'policy': seq.policy,
                'guards': seq.guards,
                'post_checks': seq.post_checks
            }
        config_dict['sequences'] = sequences_dict
        
        # Добавляем совместимость с v1.0
        if 'serial_default' in v1_config:
            config_dict['serial_default'] = v1_config['serial_default']
        
        if 'wizard' in v1_config:
            config_dict['wizard'] = v1_config['wizard']
        
        # Сохраняем конфигурацию
        print(f"Сохранение MOTTO конфигурации в {output_file}...")
        with open(output_file, 'wb') as f:
            tomli_w.dump(config_dict, f)
        
        print("✓ MOTTO конфигурация сохранена успешно")
        
        # Выводим статистику
        print("\n📊 Статистика миграции:")
        print(f"  • Команд: {len(commands)}")
        print(f"  • Последовательностей: {len(config.sequences)}")
        print(f"  • Условий: {len(config.conditions)}")
        print(f"  • Гвардов: {len(config.guards)}")
        print(f"  • Политик: {len(config.policies)}")
        print(f"  • Ресурсов: {len(config.resources)}")
        print(f"  • Событий: {len(config.events)}")
        print(f"  • Обработчиков: {len(config.handlers)}")
        
        print(f"\n✅ Миграция завершена успешно!")
        print(f"📁 Исходный файл: {input_file}")
        print(f"📁 MOTTO файл: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python migrate_to_motto.py <input_file> [output_file]")
        print("")
        print("Примеры:")
        print("  python migrate_to_motto.py config.toml")
        print("  python migrate_to_motto.py config.toml config_motto.toml")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        return 1
    
    success = migrate_config(input_file, output_file)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())