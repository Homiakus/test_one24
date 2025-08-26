"""
/**
 * @file: navigation_manager.py
 * @description: Менеджер навигации между страницами приложения
 * @dependencies: PySide6.QtWidgets, PySide6.QtCore, event_bus
 * @created: 2024-12-19
 */

Менеджер навигации отвечает за управление переключением между страницами,
состоянием навигационных кнопок и историей переходов.
"""

import logging
from typing import Dict, Optional, List, Callable
from PyQt6.QtWidgets import QPushButton, QStackedWidget
from PyQt6.QtCore import QObject, pyqtSignal as Signal

from .event_bus import event_bus


class NavigationManager(QObject):
    """
    Менеджер навигации между страницами приложения.
    
    Управляет переключением страниц, состоянием навигационных кнопок
    и обеспечивает единообразную навигацию по всему приложению.
    """
    
    # Сигналы навигации
    page_changed = Signal(str)  # page_name
    navigation_ready = Signal()
    
    def __init__(self, content_area: QStackedWidget):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Основные компоненты
        self.content_area = content_area
        self.nav_buttons: Dict[str, QPushButton] = {}
        
        # Конфигурация страниц
        self.pages_config = [
            ("wizard", "🪄 Мастер", True),
            ("sequences", "🏠 Главное меню", False),
            ("commands", "⚡ Команды", False),
            ("designer", "🖱️ Конструктор", False),
            ("settings", "⚙️ Настройки", False),
            ("firmware", "🔧 Прошивка", False),
        ]
        
        # Текущая страница
        self.current_page = "wizard"
        
        # История навигации
        self.navigation_history: List[str] = []
        self.max_history_size = 10
        
        # Подписка на события
        self._setup_event_subscriptions()
        
        self.logger.info("NavigationManager инициализирован")
    
    def _setup_event_subscriptions(self):
        """Настройка подписок на события"""
        try:
            # Подписываемся на события изменения страниц
            event_bus.subscribe("page_change_requested", self._on_page_change_requested)
            event_bus.subscribe("navigation_reset", self._on_navigation_reset)
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки подписок на события: {e}")
    
    def setup_navigation_buttons(self, buttons: Dict[str, QPushButton]):
        """
        Настройка навигационных кнопок.
        
        Args:
            buttons: Словарь кнопок навигации
        """
        try:
            self.nav_buttons = buttons
            
            # Подключаем обработчики кликов
            for page_name, button in self.nav_buttons.items():
                button.clicked.connect(lambda checked, name=page_name: self.switch_page(name))
            
            # Устанавливаем начальное состояние
            self._update_button_states()
            
            self.logger.info("Навигационные кнопки настроены")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки навигационных кнопок: {e}")
    
    def switch_page(self, page_name: str) -> bool:
        """
        Переключение на указанную страницу.
        
        Args:
            page_name: Имя страницы для переключения
            
        Returns:
            True если переключение успешно, False в противном случае
        """
        try:
            if page_name not in [page[0] for page in self.pages_config]:
                self.logger.warning(f"Неизвестная страница: {page_name}")
                return False
            
            # Обновляем историю навигации
            if self.current_page != page_name:
                self._add_to_history(self.current_page)
                self.current_page = page_name
            
            # Обновляем состояние кнопок
            self._update_button_states()
            
            # Переключаем страницу в content_area
            page_index = self._get_page_index(page_name)
            if page_index is not None:
                self.content_area.setCurrentIndex(page_index)
                
                # Отправляем событие
                event_bus.emit("page_changed", page_name=page_name)
                self.page_changed.emit(page_name)
                
                self.logger.info(f"Переключено на страницу: {page_name}")
                return True
            else:
                self.logger.error(f"Не удалось найти индекс страницы: {page_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка переключения на страницу '{page_name}': {e}")
            return False
    
    def _get_page_index(self, page_name: str) -> Optional[int]:
        """
        Получение индекса страницы по имени.
        
        Args:
            page_name: Имя страницы
            
        Returns:
            Индекс страницы или None если не найден
        """
        page_indices = {
            'wizard': 0,
            'sequences': 1,
            'commands': 2,
            'designer': 3,
            'settings': 4,
            'firmware': 5,
        }
        return page_indices.get(page_name)
    
    def _update_button_states(self):
        """Обновление состояния навигационных кнопок"""
        try:
            for page_name, button in self.nav_buttons.items():
                button.setChecked(page_name == self.current_page)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления состояния кнопок: {e}")
    
    def _add_to_history(self, page_name: str):
        """
        Добавление страницы в историю навигации.
        
        Args:
            page_name: Имя страницы для добавления
        """
        try:
            if page_name and page_name not in self.navigation_history:
                self.navigation_history.append(page_name)
                
                # Ограничиваем размер истории
                if len(self.navigation_history) > self.max_history_size:
                    self.navigation_history.pop(0)
                    
        except Exception as e:
            self.logger.error(f"Ошибка добавления в историю навигации: {e}")
    
    def go_back(self) -> bool:
        """
        Переход на предыдущую страницу.
        
        Returns:
            True если переход успешен, False в противном случае
        """
        try:
            if len(self.navigation_history) > 0:
                previous_page = self.navigation_history.pop()
                return self.switch_page(previous_page)
            else:
                self.logger.debug("История навигации пуста")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка перехода назад: {e}")
            return False
    
    def go_home(self) -> bool:
        """
        Переход на главную страницу (sequences).
        
        Returns:
            True если переход успешен, False в противном случае
        """
        return self.switch_page("sequences")
    
    def get_current_page(self) -> str:
        """
        Получение текущей страницы.
        
        Returns:
            Имя текущей страницы
        """
        return self.current_page
    
    def get_navigation_history(self) -> List[str]:
        """
        Получение истории навигации.
        
        Returns:
            Список страниц в истории
        """
        return self.navigation_history.copy()
    
    def get_available_pages(self) -> List[str]:
        """
        Получение списка доступных страниц.
        
        Returns:
            Список имен доступных страниц
        """
        return [page[0] for page in self.pages_config]
    
    def is_page_available(self, page_name: str) -> bool:
        """
        Проверка доступности страницы.
        
        Args:
            page_name: Имя страницы для проверки
            
        Returns:
            True если страница доступна, False в противном случае
        """
        return page_name in [page[0] for page in self.pages_config]
    
    def _on_page_change_requested(self, page_name: str):
        """
        Обработчик события запроса изменения страницы.
        
        Args:
            page_name: Имя запрашиваемой страницы
        """
        try:
            self.switch_page(page_name)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса изменения страницы: {e}")
    
    def _on_navigation_reset(self):
        """Обработчик события сброса навигации"""
        try:
            self.current_page = "wizard"
            self.navigation_history.clear()
            self._update_button_states()
            self.logger.info("Навигация сброшена")
            
        except Exception as e:
            self.logger.error(f"Ошибка сброса навигации: {e}")
    
    def reset_navigation(self):
        """Сброс навигации к начальному состоянию"""
        self._on_navigation_reset()
    
    def cleanup(self):
        """Очистка ресурсов NavigationManager"""
        try:
            # Отписываемся от событий
            event_bus.unsubscribe("page_change_requested", self._on_page_change_requested)
            event_bus.unsubscribe("navigation_reset", self._on_navigation_reset)
            
            # Очищаем кнопки
            for button in self.nav_buttons.values():
                try:
                    button.clicked.disconnect()
                except:
                    pass
            
            self.nav_buttons.clear()
            self.navigation_history.clear()
            
            self.logger.info("NavigationManager очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки NavigationManager: {e}")
