#!/usr/bin/env python3
"""
Создание MOTTO конфигурации с нуля

Создаёт полную MOTTO v1.1 конфигурацию на основе существующего config.toml
"""

import sys
import tomli
import tomli_w
from pathlib import Path


def create_motto_config(input_file: str, output_file: str = None) -> bool:
    """
    Создание MOTTO конфигурации с нуля
    
    Args:
        input_file: Путь к входному файлу config.toml
        output_file: Путь к выходному файлу
        
    Returns:
        True при успешном создании
    """
    try:
        # Загружаем исходную конфигурацию
        print(f"Загрузка конфигурации из {input_file}...")
        with open(input_file, 'rb') as f:
            v1_config = tomli.load(f)
        
        print("✓ Конфигурация v1.0 загружена успешно")
        
        # Определяем имя выходного файла
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.parent / f"{input_path.stem}_motto.toml"
        
        # Создаём MOTTO конфигурацию с нуля
        print("Создание MOTTO конфигурации...")
        
        motto_config = {
            'version': '1.1',
            
            # Глобальные переменные
            'vars': {
                'plant': 'LAB-01',
                'line': 'stain-processor',
                'operator': 'auto',
                'default_port': v1_config.get('serial_default', {}).get('port', 'COM4'),
                'default_baudrate': v1_config.get('serial_default', {}).get('baudrate', 115200)
            },
            
            # Профили конфигурации
            'profiles': {
                'default': {
                    'name': 'default',
                    'extends': '',
                    'env': {
                        'port': v1_config.get('serial_default', {}).get('port', 'COM4'),
                        'baudrate': v1_config.get('serial_default', {}).get('baudrate', 115200),
                        'timeout': v1_config.get('serial_default', {}).get('timeout', 1.0),
                        'safety_mode': 'normal',
                        'max_retries': 3
                    },
                    'metadata': {}
                }
            },
            
            # Контексты выполнения
            'contexts': {
                'run_env': {
                    'name': 'run_env',
                    'zones': '0010',
                    'operator': 'auto',
                    'safety_mode': 'normal',
                    'metadata': {}
                }
            },
            
            # Условия для проверки
            'conditions': {
                'no_alarms': {
                    'name': 'no_alarms',
                    'expr': 'status("alarm") == 0',
                    'description': 'Проверка отсутствия аварий',
                    'metadata': {}
                },
                'serial_connected': {
                    'name': 'serial_connected',
                    'expr': 'status("serial") == "connected"',
                    'description': 'Проверка подключения к UART',
                    'metadata': {}
                },
                'temp_safe': {
                    'name': 'temp_safe',
                    'expr': 'sensor("temp.C") >= 5 and sensor("temp.C") <= 60',
                    'description': 'Проверка безопасной температуры',
                    'metadata': {}
                },
                'pressure_safe': {
                    'name': 'pressure_safe',
                    'expr': 'sensor("press.kPa") >= 30 and sensor("press.kPa") <= 300',
                    'description': 'Проверка безопасного давления',
                    'metadata': {}
                },
                'movement_complete': {
                    'name': 'movement_complete',
                    'expr': 'status("movement") == "complete"',
                    'description': 'Проверка завершения движения',
                    'metadata': {}
                },
                'pump_ready': {
                    'name': 'pump_ready',
                    'expr': 'status("pump") == "ready"',
                    'description': 'Проверка готовности насоса',
                    'metadata': {}
                }
            },
            
            # Гварды для проверки условий
            'guards': {
                'no_alarms': {
                    'name': 'no_alarms',
                    'when': 'pre',
                    'condition': 'no_alarms',
                    'on_fail': {'action': 'abort', 'reason': 'Active alarms detected'},
                    'description': 'Проверка отсутствия аварий перед выполнением',
                    'metadata': {}
                },
                'serial_connected': {
                    'name': 'serial_connected',
                    'when': 'pre',
                    'condition': 'serial_connected',
                    'on_fail': {'action': 'retry', 'max_attempts': 3, 'cooldown_ms': 1000},
                    'description': 'Проверка подключения к UART',
                    'metadata': {}
                },
                'temp_safe': {
                    'name': 'temp_safe',
                    'when': 'pre',
                    'condition': 'temp_safe',
                    'on_fail': {'action': 'cooldown_then_retry', 'cooldown_ms': 5000, 'max_attempts': 3},
                    'description': 'Проверка безопасной температуры',
                    'metadata': {}
                },
                'pressure_safe': {
                    'name': 'pressure_safe',
                    'when': 'pre',
                    'condition': 'pressure_safe',
                    'on_fail': {'action': 'abort', 'reason': 'Pressure out of safe range'},
                    'description': 'Проверка безопасного давления',
                    'metadata': {}
                },
                'movement_complete': {
                    'name': 'movement_complete',
                    'when': 'post',
                    'condition': 'movement_complete',
                    'on_fail': {'action': 'retry', 'max_attempts': 2},
                    'description': 'Проверка завершения движения',
                    'metadata': {}
                },
                'pump_ready': {
                    'name': 'pump_ready',
                    'when': 'pre',
                    'condition': 'pump_ready',
                    'on_fail': {'action': 'wait', 'timeout_ms': 10000},
                    'description': 'Проверка готовности насоса',
                    'metadata': {}
                }
            },
            
            # Политики выполнения
            'policies': {
                'safe_retry': {
                    'name': 'safe_retry',
                    'retry_on': ['timeout', 'serial_error', 'movement_error'],
                    'max_attempts': 3,
                    'backoff': {'type': 'exponential', 'base_ms': 500, 'factor': 2.0, 'jitter': 'full'},
                    'step_timeout_ms': 60000,
                    'sequence_timeout_ms': 600000,
                    'metadata': {}
                },
                'fast_retry': {
                    'name': 'fast_retry',
                    'retry_on': ['timeout'],
                    'max_attempts': 2,
                    'backoff': {'type': 'linear', 'base_ms': 1000},
                    'step_timeout_ms': 30000,
                    'sequence_timeout_ms': 300000,
                    'metadata': {}
                }
            },
            
            # Ресурсы и мьютексы
            'resources': {
                'serial_port': {
                    'name': 'serial_port',
                    'type': 'mutex',
                    'members': ['COM3', 'COM4', 'COM5'],
                    'scope': 'machine',
                    'metadata': {}
                },
                'pump': {
                    'name': 'pump',
                    'type': 'mutex',
                    'members': ['pump_main'],
                    'scope': 'machine',
                    'metadata': {}
                },
                'valves': {
                    'name': 'valves',
                    'type': 'semaphore',
                    'capacity': 4,
                    'metadata': {}
                },
                'movement': {
                    'name': 'movement',
                    'type': 'mutex',
                    'members': ['multi', 'rright', 'clamp'],
                    'scope': 'machine',
                    'metadata': {}
                }
            },
            
            # События системы
            'events': {
                'estop': {
                    'name': 'estop',
                    'source': 'hardware',
                    'filter': 'status("estop") == 1',
                    'description': 'Аварийная остановка',
                    'metadata': {}
                },
                'overtemp': {
                    'name': 'overtemp',
                    'source': 'sensor',
                    'filter': 'sensor("temp.C") > 60',
                    'description': 'Перегрев',
                    'metadata': {}
                },
                'press_drop': {
                    'name': 'press_drop',
                    'source': 'sensor',
                    'filter': 'sensor("press.kPa") < 30 for 3s',
                    'description': 'Падение давления',
                    'metadata': {}
                },
                'serial_error': {
                    'name': 'serial_error',
                    'source': 'system',
                    'filter': 'status("serial") == "error"',
                    'description': 'Ошибка UART',
                    'metadata': {}
                },
                'movement_error': {
                    'name': 'movement_error',
                    'source': 'system',
                    'filter': 'status("movement") == "error"',
                    'description': 'Ошибка движения',
                    'metadata': {}
                }
            },
            
            # Обработчики событий
            'handlers': {
                'on_estop': {
                    'name': 'on_estop',
                    'on': 'estop',
                    'do': ['EMERGENCY_STOP', 'CLOSE_ALL_VALVES', 'POWER_OFF_PUMP'],
                    'priority': 100,
                    'description': 'Обработка аварийной остановки',
                    'metadata': {}
                },
                'on_overtemp': {
                    'name': 'on_overtemp',
                    'on': 'overtemp',
                    'do': ['POWER_OFF_HEATERS', 'OPEN_DRAIN', 'ALERT_OPERATOR'],
                    'priority': 80,
                    'description': 'Обработка перегрева',
                    'metadata': {}
                },
                'on_pressdrop': {
                    'name': 'on_pressdrop',
                    'on': 'press_drop',
                    'do': ['OPEN_DRAIN', 'CHECK_PUMP_STATUS', 'ALERT_OPERATOR'],
                    'priority': 70,
                    'description': 'Обработка падения давления',
                    'metadata': {}
                },
                'on_serial_error': {
                    'name': 'on_serial_error',
                    'on': 'serial_error',
                    'do': ['RECONNECT_SERIAL', 'RETRY_COMMAND'],
                    'priority': 50,
                    'description': 'Обработка ошибки UART',
                    'metadata': {}
                },
                'on_movement_error': {
                    'name': 'on_movement_error',
                    'on': 'movement_error',
                    'do': ['STOP_MOVEMENT', 'HOME_AXIS', 'RETRY_MOVEMENT'],
                    'priority': 60,
                    'description': 'Обработка ошибки движения',
                    'metadata': {}
                }
            },
            
            # Команды (преобразованы из buttons)
            'commands': {},
            
            # Последовательности команд
            'sequences': {},
            
            # Шаблоны для генерации
            'templates': {},
            
            # Юниты измерения
            'units': {
                'duration': ['ms', 's', 'min'],
                'temperature': ['C', 'K'],
                'pressure': ['kPa', 'bar'],
                'position': ['steps', 'mm', 'degrees']
            },
            
            # Валидаторы значений
            'validators': {
                'temp_work_range': {
                    'name': 'temp_work_range',
                    'key': 'sensor(temp.C)',
                    'range': {'min': 5, 'max': 60},
                    'description': 'Рабочий диапазон температуры',
                    'metadata': {}
                },
                'press_safe': {
                    'name': 'press_safe',
                    'key': 'sensor(press.kPa)',
                    'range': {'min': 30, 'max': 300},
                    'description': 'Безопасный диапазон давления',
                    'metadata': {}
                }
            },
            
            # Runtime конфигурация
            'runtime': {
                'profile': 'default',
                'start': 'load_tubes',
                'args': {}
            },
            
            # Настройки аудита
            'audit': {
                'log_level': 'info',
                'trace_context': True,
                'snapshots': 'on_error',
                'metrics_enabled': True
            }
        }
        
        # Конвертируем команды из buttons
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
        
        motto_config['commands'] = commands
        
        # Конвертируем последовательности
        sequences = {}
        for seq_name, steps in v1_config.get('sequences', {}).items():
            if isinstance(steps, list):
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
                
                # Создаём последовательность
                sequences[seq_name] = {
                    'name': seq_name,
                    'description': f'Последовательность {seq_name}',
                    'type': 'sequence',
                    'steps': converted_steps,
                    'policy': 'safe_retry',
                    'guards': ['no_alarms', 'serial_connected'],
                    'post_checks': ['movement_complete'],
                    'metadata': {}
                }
        
        motto_config['sequences'] = sequences
        
        # Сохраняем совместимость с v1.0
        if 'serial_default' in v1_config:
            motto_config['serial_default'] = v1_config['serial_default']
        
        if 'wizard' in v1_config:
            motto_config['wizard'] = v1_config['wizard']
        
        # Сохраняем конфигурацию
        print(f"Сохранение MOTTO конфигурации в {output_file}...")
        with open(output_file, 'wb') as f:
            tomli_w.dump(motto_config, f)
        
        print("✓ MOTTO конфигурация сохранена успешно")
        
        # Выводим статистику
        print("\n📊 Статистика создания:")
        print(f"  • Команд: {len(commands)}")
        print(f"  • Последовательностей: {len(sequences)}")
        print(f"  • Условий: {len(motto_config['conditions'])}")
        print(f"  • Гвардов: {len(motto_config['guards'])}")
        print(f"  • Политик: {len(motto_config['policies'])}")
        print(f"  • Ресурсов: {len(motto_config['resources'])}")
        print(f"  • Событий: {len(motto_config['events'])}")
        print(f"  • Обработчиков: {len(motto_config['handlers'])}")
        
        print(f"\n✅ MOTTO конфигурация создана успешно!")
        print(f"📁 Исходный файл: {input_file}")
        print(f"📁 MOTTO файл: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование: python create_motto_config.py <input_file> [output_file]")
        print("")
        print("Примеры:")
        print("  python create_motto_config.py config.toml")
        print("  python create_motto_config.py config.toml config_motto.toml")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        return 1
    
    success = create_motto_config(input_file, output_file)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())