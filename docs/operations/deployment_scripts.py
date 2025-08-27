#!/usr/bin/env python3
"""
Скрипты для автоматизации развертывания PyQt6 приложения
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
import tomli
import requests
from dataclasses import dataclass
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Конфигурация развертывания"""
    app_name: str
    app_dir: str
    venv_dir: str
    config_dir: str
    log_dir: str
    data_dir: str
    backup_dir: str
    user: str
    port: int
    python_version: str


class DeploymentManager:
    """Менеджер развертывания приложения"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.setup_directories()
    
    def setup_directories(self):
        """Создание необходимых директорий"""
        directories = [
            self.config.app_dir,
            self.config.venv_dir,
            self.config.config_dir,
            self.config.log_dir,
            self.config.data_dir,
            self.config.backup_dir
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Создана директория: {directory}")
    
    def check_system_requirements(self) -> bool:
        """Проверка системных требований"""
        logger.info("Проверка системных требований...")
        
        # Проверка Python версии
        python_version = sys.version_info
        required_version = tuple(map(int, self.config.python_version.split('.')))
        
        if python_version < required_version:
            logger.error(f"Требуется Python {self.config.python_version} или выше")
            return False
        
        # Проверка свободного места
        free_space = shutil.disk_usage(self.config.app_dir).free
        required_space = 10 * 1024 * 1024 * 1024  # 10 GB
        
        if free_space < required_space:
            logger.error("Недостаточно свободного места на диске")
            return False
        
        # Проверка прав доступа
        if not os.access(self.config.app_dir, os.W_OK):
            logger.error(f"Нет прав на запись в {self.config.app_dir}")
            return False
        
        logger.info("Системные требования выполнены")
        return True
    
    def create_virtual_environment(self) -> bool:
        """Создание виртуального окружения"""
        logger.info("Создание виртуального окружения...")
        
        try:
            subprocess.run([
                sys.executable, '-m', 'venv', self.config.venv_dir
            ], check=True, capture_output=True, text=True)
            
            logger.info("Виртуальное окружение создано")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка создания виртуального окружения: {e}")
            return False
    
    def install_dependencies(self, requirements_file: str) -> bool:
        """Установка зависимостей"""
        logger.info("Установка зависимостей...")
        
        pip_path = os.path.join(self.config.venv_dir, 'bin', 'pip')
        if os.name == 'nt':  # Windows
            pip_path = os.path.join(self.config.venv_dir, 'Scripts', 'pip.exe')
        
        try:
            subprocess.run([
                pip_path, 'install', '--upgrade', 'pip'
            ], check=True, capture_output=True, text=True)
            
            subprocess.run([
                pip_path, 'install', '-r', requirements_file
            ], check=True, capture_output=True, text=True)
            
            logger.info("Зависимости установлены")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка установки зависимостей: {e}")
            return False
    
    def setup_configuration(self, config_files: List[str]) -> bool:
        """Настройка конфигурационных файлов"""
        logger.info("Настройка конфигурации...")
        
        try:
            for config_file in config_files:
                if os.path.exists(config_file):
                    dest_path = os.path.join(self.config.config_dir, os.path.basename(config_file))
                    shutil.copy2(config_file, dest_path)
                    logger.info(f"Скопирован конфигурационный файл: {config_file}")
                else:
                    logger.warning(f"Конфигурационный файл не найден: {config_file}")
            
            return True
        except Exception as e:
            logger.error(f"Ошибка настройки конфигурации: {e}")
            return False
    
    def create_systemd_service(self) -> bool:
        """Создание systemd сервиса"""
        logger.info("Создание systemd сервиса...")
        
        service_content = f"""[Unit]
Description={self.config.app_name}
After=network.target

[Service]
Type=simple
User={self.config.user}
WorkingDirectory={self.config.app_dir}
Environment=PATH={self.config.venv_dir}/bin
ExecStart={self.config.venv_dir}/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_path = f"/etc/systemd/system/{self.config.app_name}.service"
        
        try:
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Перезагрузка systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', f'{self.config.app_name}.service'], check=True)
            
            logger.info("Systemd сервис создан и активирован")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания systemd сервиса: {e}")
            return False
    
    def deploy(self, source_dir: str, requirements_file: str, config_files: List[str]) -> bool:
        """Полное развертывание приложения"""
        logger.info("Начало развертывания приложения...")
        
        # Проверка требований
        if not self.check_system_requirements():
            return False
        
        # Создание виртуального окружения
        if not self.create_virtual_environment():
            return False
        
        # Копирование исходного кода
        try:
            if os.path.exists(source_dir):
                shutil.copytree(source_dir, self.config.app_dir, dirs_exist_ok=True)
                logger.info("Исходный код скопирован")
            else:
                logger.error(f"Исходная директория не найдена: {source_dir}")
                return False
        except Exception as e:
            logger.error(f"Ошибка копирования исходного кода: {e}")
            return False
        
        # Установка зависимостей
        if not self.install_dependencies(requirements_file):
            return False
        
        # Настройка конфигурации
        if not self.setup_configuration(config_files):
            return False
        
        # Создание systemd сервиса
        if not self.create_systemd_service():
            return False
        
        logger.info("Развертывание завершено успешно")
        return True


