#!/usr/bin/env python3
"""
Главный файл приложения с поддержкой MOTTO

Запускает приложение с интеграцией MOTTO конфигурации
"""

import sys
import logging
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from ui.main_window_motto import MainWindowMOTTO


def setup_logging():
    """Настройка логирования"""
    # Создаем директорию для логов если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "motto_app.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_config_files():
    """Проверка наличия конфигурационных файлов"""
    config_files = {
        'standard': 'config.toml',
        'motto': 'config_motto_fixed.toml'
    }
    
    available_configs = {}
    
    for name, file_path in config_files.items():
        if Path(file_path).exists():
            available_configs[name] = file_path
            print(f"✅ Найден {name} конфигурационный файл: {file_path}")
        else:
            print(f"❌ Не найден {name} конфигурационный файл: {file_path}")
    
    return available_configs


def select_config_file(available_configs):
    """Выбор конфигурационного файла"""
    if not available_configs:
        print("❌ Не найдено ни одного конфигурационного файла!")
        return None
    
    if len(available_configs) == 1:
        # Если доступен только один файл, используем его
        config_name = list(available_configs.keys())[0]
        config_file = available_configs[config_name]
        print(f"📋 Используется единственный доступный конфигурационный файл: {config_file}")
        return config_file
    
    # Если доступно несколько файлов, предлагаем выбор
    print("\n📋 Доступные конфигурационные файлы:")
    for i, (name, file_path) in enumerate(available_configs.items(), 1):
        print(f"  {i}. {name}: {file_path}")
    
    while True:
        try:
            choice = input(f"\nВыберите конфигурационный файл (1-{len(available_configs)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(available_configs):
                config_name = list(available_configs.keys())[choice_num - 1]
                config_file = available_configs[config_name]
                print(f"✅ Выбран конфигурационный файл: {config_file}")
                return config_file
            else:
                print(f"❌ Неверный выбор. Введите число от 1 до {len(available_configs)}")
        except ValueError:
            print("❌ Неверный ввод. Введите число.")
        except KeyboardInterrupt:
            print("\n👋 Выход из программы")
            return None


def main():
    """Главная функция"""
    print("🚀 Запуск приложения с поддержкой MOTTO")
    print("=" * 50)
    
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Проверяем конфигурационные файлы
        print("🔍 Проверка конфигурационных файлов...")
        available_configs = check_config_files()
        
        # Выбираем конфигурационный файл
        config_file = select_config_file(available_configs)
        if config_file is None:
            return 1
        
        # Создаем приложение
        app = QApplication(sys.argv)
        app.setApplicationName("Лабораторное оборудование - MOTTO")
        app.setApplicationVersion("1.1")
        
        # Настройка стиля приложения
        app.setStyle('Fusion')
        
        # Создаем главное окно
        logger.info(f"Создание главного окна с конфигурацией: {config_file}")
        window = MainWindowMOTTO(config_file)
        
        # Показываем окно
        window.show()
        
        # Запускаем приложение
        logger.info("Запуск приложения")
        return app.exec()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске приложения: {e}")
        print(f"❌ Критическая ошибка: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())