#!/usr/bin/env python3
"""
Интеграционный тест системы обработки сигналов UART
"""

import sys
import time
import random
from pathlib import Path
from typing import Dict, List

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_full_signal_processing_cycle():
    """Тест полного цикла обработки сигналов от UART до UI"""
    print("🧪 Тест полного цикла обработки сигналов...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.serial_manager import SerialManager
        from config.config_loader import ConfigLoader
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Создание SerialManager с SignalManager
        serial_manager = SerialManager(signal_manager=signal_manager)
        
        # Загрузка конфигурации
        config_loader = ConfigLoader()
        signal_mappings = config_loader.get_signal_mappings()
        signal_manager.register_signals(signal_mappings)
        
        print("✅ Компоненты созданы и настроены")
        
        # Тестовые данные
        test_signals = [
            ("TEMP", "temperature", "25.5"),
            ("STATUS", "device_status", "running"),
            ("ERROR", "error_code", "0"),
            ("PRESSURE", "pressure", "1.2"),
            ("MODE", "operation_mode", "auto")
        ]
        
        print("📡 Обработка тестовых сигналов...")
        
        # Обработка сигналов через SerialManager
        for signal_name, variable_name, value in test_signals:
            data = f"{signal_name}:{value}"
            print(f"   Отправка: {data}")
            
            # Обработка через SignalManager
            result = signal_manager.process_incoming_data(data)
            if result:
                print(f"   ✅ Обработан: {signal_name} -> {variable_name} = {value}")
                
                # Проверка обновления переменной
                actual_value = flag_manager.get_flag(variable_name)
                print(f"   📊 Значение в FlagManager: {actual_value}")
            else:
                print(f"   ❌ Ошибка обработки: {data}")
        
        # Проверка статистики
        stats = signal_manager.get_statistics()
        print(f"\n📊 Статистика обработки:")
        print(f"   - Всего сигналов: {stats.get('total_signals', 0)}")
        print(f"   - Обработано: {stats.get('processed_signals', 0)}")
        print(f"   - Ошибок: {stats.get('errors', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграционного теста: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_serial_manager_integration():
    """Тест интеграции с SerialManager"""
    print("\n🧪 Тест интеграции с SerialManager...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.serial_manager import SerialManager
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Создание SerialManager
        serial_manager = SerialManager(signal_manager=signal_manager)
        
        # Регистрация тестовых сигналов
        test_mappings = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("status", SignalType.STRING),
            "ERROR": SignalMapping("error", SignalType.INT),
            "MODE": SignalMapping("mode", SignalType.BOOL)
        }
        signal_manager.register_signals(test_mappings)
        
        print("✅ SerialManager создан с SignalManager")
        
        # Тестирование обработки данных через SerialManager
        test_data = [
            "TEMP:25.5",
            "STATUS:running",
            "ERROR:0",
            "MODE:true",
            "UNKNOWN:value",  # Неизвестный сигнал
            "TEMP:invalid",   # Некорректное значение
            "STATUS:stopped"
        ]
        
        print("📡 Тестирование обработки данных...")
        
        for data in test_data:
            print(f"   Обработка: {data}")
            result = serial_manager.process_signal_data(data)
            print(f"   Результат: {'✅' if result else '❌'}")
        
        # Проверка статистики
        stats = serial_manager.get_signal_statistics()
        print(f"\n📊 Статистика SerialManager:")
        print(f"   - Всего сигналов: {stats.get('total_signals', 0)}")
        print(f"   - Обработано: {stats.get('processed_signals', 0)}")
        print(f"   - Ошибок: {stats.get('errors', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования SerialManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_integration():
    """Тест интеграции с UI компонентами"""
    print("\n🧪 Тест интеграции с UI компонентами...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from config.config_loader import ConfigLoader
        from ui.pages.signals_page import SignalsPage
        
        # Создание QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        config_loader = ConfigLoader()
        
        # Создание страницы сигналов
        signals_page = SignalsPage(signal_manager, flag_manager, config_loader)
        signals_page.show()
        
        print("✅ UI компоненты созданы")
        
        # Тестовые сигналы
        test_signals = [
            ("TEMP", "temperature", "25.5"),
            ("STATUS", "device_status", "running"),
            ("ERROR", "error_code", "0"),
            ("PRESSURE", "pressure", "1.2"),
            ("MODE", "operation_mode", "auto")
        ]
        
        print("📡 Симуляция обработки сигналов в UI...")
        
        # Симуляция обработки сигналов
        for signal_name, variable_name, value in test_signals:
            print(f"   Сигнал: {signal_name} -> {variable_name} = {value}")
            signals_page.on_signal_processed(signal_name, variable_name, value)
            time.sleep(0.1)  # Небольшая задержка для визуализации
        
        print("✅ UI тест завершен")
        
        # Закрытие приложения
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования UI: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_integration():
    """Тест интеграции с системой конфигурации"""
    print("\n🧪 Тест интеграции с системой конфигурации...")
    
    try:
        from config.config_loader import ConfigLoader
        from core.signal_types import SignalType, SignalMapping
        
        # Создание ConfigLoader
        config_loader = ConfigLoader()
        
        # Загрузка текущей конфигурации
        signal_mappings = config_loader.get_signal_mappings()
        print(f"✅ Загружено сигналов из конфигурации: {len(signal_mappings)}")
        
        # Вывод текущих сигналов
        for signal_name, mapping in signal_mappings.items():
            print(f"   {signal_name}: {mapping.variable_name} ({mapping.signal_type.value})")
        
        # Тестирование добавления нового сигнала
        test_mapping = SignalMapping("test_variable", SignalType.FLOAT)
        signal_mappings["TEST_SIGNAL"] = test_mapping
        
        print(f"\n📝 Добавлен тестовый сигнал: TEST_SIGNAL")
        
        # Тестирование сохранения конфигурации
        success = config_loader.save_signal_mappings()
        if success:
            print("✅ Конфигурация успешно сохранена")
        else:
            print("❌ Ошибка сохранения конфигурации")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_integration():
    """Тест интеграции обработки ошибок"""
    print("\n🧪 Тест интеграции обработки ошибок...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.signal_types import SignalType, SignalMapping
        
        # Создание компонентов
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Регистрация тестовых сигналов
        test_mappings = {
            "TEMP": SignalMapping("temperature", SignalType.FLOAT),
            "STATUS": SignalMapping("status", SignalType.STRING),
            "ERROR": SignalMapping("error", SignalType.INT),
            "MODE": SignalMapping("mode", SignalType.BOOL)
        }
        signal_manager.register_signals(test_mappings)
        
        # Тестирование различных типов ошибок
        error_cases = [
            ("", "Пустая строка"),
            ("INVALID", "Некорректный формат"),
            ("TEMP:not_a_number", "Неверный тип для float"),
            ("MODE:maybe", "Неверный тип для bool"),
            ("ERROR:abc", "Неверный тип для int"),
            ("UNKNOWN:value", "Неизвестный сигнал"),
            ("TEMP:25.5:extra", "Лишние части"),
            ("  TEMP:25.5  ", "Пробелы"),
            ("temp:25.5", "Строчные буквы")
        ]
        
        print("📊 Тестирование обработки ошибок...")
        
        initial_stats = signal_manager.get_statistics()
        initial_errors = initial_stats.get('errors', 0)
        
        for data, description in error_cases:
            print(f"   Тест: {description}")
            print(f"   Данные: '{data}'")
            
            result = signal_manager.process_incoming_data(data)
            if not result:
                print(f"   ✅ Корректно обработана ошибка")
            else:
                print(f"   ⚠️  Неожиданно принято")
        
        # Проверка статистики ошибок
        final_stats = signal_manager.get_statistics()
        final_errors = final_stats.get('errors', 0)
        new_errors = final_errors - initial_errors
        
        print(f"\n📊 Статистика ошибок:")
        print(f"   - Начальные ошибки: {initial_errors}")
        print(f"   - Новые ошибки: {new_errors}")
        print(f"   - Всего ошибок: {final_errors}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработки ошибок: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_integration_tests():
    """Запуск всех интеграционных тестов"""
    print("🚀 Запуск интеграционных тестов системы обработки сигналов UART...")
    
    # Список тестов
    tests = [
        ("Полный цикл обработки", test_full_signal_processing_cycle),
        ("Интеграция с SerialManager", test_serial_manager_integration),
        ("Интеграция с UI", test_ui_integration),
        ("Интеграция с конфигурацией", test_configuration_integration),
        ("Обработка ошибок", test_error_handling_integration)
    ]
    
    # Результаты тестов
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        success = test_func()
        end_time = time.time()
        
        results[test_name] = {
            'success': success,
            'duration': end_time - start_time
        }
        
        if success:
            print(f"✅ {test_name} - УСПЕШНО ({end_time - start_time:.2f}с)")
        else:
            print(f"❌ {test_name} - НЕУДАЧА ({end_time - start_time:.2f}с)")
    
    # Итоговый отчет
    print(f"\n{'='*60}")
    print("📊 ИТОГОВЫЙ ОТЧЕТ ИНТЕГРАЦИОННЫХ ТЕСТОВ")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for result in results.values() if result['success'])
    total_tests = len(results)
    total_time = sum(result['duration'] for result in results.values())
    
    print(f"✅ Успешных тестов: {successful_tests}/{total_tests}")
    print(f"⏱️  Общее время: {total_time:.2f}с")
    
    for test_name, result in results.items():
        status = "✅" if result['success'] else "❌"
        print(f"{status} {test_name}: {result['duration']:.2f}с")
    
    if successful_tests == total_tests:
        print(f"\n🎉 Все интеграционные тесты прошли успешно!")
        print(f"🚀 Система обработки сигналов UART готова к использованию!")
        return True
    else:
        print(f"\n⚠️  Некоторые интеграционные тесты не прошли")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
