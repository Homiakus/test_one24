#!/usr/bin/env python3
"""
Упрощённый скрипт миграции config.toml в MOTTO формат

Использует готовый шаблон config_motto.toml и адаптирует его под существующую конфигурацию.
"""

import sys
import tomli
import tomli_w
from pathlib import Path


def migrate_config_simple(input_file: str, output_file: str = None) -> bool:
    """
    Простая миграция конфигурации
    
    Args:
        input_file: Путь к входному файлу config.toml
        output_file: Путь к выходному файлу
        
    Returns:
        True при успешной миграции
    """
    try:
        # Загружаем исходную конфигурацию
        print(f"Загрузка конфигурации из {input_file}...")
        with open(input_file, 'rb') as f:
            v1_config = tomli.load(f)
        
        print("✓ Конфигурация v1.0 загружена успешно")
        
        # Загружаем шаблон MOTTO
        print("Загрузка шаблона MOTTO...")
        with open('config_motto.toml', 'rb') as f:
            motto_template = tomli.load(f)
        
        print("✓ Шаблон MOTTO загружен успешно")
        
        # Определяем имя выходного файла
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_motto.toml"
        
        # Адаптируем шаблон под существующую конфигурацию
        print("Адаптация под существующую конфигурацию...")
        
        # Обновляем переменные
        motto_template['vars']['default_port'] = v1_config.get('serial_default', {}).get('port', 'COM4')
        motto_template['vars']['default_baudrate'] = v1_config.get('serial_default', {}).get('baudrate', 115200)
        
        # Обновляем профили
        if 'env' not in motto_template['profiles']['default']:
            motto_template['profiles']['default']['env'] = {}
        motto_template['profiles']['default']['env']['port'] = v1_config.get('serial_default', {}).get('port', 'COM4')
        motto_template['profiles']['default']['env']['baudrate'] = v1_config.get('serial_default', {}).get('baudrate', 115200)
        motto_template['profiles']['default']['env']['timeout'] = v1_config.get('serial_default', {}).get('timeout', 1.0)
        
        # Добавляем команды из buttons
        commands = {}
        for button_name, command in v1_config.get('buttons', {}).items():
            # Нормализуем имя команды
            command_name = button_name.replace(' ', '_').replace('→', '_').replace('(', '').replace(')', '').lower()
            while '__' in command_name:
                command_name = command_name.replace('__', '_')
            command_name = command_name.rstrip('_')
            
            # Заменяем русские слова
            replacements = {
                'multi': 'multi',
                'rright': 'rright',
                'clamp': 'clamp',
                'kl1': 'kl1',
                'kl2': 'kl2',
                'насос': 'pump',
                'хоминг': 'home',
                'слив': 'drain',
                'экспозиция': 'exposure',
                'верх': 'up',
                'загрузка_пробирок': 'load_tubes',
                'извлечение_пробирок': 'extract_tubes',
                'предноль': 'pre_zero',
                'сжать': 'close',
                'разжать': 'open',
                'включить': 'on',
                'выключить': 'off',
                'продувка': 'flush',
                'тестовая_команда': 'test_command',
                'статус_системы': 'system_status'
            }
            
            for ru, en in replacements.items():
                command_name = command_name.replace(ru, en)
            
            commands[command_name] = command
        
        motto_template['commands'] = commands
        
        # Обновляем последовательности
        for seq_name, steps in v1_config.get('sequences', {}).items():
            if seq_name in motto_template['sequences']:
                # Конвертируем шаги
                converted_steps = []
                for step in steps:
                    if step.startswith('wait '):
                        converted_steps.append(step)
                    else:
                        # Ищем соответствующую команду
                        found_command = None
                        for cmd_name, cmd_value in commands.items():
                            if step in cmd_value or cmd_value in step:
                                found_command = cmd_name
                                break
                        
                        if found_command:
                            converted_steps.append(found_command)
                        else:
                            converted_steps.append(step)
                
                motto_template['sequences'][seq_name]['steps'] = converted_steps
        
        # Сохраняем совместимость с v1.0
        if 'serial_default' in v1_config:
            motto_template['serial_default'] = v1_config['serial_default']
        
        if 'wizard' in v1_config:
            motto_template['wizard'] = v1_config['wizard']
        
        # Сохраняем конфигурацию
        print(f"Сохранение MOTTO конфигурации в {output_file}...")
        with open(output_file, 'wb') as f:
            tomli_w.dump(motto_template, f)
        
        print("✓ MOTTO конфигурация сохранена успешно")
        
        # Выводим статистику
        print("\n📊 Статистика миграции:")
        print(f"  • Команд: {len(commands)}")
        print(f"  • Последовательностей: {len(v1_config.get('sequences', {}))}")
        print(f"  • Условий: {len(motto_template.get('conditions', {}))}")
        print(f"  • Гвардов: {len(motto_template.get('guards', {}))}")
        print(f"  • Политик: {len(motto_template.get('policies', {}))}")
        print(f"  • Ресурсов: {len(motto_template.get('resources', {}))}")
        print(f"  • Событий: {len(motto_template.get('events', {}))}")
        print(f"  • Обработчиков: {len(motto_template.get('handlers', {}))}")
        
        print(f"\n✅ Миграция завершена успешно!")
        print(f"📁 Исходный файл: {input_file}")
        print(f"📁 MOTTO файл: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python migrate_simple.py <input_file> [output_file]")
        print("")
        print("Примеры:")
        print("  python migrate_simple.py config.toml")
        print("  python migrate_simple.py config.toml config_motto.toml")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        return 1
    
    if not Path('config_motto.toml').exists():
        print(f"❌ Файл config_motto.toml не найден (шаблон)")
        return 1
    
    success = migrate_config_simple(input_file, output_file)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())