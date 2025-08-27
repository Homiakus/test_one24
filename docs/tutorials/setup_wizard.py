#!/usr/bin/env python3
"""
Мастер настройки приложения управления устройством

Интерактивный скрипт для автоматической настройки и проверки системы.
Помогает пользователям быстро настроить приложение и проверить работоспособность.
"""

import sys
import os
import subprocess
import importlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup_wizard.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SetupWizard:
    """Мастер настройки приложения"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.results = {
            'python_version': None,
            'dependencies': {},
            'serial_ports': [],
            'config_files': {},
            'tests_passed': [],
            'issues': []
        }
        
    def print_header(self):
        """Вывод заголовка мастера"""
        print("=" * 80)
        print("🚀 МАСТЕР НАСТРОЙКИ ПРИЛОЖЕНИЯ УПРАВЛЕНИЯ УСТРОЙСТВОМ")
        print("=" * 80)
        print("Этот мастер поможет вам настроить и проверить приложение.")
        print("Следуйте инструкциям для успешной настройки.\n")
    
    def check_python_version(self) -> bool:
        """Проверка версии Python"""
        print("🔍 Проверка версии Python...")
        
        version = sys.version_info
        self.results['python_version'] = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 8:
            print(f"✅ Python {self.results['python_version']} - подходящая версия")
            return True
        else:
            print(f"❌ Python {self.results['python_version']} - требуется Python 3.8+")
            self.results['issues'].append("Неподходящая версия Python")
            return False
    
    def check_dependencies(self) -> bool:
        """Проверка и установка зависимостей"""
        print("\n📦 Проверка зависимостей...")
        
        required_packages = [
            'PyQt6',
            'serial',
            'qt_material',
            'tomli',
            'gitpython',
            'psutil'
        ]
        
        all_installed = True
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"✅ {package} - установлен")
                self.results['dependencies'][package] = True
            except ImportError:
                print(f"❌ {package} - не установлен")
                self.results['dependencies'][package] = False
                all_installed = False
                self.results['issues'].append(f"Не установлен пакет: {package}")
        
        if not all_installed:
            print("\n⚠️  Некоторые зависимости не установлены.")
            response = input("Установить недостающие зависимости? (y/n): ").lower()
            
            if response == 'y':
                return self.install_dependencies()
            else:
                print("❌ Установка зависимостей пропущена")
                return False
        
        return True
    
    def install_dependencies(self) -> bool:
        """Установка зависимостей"""
        print("\n📥 Установка зависимостей...")
        
        try:
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ])
                print("✅ Зависимости установлены успешно")
                return True
            else:
                print("❌ Файл requirements.txt не найден")
                return False
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки зависимостей: {e}")
            return False
    
    def check_serial_ports(self) -> bool:
        """Проверка доступных Serial портов"""
        print("\n🔌 Проверка Serial портов...")
        
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            
            if ports:
                print("Доступные порты:")
                for port in ports:
                    print(f"  - {port.device}: {port.description}")
                    self.results['serial_ports'].append({
                        'device': port.device,
                        'description': port.description
                    })
                return True
            else:
                print("⚠️  Serial порты не найдены")
                self.results['issues'].append("Serial порты не найдены")
                return False
        except ImportError:
            print("❌ Модуль serial не установлен")
            return False
    
    def check_config_files(self) -> bool:
        """Проверка конфигурационных файлов"""
        print("\n⚙️  Проверка конфигурационных файлов...")
        
        config_files = [
            'resources/config.toml',
            'resources/di_config.toml',
            'serial_settings.json'
        ]
        
        all_exist = True
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                print(f"✅ {config_file} - найден")
                self.results['config_files'][config_file] = True
            else:
                print(f"❌ {config_file} - не найден")
                self.results['config_files'][config_file] = False
                all_exist = False
                self.results['issues'].append(f"Конфигурационный файл не найден: {config_file}")
        
        return all_exist
    
    def test_application_startup(self) -> bool:
        """Тест запуска приложения"""
        print("\n🚀 Тест запуска приложения...")
        
        try:
            # Импортируем основные модули
            sys.path.insert(0, str(self.project_root))
            
            # Тест импорта основных модулей
            modules_to_test = [
                'main',
                'ui.main_window',
                'core.serial_manager',
                'config.config_loader'
            ]
            
            for module in modules_to_test:
                try:
                    importlib.import_module(module)
                    print(f"✅ {module} - импортируется")
                    self.results['tests_passed'].append(f"Импорт {module}")
                except ImportError as e:
                    print(f"❌ {module} - ошибка импорта: {e}")
                    self.results['issues'].append(f"Ошибка импорта {module}: {e}")
                    return False
            
            print("✅ Все модули импортируются успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            self.results['issues'].append(f"Ошибка тестирования: {e}")
            return False
    
    def create_sample_config(self) -> bool:
        """Создание образца конфигурации"""
        print("\n📝 Создание образца конфигурации...")
        
        try:
            config_dir = self.project_root / "resources"
            config_dir.mkdir(exist_ok=True)
            
            # Создаем базовую конфигурацию
            sample_config = """# Образец конфигурации
