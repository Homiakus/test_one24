#!/usr/bin/env python3
"""
Тест интеграции UART системы с обработкой сигналов
"""
import sys
import time
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_uart_integration():
    """Тест интеграции UART системы"""
    print("🧪 Тестирование интеграции UART системы...")
    
    try:
        # Импортируем необходимые компоненты
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.serial_manager import SerialManager
        from core.flag_manager import FlagManager
        from config.config_loader import ConfigLoader
        
        print("✅ Импорты успешны")
        
        # Создаем компоненты
        print("1. Создание компонентов...")
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Создаем SerialManager с интеграцией SignalManager
        serial_manager = SerialManager(signal_manager=signal_manager)
        
        print("✅ Компоненты созданы")
        
        # Загружаем конфигурацию сигналов
        print("2. Загрузка конфигурации сигналов...")
        config_loader = ConfigLoader()
        signal_mappings = config_loader.get_signal_mappings()
        
        print(f"✅ Загружено {len(signal_mappings)} сигналов")
        for signal_name, mapping in signal_mappings.items():
            print(f"   - {signal_name} -> {mapping.variable_name} ({mapping.signal_type.value})")
        
        # Регистрируем сигналы
        print("3. Регистрация сигналов...")
        signal_manager.register_signals(signal_mappings)
        print("✅ Сигналы зарегистрированы")
        
        # Тестируем обработку входящих данных
        print("4. Тестирование обработки входящих данных...")
        
        # Тестовые данные в формате "SIGNAL:VALUE"
        test_data = [
            "TEMP:25.5",
            "STATUS:running",
            "ERROR:0",
            "PRESSURE:1.2",
            "MODE:auto",
            "INVALID:data"  # Невалидные данные
        ]
        
        processed_count = 0
        for data in test_data:
            try:
                result = signal_manager.process_incoming_data(data)
                if result and result.is_success:
                    print(f"   ✅ {data} -> {result.signal_name} = {result.value}")
                    processed_count += 1
                else:
                    print(f"   ❌ {data} -> не обработан")
            except Exception as e:
                print(f"   ❌ {data} -> ошибка: {e}")
        
        print(f"✅ Обработано {processed_count} из {len(test_data)} сигналов")
        
        # Проверяем обновление переменных в FlagManager
        print("5. Проверка обновления переменных...")
        for signal_name, mapping in signal_mappings.items():
            if mapping.variable_name in flag_manager.flags:
                value = flag_manager.get_flag(mapping.variable_name)
                print(f"   - {mapping.variable_name} = {value}")
        
        # Получаем статистику
        print("6. Получение статистики...")
        stats = signal_manager.get_statistics()
        print(f"   - Всего сигналов: {stats.get('total_signals', 0)}")
        print(f"   - Обработано: {stats.get('processed_signals', 0)}")
        print(f"   - Ошибок: {stats.get('errors', 0)}")
        
        print("\n🎉 Тест интеграции UART системы завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_processing():
    """Тест обработки сигналов"""
    print("\n🧪 Тестирование обработки сигналов...")
    
    try:
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from core.signal_types import SignalType
        
        # Создаем компоненты
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        # Тестируем различные форматы данных
        test_cases = [
            ("TEMP:25.5", "TEMP", "temperature", SignalType.FLOAT, 25.5),
            ("STATUS:running", "STATUS", "device_status", SignalType.STRING, "running"),
            ("ERROR:0", "ERROR", "error_code", SignalType.INT, 0),
            ("PRESSURE:1.2", "PRESSURE", "pressure", SignalType.FLOAT, 1.2),
            ("MODE:auto", "MODE", "operation_mode", SignalType.STRING, "auto"),
        ]
        
        success_count = 0
        for data, expected_signal, expected_var, expected_type, expected_value in test_cases:
            try:
                result = signal_manager.process_incoming_data(data)
                if (result and result.is_success and 
                    result.signal_name == expected_signal and
                    result.variable_name == expected_var and
                    result.signal_type == expected_type and
                    result.value == expected_value):
                    print(f"   ✅ {data} -> {result.signal_name} = {result.value}")
                    success_count += 1
                else:
                    print(f"   ❌ {data} -> неверный результат")
            except Exception as e:
                print(f"   ❌ {data} -> ошибка: {e}")
        
        print(f"✅ Успешно обработано {success_count} из {len(test_cases)} тестовых случаев")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработки сигналов: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов интеграции UART системы...")
    
    # Тест интеграции
    integration_success = test_uart_integration()
    
    # Тест обработки сигналов
    processing_success = test_signal_processing()
    
    # Итоговый результат
    if integration_success and processing_success:
        print("\n🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n❌ Некоторые тесты не прошли")
        sys.exit(1)
