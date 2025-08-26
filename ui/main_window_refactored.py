"""
/**
 * @file: main_window_refactored.py
 * @description: Рефакторенная версия MainWindow с использованием специализированных компонентов
 * @dependencies: PySide6.QtWidgets, PySide6.QtCore, ui.components, event_bus
 * @created: 2024-12-19
 */

Рефакторенная версия MainWindow, которая использует специализированные компоненты:
- EventBus для централизованных событий
- NavigationManager для управления навигацией
- PageManager для жизненного цикла страниц
- ConnectionManager для Serial подключений

MainWindow теперь является координатором, а не исполнителем.
"""

import logging
from typing import Dict, Optional, Any
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QToolButton, QMenu, QMessageBox, QApplication,
    QGroupBox, QCheckBox
)
from PyQt6.QtGui import QAction

from config.settings import SettingsManager
from config.config_loader import ConfigLoader
from core.serial_manager import SerialManager
from core.sequence_manager import SequenceManager, CommandSequenceExecutor
from ui.pages.wizard_page import WizardPage
from ui.pages.settings_page import SettingsPage
from ui.pages.sequences_page import SequencesPage
from ui.pages.commands_page import CommandsPage
from ui.pages.designer_page import DesignerPage
from ui.pages.firmware_page import FirmwarePage
from ui.widgets.modern_widgets import ModernCard

# Импортируем новые компоненты
from ui.components.event_bus import event_bus
from ui.components.navigation_manager import NavigationManager
from ui.components.page_manager import PageManager
from ui.components.connection_manager import ConnectionManager


