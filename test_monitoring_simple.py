#!/usr/bin/env python3
"""
Простой тест системы мониторинга
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from monitoring import MonitoringManager, AlertLevel
    from utils.logger import Logger
    print("✓ Модули импортированы успешно")
    
    # Создаем менеджер мониторинга
    logger = Logger(__name__)
    monitoring_manager = MonitoringManager(logger)
    print("✓ MonitoringManager создан")
    
    # Тестируем запись событий
    monitoring_manager.record_command_execution("test_command", 1.5, True)
    monitoring_manager.record_page_visit("test_page", 30.0)
    monitoring_manager.send_alert(AlertLevel.INFO, "Test alert", "test_source")
    print("✓ События записаны")
    
    # Получаем сводку
    summary = monitoring_manager.get_comprehensive_summary(hours=24)
    print("✓ Сводка получена")
    print(f"  - Событий: {summary.get('usage', {}).get('total_events', 0)}")
    print(f"  - Уведомлений: {summary.get('alerts', {}).get('total_alerts', 0)}")
    
    # Тестируем экспорт
    monitoring_manager.export_all_data()
    print("✓ Экспорт выполнен")
    
    print("\n🎉 Все тесты прошли успешно!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
