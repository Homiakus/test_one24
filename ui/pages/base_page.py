"""
Базовый класс для страниц приложения
"""
import logging
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal as pyqtSignal as Signal

from ..shared.base_classes import BasePage as SharedBasePage
from ..shared.mixins import (
    LayoutMixin, TitleMixin, ScrollableMixin, 
    CardMixin, SignalMixin, ButtonMixin, ValidationMixin
)


class BasePage(SharedBasePage, LayoutMixin, TitleMixin, ScrollableMixin, 
               CardMixin, SignalMixin, ButtonMixin, ValidationMixin):
    """Базовый класс для всех страниц приложения с расширенной функциональностью"""

    def __init__(self, page_name: str = "", parent=None):
        super().__init__(page_name, parent)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _setup_ui(self):
        """Настройка интерфейса страницы - использует общие утилиты"""
        # Создаем стандартный layout для страницы
        self.layout = self.create_page_layout()
        
        # Добавляем заголовок
        self.title_label = self.add_title_to_layout(self.layout, self._get_page_title())
        
        # Создаем основную область контента
        self._create_content_area()
        
        # Настраиваем дополнительные элементы
        self._setup_additional_ui()

    def _get_page_title(self) -> str:
        """Получить заголовок страницы - переопределяется в подклассах"""
        return f"📄 {self.page_name}"

    def _create_content_area(self):
        """Создание основной области контента"""
        # Создаем scroll area для контента
        self.scroll_area = self.create_scroll_area()
        self.layout.addWidget(self.scroll_area)
        
        # Создаем widget для scroll area
        self.content_widget = self.create_scrollable_widget()
        self.scroll_area.setWidget(self.content_widget)
        
        # Создаем layout для контента
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(15)

    def _setup_additional_ui(self):
        """Настройка дополнительных элементов UI - переопределяется в подклассах"""
        pass

    def refresh(self):
        """Обновление содержимого страницы"""
        self.logger.debug(f"Refreshing page: {self.page_name}")

    def cleanup(self):
        """Очистка ресурсов при закрытии страницы"""
        self.logger.debug(f"Cleaning up page: {self.page_name}")

    def show_status_message(self, message: str, timeout: int = 3000):
        """Показать статусное сообщение"""
        self.emit_status(message, timeout)

    def show_terminal_message(self, message: str, message_type: str = "info"):
        """Показать сообщение в терминале"""
        self.emit_terminal(message, message_type)

    def show_error_message(self, error_message: str, error_type: str = "error"):
        """Показать сообщение об ошибке"""
        self.emit_error(error_message, error_type)