class MainWindow(QMainWindow):
    """
    Рефакторенная версия главного окна приложения.
    
    Теперь является координатором специализированных компонентов,
    а не исполнителем всех функций.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        try:
            # Инициализация менеджеров
            self.logger.info("Инициализация менеджеров...")
            self._init_managers()
            
            # Загрузка конфигурации
            self.logger.info("Загрузка конфигурации...")
            self.config = self.config_loader.load()
            self.logger.info("Конфигурация загружена")
            
            # Инициализация компонентов
            self.logger.info("Инициализация компонентов...")
            self._init_components()
            self.logger.info("Компоненты инициализированы")

            # Настройка UI
            self.logger.info("Настройка UI...")
            self._setup_ui()
            self.logger.info("UI настроен")

            # Настройка соединений
            self.logger.info("Настройка соединений...")
            self._setup_connections()
            self.logger.info("Соединения настроены")

            # Автоподключение
            if self.settings_manager.update_settings.auto_connect:
                self.logger.info("Настройка автоподключения...")
                self._setup_auto_connect()
            
            # Запуск в обычном режиме
            self.logger.info("Показ окна...")
            self.show()
            self.is_fullscreen = False

            self.logger.info("Приложение запущено")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Ошибка инициализации",
                f"Не удалось запустить приложение:\n{e}"
            )
            raise

    def _init_managers(self):
        """Инициализация основных менеджеров"""
        self.settings_manager = SettingsManager()
        self.config_loader = ConfigLoader()
        self.serial_manager = SerialManager()
        self.sequence_manager = SequenceManager(
            {}, {}  # Будет обновлено после загрузки конфигурации
        )

    def _init_components(self):
        """Инициализация специализированных компонентов"""
        # Создаем content_area для компонентов
        self.content_area = QStackedWidget()
        
        # Инициализируем PageManager
        self.page_manager = PageManager(self.content_area)
        
        # Инициализируем NavigationManager
        self.navigation_manager = NavigationManager(self.content_area)
        
        # Инициализируем ConnectionManager
        self.connection_manager = ConnectionManager(
            self.serial_manager, 
            self.statusBar()
        )
        
        # Регистрируем фабрики страниц
        self._register_page_factories()
        
        # Обновляем SequenceManager с загруженной конфигурацией
        self.sequence_manager = SequenceManager(
            self.config.get('sequences', {}),
            self.config.get('buttons', {})
        )

    def _register_page_factories(self):
        """Регистрация фабрик для создания страниц"""
        # Фабрики страниц
        page_factories = {
            'wizard': lambda config: WizardPage(config),
            'sequences': lambda config: SequencesPage(config),
            'commands': lambda config: CommandsPage(config),
            'designer': lambda config: DesignerPage(config),
            'settings': lambda config: SettingsPage(self.settings_manager),
            'firmware': lambda config: FirmwarePage()
        }
        
        # Регистрируем фабрики
        for page_name, factory in page_factories.items():
            self.page_manager.register_page_factory(page_name, factory)

    def _setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Панель управления устройством (Рефакторинг)")
        self.setMinimumSize(1200, 800)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Боковая панель
        self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Область контента
        main_layout.addWidget(self.content_area, 1)

        # Статусная строка
        self.statusBar().showMessage("Готов к работе")

        # Создаем все страницы
        self.page_manager.create_all_pages(self.config)
        
        # Настраиваем навигацию
        self.navigation_manager.setup_navigation_buttons(self.nav_buttons)

    def _create_sidebar(self):
        """Создание боковой панели"""
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 20)
        sidebar_layout.setSpacing(6)

        # Меню
        self._create_menu_button(sidebar_layout)

        # Заголовок
        self._create_header(sidebar_layout)

        # Навигация
        self._create_navigation(sidebar_layout)

        sidebar_layout.addStretch()

        # Статус подключения
        self._create_connection_status(sidebar_layout)

    def _create_menu_button(self, parent_layout):
        """Создание кнопки меню"""
        menu_button = QToolButton()
        menu_button.setText("☰")
        menu_button.setPopupMode(QToolButton.InstantPopup)

        menu = QMenu(self)

        actions = [
            ('🔄 Перезагрузить конфигурацию', self._reload_config),
            ('📺 Полноэкранный режим', self._toggle_fullscreen),
            ('🎨 Переключить тему', self._toggle_theme),
            ('ℹ️ О программе', self._show_about),
            ('❌ Выход', self.close),
        ]

        for text, handler in actions:
            action = QAction(text, self)
            action.triggered.connect(handler)
            menu.addAction(action)

        menu_button.setMenu(menu)
        parent_layout.addWidget(menu_button)

    def _create_header(self, parent_layout):
        """Создание заголовка"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 20)

        title = QLabel("Панель управления")
        title.setObjectName("sidebar_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Система контроля")
        subtitle.setObjectName("sidebar_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        parent_layout.addWidget(header_widget)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        parent_layout.addWidget(separator)

    def _create_navigation(self, parent_layout):
        """Создание навигации"""
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)

        self.nav_buttons = {}

        pages = [
            ("wizard", "🪄 Мастер", True),
            ("sequences", "🏠 Главное меню", False),
            ("commands", "⚡ Команды", False),
            ("designer", "🖱️ Конструктор", False),
            ("settings", "⚙️ Настройки", False),
            ("firmware", "🔧 Прошивка", False),
        ]

        for key, text, checked in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.setObjectName("nav_button")
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        parent_layout.addWidget(nav_widget)

    def _create_connection_status(self, parent_layout):
        """Создание индикатора подключения"""
        self.connection_card = ModernCard()
        layout = QVBoxLayout()

        self.connection_status = QLabel("● Отключено")
        self.connection_status.setObjectName("connection_status")
        layout.addWidget(self.connection_status)

        self.connection_card.addLayout(layout)
        parent_layout.addWidget(self.connection_card)

    def _setup_connections(self):
        """Настройка соединений сигналов и слотов"""
        # Подписываемся на события EventBus
        event_bus.subscribe("connection_status_changed", self._on_connection_status_changed)
        event_bus.subscribe("page_changed", self._on_page_changed)
        event_bus.subscribe("data_received", self._on_data_received)
        event_bus.subscribe("error_occurred", self._on_error_occurred)
        
        # Подписываемся на события страниц
        self._setup_page_connections()

    def _setup_page_connections(self):
        """Настройка соединений с страницами"""
        # Получаем страницы из PageManager
        wizard_page = self.page_manager.get_page('wizard')
        if wizard_page:
            wizard_page.sequence_requested.connect(self._start_sequence)
            wizard_page.zone_selection_changed.connect(self._on_zone_changed)

        settings_page = self.page_manager.get_page('settings')
        if settings_page:
            settings_page.connect_requested.connect(self._on_connect_requested)
            settings_page.disconnect_requested.connect(self._on_disconnect_requested)
            settings_page.config_reload_requested.connect(self._reload_config)
            settings_page.status_message.connect(
                lambda msg, timeout: self.statusBar().showMessage(msg, timeout)
            )

        sequences_page = self.page_manager.get_page('sequences')
        if sequences_page:
            sequences_page.sequence_execute_requested.connect(self._start_sequence)
            sequences_page.sequence_edited.connect(self._on_sequence_edited)

        commands_page = self.page_manager.get_page('commands')
        if commands_page:
            commands_page.command_execute_requested.connect(self._execute_command)

        designer_page = self.page_manager.get_page('designer')
        if designer_page:
            designer_page.sequence_created.connect(self._on_sequence_created)

    def _setup_auto_connect(self):
        """Настройка автоподключения"""
        try:
            # Включаем автоподключение в ConnectionManager
            self.connection_manager.enable_auto_connect(True)
            
            # Получаем настройки автоподключения
            port = self.settings_manager.serial_settings.port
            if port and port.strip():
                # Выполняем автоподключение через ConnectionManager
                self.connection_manager.perform_auto_connect(
                    port, 
                    self.settings_manager.serial_settings.__dict__
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка настройки автоподключения: {e}")

    def _on_connection_status_changed(self, status: str, message: str):
        """Обработчик изменения статуса подключения"""
        try:
            # Обновляем индикатор подключения
            status_config = {
                "connected": ("● Подключено", "color: #50fa7b;"),
                "disconnected": ("● Отключено", "color: #ffb86c;"),
                "error": ("● Ошибка", "color: #ff5555;"),
                "connecting": ("● Подключение...", "color: #ffb86c;")
            }
            
            text, color = status_config.get(status, ("● Неизвестно", "color: #ff5555;"))
            self.connection_status.setText(text)
            self.connection_status.setStyleSheet(color)
            
            # Обновляем статусную строку
            if message:
                self.statusBar().showMessage(message, 3000)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса подключения: {e}")

    def _on_page_changed(self, page_name: str):
        """Обработчик изменения страницы"""
        self.logger.info(f"Страница изменена на: {page_name}")

    def _on_data_received(self, data: str):
        """Обработчик получения данных"""
        self.logger.debug(f"Получено: {data}")

        # Передаем данные исполнителю последовательности
        if hasattr(self, 'sequence_executor') and self.sequence_executor and self.sequence_executor.isRunning():
            self.sequence_executor.add_response(data)

        # Передаем в терминал если есть
        terminal_page = self.page_manager.get_page('commands')
        if terminal_page:
            terminal_page.add_command_output(f"Получено: {data}")

    def _on_error_occurred(self, error_type: str, message: str):
        """Обработчик ошибок"""
        self.logger.error(f"Ошибка {error_type}: {message}")
        self.statusBar().showMessage(f"Ошибка: {message}", 5000)

    def _on_connect_requested(self):
        """Обработчик запроса подключения"""
        try:
            settings = self.settings_manager.serial_settings
            if settings.port and settings.port.strip():
                # Отправляем событие подключения через EventBus
                event_bus.emit("connect_requested", 
                              port=settings.port, 
                              settings=settings.__dict__)
            else:
                QMessageBox.warning(self, "Предупреждение", "Порт не указан в настройках")
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса подключения: {e}")

    def _on_disconnect_requested(self):
        """Обработчик запроса отключения"""
        try:
            # Отправляем событие отключения через EventBus
            event_bus.emit("disconnect_requested")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки запроса отключения: {e}")

    def _start_sequence(self, sequence_name: str, next_step: int = 0):
        """Запуск последовательности команд"""
        if not self.connection_manager.is_connected():
            QMessageBox.warning(
                self,
                "Нет подключения",
                "Подключитесь к устройству перед запуском последовательности"
            )
            return

        # Останавливаем предыдущую последовательность
        if hasattr(self, 'sequence_executor') and self.sequence_executor and self.sequence_executor.isRunning():
            self.sequence_executor.stop()

        # Разворачиваем последовательность
        commands = self.sequence_manager.expand_sequence(sequence_name)
        if not commands:
            self.logger.error(f"Последовательность '{sequence_name}' пуста или не найдена")
            return

        # Создаем и запускаем исполнитель
        self.sequence_executor = CommandSequenceExecutor(
            self.serial_manager,
            commands,
            self.config_loader.sequence_keywords
        )

        # Подключаем сигналы
        self.sequence_executor.progress_updated.connect(self._on_sequence_progress)
        self.sequence_executor.command_sent.connect(self._on_command_sent)
        self.sequence_executor.sequence_finished.connect(
            lambda success, msg: self._on_sequence_finished(success, msg, next_step)
        )

        # Запускаем
        self.sequence_executor.start()
        self.logger.info(f"Запущена последовательность '{sequence_name}'")

    def _execute_command(self, command: str):
        """Выполнение отдельной команды"""
        if not self.connection_manager.is_connected():
            QMessageBox.warning(
                self,
                "Нет подключения",
                "Подключитесь к устройству перед выполнением команды"
            )
            return

        success = self.serial_manager.send_command(command)
        if success:
            self.logger.info(f"Команда выполнена: {command}")
            self.statusBar().showMessage(f"Команда выполнена: {command}", 3000)
        else:
            self.logger.error(f"Не удалось выполнить команду: {command}")
            self.statusBar().showMessage(f"Ошибка выполнения команды", 5000)

    def _on_sequence_progress(self, current: int, total: int):
        """Обновление прогресса последовательности"""
        # Обновляем прогресс на странице мастера
        wizard_page = self.page_manager.get_page('wizard')
        if wizard_page:
            wizard_page.update_progress(current, total)

        self.statusBar().showMessage(
            f"Выполнение: {current}/{total}", 1000
        )

    def _on_command_sent(self, command: str):
        """Обработка отправленной команды"""
        self.logger.info(f"Отправлено: {command}")

    def _on_sequence_finished(self, success: bool, message: str, next_step: int):
        """Обработка завершения последовательности"""
        self.logger.info(f"Последовательность завершена: {message}")

        # Уведомляем страницу мастера
        wizard_page = self.page_manager.get_page('wizard')
        if wizard_page:
            wizard_page.on_sequence_finished(success, next_step)

        if success:
            self.statusBar().showMessage("✓ " + message, 3000)
        else:
            self.statusBar().showMessage("✗ " + message, 5000)

    def _on_zone_changed(self, zones: Dict[str, bool]):
        """Обработка изменения выбора зон"""
        self.logger.info(f"Выбраны зоны: {zones}")

    def _on_sequence_created(self, sequence_name: str, commands: list):
        """Обработка создания последовательности в конструкторе"""
        self.config['sequences'][sequence_name] = commands
        self.config_loader.save_sequences(self.config['sequences'])
        self.logger.info(f"Создана последовательность: {sequence_name}")

    def _on_sequence_edited(self, sequence_name: str, commands: list):
        """Обработка редактирования последовательности"""
        self.config['sequences'][sequence_name] = commands
        self.config_loader.save_sequences(self.config['sequences'])
        self.logger.info(f"Отредактирована последовательность: {sequence_name}")

    def _reload_config(self):
        """Перезагрузка конфигурации"""
        try:
            self.logger.info("Начало перезагрузки конфигурации...")
            
            # Загружаем конфигурацию
            self.config = self.config_loader.load()
            
            # Обновляем SequenceManager
            self.sequence_manager = SequenceManager(
                self.config.get('sequences', {}),
                self.config.get('buttons', {})
            )
            
            # Отправляем событие перезагрузки конфигурации
            event_bus.emit("config_reloaded")
            
            self.statusBar().showMessage("Конфигурация перезагружена", 3000)
            self.logger.info("Конфигурация успешно перезагружена")

        except Exception as e:
            self.logger.error(f"Ошибка перезагрузки конфигурации: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка перезагрузки конфигурации:\n{e}"
            )

    def _toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True

    def _toggle_theme(self):
        """Переключение темы"""
        current = self.settings_manager.update_settings.theme
        new_theme = 'light' if current == 'dark' else 'dark'

        self.settings_manager.update_settings.theme = new_theme
        self.settings_manager.save_update_settings()

        # Применяем тему
        from main import apply_theme
        apply_theme(QApplication.instance(), new_theme)

        self.statusBar().showMessage(
            f"Тема изменена на {'светлую' if new_theme == 'light' else 'тёмную'}",
            3000
        )

    def _show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "<h2>Панель управления устройством</h2>"
            "<p><b>Версия:</b> 2.0 (Рефакторинг - Компонентная архитектура)</p>"
            "<p><b>Технологии:</b> Python, PySide6, Serial, EventBus</p>"
            "<p>© 2024 Все права защищены</p>"
        )

    def keyPressEvent(self, event: QKeyEvent):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key.Key_Escape:
            if self.is_fullscreen:
                self._toggle_fullscreen()
            else:
                self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            self.logger.info("Начало процесса закрытия приложения...")
            
            # Очищаем компоненты
            self._cleanup_components()
            
            # Останавливаем последовательность
            if hasattr(self, 'sequence_executor') and self.sequence_executor:
                if self.sequence_executor.isRunning():
                    self.sequence_executor.stop()
            
            # Сохраняем настройки
            if hasattr(self, 'settings_manager'):
                self.settings_manager.save_all()
            
            self.logger.info("Приложение успешно закрыто")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {e}")
            event.accept()

    def _cleanup_components(self):
        """Очистка ресурсов компонентов"""
        try:
            # Очищаем компоненты
            if hasattr(self, 'page_manager'):
                self.page_manager.cleanup()
            
            if hasattr(self, 'navigation_manager'):
                self.navigation_manager.cleanup()
            
            if hasattr(self, 'connection_manager'):
                self.connection_manager.cleanup()
            
            # Очищаем EventBus
            event_bus.cleanup()
            
            self.logger.info("Компоненты очищены")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки компонентов: {e}")
