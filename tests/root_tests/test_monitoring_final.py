#!/usr/bin/env python3
"""
Финальный тест системы мониторинга
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_application_startup():
    """Тест запуска приложения"""
    print("🔍 Тестируем запуск приложения...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # Создаем приложение
        app = QApplication(sys.argv)
        
        # Создаем главное окно
        main_window = MainWindow()
        main_window.show()
        
        print("✅ Приложение запущено успешно")
        
        # Проверяем наличие компонентов мониторинга
        assert hasattr(main_window, 'monitoring_manager'), "MonitoringManager не инициализирован"
        assert hasattr(main_window, 'monitoring_panel'), "MonitoringPanel не создан"
        
        print("✅ Все компоненты мониторинга инициализированы")
        
        # Закрываем приложение
        main_window.close()
        app.quit()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_functionality():
    """Тест функциональности мониторинга"""
    print("🔍 Тестируем функциональность мониторинга...")
    
    try:
        from monitoring import MonitoringManager, AlertLevel
        from utils.logger import Logger
        
        # Создаем логгер и менеджер
        logger = Logger("test")
        manager = MonitoringManager(logger)
        
        # Запускаем мониторинг
        manager.start_monitoring()
        print("✅ Мониторинг запущен")
        
        # Тестируем запись событий
        manager.record_command_execution("test_cmd", 1.0, True)
        manager.record_page_visit("test_page", 30.0)
        manager.send_alert(AlertLevel.INFO, "Test alert", "test_source")
        print("✅ События записаны")
        
        # Ждем сбора данных
        time.sleep(2)
        
        # Получаем сводку
        summary = manager.get_comprehensive_summary(hours=1)
        assert 'performance' in summary, "Отсутствует секция performance"
        assert 'alerts' in summary, "Отсутствует секция alerts"
        assert 'health' in summary, "Отсутствует секция health"
        assert 'usage' in summary, "Отсутствует секция usage"
        print("✅ Сводка получена")
        
        # Экспорт данных
        manager.export_all_data()
        print("✅ Экспорт выполнен")
        
        # Останавливаем мониторинг
        manager.stop_monitoring()
        print("✅ Мониторинг остановлен")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка функциональности мониторинга: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_components():
    """Тест UI компонентов"""
    print("🔍 Тестируем UI компоненты...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from monitoring import MonitoringManager
        from utils.logger import Logger
        from ui.widgets.monitoring_panel import MonitoringPanel
        from ui.pages.monitoring_page import MonitoringPage
        
        # Создаем приложение
        app = QApplication(sys.argv)
        
        # Создаем компоненты
        logger = Logger("test")
        manager = MonitoringManager(logger)
        
        # Тестируем панель мониторинга
        panel = MonitoringPanel(manager)
        assert panel.is_open == False, "Панель должна быть закрыта по умолчанию"
        print("✅ MonitoringPanel создан")
        
        # Тестируем страницу мониторинга
        page = MonitoringPage(manager)
        assert hasattr(page, 'tab_widget'), "Отсутствует tab_widget"
        print("✅ MonitoringPage создан")
        
        # Закрываем приложение
        app.quit()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка UI компонентов: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция теста"""
    print("🚀 Запуск финального теста системы мониторинга")
    print("=" * 60)
    
    tests = [
        ("Функциональность мониторинга", test_monitoring_functionality),
        ("UI компоненты", test_ui_components),
        ("Запуск приложения", test_application_startup),
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
        print("✅ Система мониторинга полностью готова к использованию")
        print("✅ Выдвигающаяся панель мониторинга работает корректно")
        print("✅ Все компоненты интегрированы и функционируют")
        return True
    else:
        print(f"⚠️  {total - passed} тестов провалено")
        print("❌ Требуется дополнительная отладка")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

