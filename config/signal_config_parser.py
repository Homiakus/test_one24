"""
Парсер конфигурации сигналов из config.toml
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from core.signal_types import SignalMapping, SignalType, SignalParser


class SignalConfigParser:
    """Парсер конфигурации сигналов из TOML файла"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_config_file(self, config_path: Path) -> Dict[str, SignalMapping]:
        """
        Парсинг файла конфигурации и извлечение секции signals

        Args:
            config_path: Путь к файлу конфигурации

        Returns:
            Словарь маппингов сигналов
        """
        try:
            self.logger.info(f"Парсинг конфигурации сигналов из: {config_path}")
            
            if not config_path.exists():
                self.logger.warning(f"Файл конфигурации не найден: {config_path}")
                return {}

            # Читаем файл
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Извлекаем секцию signals
            signals_section = self._extract_signals_section(content)
            if not signals_section:
                self.logger.info("Секция signals не найдена в конфигурации")
                return {}

            # Парсим сигналы
            signals = self._parse_signals_section(signals_section)
            
            self.logger.info(f"Успешно загружено {len(signals)} сигналов")
            return signals

        except Exception as e:
            self.logger.error(f"Ошибка парсинга конфигурации сигналов: {e}")
            return {}

    def _extract_signals_section(self, content: str) -> Optional[str]:
        """
        Извлечение секции signals из содержимого файла

        Args:
            content: Содержимое файла конфигурации

        Returns:
            Содержимое секции signals или None
        """
        try:
            # Ищем секцию [signals]
            pattern = r'\[signals\](.*?)(?=\n\[|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            
            if match:
                section_content = match.group(1).strip()
                self.logger.debug(f"Найдена секция signals: {section_content[:100]}...")
                return section_content
            else:
                self.logger.debug("Секция signals не найдена")
                return None

        except Exception as e:
            self.logger.error(f"Ошибка извлечения секции signals: {e}")
            return None

    def _parse_signals_section(self, section_content: str) -> Dict[str, SignalMapping]:
        """
        Парсинг содержимого секции signals

        Args:
            section_content: Содержимое секции signals

        Returns:
            Словарь маппингов сигналов
        """
        signals = {}
        
        try:
            # Разбиваем на строки
            lines = section_content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue
                
                # Парсим строку сигнала
                signal_mapping = self._parse_signal_line(line, line_num)
                if signal_mapping:
                    signal_name, mapping = signal_mapping
                    signals[signal_name] = mapping

        except Exception as e:
            self.logger.error(f"Ошибка парсинга секции signals: {e}")

        return signals

    def _parse_signal_line(self, line: str, line_num: int) -> Optional[Tuple[str, SignalMapping]]:
        """
        Парсинг одной строки сигнала

        Args:
            line: Строка для парсинга
            line_num: Номер строки для логирования

        Returns:
            Кортеж (имя_сигнала, маппинг) или None
        """
        try:
            # Паттерн для строки сигнала: "SIGNAL" = "mapping (type)"
            pattern = r'"([^"]+)"\s*=\s*"([^"]+)"'
            match = re.match(pattern, line)
            
            if not match:
                self.logger.warning(f"Неверный формат строки {line_num}: {line}")
                return None
            
            signal_name = match.group(1).strip()
            mapping_str = match.group(2).strip()
            
            # Валидируем имя сигнала
            if not self._validate_signal_name(signal_name):
                self.logger.warning(f"Неверное имя сигнала в строке {line_num}: {signal_name}")
                return None
            
            # Парсим маппинг
            mapping = SignalParser.parse_signal_mapping(mapping_str)
            if not mapping:
                self.logger.warning(f"Неверный формат маппинга в строке {line_num}: {mapping_str}")
                return None
            
            self.logger.debug(f"Успешно распарсен сигнал: {signal_name} -> {mapping}")
            return signal_name, mapping

        except Exception as e:
            self.logger.error(f"Ошибка парсинга строки {line_num}: {e}")
            return None

    def _validate_signal_name(self, signal_name: str) -> bool:
        """
        Валидация имени сигнала

        Args:
            signal_name: Имя сигнала для валидации

        Returns:
            True если имя валидно
        """
        if not signal_name:
            return False
        
        # Проверяем, что имя содержит только допустимые символы
        if not re.match(r'^[A-Z0-9_]+$', signal_name):
            return False
        
        # Проверяем длину
        if len(signal_name) > 50:
            return False
        
        return True

    def validate_signal_config(self, signals: Dict[str, SignalMapping]) -> List[str]:
        """
        Валидация конфигурации сигналов

        Args:
            signals: Словарь сигналов для валидации

        Returns:
            Список ошибок валидации
        """
        errors = []
        
        try:
            # Проверяем уникальность имен сигналов
            signal_names = list(signals.keys())
            if len(signal_names) != len(set(signal_names)):
                errors.append("Обнаружены дублирующиеся имена сигналов")
            
            # Проверяем уникальность имен переменных
            variable_names = [mapping.variable_name for mapping in signals.values()]
            if len(variable_names) != len(set(variable_names)):
                errors.append("Обнаружены дублирующиеся имена переменных")
            
            # Проверяем каждый сигнал
            for signal_name, mapping in signals.items():
                # Валидация имени сигнала
                if not self._validate_signal_name(signal_name):
                    errors.append(f"Неверное имя сигнала: {signal_name}")
                
                # Валидация имени переменной
                if not mapping.variable_name or not mapping.variable_name.strip():
                    errors.append(f"Пустое имя переменной для сигнала: {signal_name}")
                elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', mapping.variable_name):
                    errors.append(f"Неверное имя переменной для сигнала {signal_name}: {mapping.variable_name}")
                
                # Валидация типа
                if mapping.signal_type not in SignalType:
                    errors.append(f"Неверный тип для сигнала {signal_name}: {mapping.signal_type}")

        except Exception as e:
            errors.append(f"Ошибка валидации конфигурации: {e}")

        return errors

    def create_default_config(self) -> str:
        """
        Создание конфигурации сигналов по умолчанию

        Returns:
            Строка с конфигурацией по умолчанию
        """
        return '''[signals]
# Сигналы UART для автоматического обновления переменных
# Формат: "сигнал" = "переменная (тип)"

# Температура
"TEMP" = "temperature (float)"

# Статус устройства
"STATUS" = "device_status (string)"

# Код ошибки
"ERROR" = "error_code (int)"

# Давление
"PRESSURE" = "pressure (float)"

# Режим работы
"MODE" = "operation_mode (string)"

# Уровень жидкости
"LEVEL" = "fluid_level (float)"

# Скорость
"SPEED" = "speed (float)"

# Время работы
"TIME" = "work_time (int)"

# Состояние
"STATE" = "state (bool)"

# Конфигурация
"CONFIG" = "config (json)"
'''

    def save_signals_config(self, config_path: Path, signals: Dict[str, SignalMapping]) -> bool:
        """
        Сохранение конфигурации сигналов в файл

        Args:
            config_path: Путь к файлу конфигурации
            signals: Словарь сигналов для сохранения

        Returns:
            True при успешном сохранении
        """
        try:
            self.logger.info(f"Сохранение конфигурации сигналов в: {config_path}")
            
            # Читаем текущий файл
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Формируем новую секцию signals
            signals_section = self._format_signals_section(signals)
            
            # Заменяем или добавляем секцию signals
            new_content = self._update_signals_section(content, signals_section)
            
            # Сохраняем файл
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.logger.info(f"Конфигурация сигналов успешно сохранена: {len(signals)} сигналов")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации сигналов: {e}")
            return False

    def _format_signals_section(self, signals: Dict[str, SignalMapping]) -> str:
        """
        Форматирование секции signals для сохранения

        Args:
            signals: Словарь сигналов

        Returns:
            Отформатированная секция signals
        """
        lines = ['[signals]', '']
        
        # Добавляем комментарий
        lines.append('# Сигналы UART для автоматического обновления переменных')
        lines.append('# Формат: "сигнал" = "переменная (тип)"')
        lines.append('')
        
        # Добавляем сигналы
        for signal_name, mapping in signals.items():
            mapping_str = f'{mapping.variable_name} ({mapping.signal_type.value})'
            lines.append(f'"{signal_name}" = "{mapping_str}"')
        
        return '\n'.join(lines)

    def _update_signals_section(self, content: str, new_signals_section: str) -> str:
        """
        Обновление секции signals в содержимом файла

        Args:
            content: Текущее содержимое файла
            new_signals_section: Новая секция signals

        Returns:
            Обновленное содержимое файла
        """
        # Проверяем, есть ли уже секция signals
        if '[signals]' in content:
            # Заменяем существующую секцию
            pattern = r'\[signals\].*?(?=\n\[|\Z)'
            new_content = re.sub(pattern, new_signals_section, content, flags=re.DOTALL | re.IGNORECASE)
        else:
            # Добавляем новую секцию в конец
            new_content = content.rstrip() + '\n\n' + new_signals_section + '\n'
        
        return new_content