class BackupManager:
    """Менеджер резервного копирования"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def create_backup(self) -> Optional[str]:
        """Создание резервной копии"""
        logger.info("Создание резервной копии...")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"backup-{timestamp}.tar.gz"
        backup_path = os.path.join(self.config.backup_dir, backup_name)
        
        try:
            # Создание архива
            subprocess.run([
                'tar', '-czf', backup_path,
                '--exclude', f'{self.config.app_dir}/venv',
                '--exclude', f'{self.config.app_dir}/logs',
                '-C', self.config.app_dir, '.'
            ], check=True, capture_output=True, text=True)
            
            logger.info(f"Резервная копия создана: {backup_path}")
            return backup_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Восстановление из резервной копии"""
        logger.info(f"Восстановление из резервной копии: {backup_path}")
        
        if not os.path.exists(backup_path):
            logger.error(f"Файл резервной копии не найден: {backup_path}")
            return False
        
        try:
            # Остановка сервиса
            subprocess.run(['systemctl', 'stop', f'{self.config.app_name}.service'], 
                         check=False, capture_output=True)
            
            # Восстановление из архива
            subprocess.run([
                'tar', '-xzf', backup_path, '-C', self.config.app_dir
            ], check=True, capture_output=True, text=True)
            
            # Запуск сервиса
            subprocess.run(['systemctl', 'start', f'{self.config.app_name}.service'], 
                         check=True, capture_output=True)
            
            logger.info("Восстановление завершено успешно")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка восстановления: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int = 30):
        """Очистка старых резервных копий"""
        logger.info(f"Очистка резервных копий старше {retention_days} дней...")
        
        try:
            subprocess.run([
                'find', self.config.backup_dir,
                '-name', 'backup-*.tar.gz',
                '-mtime', f'+{retention_days}',
                '-delete'
            ], check=True, capture_output=True, text=True)
            
            logger.info("Старые резервные копии удалены")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка очистки резервных копий: {e}")


