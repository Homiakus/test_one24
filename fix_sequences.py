#!/usr/bin/env python3
"""
Исправление последовательностей в MOTTO конфигурации

Заменяет старые имена команд на новые нормализованные имена
"""

import tomli
import tomli_w
from pathlib import Path


def normalize_command_name(button_name: str) -> str:
    """Нормализация имени команды"""
    # Убираем специальные символы и пробелы
    name = button_name.replace(' ', '_').replace('→', '_').replace('(', '').replace(')', '').lower()
    while '__' in name:
        name = name.replace('__', '_')
    name = name.rstrip('_')
    
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
        name = name.replace(ru, en)
    
    return name


def fix_sequences():
    """Исправление последовательностей"""
    print("Загрузка MOTTO конфигурации...")
    with open('config_motto.toml', 'rb') as f:
        config = tomli.load(f)
    
    print("Получение карты команд...")
    # Создаём карту старых имён на новые
    command_map = {}
    for old_name, command in config['commands'].items():
        # Находим оригинальное имя из старого config.toml
        with open('config.toml', 'rb') as f:
            old_config = tomli.load(f)
        
        for original_name, original_command in old_config['buttons'].items():
            if original_command == command:
                command_map[original_name] = old_name
                break
    
    print(f"Найдено {len(command_map)} соответствий команд")
    
    # Исправляем последовательности
    print("Исправление последовательностей...")
    for seq_name, seq_data in config['sequences'].items():
        if 'steps' in seq_data:
            old_steps = seq_data['steps']
            new_steps = []
            
            for step in old_steps:
                if step.startswith('wait '):
                    new_steps.append(step)
                elif step in command_map:
                    new_steps.append(command_map[step])
                else:
                    # Пробуем нормализовать
                    normalized = normalize_command_name(step)
                    if normalized in config['commands']:
                        new_steps.append(normalized)
                    else:
                        new_steps.append(step)
            
            config['sequences'][seq_name]['steps'] = new_steps
            print(f"  {seq_name}: {len(old_steps)} -> {len(new_steps)} шагов")
    
    # Сохраняем исправленную конфигурацию
    print("Сохранение исправленной конфигурации...")
    with open('config_motto_fixed.toml', 'wb') as f:
        tomli_w.dump(config, f)
    
    print("✅ Конфигурация исправлена и сохранена в config_motto_fixed.toml")
    
    # Показываем пример исправления
    print("\n=== ПРИМЕР ИСПРАВЛЕНИЯ ===")
    og_seq = config['sequences']['og']
    print("Последовательность 'og':")
    print("  steps:", og_seq['steps'])
    print("  policy:", og_seq['policy'])
    print("  guards:", og_seq['guards'])


if __name__ == '__main__':
    fix_sequences()