"""
Менеджер тегов команд
"""
import logging
import re
from typing import List, Dict, Any, Callable, Optional
from .interfaces import ITagManager
from .tag_types import TagType, TagInfo, TagResult, ParsedCommand, TagProcessingError


class TagManager(ITagManager):
    """Менеджер тегов команд"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._tag_processors: Dict[TagType, Callable] = {}
        # Паттерн для поиска тегов в конце команды
        self._tag_pattern = re.compile(r'_([a-zA-Z][a-zA-Z0-9_]*)$')
        
        # Регистрируем стандартные обработчики тегов
        self._register_default_processors()
    
    def parse_command(self, command: str) -> ParsedCommand:
        """
        Парсинг команды с извлечением тегов.
        
        Args:
            command: Команда для парсинга
            
        Returns:
            Распарсенная команда с тегами
        """
        self.logger.debug(f"Парсинг команды: {command}")
        
        # Разбиваем команду на части по подчеркиваниям
        parts = command.split('_')
        
        if len(parts) <= 1:
            # Нет подчеркиваний, возвращаем команду как есть
            return ParsedCommand(
                base_command=command,
                tags=[],
                original_command=command
            )
        
        # Базовая команда - все части кроме последней
        base_command = '_'.join(parts[:-1])
        
        # Последняя часть может быть тегом
        potential_tag = parts[-1]
        
        # Проверяем, является ли последняя часть валидным тегом
        tags = []
        try:
            tag_type = TagType(potential_tag)
            tag_info = TagInfo(
                tag_type=tag_type,
                tag_name=f"_{potential_tag}",
                parameters={},
                position=0
            )
            tags.append(tag_info)
            self.logger.debug(f"Найден тег: {tag_type}")
        except ValueError:
            # Последняя часть не является тегом, возвращаем команду как есть
            self.logger.debug(f"'{potential_tag}' не является валидным тегом")
            return ParsedCommand(
                base_command=command,
                tags=[],
                original_command=command
            )
        
        parsed_command = ParsedCommand(
            base_command=base_command,
            tags=tags,
            original_command=command
        )
        
        self.logger.debug(f"Распарсена команда: {parsed_command}")
        return parsed_command
    
    def validate_tags(self, tags: List[TagInfo]) -> bool:
        """
        Валидация списка тегов.
        
        Args:
            tags: Список тегов для валидации
            
        Returns:
            True если все теги валидны, False в противном случае
        """
        self.logger.debug(f"Валидация тегов: {tags}")
        
        for tag in tags:
            # Проверяем, есть ли обработчик для этого типа тега
            if tag.tag_type not in self._tag_processors:
                self.logger.error(f"Нет обработчика для тега типа: {tag.tag_type}")
                return False
            
            # Проверяем, что обработчик может валидировать тег
            processor = self._tag_processors[tag.tag_type]
            if hasattr(processor, 'validate'):
                if not processor.validate(tag):
                    self.logger.error(f"Тег не прошел валидацию: {tag}")
                    return False
            elif hasattr(processor, 'validate_tag'):
                if not processor.validate_tag(tag):
                    self.logger.error(f"Тег не прошел валидацию: {tag}")
                    return False
        
        self.logger.debug("Все теги прошли валидацию")
        return True
    
    def process_tags(self, tags: List[TagInfo], context: Dict[str, Any]) -> List[TagResult]:
        """
        Обработка списка тегов.
        
        Args:
            tags: Список тегов для обработки
            context: Контекст выполнения (переменные, состояние)
            
        Returns:
            Список результатов обработки тегов
        """
        self.logger.debug(f"Обработка тегов: {tags}")
        
        results = []
        
        for tag in tags:
            try:
                # Получаем обработчик для тега
                processor = self._tag_processors.get(tag.tag_type)
                if not processor:
                    self.logger.error(f"Нет обработчика для тега: {tag.tag_type}")
                    results.append(TagResult(
                        success=False,
                        should_continue=False,
                        message=f"Нет обработчика для тега: {tag.tag_type}"
                    ))
                    continue
                
                # Обрабатываем тег
                if hasattr(processor, 'process'):
                    result = processor.process(tag, context)
                elif hasattr(processor, 'process_tag'):
                    result = processor.process_tag(tag, context)
                else:
                    # Простой обработчик - функция
                    result = processor(tag, context)
                
                results.append(result)
                
                # Если тег не прошел, останавливаем обработку
                if not result.success or not result.should_continue:
                    self.logger.debug(f"Обработка тегов остановлена: {result}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Ошибка обработки тега {tag}: {e}")
                results.append(TagResult(
                    success=False,
                    should_continue=False,
                    message=f"Ошибка обработки тега: {e}"
                ))
                break
        
        self.logger.debug(f"Результаты обработки тегов: {results}")
        return results
    
    def register_tag_processor(self, tag_type: TagType, processor: Callable) -> None:
        """
        Регистрация обработчика тега.
        
        Args:
            tag_type: Тип тега
            processor: Функция обработки тега
        """
        self.logger.info(f"Регистрация обработчика для тега: {tag_type}")
        self._tag_processors[tag_type] = processor
    
    def _register_default_processors(self):
        """Регистрация стандартных обработчиков тегов"""
        try:
            from .tags.wanted_tag import WantedTag
            wanted_processor = WantedTag()
            self.register_tag_processor(TagType.WANTED, wanted_processor)
            self.logger.info("Зарегистрирован обработчик для тега WANTED")
        except ImportError as e:
            self.logger.warning(f"Не удалось загрузить WantedTag: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка регистрации обработчиков тегов: {e}")
    
    def get_supported_tag_types(self) -> List[TagType]:
        """Получение поддерживаемых типов тегов"""
        return list(self._tag_processors.keys())
    
    def has_processor(self, tag_type: TagType) -> bool:
        """Проверка наличия обработчика для типа тега"""
        return tag_type in self._tag_processors
    
    def _has_tags(self, command: str) -> bool:
        """
        Проверяет наличие тегов в команде
        
        Args:
            command: Команда для проверки
            
        Returns:
            True если в команде есть теги
        """
        try:
            # Разбиваем команду на части по подчеркиваниям
            parts = command.split('_')
            
            if len(parts) <= 1:
                return False
            
            # Проверяем, является ли последняя часть валидным тегом
            potential_tag = parts[-1]
            try:
                TagType(potential_tag)
                return True
            except ValueError:
                return False
        except Exception as e:
            self.logger.error(f"Ошибка при проверке наличия тегов: {e}")
            return False