class HealthChecker:
    """Проверка здоровья приложения"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
    
    def check_application_health(self) -> bool:
        """Проверка здоровья приложения"""
        logger.info("Проверка здоровья приложения...")
        
        try:
            # Проверка статуса сервиса
            result = subprocess.run([
                'systemctl', 'is-active', f'{self.config.app_name}.service'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("Сервис не активен")
                return False
            
            # Проверка HTTP endpoint (если есть)
            if hasattr(self.config, 'health_url'):
                try:
                    response = requests.get(self.config.health_url, timeout=5)
                    if response.status_code == 200:
                        logger.info("Приложение отвечает на HTTP запросы")
                    else:
                        logger.warning(f"HTTP endpoint вернул статус: {response.status_code}")
                except requests.RequestException as e:
                    logger.warning(f"HTTP endpoint недоступен: {e}")
            
            logger.info("Приложение здорово")
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья: {e}")
            return False
    
    def check_system_resources(self) -> Dict[str, float]:
        """Проверка системных ресурсов"""
        logger.info("Проверка системных ресурсов...")
        
        resources = {}
        
        try:
            # Проверка дискового пространства
            disk_usage = shutil.disk_usage(self.config.app_dir)
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            resources['disk_usage_percent'] = disk_percent
            
            # Проверка памяти (Linux)
            if os.name == 'posix':
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                total_mem = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
                available_mem = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1])
                mem_percent = ((total_mem - available_mem) / total_mem) * 100
                resources['memory_usage_percent'] = mem_percent
            
            logger.info(f"Использование диска: {disk_percent:.1f}%")
            if 'memory_usage_percent' in resources:
                logger.info(f"Использование памяти: {mem_percent:.1f}%")
            
            return resources
        except Exception as e:
            logger.error(f"Ошибка проверки ресурсов: {e}")
            return {}


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Скрипты развертывания PyQt6 приложения')
    parser.add_argument('action', choices=['deploy', 'backup', 'restore', 'health', 'update'],
                       help='Действие для выполнения')
    parser.add_argument('--config', default='deployment_config.json',
                       help='Файл конфигурации развертывания')
    parser.add_argument('--source', help='Директория с исходным кодом')
    parser.add_argument('--requirements', help='Файл requirements.txt')
    parser.add_argument('--backup-file', help='Файл резервной копии для восстановления')
    
    args = parser.parse_args()
    
    # Загрузка конфигурации
    try:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
        
        config = DeploymentConfig(**config_data)
    except FileNotFoundError:
        logger.error(f"Файл конфигурации не найден: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        sys.exit(1)
    
    # Выполнение действий
    if args.action == 'deploy':
        if not args.source or not args.requirements:
            logger.error("Для развертывания требуются --source и --requirements")
            sys.exit(1)
        
        manager = DeploymentManager(config)
        config_files = ['config/config.toml', 'config/di_config.toml']
        
        if manager.deploy(args.source, args.requirements, config_files):
            logger.info("Развертывание завершено успешно")
        else:
            logger.error("Развертывание завершилось с ошибкой")
            sys.exit(1)
    
    elif args.action == 'backup':
        backup_manager = BackupManager(config)
        backup_path = backup_manager.create_backup()
        if backup_path:
            backup_manager.cleanup_old_backups()
            logger.info("Резервное копирование завершено")
        else:
            logger.error("Резервное копирование завершилось с ошибкой")
            sys.exit(1)
    
    elif args.action == 'restore':
        if not args.backup_file:
            logger.error("Для восстановления требуется --backup-file")
            sys.exit(1)
        
        backup_manager = BackupManager(config)
        if backup_manager.restore_backup(args.backup_file):
            logger.info("Восстановление завершено успешно")
        else:
            logger.error("Восстановление завершилось с ошибкой")
            sys.exit(1)
    
    elif args.action == 'health':
        health_checker = HealthChecker(config)
        
        # Проверка здоровья приложения
        app_healthy = health_checker.check_application_health()
        
        # Проверка системных ресурсов
        resources = health_checker.check_system_resources()
        
        if app_healthy:
            logger.info("Проверка здоровья завершена успешно")
        else:
            logger.error("Проверка здоровья выявила проблемы")
            sys.exit(1)
    
    elif args.action == 'update':
        logger.info("Обновление приложения...")
        
        # Создание резервной копии
        backup_manager = BackupManager(config)
        backup_path = backup_manager.create_backup()
        
        if not backup_path:
            logger.error("Не удалось создать резервную копию")
            sys.exit(1)
        
        # Остановка сервиса
        try:
            subprocess.run(['systemctl', 'stop', f'{config.app_name}.service'], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.warning("Не удалось остановить сервис")
        
        # Обновление кода (git pull)
        try:
            subprocess.run(['git', 'pull', 'origin', 'main'], 
                         cwd=config.app_dir, check=True, capture_output=True)
            logger.info("Код обновлен")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка обновления кода: {e}")
            # Восстановление из резервной копии
            backup_manager.restore_backup(backup_path)
            sys.exit(1)
        
        # Обновление зависимостей
        pip_path = os.path.join(config.venv_dir, 'bin', 'pip')
        if os.name == 'nt':
            pip_path = os.path.join(config.venv_dir, 'Scripts', 'pip.exe')
        
        try:
            subprocess.run([pip_path, 'install', '--upgrade', '-r', 'requirements.txt'], 
                         cwd=config.app_dir, check=True, capture_output=True)
            logger.info("Зависимости обновлены")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка обновления зависимостей: {e}")
            backup_manager.restore_backup(backup_path)
            sys.exit(1)
        
        # Запуск сервиса
        try:
            subprocess.run(['systemctl', 'start', f'{config.app_name}.service'], 
                         check=True, capture_output=True)
            logger.info("Сервис запущен")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка запуска сервиса: {e}")
            backup_manager.restore_backup(backup_path)
            sys.exit(1)
        
        # Проверка здоровья
        health_checker = HealthChecker(config)
        if health_checker.check_application_health():
            logger.info("Обновление завершено успешно")
        else:
            logger.error("Приложение не работает после обновления")
            backup_manager.restore_backup(backup_path)
            sys.exit(1)


if __name__ == '__main__':
    main()
