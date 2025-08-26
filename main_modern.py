"""
Улучшенная точка входа в приложение управления устройством.

Этот модуль содержит главную функцию запуска приложения с современным дизайном,
правильными пропорциями золотого сечения и улучшенной архитектурой.
"""
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional, NoReturn

# Проверка критических зависимостей
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
except ImportError as e:
    print(f"Критическая ошибка: Не удалось импортировать PyQt6: {e}")
    print("Убедитесь, что PyQt6 установлен: pip install PyQt6")
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
    from ui.main_window_improved import ModernMainWindow
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
        ('PyQt6.QtWidgets', 'PyQt6'),
        ('PyQt6.QtCore', 'PyQt6'),
        ('ui.main_window_improved', 'ui.main_window_improved'),
        ('utils.logger', 'utils.logger'),
    ]
    
    return check_imports(critical_modules)


def load_stylesheet() -> str:
    """
    Загрузка файла стилей.
    
    Returns:
        Содержимое файла стилей или пустая строка в случае ошибки
    """
    try:
        style_file = Path(__file__).parent / "ui" / "styles" / "modern_style.qss"
        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logging.warning(f"Файл стилей не найден: {style_file}")
            return ""
    except Exception as e:
        logging.error(f"Ошибка загрузки файла стилей: {e}")
        return ""


def apply_modern_theme(app: QApplication, theme: str = "light") -> bool:
    """
    Применение современной темы к приложению
    
    Args:
        app: Экземпляр QApplication
        theme: Название темы ("light" или "dark")
        
    Returns:
        bool: True если тема применена успешно, False в противном случае
    """
    try:
        # Загружаем кастомные стили
        custom_styles = load_stylesheet()
        
        if qt_material_available:
            # Применяем qt_material с кастомными стилями
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
            
            # Применяем дополнительные кастомные стили
            if custom_styles:
                app.setStyleSheet(app.styleSheet() + "\n" + custom_styles)
            
            logging.info(f"Современная тема '{theme}' применена успешно")
            return True
        else:
            # Используем только кастомные стили
            if custom_styles:
                app.setStyleSheet(custom_styles)
                logging.info("Применены кастомные стили")
                return True
            else:
                # Fallback на стандартную тему
                app.setStyle('Fusion')
                logging.info("Применена стандартная тема Fusion")
                return True
                
    except Exception as e:
        logging.error(f"Ошибка применения современной темы: {e}")
        # Fallback на стандартную тему
        try:
            app.setStyle('Fusion')
            logging.info("Применена стандартная тема Fusion (fallback)")
            return True
        except Exception as fallback_error:
            logging.error(f"Не удалось применить стандартную тему: {fallback_error}")
            return False


def setup_application_style(app: QApplication) -> None:
    """
    Настройка стиля приложения
    
    Args:
        app: Экземпляр QApplication
    """
    # Устанавливаем глобальные настройки шрифтов
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Применяем современную тему
    apply_modern_theme(app, "light")


def main() -> None:
    """
    Главная функция запуска приложения.
    
    Инициализирует Qt приложение, настраивает логирование,
    применяет современную тему и создает главное окно.
    
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
    logging.info("Запуск улучшенного приложения управления устройством")
    logging.info(f"Python: {sys.version}")
    logging.info(f"PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}")
    logging.info(f"qt_material доступен: {qt_material_available}")

    # Создание приложения с обработкой ошибок
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Система управления устройством")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Modern UI Team")
    except Exception as e:
        error_msg = f"Не удалось создать Qt приложение: {e}"
        print(error_msg)
        sys.exit(1)

    # Настройка стиля приложения
    try:
        setup_application_style(app)
        logging.info("Современный стиль применен успешно")
    except Exception as e:
        logging.error(f"Ошибка применения стиля: {e}")
        logging.info("Применена стандартная тема Fusion")
        try:
            app.setStyle('Fusion')
        except Exception as style_error:
            logging.error(f"Не удалось применить стандартную тему: {style_error}")

    # Создание и показ главного окна с обработкой ошибок
    try:
        window = ModernMainWindow()
        window.show()
        logging.info("Современное главное окно создано и отображено")
        
        # Центрируем окно на экране
        screen = app.primaryScreen().geometry()
        window_geometry = window.geometry()
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        window.move(x, y)
        
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