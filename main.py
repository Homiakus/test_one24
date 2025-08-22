"""
Точка входа в приложение управления устройством.

Этот модуль содержит главную функцию запуска приложения,
включая инициализацию Qt, настройку логирования и обработку ошибок.
"""
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional, NoReturn

# Проверка критических зависимостей
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import Qt
except ImportError as e:
    print(f"Критическая ошибка: Не удалось импортировать PySide6: {e}")
    print("Убедитесь, что PySide6 установлен: pip install PySide6")
    sys.exit(1)

# Проверка qt_material с graceful fallback
qt_material_available = False
try:
    from qt_material import apply_stylesheet
    qt_material_available = True
except ImportError as e:
    print(f"Предупреждение: qt_material недоступен: {e}")
    print("Будет использована стандартная тема Qt")
    print("Для установки: pip install qt-material")

try:
    from ui.main_window import MainWindow
    from utils.logger import setup_logging
    from utils.error_handler import error_handler, graceful_shutdown, check_imports
except ImportError as e:
    print(f"Критическая ошибка: Не удалось импортировать модули приложения: {e}")
    print("Убедитесь, что все файлы проекта на месте")
    sys.exit(1)


def safe_import_check() -> bool:
    """
    Проверка всех критических импортов.
    
    Проверяет доступность всех необходимых модулей для работы приложения.
    
    Returns:
        True если все импорты успешны, False в противном случае
    """
    critical_modules = [
        ('PySide6.QtWidgets', 'PySide6'),
        ('PySide6.QtCore', 'PySide6'),
        ('ui.main_window', 'ui.main_window'),
        ('utils.logger', 'utils.logger'),
    ]
    
    return check_imports(critical_modules)


def main() -> None:
    """
    Главная функция запуска приложения.
    
    Инициализирует Qt приложение, настраивает логирование,
    применяет тему и создает главное окно.
    
    Raises:
        SystemExit: При критических ошибках инициализации
    """
    # Проверка критических импортов
    if not safe_import_check():
        sys.exit(1)
    
    # Настройка логирования с обработкой ошибок
    try:
        setup_logging()
    except Exception as e:
        print(f"Ошибка настройки логирования: {e}")
        # Продолжаем без логирования, но с базовым выводом в консоль
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    logging.info("=" * 80)
    logging.info("Запуск приложения управления устройством")
    logging.info(f"Python: {sys.version}")
    logging.info(f"qt_material доступен: {qt_material_available}")

    # Создание приложения с обработкой ошибок
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Управление устройством")
        app.setApplicationVersion("1.0.0")
    except Exception as e:
        error_msg = f"Не удалось создать Qt приложение: {e}"
        print(error_msg)
        sys.exit(1)

    # Применение темы по умолчанию с улучшенной обработкой ошибок
    try:
        apply_theme(app)
        logging.info("Тема применена успешно")
    except Exception as e:
        logging.error(f"Ошибка применения темы: {e}")
        logging.info("Применена стандартная тема Fusion")
        try:
            app.setStyle('Fusion')
        except Exception as style_error:
            logging.error(f"Не удалось применить стандартную тему: {style_error}")

    # Создание и показ главного окна с обработкой ошибок
    try:
        window = MainWindow()
        window.show()
        logging.info("Главное окно создано и отображено")
    except Exception as e:
        error_msg = f"Не удалось создать главное окно: {e}"
        logging.critical(error_msg, exc_info=True)
        graceful_shutdown(app, error_msg)

    # Запуск главного цикла с обработкой ошибок
    try:
        logging.info("Запуск главного цикла приложения")
        exit_code = app.exec()
        logging.info(f"Приложение завершено с кодом: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("Приложение прервано пользователем (Ctrl+C)")
        graceful_shutdown(app, "Приложение прервано пользователем")
    except Exception as e:
        error_msg = f"Критическая ошибка в главном цикле: {e}"
        logging.critical(error_msg, exc_info=True)
        graceful_shutdown(app, error_msg)


def apply_theme(app: QApplication, theme: str = "dark") -> bool:
    """
    Применение темы к приложению с улучшенной обработкой ошибок
    
    Args:
        app: Экземпляр QApplication
        theme: Название темы ("dark" или "light")
        
    Returns:
        bool: True если тема применена успешно, False в противном случае
    """
    if not qt_material_available:
        logging.warning("qt_material недоступен, используется стандартная тема")
        try:
            app.setStyle('Fusion')
            return True
        except Exception as e:
            logging.error(f"Не удалось применить стандартную тему: {e}")
            return False
    
    try:
        extra = {
            'danger': '#dc3545',
            'warning': '#ffc107',
            'success': '#17a2b8',
            'font_family': 'Segoe UI',
        }

        if theme == "light":
            apply_stylesheet(app, theme='light_blue.xml',
                            invert_secondary=True, extra=extra)
        else:
            apply_stylesheet(app, theme='dark_teal.xml', extra=extra)
        
        logging.info(f"Тема '{theme}' применена успешно")
        return True
        
    except ImportError as e:
        logging.error(f"Ошибка импорта qt_material: {e}")
        logging.info("Переключение на стандартную тему")
    except Exception as e:
        logging.error(f"Ошибка применения темы '{theme}': {e}")
        logging.info("Переключение на стандартную тему")
    
    # Fallback на стандартную тему
    try:
        app.setStyle('Fusion')
        logging.info("Применена стандартная тема Fusion")
        return True
    except Exception as e:
        logging.error(f"Не удалось применить стандартную тему: {e}")
        return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПриложение прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")
        print("Полная информация об ошибке:")
        traceback.print_exc()
        sys.exit(1)
