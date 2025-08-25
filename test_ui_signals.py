#!/usr/bin/env python3
"""
Тест UI компонентов страницы сигналов
"""
import sys
import time
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_signals_page_ui():
    """Тест UI компонентов страницы сигналов"""
    print("🧪 Тестирование UI компонентов страницы сигналов...")
    
    try:
        # Импортируем необходимые компоненты
        from PySide6.QtWidgets import QApplication
        from ui.pages.signals_page import SignalsPage
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        from config.config_loader import ConfigLoader
        
        print("✅ Импорты успешны")
        
        # Создаем QApplication
        app = QApplication(sys.argv)
        print("✅ QApplication создан")
        
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
        config_loader = ConfigLoader()
        
        print("✅ Компоненты созданы")
        
        # Создаем страницу сигналов
        print("2. Создание страницы сигналов...")
        signals_page = SignalsPage(signal_manager, flag_manager, config_loader)
        signals_page.show()
        print("✅ Страница сигналов создана и отображена")
        
        # Тестируем обработку сигналов
        print("3. Тестирование обработки сигналов...")
        
        # Симулируем получение сигналов
        test_signals = [
            ("TEMP", "temperature", "25.5"),
            ("STATUS", "device_status", "running"),
            ("ERROR", "error_code", "0"),
            ("PRESSURE", "pressure", "1.2"),
            ("MODE", "operation_mode", "auto")
        ]
        
        for signal_name, variable_name, value in test_signals:
            signals_page.on_signal_processed(signal_name, variable_name, value)
            print(f"   ✅ Сигнал обработан: {signal_name} -> {variable_name} = {value}")
            time.sleep(0.5)  # Небольшая задержка для визуализации
        
        print("✅ Все сигналы обработаны")
        
        # Запускаем приложение на короткое время
        print("4. Запуск приложения на 5 секунд...")
        QTimer = app.__class__.processEvents
        start_time = time.time()
        
        while time.time() - start_time < 5:
            app.processEvents()
            time.sleep(0.1)
        
        print("✅ Приложение запущено и протестировано")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования UI: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_config_widget():
    """Тест виджета конфигурации сигналов"""
    print("\n🧪 Тестирование виджета конфигурации сигналов...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.pages.signals_page import SignalConfigWidget
        from config.config_loader import ConfigLoader
        
        # Создаем QApplication если еще не создан
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Создаем компоненты
        config_loader = ConfigLoader()
        config_widget = SignalConfigWidget(config_loader)
        config_widget.show()
        
        print("✅ Виджет конфигурации создан и отображен")
        
        # Запускаем на короткое время
        start_time = time.time()
        while time.time() - start_time < 3:
            app.processEvents()
            time.sleep(0.1)
        
        print("✅ Виджет конфигурации протестирован")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования виджета конфигурации: {e}")
        return False

def test_signal_monitor_widget():
    """Тест виджета мониторинга сигналов"""
    print("\n🧪 Тестирование виджета мониторинга сигналов...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.pages.signals_page import SignalMonitorWidget
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        from core.flag_manager import FlagManager
        
        # Создаем QApplication если еще не создан
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Создаем компоненты
        flag_manager = FlagManager()
        signal_processor = SignalProcessor()
        signal_validator = SignalValidator()
        signal_manager = SignalManager(
            processor=signal_processor,
            validator=signal_validator,
            flag_manager=flag_manager
        )
        
        monitor_widget = SignalMonitorWidget(signal_manager, flag_manager)
        monitor_widget.show()
        
        print("✅ Виджет мониторинга создан и отображен")
        
        # Симулируем сигналы
        test_signals = [
            ("TEMP", "temperature", "25.5"),
            ("STATUS", "device_status", "running"),
            ("ERROR", "error_code", "0")
        ]
        
        for signal_name, variable_name, value in test_signals:
            monitor_widget.add_log_entry(signal_name, variable_name, value)
            print(f"   ✅ Лог добавлен: {signal_name} -> {variable_name} = {value}")
            time.sleep(0.5)
        
        # Запускаем на короткое время
        start_time = time.time()
        while time.time() - start_time < 3:
            app.processEvents()
            time.sleep(0.1)
        
        print("✅ Виджет мониторинга протестирован")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования виджета мониторинга: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов UI компонентов страницы сигналов...")
    
    # Тест основной страницы
    main_test_success = test_signals_page_ui()
    
    # Тест виджета конфигурации
    config_test_success = test_signal_config_widget()
    
    # Тест виджета мониторинга
    monitor_test_success = test_signal_monitor_widget()
    
    # Итоговый результат
    if main_test_success and config_test_success and monitor_test_success:
        print("\n🎉 Все UI тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n❌ Некоторые UI тесты не прошли")
        sys.exit(1)
