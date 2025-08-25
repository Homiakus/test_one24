"""
Процессор тегов команд
"""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import ITagProcessor
from .tag_types import TagType, TagInfo, TagResult, TagProcessingError


class TagProcessor(ITagProcessor):
    """Процессор тегов команд"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._processors: Dict[TagType, 'BaseTagProcessor'] = {}
        self._context: Dict[str, Any] = {}
        
        # Регистрируем стандартные процессоры
        self._register_default_processors()
    
    def process_tag(self, tag: TagInfo, context: Dict[str, Any]) -> TagResult:
        """
        Обработка отдельного тега.
        
        Args:
            tag: Информация о теге
            context: Контекст выполнения
            
        Returns:
            Результат обработки тега
        """
        self.logger.debug(f"Обработка тега: {tag}")
        
        try:
            # Получаем процессор для типа тега
            processor = self._processors.get(tag.tag_type)
            if not processor:
                self.logger.error(f"Нет процессора для тега: {tag.tag_type}")
                return TagResult(
                    success=False,
                    should_continue=False,
                    message=f"Нет процессора для тега: {tag.tag_type}"
                )
            
            # Обрабатываем тег
            result = processor.process(tag, context)
            
            self.logger.debug(f"Результат обработки тега {tag.tag_type}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки тега {tag}: {e}")
            return TagResult(
                success=False,
                should_continue=False,
                message=f"Ошибка обработки тега: {e}"
            )
    
    def validate_tag(self, tag: TagInfo) -> bool:
        """
        Валидация тега.
        
        Args:
            tag: Информация о теге
            
        Returns:
            True если тег валиден, False в противном случае
        """
        self.logger.debug(f"Валидация тега: {tag}")
        
        try:
            # Получаем процессор для типа тега
            processor = self._processors.get(tag.tag_type)
            if not processor:
                self.logger.error(f"Нет процессора для тега: {tag.tag_type}")
                return False
            
            # Валидируем тег
            is_valid = processor.validate(tag)
            
            self.logger.debug(f"Результат валидации тега {tag.tag_type}: {is_valid}")
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации тега {tag}: {e}")
            return False
    
    def get_supported_tag_types(self) -> List[TagType]:
        """Получение поддерживаемых типов тегов"""
        return list(self._processors.keys())
    
    def register_processor(self, tag_type: TagType, processor: 'BaseTagProcessor') -> None:
        """
        Регистрация процессора тега.
        
        Args:
            tag_type: Тип тега
            processor: Процессор тега
        """
        self.logger.info(f"Регистрация процессора для тега: {tag_type}")
        self._processors[tag_type] = processor
    
    def _register_default_processors(self):
        """Регистрация стандартных процессоров тегов"""
        # Процессоры будут зарегистрированы позже при создании конкретных тегов
        pass


class BaseTagProcessor:
    """Базовый класс для процессоров тегов"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, tag: TagInfo, context: Dict[str, Any]) -> TagResult:
        """
        Обработка тега.
        
        Args:
            tag: Информация о теге
            context: Контекст выполнения
            
        Returns:
            Результат обработки тега
        """
        raise NotImplementedError("Метод process должен быть реализован в подклассе")
    
    def validate(self, tag: TagInfo) -> bool:
        """
        Валидация тега.
        
        Args:
            tag: Информация о теге
            
        Returns:
            True если тег валиден, False в противном случае
        """
        # Базовая валидация - проверяем, что тег не пустой
        return tag is not None and tag.tag_name is not None
    
    def get_supported_tag_types(self) -> List[TagType]:
        """Получение поддерживаемых типов тегов"""
        return []


class WantedTagProcessor(BaseTagProcessor):
    """Процессор для тега _wanted"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [TagType.WANTED]
    
    def process(self, tag: TagInfo, context: Dict[str, Any]) -> TagResult:
        """
        Обработка тега _wanted.
        
        Логика:
        - Проверяем переменную 'wanted' в контексте
        - Если wanted = True, показываем диалог
        - Если wanted = False, продолжаем выполнение
        """
        self.logger.debug(f"Обработка тега _wanted с контекстом: {context}")
        
        try:
            # Получаем значение переменной wanted
            wanted = context.get('wanted', False)
            
            if wanted:
                self.logger.info("Переменная wanted = True, требуется показ диалога")
                return TagResult(
                    success=True,
                    should_continue=False,  # Останавливаем выполнение для показа диалога
                    message="Требуется проверка жидкостей",
                    data={
                        'show_dialog': True,
                        'dialog_type': 'wanted',
                        'message': 'Закончилась жидкость. Проверьте жидкости.'
                    }
                )
            else:
                self.logger.info("Переменная wanted = False, продолжаем выполнение")
                return TagResult(
                    success=True,
                    should_continue=True,  # Продолжаем выполнение
                    message="Переменная wanted = False, продолжаем выполнение"
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки тега _wanted: {e}")
            return TagResult(
                success=False,
                should_continue=False,
                message=f"Ошибка обработки тега _wanted: {e}"
            )
    
    def validate(self, tag: TagInfo) -> bool:
        """Валидация тега _wanted"""
        if not super().validate(tag):
            return False
        
        # Проверяем, что это правильный тип тега
        if tag.tag_type != TagType.WANTED:
            self.logger.error(f"Неверный тип тега для WantedTagProcessor: {tag.tag_type}")
            return False
        
        return True
    
    def get_supported_tag_types(self) -> List[TagType]:
        """Получение поддерживаемых типов тегов"""
        return self.supported_types