[serial_default]
port = "COM4"
baudrate = 115200
timeout = 1.0

[buttons]
"Тест команда" = "status"
"Хоминг" = "home 1 1 1 0 0"

[sequences]
test_sequence = ["status", "home 1 1 1 0 0", "wait 2"]
"""
            
            config_file = config_dir / "config_sample.toml"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(sample_config)
            
            print(f"✅ Образец конфигурации создан: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания конфигурации: {e}")
            return False
    
    def run_quick_tests(self) -> bool:
        """Запуск быстрых тестов"""
        print("\n🧪 Запуск быстрых тестов...")
        
        try:
            # Тест создания основных объектов
            from core.serial_manager import SerialManager
            from config.config_loader import ConfigLoader
            
            # Тест SerialManager
            serial_manager = SerialManager()
            print("✅ SerialManager создан")
            self.results['tests_passed'].append("Создание SerialManager")
            
            # Тест ConfigLoader
            config_loader = ConfigLoader()
            print("✅ ConfigLoader создан")
            self.results['tests_passed'].append("Создание ConfigLoader")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестов: {e}")
            self.results['issues'].append(f"Ошибка тестов: {e}")
            return False
    
    def generate_setup_report(self):
        """Генерация отчета о настройке"""
        print("\n📊 Генерация отчета...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'python_version': self.results['python_version'],
            'dependencies_status': self.results['dependencies'],
            'serial_ports_found': len(self.results['serial_ports']),
            'config_files_status': self.results['config_files'],
            'tests_passed': len(self.results['tests_passed']),
            'issues_found': len(self.results['issues']),
            'overall_status': 'SUCCESS' if not self.results['issues'] else 'ISSUES_FOUND',
            'details': self.results
        }
        
        # Сохраняем отчет
        report_file = self.project_root / "setup_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Отчет сохранен: {report_file}")
        return report
    
    def print_summary(self, report: Dict):
        """Вывод итогового отчета"""
        print("\n" + "=" * 80)
        print("📋 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 80)
        
        print(f"Python версия: {report['python_version']}")
        print(f"Найдено Serial портов: {report['serial_ports_found']}")
        print(f"Пройдено тестов: {report['tests_passed']}")
        print(f"Найдено проблем: {report['issues_found']}")
        
        if report['issues_found'] > 0:
            print(f"\n⚠️  ПРОБЛЕМЫ:")
            for issue in self.results['issues']:
                print(f"  - {issue}")
        
        print(f"\n📊 Общий статус: {report['overall_status']}")
        
        if report['overall_status'] == 'SUCCESS':
            print("\n🎉 Настройка завершена успешно!")
            print("Теперь вы можете запустить приложение командой: python main.py")
        else:
            print("\n⚠️  Найдены проблемы. Исправьте их перед запуском приложения.")
    
    def run(self):
        """Запуск мастера настройки"""
        self.print_header()
        
        # Выполняем проверки
        checks = [
            ("Проверка Python", self.check_python_version),
            ("Проверка зависимостей", self.check_dependencies),
            ("Проверка Serial портов", self.check_serial_ports),
            ("Проверка конфигурации", self.check_config_files),
            ("Тест запуска", self.test_application_startup),
            ("Быстрые тесты", self.run_quick_tests),
        ]
        
        for check_name, check_func in checks:
            try:
                if not check_func():
                    print(f"❌ {check_name} не пройдена")
                    response = input("Продолжить настройку? (y/n): ").lower()
                    if response != 'y':
                        break
            except Exception as e:
                print(f"❌ Ошибка в {check_name}: {e}")
                self.results['issues'].append(f"Ошибка в {check_name}: {e}")
        
        # Создаем образец конфигурации если нужно
        if not self.results['config_files'].get('resources/config.toml', False):
            self.create_sample_config()
        
        # Генерируем отчет
        report = self.generate_setup_report()
        self.print_summary(report)
        
        return report['overall_status'] == 'SUCCESS'


def main():
    """Главная функция"""
    try:
        wizard = SetupWizard()
        success = wizard.run()
        
        if success:
            print("\n🎯 Следующие шаги:")
            print("1. Настройте конфигурацию в resources/config.toml")
            print("2. Подключите устройство к Serial порту")
            print("3. Запустите приложение: python main.py")
            print("4. Изучите документацию в docs/")
        else:
            print("\n🔧 Рекомендации:")
            print("1. Исправьте найденные проблемы")
            print("2. Установите недостающие зависимости")
            print("3. Проверьте конфигурационные файлы")
            print("4. Запустите мастер снова")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Настройка прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка в мастере настройки: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
