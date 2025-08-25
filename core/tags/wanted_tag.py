"""
Реализация тега _wanted
"""
import logging
from typing import Dict, Any
from ..tag_types import TagType, TagInfo, TagResult
from ..tag_processor import BaseTagProcessor


class WantedTag(BaseTagProcessor):
    """Реализация тега _wanted для проверки переменной wanted"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def process(self, tag: TagInfo, context: Dict[str, Any]) -> TagResult:
        """
        Обработка тега _wanted.
        
        Логика:
        - Проверяем переменную 'wanted' в контексте
        - Если wanted = True, показываем диалог "закончилась жидкость"
        - Если wanted = False, продолжаем выполнение команды
        
        Args:
            tag: Информация о теге
            context: Контекст выполнения с переменными
            
        Returns:
            TagResult с результатом обработки
        """
        self.logger.debug(f"Обработка тега _wanted с контекстом: {context}")
        
        try:
            # Получаем FlagManager из контекста
            flag_manager = context.get('flag_manager')
            if flag_manager:
                wanted = flag_manager.get_flag('wanted', False)
            else:
                wanted = context.get('wanted', False)
            
            self.logger.info(f"Значение переменной wanted: {wanted}")
            
            if wanted:
                # Переменная wanted = True, требуется показ диалога
                self.logger.info("Переменная wanted = True, требуется показ диалога")
                return TagResult(
                    success=True,
                    should_continue=False,  # Останавливаем выполнение для показа диалога
                    message="Требуется проверка жидкостей",
                    data={
                        'show_dialog': True,
                        'dialog_type': 'wanted',
                        'title': 'Проверка жидкостей',
                        'message': 'Закончилась жидкость. Проверьте жидкости.',
                        'buttons': ['Проверить жидкости', 'Отмена'],
                        'default_button': 'Проверить жидкости'
                    }
                )
            else:
                # Переменная wanted = False, продолжаем выполнение
                self.logger.info("Переменная wanted = False, продолжаем выполнение")
                return TagResult(
                    success=True,
                    should_continue=True,  # Продолжаем выполнение команды
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
        """
        Валидация тега _wanted.
        
        Args:
            tag: Информация о теге
            
        Returns:
            True если тег валиден, False в противном случае
        """
        if not super().validate(tag):
            return False
        
        # Проверяем, что это правильный тип тега
        if tag.tag_type != TagType.WANTED:
            self.logger.error(f"Неверный тип тега для WantedTag: {tag.tag_type}")
            return False
        
        # Проверяем, что имя тега корректное
        if tag.tag_name != 'wanted':
            self.logger.error(f"Неверное имя тега для WantedTag: {tag.tag_name}")
            return False
        
        self.logger.debug("Тег _wanted прошел валидацию")
        return True
    
    def get_supported_tag_types(self) -> list:
        """Получение поддерживаемых типов тегов"""
        return [TagType.WANTED]
    
    def get_description(self) -> str:
        """Получение описания тега"""
        return "Проверка переменной wanted. Если wanted = True, показывает диалог проверки жидкостей."
    
    def get_usage_example(self) -> str:
        """Получение примера использования"""
        return "test_wanted  # Проверяет переменную wanted перед выполнением команды test"
