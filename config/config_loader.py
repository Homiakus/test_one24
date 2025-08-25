"""
Загрузчик конфигурации из TOML файлов
"""
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import tomli
except ImportError:
    import tomllib as tomli  # Python 3.11+


@dataclass
class SequenceKeywords:
    """Ключевые слова для анализа ответов от устройства"""
    complete: List[str]
    received: List[str]
    error: List[str]
    complete_line: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> 'SequenceKeywords':
        """Создание из словаря"""
        return cls(
            complete=data.get('complete', ['complete', 'completed', 'done', 'COMPLETE']),
            received=data.get('received', ['received']),
            error=data.get('error', ['err', 'error', 'fail']),
            complete_line=data.get('complete_line', ['complete'])
        )


class ConfigLoader:
    """Загрузчик конфигурации приложения"""

    DEFAULT_CONFIG = """
[buttons]
# Основные команды
"Тест" = "test"
"Стоп" = "stop"

[sequences]
test = ["test", "wait 1", "stop"]

[serial_default]
port = "COM1"
baudrate = 115200

[sequence_keywords]
complete = ["complete", "completed", "done", "COMPLETE"]
received = ["received"]
error = ["err", "error", "fail"]
complete_line = ["complete"]

[signals]
# Сигналы UART для автоматического обновления переменных
# Формат: "сигнал" = "переменная (тип)"
"TEMP" = "temperature (float)"
"STATUS" = "device_status (string)"
"ERROR" = "error_code (int)"
"PRESSURE" = "pressure (float)"
"MODE" = "operation_mode (string)"

[wizard]
image_dir = "back"
paint_sequence = "paint"
rinse_sequence = "rinse"

[[wizard.step]]
id = 1
title = "Выберите зоны"
show_bar = false
sequence = ""
auto_next = 0

[[wizard.step.buttons]]
text = "Далее"
next = 2

[[wizard.step]]
id = 2
title = "Подготовка"
show_bar = true
sequence = "prepare"
auto_next = 3
"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Инициализация загрузчика

        Args:
            config_path: Путь к файлу конфигурации
        """
        if config_path is None:
            # Ищем файл в resources/ или в корне
            possible_paths = [
                Path.cwd() / "resources" / "config.toml",
                Path.cwd() / "config.toml",
                Path(__file__).parent.parent / "resources" / "config.toml"
            ]
            
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break
            else:
                config_path = Path.cwd() / "config.toml"

        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}
        self._button_groups: Dict[str, List[str]] = {}
        self.sequence_keywords: SequenceKeywords = None

    def load(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации с улучшенной обработкой ошибок

        Returns:
            Словарь с конфигурацией
        """
        try:
            self.logger.info(f"Начало загрузки конфигурации из: {self.config_path}")
            
            # Проверяем существование файла
            if not self.config_path.exists():
                self.logger.warning(
                    f"Файл конфигурации не найден: {self.config_path}"
                )
                try:
                    self._create_default_config()
                except Exception as e:
                    self.logger.error(f"Ошибка создания конфигурации по умолчанию: {e}")
                    raise

            # Создаем backup перед загрузкой
            try:
                self._create_backup()
            except Exception as e:
                self.logger.warning(f"Не удалось создать backup: {e}")

            # Загружаем TOML с обработкой ошибок
            try:
                with open(self.config_path, 'rb') as f:
                    self._config = tomli.load(f)
            except UnicodeDecodeError as e:
                self.logger.error(f"Ошибка кодировки файла конфигурации: {e}")
                # Пробуем разные кодировки
                self._config = self._load_with_different_encodings()
            except tomli.TOMLDecodeError as e:
                self.logger.error(f"Ошибка парсинга TOML: {e}")
                # Пробуем восстановить из backup
                self._config = self._recover_from_backup()
            except PermissionError as e:
                self.logger.error(f"Ошибка прав доступа к файлу конфигурации: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка загрузки TOML: {e}")
                raise

            # Валидируем структуру конфигурации
            try:
                self._validate_config_structure()
            except ValueError as e:
                self.logger.error(f"Ошибка валидации конфигурации: {e}")
                # Пробуем восстановить из backup
                self._config = self._recover_from_backup()
                # Повторно валидируем
                self._validate_config_structure()

            # Парсим группы кнопок с обработкой ошибок
            try:
                self._parse_button_groups()
            except Exception as e:
                self.logger.error(f"Ошибка парсинга групп кнопок: {e}")
                # Используем fallback группы
                self._create_fallback_button_groups()

            # Загружаем ключевые слова с обработкой ошибок
            try:
                keywords_dict = self._config.get('sequence_keywords', {})
                self.sequence_keywords = SequenceKeywords.from_dict(keywords_dict)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки ключевых слов: {e}")
                # Используем ключевые слова по умолчанию
                self.sequence_keywords = self._create_default_keywords()

            # Обрабатываем конфигурацию мастера с обработкой ошибок
            try:
                self._process_wizard_config()
            except Exception as e:
                self.logger.error(f"Ошибка обработки конфигурации мастера: {e}")
                # Используем конфигурацию мастера по умолчанию
                self._create_default_wizard_config()

            self.logger.info(
                f"Конфигурация успешно загружена: "
                f"{len(self._config.get('buttons', {}))} команд, "
                f"{len(self._config.get('sequences', {}))} последовательностей, "
                f"{len(self._config.get('flags', {}))} флагов, "
                f"{len(self._config.get('signals', {}))} сигналов"
            )

            return self._config

        except Exception as e:
            self.logger.error(f"Критическая ошибка загрузки конфигурации: {e}")
            # Возвращаем конфигурацию по умолчанию в памяти
            return self._create_in_memory_default_config()

    def _create_default_config(self):
        """Создание конфигурации по умолчанию с обработкой ошибок"""
        try:
            self.logger.info("Создание конфигурации по умолчанию")
            
            # Создаем директорию если не существует
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(self.DEFAULT_CONFIG)
                
            self.logger.info(f"Конфигурация по умолчанию создана: {self.config_path}")
            
        except PermissionError as e:
            self.logger.error(f"Ошибка прав доступа при создании конфигурации: {e}")
            raise
        except OSError as e:
            self.logger.error(f"Ошибка ОС при создании конфигурации: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка создания конфигурации: {e}")
            raise

    def _validate_config_structure(self):
        """Валидация структуры TOML конфигурации"""
        try:
            self.logger.info("Валидация структуры конфигурации...")
            
            # Проверяем обязательные секции и создаем их если отсутствуют
            required_sections = ['buttons', 'sequences', 'serial_default', 'sequence_keywords', 'flags', 'signals']
            
            for section in required_sections:
                if section not in self._config:
                    self.logger.warning(f"Отсутствует секция: {section}, создаем по умолчанию")
                    if section == 'buttons':
                        self._config[section] = {'Стоп': 'M112'}
                    elif section == 'sequences':
                        self._config[section] = {'Тест': ['G28']}
                    elif section == 'serial_default':
                        self._config[section] = {'port': 'COM1', 'baudrate': 115200}
                    elif section == 'sequence_keywords':
                        self._config[section] = {
                            'complete': ['OK'],
                            'received': ['OK'],
                            'error': ['ERROR'],
                            'complete_line': ['>']
                        }
                    elif section == 'flags':
                        self._config[section] = {
                            'auto_mode': True,
                            'safety_check': True,
                            'emergency_stop': False,
                            'maintenance_mode': False,
                            'test_mode': False
                        }
                    elif section == 'signals':
                        self._config[section] = {
                            'TEMP': 'temperature (float)',
                            'STATUS': 'device_status (string)',
                            'ERROR': 'error_code (int)',
                            'PRESSURE': 'pressure (float)',
                            'MODE': 'operation_mode (string)'
                        }
            
            # Валидируем секцию buttons
            self._validate_buttons_section()
            
            # Валидируем секцию sequences
            self._validate_sequences_section()
            
            # Валидируем секцию serial_default
            self._validate_serial_default_section()
            
            # Валидируем секцию sequence_keywords
            self._validate_sequence_keywords_section()
            
            # Валидируем секцию flags
            self._validate_flags_section()
            
            # Валидируем секцию signals
            self._validate_signals_section()
            
            # Валидируем секцию wizard (если есть)
            if 'wizard' in self._config:
                self._validate_wizard_section()
            
            self.logger.info("Валидация структуры конфигурации завершена успешно")
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации структуры конфигурации: {e}")
            raise

    def _validate_buttons_section(self):
        """Валидация секции buttons"""
        buttons = self._config.get('buttons', {})
        
        if not isinstance(buttons, dict):
            self.logger.warning("Секция 'buttons' не является словарем, создаем по умолчанию")
            self._config['buttons'] = {'Стоп': 'M112'}
            return
        
        # Удаляем некорректные записи
        invalid_keys = []
        for button_name, command in buttons.items():
            if not isinstance(button_name, str) or not isinstance(command, str):
                self.logger.warning(f"Неверный тип данных в секции 'buttons': {button_name}, удаляем")
                invalid_keys.append(button_name)
            elif not button_name.strip() or not command.strip():
                self.logger.warning(f"Пустые значения в секции 'buttons': {button_name}, удаляем")
                invalid_keys.append(button_name)
        
        for key in invalid_keys:
            del buttons[key]

    def _validate_sequences_section(self):
        """Валидация секции sequences"""
        sequences = self._config.get('sequences', {})
        
        if not isinstance(sequences, dict):
            self.logger.warning("Секция 'sequences' не является словарем, создаем по умолчанию")
            self._config['sequences'] = {'Тест': ['G28']}
            return
        
        # Удаляем некорректные записи
        invalid_keys = []
        for sequence_name, commands in sequences.items():
            if not isinstance(sequence_name, str):
                self.logger.warning(f"Неверный тип имени последовательности: {sequence_name}, удаляем")
                invalid_keys.append(sequence_name)
            elif not isinstance(commands, list):
                self.logger.warning(f"Последовательность '{sequence_name}' не является списком, удаляем")
                invalid_keys.append(sequence_name)
            else:
                # Проверяем команды в последовательности
                invalid_commands = []
                for i, command in enumerate(commands):
                    if not isinstance(command, str):
                        self.logger.warning(f"Команда {i} в последовательности '{sequence_name}' не является строкой, удаляем")
                        invalid_commands.append(i)
                
                # Удаляем некорректные команды (в обратном порядке)
                for i in reversed(invalid_commands):
                    del commands[i]
        
        for key in invalid_keys:
            del sequences[key]

    def _validate_serial_default_section(self):
        """Валидация секции serial_default"""
        serial_default = self._config.get('serial_default', {})
        
        if not isinstance(serial_default, dict):
            raise ValueError("Секция 'serial_default' должна быть словарем")
        
        required_fields = ['port', 'baudrate']
        for field in required_fields:
            if field not in serial_default:
                self.logger.warning(f"Отсутствует поле '{field}' в секции 'serial_default', создаем по умолчанию")
                if field == 'port':
                    serial_default[field] = 'COM1'
                elif field == 'baudrate':
                    serial_default[field] = 115200
        
        # Проверяем тип baudrate
        if not isinstance(serial_default['baudrate'], int):
            self.logger.warning("Поле 'baudrate' не является числом, исправляем")
            serial_default['baudrate'] = 115200

    def _validate_sequence_keywords_section(self):
        """Валидация секции sequence_keywords"""
        keywords = self._config.get('sequence_keywords', {})
        
        if not isinstance(keywords, dict):
            raise ValueError("Секция 'sequence_keywords' должна быть словарем")
        
        required_keywords = ['complete', 'received', 'error', 'complete_line']
        for keyword_type in required_keywords:
            if keyword_type not in keywords:
                self.logger.warning(f"Отсутствует ключевое слово '{keyword_type}', создаем по умолчанию")
                keywords[keyword_type] = ['OK']
            
            if not isinstance(keywords[keyword_type], list):
                self.logger.warning(f"Ключевое слово '{keyword_type}' не является списком, исправляем")
                keywords[keyword_type] = ['OK']

    def _validate_flags_section(self):
        """Валидация секции flags"""
        flags = self._config.get('flags', {})
        
        if not isinstance(flags, dict):
            self.logger.warning("Секция 'flags' должна быть словарем, создаем по умолчанию")
            self._config['flags'] = {
                'auto_mode': True,
                'safety_check': True,
                'emergency_stop': False,
                'maintenance_mode': False,
                'test_mode': False
            }
            return
        
        # Удаляем некорректные записи
        invalid_keys = []
        for flag_name, value in flags.items():
            if not isinstance(flag_name, str):
                self.logger.warning(f"Неверное имя флага: {flag_name}, удаляем")
                invalid_keys.append(flag_name)
            elif not isinstance(value, bool):
                self.logger.warning(f"Неверное значение флага '{flag_name}': {value}, удаляем")
                invalid_keys.append(flag_name)
            elif not flag_name.strip():
                self.logger.warning(f"Пустое имя флага, удаляем")
                invalid_keys.append(flag_name)
        
        for key in invalid_keys:
            del flags[key]
        
        # Добавляем обязательные флаги если отсутствуют
        required_flags = {
            'auto_mode': True,
            'safety_check': True,
            'emergency_stop': False,
            'maintenance_mode': False,
            'test_mode': False
        }
        
        for flag_name, default_value in required_flags.items():
            if flag_name not in flags:
                self.logger.info(f"Добавляем обязательный флаг '{flag_name}' со значением {default_value}")
                flags[flag_name] = default_value

    def _validate_signals_section(self):
        """Валидация секции signals"""
        signals = self._config.get('signals', {})
        
        if not isinstance(signals, dict):
            self.logger.warning("Секция 'signals' должна быть словарем, создаем по умолчанию")
            self._config['signals'] = {
                'TEMP': 'temperature (float)',
                'STATUS': 'device_status (string)',
                'ERROR': 'error_code (int)',
                'PRESSURE': 'pressure (float)',
                'MODE': 'operation_mode (string)'
            }
            return
        
        # Удаляем некорректные записи
        invalid_keys = []
        for signal_name, mapping_str in signals.items():
            if not isinstance(signal_name, str):
                self.logger.warning(f"Неверное имя сигнала: {signal_name}, удаляем")
                invalid_keys.append(signal_name)
            elif not isinstance(mapping_str, str):
                self.logger.warning(f"Неверное значение маппинга для сигнала '{signal_name}': {mapping_str}, удаляем")
                invalid_keys.append(signal_name)
            elif not signal_name.strip():
                self.logger.warning(f"Пустое имя сигнала, удаляем")
                invalid_keys.append(signal_name)
            else:
                # Проверяем формат маппинга: "переменная (тип)"
                try:
                    from core.signal_types import SignalParser
                    mapping = SignalParser.parse_signal_mapping(mapping_str)
                    if not mapping:
                        self.logger.warning(f"Неверный формат маппинга для сигнала '{signal_name}': {mapping_str}, удаляем")
                        invalid_keys.append(signal_name)
                except Exception as e:
                    self.logger.warning(f"Ошибка парсинга маппинга для сигнала '{signal_name}': {e}, удаляем")
                    invalid_keys.append(signal_name)
        
        for key in invalid_keys:
            del signals[key]
        
        # Добавляем обязательные сигналы если отсутствуют
        required_signals = {
            'TEMP': 'temperature (float)',
            'STATUS': 'device_status (string)',
            'ERROR': 'error_code (int)',
            'PRESSURE': 'pressure (float)',
            'MODE': 'operation_mode (string)'
        }
        
        for signal_name, default_mapping in required_signals.items():
            if signal_name not in signals:
                self.logger.info(f"Добавляем обязательный сигнал '{signal_name}' с маппингом {default_mapping}")
                signals[signal_name] = default_mapping

    def _validate_wizard_section(self):
        """Валидация секции wizard"""
        wizard = self._config.get('wizard', {})
        
        if not isinstance(wizard, dict):
            self.logger.warning("Секция 'wizard' не является словарем, создаем по умолчанию")
            self._config['wizard'] = {}
            return
        
        # Проверяем обязательные поля и создаем их если отсутствуют
        required_fields = ['image_dir', 'paint_sequence', 'rinse_sequence']
        for field in required_fields:
            if field not in wizard:
                self.logger.warning(f"Отсутствует поле '{field}' в секции 'wizard', создаем по умолчанию")
                if field == 'image_dir':
                    wizard[field] = 'back'
                elif field == 'paint_sequence':
                    wizard[field] = 'coloring'
                elif field == 'rinse_sequence':
                    wizard[field] = 'water'
        
        # Валидируем шаги если есть
        if 'step' in wizard:
            steps = wizard['step']
            if isinstance(steps, list):
                for i, step in enumerate(steps):
                    self._validate_wizard_step(step, i)
            elif isinstance(steps, dict):
                self._validate_wizard_step(steps, 0)

    def _validate_wizard_step(self, step, step_index):
        """Валидация шага мастера"""
        if not isinstance(step, dict):
            self.logger.warning(f"Шаг {step_index} не является словарем, пропускаем")
            return
        
        required_fields = ['id', 'title']
        for field in required_fields:
            if field not in step:
                self.logger.warning(f"Отсутствует поле '{field}' в шаге {step_index}, создаем по умолчанию")
                if field == 'id':
                    step[field] = step_index + 1
                elif field == 'title':
                    step[field] = f"Шаг {step_index + 1}"
        
        if not isinstance(step['id'], int):
            self.logger.warning(f"Поле 'id' в шаге {step_index} не является числом, исправляем")
            step['id'] = step_index + 1
        
        if not isinstance(step['title'], str):
            self.logger.warning(f"Поле 'title' в шаге {step_index} не является строкой, исправляем")
            step['title'] = f"Шаг {step_index + 1}"

    def _create_backup(self):
        """Создание резервной копии конфигурации"""
        try:
            if not self.config_path.exists():
                self.logger.info("Файл конфигурации не существует, резервная копия не требуется")
                return True
            
            backup_dir = self.config_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{self.config_path.stem}_backup_{timestamp}.toml"
            backup_path = backup_dir / backup_name
            
            # Копируем файл
            import shutil
            shutil.copy2(self.config_path, backup_path)
            
            self.logger.info(f"Резервная копия создана: {backup_path}")
            
            # Удаляем старые резервные копии (оставляем только 5 последних)
            self._cleanup_old_backups(backup_dir)
            
            return True
            
        except PermissionError as e:
            self.logger.error(f"Ошибка прав доступа при создании резервной копии: {e}")
            return False
        except OSError as e:
            self.logger.error(f"Ошибка ОС при создании резервной копии: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка создания резервной копии: {e}")
            return False

    def _cleanup_old_backups(self, backup_dir):
        """Удаление старых резервных копий"""
        try:
            backup_files = list(backup_dir.glob(f"{self.config_path.stem}_backup_*.toml"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Оставляем только 5 последних резервных копий
            for old_backup in backup_files[5:]:
                try:
                    old_backup.unlink()
                    self.logger.debug(f"Удалена старая резервная копия: {old_backup}")
                except Exception as e:
                    self.logger.warning(f"Не удалось удалить старую резервную копию {old_backup}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Ошибка очистки старых резервных копий: {e}")

    def _recover_from_backup(self):
        """Восстановление конфигурации из резервной копии"""
        try:
            backup_dir = self.config_path.parent / 'backups'
            if not backup_dir.exists():
                self.logger.warning("Директория резервных копий не найдена")
                return False
            
            # Ищем последнюю резервную копию
            backup_files = list(backup_dir.glob(f"{self.config_path.stem}_backup_*.toml"))
            if not backup_files:
                self.logger.warning("Резервные копии не найдены")
                return False
            
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_backup = backup_files[0]
            
            self.logger.info(f"Восстановление из резервной копии: {latest_backup}")
            
            # Копируем резервную копию
            import shutil
            shutil.copy2(latest_backup, self.config_path)
            
            # Перезагружаем конфигурацию
            with open(self.config_path, 'rb') as f:
                self._config = tomli.load(f)
            
            self.logger.info("Конфигурация успешно восстановлена из резервной копии")
            return True
            
        except PermissionError as e:
            self.logger.error(f"Ошибка прав доступа при восстановлении из резервной копии: {e}")
            return False
        except OSError as e:
            self.logger.error(f"Ошибка ОС при восстановлении из резервной копии: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка восстановления из резервной копии: {e}")
            return False

    def _load_with_different_encodings(self):
        """Загрузка конфигурации с различными кодировками"""
        encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                self.logger.info(f"Попытка загрузки с кодировкой: {encoding}")
                
                with open(self.config_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                # Парсим TOML
                self._config = tomli.loads(content)
                
                self.logger.info(f"Конфигурация успешно загружена с кодировкой: {encoding}")
                return True
                
            except UnicodeDecodeError:
                self.logger.debug(f"Кодировка {encoding} не подходит")
                continue
            except Exception as e:
                self.logger.debug(f"Ошибка при загрузке с кодировкой {encoding}: {e}")
                continue
        
        self.logger.error("Не удалось загрузить конфигурацию ни с одной из кодировок")
        return False

    def _create_fallback_button_groups(self):
        """Создание fallback групп кнопок"""
        try:
            self.logger.warning("Создание fallback групп кнопок")
            
            # Создаем базовые группы кнопок
            button_groups = {
                'Основные команды': ['Вперед', 'Назад', 'Стоп', 'Домой'],
                'Последовательности': ['Покраска', 'Промывка', 'Тест'],
                'Настройки': ['Настройки', 'Калибровка', 'Сброс']
            }
            
            self.button_groups = button_groups
            self.logger.info("Fallback группы кнопок созданы")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания fallback групп кнопок: {e}")
            # Создаем минимальную fallback конфигурацию
            self.button_groups = {'Основные': ['Вперед', 'Назад', 'Стоп']}

    def _create_default_keywords(self):
        """Создание fallback ключевых слов"""
        try:
            self.logger.warning("Создание fallback ключевых слов")
            
            from core.sequence_manager import SequenceKeywords
            
            # Создаем базовые ключевые слова
            keywords_dict = {
                'complete': ['OK', 'DONE', 'COMPLETE', 'SUCCESS'],
                'received': ['RECEIVED', 'ACK', 'OK'],
                'error': ['ERROR', 'FAIL', 'FAILED', 'ERR'],
                'complete_line': ['READY', 'IDLE', '>']
            }
            
            self.sequence_keywords = SequenceKeywords.from_dict(keywords_dict)
            self.logger.info("Fallback ключевые слова созданы")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания fallback ключевых слов: {e}")
            # Создаем минимальную fallback конфигурацию
            self.sequence_keywords = None

    def _create_default_wizard_config(self):
        """Создание fallback конфигурации мастера"""
        try:
            self.logger.warning("Создание fallback конфигурации мастера")
            
            # Создаем базовую конфигурацию мастера
            wizard_config = {
                'image_dir': 'back',
                'paint_sequence': 'Покраска',
                'rinse_sequence': 'Промывка',
                'step': [
                    {'id': 1, 'title': 'Выбор изображения'},
                    {'id': 2, 'title': 'Настройка параметров'},
                    {'id': 3, 'title': 'Запуск процесса'}
                ]
            }
            
            self._config['wizard'] = wizard_config
            self.logger.info("Fallback конфигурация мастера создана")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания fallback конфигурации мастера: {e}")
            # Создаем минимальную fallback конфигурацию
            self._config['wizard'] = {
                'image_dir': 'back',
                'paint_sequence': 'Покраска',
                'rinse_sequence': 'Промывка'
            }

    def _create_in_memory_default_config(self):
        """Создание конфигурации по умолчанию в памяти"""
        try:
            self.logger.warning("Создание конфигурации по умолчанию в памяти")
            
            # Создаем базовую конфигурацию
            default_config = {
                'buttons': {
                    'Вперед': 'G1 X100',
                    'Назад': 'G1 X-100',
                    'Стоп': 'M112',
                    'Домой': 'G28',
                    'Покраска': 'M1000',
                    'Промывка': 'M1001'
                },
                'sequences': {
                    'Покраска': ['G28', 'M1000', 'G1 X100', 'M1001'],
                    'Промывка': ['G28', 'M1001', 'G1 X50', 'M1001'],
                    'Тест': ['G28', 'G1 X10', 'G1 X-10', 'G28']
                },
                'serial_default': {
                    'port': 'COM1',
                    'baudrate': 115200
                },
                'sequence_keywords': {
                    'complete': ['OK', 'DONE', 'COMPLETE'],
                    'received': ['RECEIVED', 'ACK'],
                    'error': ['ERROR', 'FAIL'],
                    'complete_line': ['READY', '>']
                },
                'wizard': {
                    'image_dir': 'back',
                    'paint_sequence': 'Покраска',
                    'rinse_sequence': 'Промывка'
                }
            }
            
            self._config = default_config
            self.button_groups = {'Основные': ['Вперед', 'Назад', 'Стоп', 'Домой']}
            
            # Создаем базовые ключевые слова
            try:
                self.sequence_keywords = SequenceKeywords.from_dict(default_config['sequence_keywords'])
            except Exception as e:
                self.logger.error(f"Ошибка создания ключевых слов: {e}")
                self.sequence_keywords = None
            
            self.logger.info("Конфигурация по умолчанию в памяти создана")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания конфигурации по умолчанию в памяти: {e}")
            # Минимальная fallback конфигурация
            self._config = {
                'buttons': {'Стоп': 'M112'},
                'sequences': {'Тест': ['G28']},
                'serial_default': {'port': 'COM1', 'baudrate': 115200},
                'sequence_keywords': {
                    'complete': ['OK'],
                    'received': ['OK'],
                    'error': ['ERROR'],
                    'complete_line': ['>']
                }
            }
            self.button_groups = {'Основные': ['Стоп']}
            self.sequence_keywords = None

    def _parse_button_groups(self):
        """Парсинг групп кнопок из комментариев в файле"""
        self._button_groups = {}
        current_group = "Основные команды"
        self._button_groups[current_group] = []

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            in_buttons_section = False

            for line in lines:
                line = line.strip()

                # Проверяем секцию
                if line == '[buttons]':
                    in_buttons_section = True
                    continue
                elif line.startswith('[') and line != '[buttons]':
                    in_buttons_section = False
                    continue

                if not in_buttons_section:
                    continue

                # Парсим комментарии как группы
                if line.startswith('#') and line != '#':
                    group_name = line[1:].strip()
                    if group_name:
                        current_group = group_name
                        if current_group not in self._button_groups:
                            self._button_groups[current_group] = []

                # Парсим команды
                elif '"' in line and '=' in line and not line.startswith('#'):
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        command_name = match.group(1)
                        self._button_groups[current_group].append(command_name)

            # Удаляем пустые группы
            self._button_groups = {
                k: v for k, v in self._button_groups.items() if v
            }

            # Добавляем в конфигурацию
            self._config['button_groups'] = self._button_groups

        except Exception as e:
            self.logger.error(f"Ошибка парсинга групп кнопок: {e}")
            self._button_groups = {
                "Основные команды": list(self._config.get('buttons', {}).keys())
            }

    def _process_wizard_config(self):
        """Обработка конфигурации мастера"""
        wizard = self._config.get('wizard', {})

        if 'step' in wizard:
            steps = wizard['step']
            # Нормализуем в список если это один элемент
            if isinstance(steps, dict):
                steps = [steps]

            # Преобразуем в словарь по id
            wizard['steps'] = {step['id']: step for step in steps}
            del wizard['step']

        self._config['wizard'] = wizard

    def save_sequences(self, sequences: Dict[str, List[str]]) -> bool:
        """
        Сохранение последовательностей в конфигурацию

        Args:
            sequences: Словарь последовательностей

        Returns:
            True при успешном сохранении
        """
        try:
            # Читаем текущий файл
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Находим секцию [sequences]
            start_idx = None
            end_idx = None

            for i, line in enumerate(lines):
                if line.strip().lower() == '[sequences]':
                    start_idx = i
                    # Ищем конец секции
                    for j in range(i + 1, len(lines)):
                        if re.match(r'^\[.*\]', lines[j]):
                            end_idx = j
                            break
                    if end_idx is None:
                        end_idx = len(lines)
                    break

            # Если секция не найдена, добавляем в конец
            if start_idx is None:
                start_idx = len(lines)
                end_idx = len(lines)
                lines.append('\n')

            # Формируем новую секцию
            new_section = ['[sequences]\n']
            for name, commands in sequences.items():
                commands_str = ', '.join(f'"{cmd}"' for cmd in commands)
                new_section.append(f'{name} = [{commands_str}]\n')

            # Заменяем секцию
            new_lines = lines[:start_idx] + new_section + lines[end_idx:]

            # Записываем обратно
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            self.logger.info("Последовательности сохранены в конфигурацию")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения последовательностей: {e}")
            return False

    def load_signals(self) -> Dict[str, str]:
        """
        Загрузка конфигурации сигналов

        Returns:
            Словарь сигналов в формате {сигнал: маппинг}
        """
        try:
            signals = self._config.get('signals', {})
            self.logger.info(f"Загружено {len(signals)} сигналов")
            return signals
        except Exception as e:
            self.logger.error(f"Ошибка загрузки сигналов: {e}")
            return {}

    def get_signal_mappings(self) -> Dict[str, 'SignalMapping']:
        """
        Получение маппингов сигналов в структурированном виде

        Returns:
            Словарь маппингов сигналов
        """
        try:
            from core.signal_types import SignalParser, SignalMapping
            
            signals = self._config.get('signals', {})
            mappings = {}
            
            for signal_name, mapping_str in signals.items():
                try:
                    mapping = SignalParser.parse_signal_mapping(mapping_str)
                    if mapping:
                        mappings[signal_name] = mapping
                except Exception as e:
                    self.logger.warning(f"Ошибка парсинга маппинга для сигнала '{signal_name}': {e}")
                    continue
            
            self.logger.info(f"Загружено {len(mappings)} валидных маппингов сигналов")
            return mappings
            
        except Exception as e:
            self.logger.error(f"Ошибка получения маппингов сигналов: {e}")
            return {}

    def save_signal_mappings(self) -> bool:
        """
        Сохранение маппингов сигналов в файл конфигурации

        Returns:
            True если сохранение успешно, False в противном случае
        """
        try:
            # Перезаписываем файл с обновленными сигналами
            import tomli_w
            with open(self.config_path, 'w', encoding='utf-8') as f:
                tomli_w.dump(self._config, f)
            self.logger.info("Сигналы успешно сохранены")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения сигналов: {e}")
            return False

    def reload(self):
        """Перезагрузка конфигурации"""
        self.logger.info("Перезагрузка конфигурации")
        return self.load()

    def get_flags(self) -> Dict[str, bool]:
        """
        Получение флагов из конфигурации

        Returns:
            Словарь с флагами {flag_name: value}
        """
        return self._config.get('flags', {})

    def set_flag(self, flag_name: str, value: bool) -> None:
        """
        Установка значения флага

        Args:
            flag_name: Имя флага
            value: Значение флага
        """
        if 'flags' not in self._config:
            self._config['flags'] = {}
        self._config['flags'][flag_name] = value
        self.logger.info(f"Флаг '{flag_name}' установлен в {value}")

    def save_flags(self) -> bool:
        """
        Сохранение флагов в файл конфигурации

        Returns:
            True если сохранение успешно, False в противном случае
        """
        try:
            # Перезаписываем файл с обновленными флагами
            import tomli_w
            with open(self.config_path, 'w', encoding='utf-8') as f:
                tomli_w.dump(self._config, f)
            self.logger.info("Флаги успешно сохранены")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения флагов: {e}")
            return False
