"""
Управление настройками приложения
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class SerialSettings:
    """Настройки Serial-порта"""
    port: str = 'COM1'
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1
    timeout: float = 1.0


@dataclass
class UpdateSettings:
    """Настройки обновления"""
    enable_auto_update: bool = True
    repository_url: str = ''
    update_check_interval: int = 3600
    auto_connect: bool = True
    platformio_path: str = ''
    upload_port: str = ''
    theme: str = 'dark'


class SettingsManager:
    """Менеджер настроек приложения"""

    def __init__(self, settings_dir: Path = None):
        """
        Инициализация менеджера настроек

        Args:
            settings_dir: Директория для хранения настроек
        """
        if settings_dir is None:
            settings_dir = Path.cwd()

        self.settings_dir = Path(settings_dir)
        self.serial_settings_file = self.settings_dir / 'serial_settings.json'
        self.update_settings_file = self.settings_dir / 'update_settings.json'

        # Инициализируем logger первым
        self.logger = logging.getLogger(__name__)

        self.serial_settings = self._load_serial_settings()
        self.update_settings = self._load_update_settings()

    def _load_serial_settings(self) -> SerialSettings:
        """Загрузка настроек Serial-порта"""
        try:
            if self.serial_settings_file.exists():
                with open(self.serial_settings_file, 'r') as f:
                    data = json.load(f)
                    return SerialSettings(**data)
        except Exception as e:
            self.logger.error(f"Ошибка загрузки настроек Serial: {e}")

        return SerialSettings()

    def _load_update_settings(self) -> UpdateSettings:
        """Загрузка настроек обновления"""
        try:
            if self.update_settings_file.exists():
                with open(self.update_settings_file, 'r') as f:
                    data = json.load(f)
                    settings = UpdateSettings(**data)

                    # Проверка platformio_path
                    if not settings.platformio_path:
                        settings.platformio_path = str(
                            self.settings_dir / 'arduino'
                        )

                    return settings
        except Exception as e:
            self.logger.error(f"Ошибка загрузки настроек обновления: {e}")

        # Создаем настройки по умолчанию
        settings = UpdateSettings()
        settings.platformio_path = str(self.settings_dir / 'arduino')
        return settings

    def save_serial_settings(self):
        """Сохранение настроек Serial-порта"""
        try:
            with open(self.serial_settings_file, 'w') as f:
                json.dump(asdict(self.serial_settings), f, indent=4)
            self.logger.info("Настройки Serial сохранены")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек Serial: {e}")

    def save_update_settings(self):
        """Сохранение настроек обновления"""
        try:
            with open(self.update_settings_file, 'w') as f:
                json.dump(asdict(self.update_settings), f, indent=4)
            self.logger.info("Настройки обновления сохранены")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек обновления: {e}")

    def save_all(self):
        """Сохранение всех настроек"""
        self.save_serial_settings()
        self.save_update_settings()
