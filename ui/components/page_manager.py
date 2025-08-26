"""
/**
 * @file: page_manager.py
 * @description: Менеджер жизненного цикла страниц приложения
 * @dependencies: PySide6.QtWidgets, PySide6.QtCore, event_bus
 * @created: 2024-12-19
 */

Менеджер страниц отвечает за создание, инициализацию, обновление
и очистку страниц приложения, обеспечивая их правильный жизненный цикл.
"""

import logging
from typing import Dict, Any, Optional, Callable
from PyQt6.QtWidgets import QStackedWidget, QWidget
from PyQt6.QtCore import QObject, pyqtSignal as Signal

from .event_bus import event_bus


class PageManager(QObject):
    """
    Менеджер жизненного цикла страниц приложения.
    
    Отвечает за создание, инициализацию, обновление и очистку страниц,
    обеспечивая их правильный жизненный цикл и управление ресурсами.
    """
    
    # Сигналы управления страницами
    page_created = Signal(str, QWidget)  # page_name, page_widget
    page_initialized = Signal(str)  # page_name
    page_refreshed = Signal(str)  # page_name
    page_cleaned = Signal(str)  # page_name
    
    def __init__(self, content_area: QStackedWidget):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Основные компоненты
        self.content_area = content_area
        
        # Реестр страниц
        self.pages: Dict[str, QWidget] = {}
        
        # Фабрики страниц
        self.page_factories: Dict[str, Callable] = {}
        
        # Конфигурация страниц
        self.pages_config = {
            'wizard': {
                'factory': None,  # Будет установлена позже
                'config_key': 'wizard',
                'auto_refresh': False
            },
            'sequences': {
                'factory': None,
                'config_key': 'sequences',
                'auto_refresh': True
            },
            'commands': {
                'factory': None,
                'config_key': 'buttons',
                'auto_refresh': False
            },
            'designer': {
                'factory': None,
                'config_key': 'buttons',
                'auto_refresh': False
            },
            'settings': {
                'factory': None,
                'config_key': None,
                'auto_refresh': False
            },
            'firmware': {
                'factory': None,
                'config_key': None,
                'auto_refresh': False
            }
        }
        
        # Подписка на события
        self._setup_event_subscriptions()
        
        self.logger.info("PageManager инициализирован")
    
    def _setup_event_subscriptions(self):
        """Настройка подписок на события"""
        try:
            # Подписываемся на события управления страницами
            event_bus.subscribe("config_reloaded", self._on_config_reloaded)
            event_bus.subscribe("page_refresh_requested", self._on_page_refresh_requested)
            event_bus.subscribe("page_cleanup_requested", self._on_page_cleanup_requested)
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки подписок на события: {e}")
    
    def register_page_factory(self, page_name: str, factory: Callable) -> bool:
        """
        Регистрация фабрики для создания страницы.
        
        Args:
            page_name: Имя страницы
            factory: Функция-фабрика для создания страницы
            
        Returns:
            True если регистрация успешна, False в противном случае
        """
        try:
            if page_name in self.pages_config:
                self.page_factories[page_name] = factory
                self.pages_config[page_name]['factory'] = factory
                self.logger.info(f"Фабрика для страницы '{page_name}' зарегистрирована")
                return True
            else:
                self.logger.warning(f"Неизвестная страница для регистрации фабрики: {page_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка регистрации фабрики для страницы '{page_name}': {e}")
            return False
    
    def create_page(self, page_name: str, config: Dict[str, Any] = None) -> Optional[QWidget]:
        """
        Создание страницы с использованием зарегистрированной фабрики.
        
        Args:
            page_name: Имя страницы для создания
            config: Конфигурация для страницы
            
        Returns:
            Созданная страница или None в случае ошибки
        """
        try:
            if page_name not in self.pages_config:
                self.logger.error(f"Неизвестная страница: {page_name}")
                return None
            
            if page_name not in self.page_factories:
                self.logger.error(f"Фабрика для страницы '{page_name}' не зарегистрирована")
                return None
            
            # Создаем страницу
            factory = self.page_factories[page_name]
            page_config = self.pages_config[page_name]
            
            if page_config['config_key'] and config:
                page_config_data = config.get(page_config['config_key'], {})
            else:
                page_config_data = config or {}
            
            # Создаем страницу с помощью фабрики
            if page_name == 'settings':
                # Для страницы настроек передаем settings_manager
                page = factory(config)
            else:
                page = factory(page_config_data)
            
            if page:
                # Сохраняем страницу
                self.pages[page_name] = page
                
                # Добавляем в content_area
                self.content_area.addWidget(page)
                
                # Отправляем событие
                event_bus.emit("page_created", page_name=page_name, page_widget=page)
                self.page_created.emit(page_name, page)
                
                self.logger.info(f"Страница '{page_name}' создана и добавлена")
                return page
            else:
                self.logger.error(f"Фабрика не смогла создать страницу '{page_name}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка создания страницы '{page_name}': {e}")
            return None
    
    def create_all_pages(self, config: Dict[str, Any]) -> bool:
        """
        Создание всех страниц приложения.
        
        Args:
            config: Конфигурация приложения
            
        Returns:
            True если все страницы созданы, False в противном случае
        """
        try:
            success_count = 0
            total_pages = len(self.pages_config)
            
            for page_name in self.pages_config.keys():
                if self.create_page(page_name, config):
                    success_count += 1
            
            self.logger.info(f"Создано {success_count}/{total_pages} страниц")
            return success_count == total_pages
            
        except Exception as e:
            self.logger.error(f"Ошибка создания всех страниц: {e}")
            return False
    
    def get_page(self, page_name: str) -> Optional[QWidget]:
        """
        Получение страницы по имени.
        
        Args:
            page_name: Имя страницы
            
        Returns:
            Страница или None если не найдена
        """
        return self.pages.get(page_name)
    
    def refresh_page(self, page_name: str) -> bool:
        """
        Обновление страницы.
        
        Args:
            page_name: Имя страницы для обновления
            
        Returns:
            True если обновление успешно, False в противном случае
        """
        try:
            if page_name not in self.pages:
                self.logger.warning(f"Страница '{page_name}' не найдена для обновления")
                return False
            
            page = self.pages[page_name]
            
            # Вызываем метод refresh если он есть
            if hasattr(page, 'refresh'):
                page.refresh()
                self.logger.info(f"Страница '{page_name}' обновлена")
                
                # Отправляем событие
                event_bus.emit("page_refreshed", page_name=page_name)
                self.page_refreshed.emit(page_name)
                
                return True
            else:
                self.logger.debug(f"Страница '{page_name}' не имеет метода refresh")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления страницы '{page_name}': {e}")
            return False
    
    def refresh_all_pages(self) -> bool:
        """
        Обновление всех страниц.
        
        Returns:
            True если все страницы обновлены, False в противном случае
        """
        try:
            success_count = 0
            total_pages = len(self.pages)
            
            for page_name in self.pages.keys():
                if self.refresh_page(page_name):
                    success_count += 1
            
            self.logger.info(f"Обновлено {success_count}/{total_pages} страниц")
            return success_count == total_pages
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления всех страниц: {e}")
            return False
    
    def cleanup_page(self, page_name: str) -> bool:
        """
        Очистка ресурсов страницы.
        
        Args:
            page_name: Имя страницы для очистки
            
        Returns:
            True если очистка успешна, False в противном случае
        """
        try:
            if page_name not in self.pages:
                self.logger.warning(f"Страница '{page_name}' не найдена для очистки")
                return False
            
            page = self.pages[page_name]
            
            # Вызываем метод cleanup если он есть
            if hasattr(page, 'cleanup'):
                page.cleanup()
            elif hasattr(page, 'close'):
                page.close()
            
            # Удаляем из content_area
            self.content_area.removeWidget(page)
            
            # Отправляем событие
            event_bus.emit("page_cleaned", page_name=page_name)
            self.page_cleaned.emit(page_name)
            
            self.logger.info(f"Страница '{page_name}' очищена")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки страницы '{page_name}': {e}")
            return False
    
    def cleanup_all_pages(self) -> bool:
        """
        Очистка всех страниц.
        
        Returns:
            True если все страницы очищены, False в противном случае
        """
        try:
            success_count = 0
            total_pages = len(self.pages)
            
            for page_name in list(self.pages.keys()):
                if self.cleanup_page(page_name):
                    success_count += 1
            
            # Очищаем реестр
            self.pages.clear()
            
            self.logger.info(f"Очищено {success_count}/{total_pages} страниц")
            return success_count == total_pages
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки всех страниц: {e}")
            return False
    
    def get_page_count(self) -> int:
        """
        Получение количества созданных страниц.
        
        Returns:
            Количество страниц
        """
        return len(self.pages)
    
    def get_page_names(self) -> list:
        """
        Получение списка имен созданных страниц.
        
        Returns:
            Список имен страниц
        """
        return list(self.pages.keys())
    
    def is_page_created(self, page_name: str) -> bool:
        """
        Проверка создания страницы.
        
        Args:
            page_name: Имя страницы для проверки
            
        Returns:
            True если страница создана, False в противном случае
        """
        return page_name in self.pages
    
    def _on_config_reloaded(self):
        """Обработчик события перезагрузки конфигурации"""
        try:
            self.logger.info("Обновление страниц после перезагрузки конфигурации")
            self.refresh_all_pages()
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления страниц после перезагрузки конфигурации: {e}")
    
    def _on_page_refresh_requested(self, page_name: str):
        """
        Обработчик события запроса обновления страницы.
        
        Args:
            page_name: Имя страницы для обновления
        """
        try:
            self.refresh_page(page_name)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса обновления страницы: {e}")
    
    def _on_page_cleanup_requested(self, page_name: str):
        """
        Обработчик события запроса очистки страницы.
        
        Args:
            page_name: Имя страницы для очистки
        """
        try:
            self.cleanup_page(page_name)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса очистки страницы: {e}")
    
    def cleanup(self):
        """Очистка ресурсов PageManager"""
        try:
            # Отписываемся от событий
            event_bus.unsubscribe("config_reloaded", self._on_config_reloaded)
            event_bus.unsubscribe("page_refresh_requested", self._on_page_refresh_requested)
            event_bus.unsubscribe("page_cleanup_requested", self._on_page_cleanup_requested)
            
            # Очищаем все страницы
            self.cleanup_all_pages()
            
            # Очищаем фабрики
            self.page_factories.clear()
            
            self.logger.info("PageManager очищен")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки PageManager: {e}")
