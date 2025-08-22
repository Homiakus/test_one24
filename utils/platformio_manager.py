"""
Менеджер PlatformIO операций
"""
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any


class PlatformIOManager:
    """Менеджер для работы с PlatformIO"""

    def __init__(self, project_path: Optional[Path] = None):
        """
        Инициализация менеджера PlatformIO

        Args:
            project_path: Путь к проекту PlatformIO
        """
        self.project_path = project_path or Path.cwd()
        self.logger = logging.getLogger(__name__)

    def is_platformio_project(self) -> bool:
        """Проверка, является ли директория проектом PlatformIO"""
        platformio_ini = self.project_path / 'platformio.ini'
        return platformio_ini.exists()

    def build(self, environment: Optional[str] = None) -> bool:
        """Сборка проекта"""
        try:
            cmd = ['pio', 'run']
            if environment:
                cmd.extend(['-e', environment])

            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 минут таймаут
            )

            success = result.returncode == 0
            if success:
                self.logger.info(f"PlatformIO сборка выполнена успешно")
            else:
                self.logger.error(f"Ошибка PlatformIO сборки: {result.stderr}")

            return success

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Ошибка выполнения PlatformIO сборки: {e}")
            return False

    def upload(self, environment: Optional[str] = None, port: Optional[str] = None) -> bool:
        """Загрузка прошивки"""
        try:
            cmd = ['pio', 'run', '--target', 'upload']
            if environment:
                cmd.extend(['-e', environment])
            if port:
                cmd.extend(['--upload-port', port])

            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            success = result.returncode == 0
            if success:
                self.logger.info(f"PlatformIO загрузка выполнена успешно")
            else:
                self.logger.error(f"Ошибка PlatformIO загрузки: {result.stderr}")

            return success

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Ошибка выполнения PlatformIO загрузки: {e}")
            return False

    def clean(self, environment: Optional[str] = None) -> bool:
        """Очистка проекта"""
        try:
            cmd = ['pio', 'run', '--target', 'clean']
            if environment:
                cmd.extend(['-e', environment])

            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            success = result.returncode == 0
            if success:
                self.logger.info(f"PlatformIO очистка выполнена успешно")
            else:
                self.logger.error(f"Ошибка PlatformIO очистки: {result.stderr}")

            return success

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.error(f"Ошибка выполнения PlatformIO очистки: {e}")
            return False

    def get_environments(self) -> List[str]:
        """Получение списка сред разработки"""
        try:
            result = subprocess.run(
                ['pio', 'project', 'config', '--json-output'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                import json
                config = json.loads(result.stdout)
                envs = config.get('env', [])
                return list(envs.keys())

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Ошибка получения сред PlatformIO: {e}")

        return []

    def monitor(self, environment: Optional[str] = None, port: Optional[str] = None,
                baud: int = 115200) -> subprocess.Popen:
        """Запуск мониторинга Serial порта"""
        try:
            cmd = ['pio', 'device', 'monitor']
            if environment:
                cmd.extend(['-e', environment])
            if port:
                cmd.extend(['-p', port])
            cmd.extend(['-b', str(baud)])

            process = subprocess.Popen(
                cmd,
                cwd=self.project_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.logger.info(f"PlatformIO монитор запущен на порту {port}")
            return process

        except FileNotFoundError as e:
            self.logger.error(f"Ошибка запуска PlatformIO монитора: {e}")
            raise
