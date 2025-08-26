#!/usr/bin/env python3
"""
Полный тест системы мониторинга
"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Тест базовых импортов"""
    print("🔍 Тестируем базовые импорты...")
    
    try:
        from monitoring import MonitoringManager, AlertLevel
        from monitoring import PerformanceMonitor, ErrorAlerter, HealthChecker, UsageMetrics
        from utils.logger import Logger
        print("✅ Все базовые модули импортированы")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_logger_functionality():
    """Тест функциональности логгера"""
    print("🔍 Тестируем логгер...")
    
    try:
        from utils.logger import Logger
        
        # Создаем логгер
        logger = Logger("test_logger")
        
        # Тестируем все уровни логирования
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        print("✅ Логгер работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка логгера: {e}")
        return False

def test_monitoring_components():
    """Тест компонентов мониторинга"""
    print("🔍 Тестируем компоненты мониторинга...")
    
    try:
        from monitoring import MonitoringManager, AlertLevel
        from utils.logger import Logger
        
        logger = Logger("test")
        manager = MonitoringManager(logger)
        
        # Проверяем инициализацию компонентов
        assert hasattr(manager, 'performance_monitor')
        assert hasattr(manager, 'error_alerter')
        assert hasattr(manager, 'health_checker')
        assert hasattr(manager, 'usage_metrics')
        
        print("✅ Все компоненты инициализированы")
        
        # Запускаем мониторинг
        manager.start_monitoring()
        print("✅ Мониторинг запущен")
        
        # Тестируем запись событий
        manager.record_command_execution("test_cmd", 0.5, True)
        manager.record_page_visit("test_page", 10.0)
        manager.send_alert(AlertLevel.INFO, "Test alert", "test")
        print("✅ События записаны")
        
        # Ждем сбора данных
        time.sleep(2)
        
        # Получаем сводку
        summary = manager.get_comprehensive_summary(hours=1)
        assert 'performance' in summary
        assert 'alerts' in summary
        assert 'health' in summary
        assert 'usage' in summary
        print("✅ Сводка получена")
        
        # Экспорт данных
        manager.export_all_data()
        print("✅ Экспорт выполнен")
        
        # Останавливаем мониторинг
        manager.stop_monitoring()
        print("✅ Мониторинг остановлен")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка компонентов мониторинга: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_imports():
    """Тест импортов UI"""
    print("🔍 Тестируем импорты UI...")
    
    try:
        # Тестируем без создания QApplication (избегаем GUI)
        import importlib.util
        
        # Проверяем, что файлы существуют и импортируются на уровне синтаксиса
        ui_modules = [
            'ui.pages.monitoring_page',
            'ui.widgets.monitoring_panel',
            'ui.shared.base_classes',
            'ui.shared.mixins',
            'ui.shared.utils'
        ]
        
        for module_name in ui_modules:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    print(f"❌ Модуль {module_name} не найден")
                    return False
                print(f"✅ Модуль {module_name} доступен")
            except Exception as e:
                print(f"❌ Ошибка импорта {module_name}: {e}")
                return False
        
        print("✅ Все UI модули доступны")
        return True
    except Exception as e:
        print(f"❌ Ошибка UI импортов: {e}")
        return False

def test_main_window_import():
    """Тест импорта главного окна"""
    print("🔍 Тестируем импорт главного окна...")
    
    try:
        # Импортируем только класс, не создаем экземпляр
        from ui.main_window import MainWindow
        print("✅ MainWindow импортирован успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта MainWindow: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция теста"""
    print("🚀 Запуск полного теста системы мониторинга")
    print("=" * 60)
    
    tests = [
        ("Базовые импорты", test_basic_imports),
        ("Функциональность логгера", test_logger_functionality),
        ("Компоненты мониторинга", test_monitoring_components),
        ("UI импорты", test_ui_imports),
        ("Импорт главного окна", test_main_window_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Тест '{test_name}' провален")
        except Exception as e:
            print(f"❌ Исключение в тесте '{test_name}': {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Система мониторинга готова к использованию")
        return True
    else:
        print(f"⚠️  {total - passed} тестов провалено")
        print("❌ Требуется дополнительная отладка")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

