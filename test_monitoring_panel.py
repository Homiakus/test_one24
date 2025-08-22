#!/usr/bin/env python3
"""
Тест выдвигающейся панели мониторинга
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from monitoring import MonitoringManager
    from ui.widgets.monitoring_panel import MonitoringPanel
    from utils.logger import Logger
    
    print("✓ Модули импортированы успешно")
    
    # Создаем приложение
    app = QApplication(sys.argv)
    print("✓ QApplication создан")
    
    # Создаем логгер и менеджер мониторинга
    logger = Logger(__name__)
    monitoring_manager = MonitoringManager(logger)
    print("✓ MonitoringManager создан")
    
    # Создаем панель мониторинга
    panel = MonitoringPanel(monitoring_manager)
    print("✓ MonitoringPanel создан")
    
    # Запускаем мониторинг
    monitoring_manager.start_monitoring()
    print("✓ Мониторинг запущен")
    
    # Показываем панель
    panel.show_panel()
    print("✓ Панель показана")
    
    # Таймер для автоматического закрытия через 10 секунд
    def close_app():
        print("✓ Тест завершен успешно")
        app.quit()
    
    QTimer.singleShot(10000, close_app)
    
    # Запускаем приложение
    print("✓ Приложение запущено (закроется через 10 секунд)")
    sys.exit(app.exec())
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
