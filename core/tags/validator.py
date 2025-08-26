"""
Валидатор тегов команд
"""
import logging
import re
from typing import List, Dict, Any
from .types import TagType, TagInfo, TagValidationError


class TagValidator:
    """Валидатор тегов команд"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._tag_name_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        self._supported_tags = {
            TagType.WANTED: {
                'description': 'Проверка переменной wanted',
                'parameters': [],
                'required': False
            }
            # Будущие теги можно добавить здесь
        }
    
    def validate_tag_name(self, tag_name: str) -> bool:
        """
        Валидация имени тега.
        
        Args:
            tag_name: Имя тега для валидации
            
        Returns:
            True если имя тега валидно, False в противном случае
        """
        if not tag_name:
            self.logger.error("Имя тега не может быть пустым")
            return False
        
        if not self._tag_name_pattern.match(tag_name):
            self.logger.error(f"Недопустимое имя тега: {tag_name}")
            return False
        
        return True
    
    def validate_tag_type(self, tag_type: TagType) -> bool:
        """
        Валидация типа тега.
        
        Args:
            tag_type: Тип тега для валидации
            
        Returns:
            True если тип тега поддерживается, False в противном случае
        """
        if tag_type not in self._supported_tags:
            self.logger.error(f"Неподдерживаемый тип тега: {tag_type}")
            return False
        
        return True
    
    def validate_tag(self, tag: TagInfo) -> bool:
        """
        Валидация тега.
        
        Args:
            tag: Информация о теге для валидации
            
        Returns:
            True если тег валиден, False в противном случае
        """
        self.logger.debug(f"Валидация тега: {tag}")
        
        try:
            # Проверяем имя тега
            if not self.validate_tag_name(tag.tag_name):
                return False
            
            # Проверяем тип тега
            if not self.validate_tag_type(tag.tag_type):
                return False
            
            # Проверяем параметры тега
            if not self.validate_tag_parameters(tag):
                return False
            
            self.logger.debug(f"Тег прошел валидацию: {tag}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка валидации тега {tag}: {e}")
            return False
    
    def validate_tag_parameters(self, tag: TagInfo) -> bool:
        """
        Валидация параметров тега.
        
        Args:
            tag: Информация о теге
            
        Returns:
            True если параметры валидны, False в противном случае
        """
        tag_config = self._supported_tags.get(tag.tag_type)
        if not tag_config:
            return False
        
        # Проверяем обязательные параметры
        required_params = tag_config.get('required', [])
        for param in required_params:
            if param not in tag.parameters:
                self.logger.error(f"Отсутствует обязательный параметр {param} для тега {tag.tag_type}")
                return False
        
        # Проверяем допустимые параметры
        allowed_params = tag_config.get('parameters', [])
        for param in tag.parameters:
            if param not in allowed_params:
                self.logger.error(f"Недопустимый параметр {param} для тега {tag.tag_type}")
                return False
        
        return True
    
    def validate_tags(self, tags: List[TagInfo]) -> bool:
        """
        Валидация списка тегов.
        
        Args:
            tags: Список тегов для валидации
            
        Returns:
            True если все теги валидны, False в противном случае
        """
        self.logger.debug(f"Валидация списка тегов: {tags}")
        
        for tag in tags:
            if not self.validate_tag(tag):
                return False
        
        self.logger.debug("Все теги прошли валидацию")
        return True
    
    def validate_command_with_tags(self, command: str) -> bool:
        """
        Валидация команды с тегами.
        
        Args:
            command: Команда для валидации
            
        Returns:
            True если команда валидна, False в противном случае
        """
        self.logger.debug(f"Валидация команды с тегами: {command}")
        
        # Проверяем базовую структуру команды
        if not command or not command.strip():
            self.logger.error("Команда не может быть пустой")
            return False
        
        # Проверяем, что команда не заканчивается на подчеркивание
        if command.endswith('_'):
            self.logger.error("Команда не может заканчиваться на подчеркивание")
            return False
        
        # Проверяем, что нет двойных подчеркиваний
        if '__' in command:
            self.logger.error("Команда не может содержать двойные подчеркивания")
            return False
        
        # Извлекаем теги из команды
        import re
        tag_pattern = re.compile(r'_([a-zA-Z_][a-zA-Z0-9_]*)')
        tag_matches = tag_pattern.findall(command)
        
        # Валидируем каждый тег
        for tag_name in tag_matches:
            if not self.validate_tag_name(tag_name):
                return False
            
            # Проверяем, что тип тега поддерживается
            try:
                tag_type = TagType(tag_name)
                if not self.validate_tag_type(tag_type):
                    return False
            except ValueError:
                self.logger.error(f"Неизвестный тип тега: {tag_name}")
                return False
        
        self.logger.debug("Команда с тегами прошла валидацию")
        return True
    
    def get_supported_tag_types(self) -> List[TagType]:
        """Получение поддерживаемых типов тегов"""
        return list(self._supported_tags.keys())
    
    def get_tag_info(self, tag_type: TagType) -> Dict[str, Any]:
        """Получение информации о типе тега"""
        return self._supported_tags.get(tag_type, {})
    
    def register_tag_type(self, tag_type: TagType, config: Dict[str, Any]) -> None:
        """
        Регистрация нового типа тега.
        
        Args:
            tag_type: Тип тега
            config: Конфигурация тега
        """
        self.logger.info(f"Регистрация типа тега: {tag_type}")
        self._supported_tags[tag_type] = config
