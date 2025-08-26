"""
Главное окно приложения
"""
import logging
from typing import Dict, Optional
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QKeyEvent, QMouseEvent
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
from core.multizone_manager import MultizoneManager

from monitoring.monitoring_manager import MonitoringManager
from core.flag_manager import FlagManager
from core.tag_manager import TagManager
from core.tag_validator import TagValidator
from core.tag_processor import TagProcessor
from ui.pages.wizard_page import WizardPage
from ui.pages.settings_page import SettingsPage
from ui.pages.sequences_page import SequencesPage
from ui.pages.commands_page import CommandsPage
from ui.pages.designer_page import DesignerPage
from ui.pages.firmware_page import FirmwarePage
from ui.pages.flags_page import FlagsPage
from ui.pages.signals_page import SignalsPage
from ui.widgets.modern_widgets import ModernCard
from ui.widgets.info_panel import InfoPanel
from ui.dialogs.tag_dialogs import TagDialogManager


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        try:
            # Создаем сервисы напрямую (упрощенный подход)
            self.logger.info("Создание сервисов напрямую...")
            self._create_services_directly()

            # Сервисы уже созданы в _create_services_directly()
            self.logger.info("Все сервисы инициализированы")

            # Загрузка конфигурации
            self.logger.info("Загрузка конфигурации...")
            self.config = self.config_loader.load()
            
            # Проверяем, что конфигурация загружена
            if self.config is None:
                self.logger.warning("Конфигурация не загружена, создаем пустую")
                self.config = {}
            
            self.logger.info("Конфигурация загружена")
            
            # Загружаем флаги из конфигурации
            flags = self.config.get('flags', {})
            for flag_name, value in flags.items():
                self.sequence_manager.set_flag(flag_name, value)
            
            self.logger.info("SequenceManager инициализирован")

            # Текущий исполнитель последовательности
            self.sequence_executor: Optional[CommandSequenceExecutor] = None

            # Настройка UI
            self.logger.info("Настройка UI...")
            self._setup_ui()
            self.logger.info("UI настроен")

            # Настройка соединений
            self.logger.info("Настройка соединений...")
            self._setup_connections()
            self._setup_tag_connections()
            self.logger.info("Соединения настроены")

            # Автоподключение с обработкой ошибок
            if self.settings_manager.update_settings.auto_connect:
                self.logger.info("Настройка автоподключения...")
                # Запускаем с задержкой и обработкой ошибок
                QTimer.singleShot(2000, self._safe_auto_connect)
            else:
                self.logger.info("Автоподключение отключено в настройках")
            
            # Периодическая проверка состояния подключения
            self.connection_check_timer = QTimer()
            self.connection_check_timer.timeout.connect(self._check_connection_status)
            self.connection_check_timer.start(5000)  # Проверяем каждые 5 секунд

            # Включаем отслеживание мыши для свайпа
            self.setMouseTracking(True)

            # Запуск в обычном режиме (не полноэкранном)
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


    
    def _create_services_directly(self):
        """Создание сервисов напрямую без DI"""
        self.logger.info("Создание сервисов напрямую...")
        
        # Создаем сервисы напрямую
        self.config_loader = ConfigLoader()
        self.settings_manager = SettingsManager()
        
        # Создаем SignalManager для обработки входящих сигналов UART
        from core.signal_manager import SignalManager
        from core.signal_processor import SignalProcessor
        from core.signal_validator import SignalValidator
        
        self.signal_manager = SignalManager(flag_manager=None)  # Будет установлен после создания flag_manager
        
        # Создаем SerialManager с интеграцией SignalManager
        self.serial_manager = SerialManager(signal_manager=self.signal_manager)
        
        self.multizone_manager = MultizoneManager()
        self.flag_manager = FlagManager()
        
        # Устанавливаем flag_manager в signal_manager для обновления переменных
        self.signal_manager.flag_manager = self.flag_manager
        
        # Загружаем конфигурацию сигналов
        try:
            signal_mappings = self.config_loader.get_signal_mappings()
            self.signal_manager.register_signals(signal_mappings)
            self.logger.info(f"Зарегистрировано {len(signal_mappings)} сигналов")
        except Exception as e:
            self.logger.warning(f"Ошибка загрузки конфигурации сигналов: {e}")
        
        self.tag_manager = TagManager()
        self.tag_validator = TagValidator()
        self.tag_processor = TagProcessor()
        self.tag_dialog_manager = TagDialogManager()
        self.monitoring_manager = MonitoringManager(self.logger, multizone_manager=self.multizone_manager)
        
        # Создаем CommandExecutorFactory
        from core.command_executor import CommandExecutorFactory
        self.command_executor_factory = CommandExecutorFactory()
        
        # Создаем SequenceManager с зависимостями
        self.sequence_manager = SequenceManager(
            config={},  # Пустая конфигурация последовательностей
            buttons_config={},  # Пустая конфигурация кнопок
            flag_manager=self.flag_manager
        )
        
        self.logger.info("Сервисы созданы напрямую")
    
    def _setup_tag_connections(self):
        """Настройка соединений для системы тегов"""
        try:
            # Подключаем обработчики для диалогов тегов
            if hasattr(self, 'tag_dialog_manager'):
                # Обработчик для диалога _wanted
                self.tag_dialog_manager.on_wanted_dialog_result = self._on_wanted_dialog_result
                self.logger.info("Обработчики тегов подключены")
        except Exception as e:
            self.logger.error(f"Ошибка при настройке соединений тегов: {e}")
    
    def _on_wanted_dialog_result(self, result: str):
        """
        Обработчик результата диалога _wanted
        
        Args:
            result: Результат диалога ('check_fluids' или 'cancel')
        """
        try:
            self.logger.info(f"Получен результат диалога _wanted: {result}")
            
            if result == 'check_fluids':
                # Пользователь подтвердил проверку жидкостей
                self.logger.info("Пользователь подтвердил проверку жидкостей")
                
                # Устанавливаем флаг wanted в False
                if hasattr(self, 'flag_manager'):
                    self.flag_manager.set_flag('wanted', False)
                    self.logger.info("Флаг 'wanted' установлен в False")
                
                # Показываем уведомление
                QMessageBox.information(
                    self,
                    "Проверка жидкостей",
                    "Спасибо! Выполнение команды будет продолжено.",
                    QMessageBox.Ok
                )
                
                # Возобновляем выполнение команды
                self._resume_command_execution()
                
            elif result == 'cancel':
                # Пользователь отменил операцию
                self.logger.info("Пользователь отменил операцию")
                
                # Показываем уведомление
                QMessageBox.information(
                    self,
                    "Операция отменена",
                    "Операция была отменена пользователем.",
                    QMessageBox.Ok
                )
                
                # Останавливаем выполнение команды
                self._cancel_command_execution()
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке результата диалога _wanted: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Произошла ошибка при обработке результата диалога: {e}",
                QMessageBox.Ok
            )
    
    def _resume_command_execution(self):
        """Возобновление выполнения команды после обработки тега"""
        try:
            self.logger.info("Возобновление выполнения команды")
            
            # Здесь должна быть логика возобновления выполнения
            # Пока просто логируем
            self.logger.info("Выполнение команды возобновлено")
            
        except Exception as e:
            self.logger.error(f"Ошибка при возобновлении выполнения команды: {e}")
    
    def _cancel_command_execution(self):
        """Отмена выполнения команды"""
        try:
            self.logger.info("Отмена выполнения команды")
            
            # Здесь должна быть логика отмены выполнения
            # Пока просто логируем
            self.logger.info("Выполнение команды отменено")
            
        except Exception as e:
            self.logger.error(f"Ошибка при отмене выполнения команды: {e}")

    def _setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Система управления устройством")
        self.setMinimumSize(1200, 800)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Левая панель навигации (интегрированная в layout)
        self._create_sidebar()
        main_layout.addWidget(self.sidebar, 0)  # Добавляем в layout с растяжкой 0

        # Область контента
        self._create_content_area()
        main_layout.addWidget(self.content_area, 1)

        # Информационная панель (выдвигающаяся справа)
        self._create_info_panel()

        # Статусная строка
        self.statusBar().showMessage("Готов к работе")

        # Добавляем панель управления флагами
        self._setup_flag_control_panel()

    def _create_sidebar(self):
        """Создание левой панели навигации"""
        self.logger.info("Создание левой панели навигации...")
        
        # Создаем левую панель
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)
        
        # Добавляем анимацию для сворачивания/разворачивания
        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.sidebar_animation.setDuration(300)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.sidebar_animation.finished.connect(self._on_sidebar_animation_finished)

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
        
        # Панель видима по умолчанию
        self.sidebar_visible = True
        
        self.logger.info("Левая панель навигации создана")

    def _create_menu_button(self, parent_layout):
        """Создание кнопки меню"""
        # Контейнер для кнопок
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 5, 10, 5)
        button_layout.setSpacing(5)

        # Кнопка меню
        self.menu_button = QToolButton()
        self.menu_button.setText("☰")
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.menu_button.clicked.connect(self._toggle_sidebar)
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setStyleSheet("""
            QToolButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #505050;
            }
        """)

        # Кнопка закрытия панели
        self.close_sidebar_button = QPushButton("✕")
        self.close_sidebar_button.setFixedSize(40, 40)
        self.close_sidebar_button.clicked.connect(self._hide_sidebar)
        self.close_sidebar_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)

        menu = QMenu(self)

        actions = [
            ('📊 Информационная панель', self._toggle_info_panel),
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

        self.menu_button.setMenu(menu)
        
        button_layout.addWidget(self.menu_button)
        button_layout.addWidget(self.close_sidebar_button)
        button_layout.addStretch()
        
        parent_layout.addWidget(button_container)

    def _create_header(self, parent_layout):
        """Создание заголовка"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 20)

        title = QLabel("Навигация")
        title.setObjectName("sidebar_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Панель управления")
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
            ("wizard", "🪄 Мастер настройки", True),
            ("sequences", "📋 Последовательности", False),
            ("commands", "⚡ Команды управления", False),
            ("flags", "🚩 Управление флагами", False),
            ("signals", "📡 Сигналы UART", False),
            ("designer", "🔧 Конструктор", False),
            ("settings", "⚙️ Настройки", False),
            ("firmware", "💾 Прошивка", False),
        ]

        for key, text, checked in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.setObjectName("nav_button")
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
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

    def _create_content_area(self):
        """Создание области контента"""
        # Создаем контейнер для контента с кнопкой информационной панели
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Верхняя панель с кнопкой информационной панели
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 5, 10, 5)
        top_layout.setSpacing(0)
        
        # Добавляем растяжку слева
        top_layout.addStretch()
        
        # Кнопка информационной панели
        self.info_panel_button = QPushButton("📊")
        self.info_panel_button.setToolTip("Информационная панель")
        self.info_panel_button.setFixedSize(40, 40)
        self.info_panel_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """)
        self.info_panel_button.clicked.connect(self._toggle_info_panel)
        top_layout.addWidget(self.info_panel_button)
        
        content_layout.addWidget(top_panel)
        
        # Область контента
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        # Создаем страницы
        self.logger.info("Создание страниц...")
        
        self.logger.info("Создание WizardPage...")
        self.pages = {
            'wizard': WizardPage(self.config.get('wizard', {}), self.multizone_manager),
        }
        self.logger.info("WizardPage создана")
        
        self.logger.info("Создание SettingsPage...")
        self.pages['settings'] = SettingsPage(self.settings_manager)
        self.logger.info("SettingsPage создана")
        
        self.logger.info("Создание SequencesPage...")
        self.pages['sequences'] = SequencesPage(self.config.get('sequences', {}))
        self.logger.info("SequencesPage создана")
        
        self.logger.info("Создание CommandsPage...")
        self.pages['commands'] = CommandsPage(self.config.get('buttons', {}))
        self.logger.info("CommandsPage создана")
        
        self.logger.info("Создание DesignerPage...")
        self.pages['designer'] = DesignerPage(self.config.get('buttons', {}))
        self.logger.info("DesignerPage создана")
        
        self.logger.info("Создание FirmwarePage...")
        self.pages['firmware'] = FirmwarePage()
        self.logger.info("FirmwarePage создана")
        
        self.logger.info("Создание FlagsPage...")
        self.pages['flags'] = FlagsPage(self.sequence_manager)
        self.logger.info("FlagsPage создана")
        
        self.logger.info("Создание SignalsPage...")
        self.pages['signals'] = SignalsPage(self.signal_manager, self.flag_manager, self.config_loader)
        self.logger.info("SignalsPage создана")

        for page in self.pages.values():
            self.stacked_widget.addWidget(page)
        
        self.logger.info("Все страницы добавлены в stacked_widget")
        
        # Сохраняем ссылку на контейнер как content_area
        self.content_area = content_container

    def _create_info_panel(self):
        """Создание информационной панели"""
        self.logger.info("Создание информационной панели...")
        
        # Создаем информационную панель
        self.info_panel = InfoPanel(self.monitoring_manager, self)
        
        # Устанавливаем начальную позицию (скрыта справа)
        self.info_panel.setGeometry(
            self.width(),
            0,
            self.info_panel.get_panel_width(),
            self.height()
        )
        
        # Запускаем мониторинг
        self.monitoring_manager.start_monitoring()
        
        # Таймер для обновления данных мониторинга
        self.monitoring_update_timer = QTimer()
        self.monitoring_update_timer.timeout.connect(self._update_monitoring_data)
        self.monitoring_update_timer.start(5000)  # Обновляем каждые 5 секунд
        
        self.logger.info("Информационная панель создана")

    def _update_monitoring_data(self):
        """Обновление данных мониторинга"""
        try:
            if hasattr(self, 'info_panel'):
                self.info_panel.update_monitoring_data()
        except Exception as e:
            self.logger.error(f"Ошибка обновления данных мониторинга: {e}")

    def _setup_connections(self):
        """Настройка соединений сигналов и слотов"""
        # Подключение сигналов от serial_manager
        if self.serial_manager.reader_thread:
            self.serial_manager.reader_thread.data_received.connect(
                self._on_data_received
            )
            self.serial_manager.reader_thread.error_occurred.connect(
                self._on_serial_error
            )
            # Подключение сигнала обработки сигналов UART
            self.serial_manager.reader_thread.signal_processed.connect(
                self._on_signal_processed
            )

        # Подключение сигналов от страниц
        wizard_page = self.pages.get('wizard')
        if wizard_page:
            wizard_page.sequence_requested.connect(self._start_sequence)
            wizard_page.zone_selection_changed.connect(self._on_zone_changed)

        settings_page = self.pages.get('settings')
        if settings_page:
            settings_page.connect_requested.connect(self._connect_serial)
            settings_page.disconnect_requested.connect(self._disconnect_serial)
            settings_page.config_reload_requested.connect(self._reload_config)
            settings_page.status_message.connect(
                lambda msg, timeout: self.statusBar().showMessage(msg, timeout)
            )

        sequences_page = self.pages.get('sequences')
        if sequences_page:
            sequences_page.sequence_execute_requested.connect(self._start_sequence)
            sequences_page.sequence_edited.connect(self._on_sequence_edited)

        commands_page = self.pages.get('commands')
        if commands_page:
            commands_page.command_execute_requested.connect(self._execute_command)

        designer_page = self.pages.get('designer')
        if designer_page:
            designer_page.sequence_created.connect(self._on_sequence_created)

    def _switch_page(self, page_name: str):
        """Переключение страницы"""
        # Обновляем состояние кнопок
        for name, button in self.nav_buttons.items():
            button.setChecked(name == page_name)

        # Переключаем страницу
        page_indices = {
            'wizard': 0,
            'sequences': 1,
            'commands': 2,
            'designer': 3,
            'settings': 4,
            'firmware': 5,
        }

        index = page_indices.get(page_name, 0)
        self.stacked_widget.setCurrentIndex(index)

        self.logger.info(f"Переключено на страницу: {page_name}")

    def _safe_auto_connect(self):
        """Безопасное автоматическое подключение при запуске с улучшенной обработкой ошибок"""
        try:
            self.logger.info("Начало безопасного автоподключения...")
            
            # Проверяем доступность settings_manager
            if not hasattr(self, 'settings_manager') or not self.settings_manager:
                self.logger.error("SettingsManager недоступен")
                self.statusBar().showMessage("Ошибка: SettingsManager недоступен", 5000)
                return
            
            port = self.settings_manager.serial_settings.port
            self.logger.info(f"Попытка подключения к порту: {port}")
            
            # Проверяем, что порт не пустой
            if not port or port.strip() == '':
                self.logger.warning("Порт не указан в настройках")
                self.statusBar().showMessage("Порт не указан в настройках", 5000)
                return
            
            # Получаем список портов с таймаутом и обработкой ошибок
            try:
                self.logger.info("Получение списка доступных портов...")
                available_ports = SerialManager.get_available_ports()
                
                if not available_ports:
                    self.logger.warning("Не удалось получить список портов")
                    self.statusBar().showMessage("Не удалось получить список портов", 5000)
                    return
                
                self.logger.info(f"Доступные порты: {available_ports}")

                if port in available_ports:
                    self.logger.info(f"Порт {port} найден, подключаемся...")
                    # Запускаем подключение с небольшой задержкой
                    QTimer.singleShot(500, lambda: self._safe_connect_serial(port))
                else:
                    self.logger.warning(f"Порт {port} не найден в списке доступных")
                    self.statusBar().showMessage(
                        f"Порт {port} недоступен. Доступные: {', '.join(available_ports)}", 5000
                    )
            except ImportError as e:
                self.logger.error(f"Ошибка импорта SerialManager: {e}")
                self.statusBar().showMessage("Ошибка: SerialManager недоступен", 5000)
            except PermissionError as e:
                self.logger.error(f"Ошибка прав доступа к портам: {e}")
                self.statusBar().showMessage("Ошибка прав доступа к портам", 5000)
            except OSError as e:
                self.logger.error(f"Системная ошибка при получении портов: {e}")
                self.statusBar().showMessage("Системная ошибка при получении портов", 5000)
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка получения списка портов: {e}")
                self.statusBar().showMessage("Ошибка получения списка портов", 5000)
                
        except AttributeError as e:
            self.logger.error(f"Ошибка доступа к атрибутам: {e}")
            self.statusBar().showMessage("Ошибка доступа к настройкам", 5000)
        except Exception as e:
            self.logger.error(f"Критическая ошибка безопасного автоподключения: {e}")
            self.statusBar().showMessage("Критическая ошибка автоподключения", 5000)

    def _safe_connect_serial(self, port: str):
        """Безопасное подключение к Serial порту с улучшенной обработкой ошибок"""
        try:
            self.logger.info(f"Безопасное подключение к {port}...")
            
            # Проверяем доступность менеджеров
            if not hasattr(self, 'settings_manager') or not self.settings_manager:
                self.logger.error("SettingsManager недоступен")
                self._update_connection_status("error", "SettingsManager недоступен")
                return
                
            if not hasattr(self, 'serial_manager') or not self.serial_manager:
                self.logger.error("SerialManager недоступен")
                self._update_connection_status("error", "SerialManager недоступен")
                return
            
            # Проверяем настройки
            try:
                settings = self.settings_manager.serial_settings
                self.logger.info(f"Параметры подключения: {settings}")
            except AttributeError as e:
                self.logger.error(f"Ошибка доступа к настройкам Serial: {e}")
                self._update_connection_status("error", "Ошибка доступа к настройкам")
                return
            
            # Выполняем подключение с обработкой ошибок
            try:
                success = self.serial_manager.connect(
                    port=port,
                    baudrate=settings.baudrate,
                    bytesize=settings.bytesize,
                    parity=settings.parity,
                    stopbits=settings.stopbits,
                    timeout=settings.timeout
                )
            except PermissionError as e:
                self.logger.error(f"Ошибка прав доступа к порту {port}: {e}")
                self._update_connection_status("error", f"Нет прав доступа к порту {port}")
                return
            except OSError as e:
                self.logger.error(f"Системная ошибка подключения к {port}: {e}")
                self._update_connection_status("error", f"Системная ошибка подключения")
                return
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка подключения к {port}: {e}")
                self._update_connection_status("error", f"Неожиданная ошибка подключения")
                return
            
            if success:
                self._update_connection_status("connected", f"Подключено к {port}")
                self.logger.info(f"Успешно подключено к {port}")
                
                # Подключаем обработчики данных с обработкой ошибок
                self._setup_data_handlers()
            else:
                self._update_connection_status("error", f"Не удалось подключиться к {port}")
                self.logger.error(f"Не удалось подключиться к {port}")
                
        except Exception as e:
            self.logger.error(f"Критическая ошибка безопасного подключения: {e}")
            self._update_connection_status("error", f"Критическая ошибка подключения")

    def _auto_connect(self):
        """Автоматическое подключение при запуске (устаревший метод)"""
        self._safe_auto_connect()

    def _connect_serial(self):
        """Подключение к Serial порту с улучшенной обработкой ошибок"""
        try:
            self.logger.info("Начало подключения к Serial порту...")
            
            # Проверяем доступность менеджеров
            if not hasattr(self, 'settings_manager') or not self.settings_manager:
                self.logger.error("SettingsManager недоступен")
                QMessageBox.critical(self, "Ошибка", "SettingsManager недоступен")
                return
                
            if not hasattr(self, 'serial_manager') or not self.serial_manager:
                self.logger.error("SerialManager недоступен")
                QMessageBox.critical(self, "Ошибка", "SerialManager недоступен")
                return
            
            settings = self.settings_manager.serial_settings
            self.logger.info(f"Параметры подключения: {settings}")

            # Проверяем, что порт указан
            if not settings.port or settings.port.strip() == '':
                self.logger.error("Порт не указан в настройках")
                QMessageBox.warning(self, "Предупреждение", "Порт не указан в настройках")
                return

            try:
                success = self.serial_manager.connect(
                    port=settings.port,
                    baudrate=settings.baudrate,
                    bytesize=settings.bytesize,
                    parity=settings.parity,
                    stopbits=settings.stopbits,
                    timeout=settings.timeout
                )
                self.logger.info(f"Результат подключения: {success}")
            except PermissionError as e:
                self.logger.error(f"Ошибка прав доступа к порту {settings.port}: {e}")
                QMessageBox.critical(self, "Ошибка", f"Нет прав доступа к порту {settings.port}")
                success = False
            except OSError as e:
                self.logger.error(f"Системная ошибка подключения: {e}")
                QMessageBox.critical(self, "Ошибка", f"Системная ошибка подключения: {e}")
                success = False
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка подключения: {e}")
                QMessageBox.critical(self, "Ошибка", f"Неожиданная ошибка подключения: {e}")
                success = False

            if success:
                self._update_connection_status("connected", f"Подключено к {settings.port}")
                # Подключаем обработчики с обработкой ошибок
                self._setup_data_handlers()
            else:
                self._update_connection_status("error", f"Не удалось подключиться к {settings.port}")
                
        except Exception as e:
            self.logger.error(f"Критическая ошибка подключения: {e}")
            QMessageBox.critical(self, "Критическая ошибка", f"Критическая ошибка подключения: {e}")

    def _disconnect_serial(self):
        """Отключение от Serial порта с улучшенной обработкой ошибок"""
        try:
            self.logger.info("Отключение от Serial порта...")
            
            # Проверяем доступность SerialManager
            if not hasattr(self, 'serial_manager') or not self.serial_manager:
                self.logger.error("SerialManager недоступен")
                self._update_connection_status("error", "SerialManager недоступен")
                return
            
            # Отключаем обработчики данных перед отключением
            if self.serial_manager.reader_thread:
                try:
                    self.serial_manager.reader_thread.data_received.disconnect()
                    self.serial_manager.reader_thread.error_occurred.disconnect()
                except:
                    pass  # Игнорируем ошибки отключения обработчиков
            
            # Отключаемся от порта
            try:
                self.serial_manager.disconnect()
                self._update_connection_status("disconnected", "Отключено")
                self.logger.info("Отключение завершено")
            except OSError as e:
                self.logger.error(f"Системная ошибка отключения: {e}")
                self._update_connection_status("error", f"Системная ошибка отключения")
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка отключения: {e}")
                self._update_connection_status("error", f"Неожиданная ошибка отключения")
                
        except Exception as e:
            self.logger.error(f"Критическая ошибка отключения: {e}")
            self._update_connection_status("error", f"Критическая ошибка отключения")

    def _on_data_received(self, data: str):
        """Обработка полученных данных"""
        self.logger.debug(f"Получено: {data}")

        # Передаем данные исполнителю последовательности
        if self.sequence_executor and self.sequence_executor.isRunning():
            self.sequence_executor.add_response(data)

        # Передаем в терминал если есть
        terminal_page = self.pages.get('commands')
        if terminal_page:
            terminal_page.add_command_output(f"Получено: {data}")

    def _on_signal_processed(self, signal_name: str, variable_name: str, value: str):
        """
        Обработка успешно обработанного сигнала UART
        
        Args:
            signal_name: Имя сигнала
            variable_name: Имя переменной
            value: Значение переменной
        """
        try:
            self.logger.info(f"Сигнал обработан: {signal_name} -> {variable_name} = {value}")
            
            # Показываем уведомление в статусной строке
            self.statusBar().showMessage(
                f"Сигнал {signal_name}: {variable_name} = {value}", 
                3000
            )
            
            # Передаем информацию в терминал если есть
            terminal_page = self.pages.get('commands')
            if terminal_page:
                terminal_page.add_command_output(
                    f"Сигнал {signal_name}: {variable_name} = {value}"
                )
            
            # Передаем сигнал на страницу сигналов если есть
            signals_page = self.pages.get('signals')
            if signals_page:
                signals_page.on_signal_processed(signal_name, variable_name, value)
            
            # Обновляем информацию о сигналах в UI если есть
            self._update_signal_display(signal_name, variable_name, value)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сигнала {signal_name}: {e}")

    def _update_signal_display(self, signal_name: str, variable_name: str, value: str):
        """
        Обновление отображения сигналов в UI
        
        Args:
            signal_name: Имя сигнала
            variable_name: Имя переменной
            value: Значение переменной
        """
        try:
            # Здесь можно добавить обновление UI для отображения сигналов
            # Например, обновление панели мониторинга или специальной страницы сигналов
            pass
        except Exception as e:
            self.logger.error(f"Ошибка обновления отображения сигнала: {e}")

    def _on_serial_error(self, error: str):
        """Обработка ошибки Serial"""
        self.logger.error(f"Ошибка Serial: {error}")
        self.statusBar().showMessage(f"Ошибка: {error}", 5000)
        
        # Обновляем статус подключения
        self.connection_status.setText("● Ошибка")
        self.connection_status.setStyleSheet("color: #ff5555;")

    def _check_connection_status(self):
        """Проверка состояния подключения с обработкой ошибок"""
        try:
            if not hasattr(self, 'serial_manager') or not self.serial_manager:
                self._update_connection_status("error", "SerialManager недоступен")
                return
                
            if self.serial_manager.is_connected:
                self._update_connection_status("connected", "Подключено")
            else:
                self._update_connection_status("disconnected", "Отключено")
        except AttributeError as e:
            self.logger.error(f"Ошибка доступа к атрибутам SerialManager: {e}")
            self._update_connection_status("error", "Ошибка доступа к SerialManager")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка проверки состояния подключения: {e}")
            self._update_connection_status("error", "Неожиданная ошибка проверки")

    def _update_connection_status(self, status: str, message: str = ""):
        """Обновление статуса подключения с recovery стратегией"""
        try:
            if not hasattr(self, 'connection_status'):
                self.logger.error("connection_status недоступен")
                return
                
            status_config = {
                "connected": ("● Подключено", "color: #50fa7b;"),
                "disconnected": ("● Отключено", "color: #ffb86c;"),
                "error": ("● Ошибка", "color: #ff5555;"),
                "connecting": ("● Подключение...", "color: #ffb86c;")
            }
            
            text, color = status_config.get(status, ("● Неизвестно", "color: #ff5555;"))
            self.connection_status.setText(text)
            self.connection_status.setStyleSheet(color)
            
            if message:
                self.statusBar().showMessage(message, 3000)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса подключения: {e}")
            # Fallback - пытаемся обновить только статусную строку
            try:
                if message:
                    self.statusBar().showMessage(f"Ошибка статуса: {message}", 3000)
            except Exception as fallback_error:
                self.logger.error(f"Fallback обновления статуса также не удался: {fallback_error}")

    def _setup_data_handlers(self):
        """Настройка обработчиков данных с recovery стратегией"""
        try:
            if not hasattr(self, 'serial_manager') or not self.serial_manager:
                self.logger.error("SerialManager недоступен для настройки обработчиков")
                return
                
            if not self.serial_manager.reader_thread:
                self.logger.warning("Reader thread недоступен")
                return
                
            # Отключаем старые обработчики для избежания дублирования
            try:
                self.serial_manager.reader_thread.data_received.disconnect()
            except:
                pass  # Игнорируем ошибки отключения
                
            try:
                self.serial_manager.reader_thread.error_occurred.disconnect()
            except:
                pass  # Игнорируем ошибки отключения
                
            try:
                self.serial_manager.reader_thread.signal_processed.disconnect()
            except:
                pass  # Игнорируем ошибки отключения
            
            # Подключаем новые обработчики
            self.serial_manager.reader_thread.data_received.connect(
                self._on_data_received
            )
            self.serial_manager.reader_thread.error_occurred.connect(
                self._on_serial_error
            )
            self.serial_manager.reader_thread.signal_processed.connect(
                self._on_signal_processed
            )
            self.logger.info("Обработчики данных подключены")
            
        except Exception as e:
            self.logger.error(f"Ошибка настройки обработчиков данных: {e}")

    def _recover_ui_components(self):
        """Recovery стратегия для UI компонентов"""
        try:
            self.logger.info("Запуск recovery стратегии для UI компонентов...")
            
            # Восстанавливаем статус подключения
            if hasattr(self, 'connection_status'):
                self._check_connection_status()
            
            # Восстанавливаем обработчики данных
            if hasattr(self, 'serial_manager') and self.serial_manager and self.serial_manager.is_connected:
                self._setup_data_handlers()
            
            # Обновляем страницы
            for page_name, page in self.pages.items():
                try:
                    if hasattr(page, 'refresh'):
                        page.refresh()
                except Exception as e:
                    self.logger.error(f"Ошибка обновления страницы {page_name}: {e}")
            
            self.logger.info("Recovery стратегия завершена")
            
        except Exception as e:
            self.logger.error(f"Ошибка recovery стратегии: {e}")

    def _start_sequence(self, sequence_name: str, next_step: int = 0):
        """Запуск последовательности команд"""
        if not self.serial_manager.is_connected:
            QMessageBox.warning(
                self,
                "Нет подключения",
                "Подключитесь к устройству перед запуском последовательности"
            )
            return

        # Останавливаем предыдущую последовательность
        if self.sequence_executor and self.sequence_executor.isRunning():
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
            self.config_loader.sequence_keywords,
            multizone_manager=self.multizone_manager
        )
        
        # Подключаем сигнал для записи мультизональной статистики
        self.sequence_executor.sequence_finished.connect(self._on_sequence_finished)

        # Подключаем сигналы
        self.sequence_executor.progress_updated.connect(self._on_sequence_progress)
        self.sequence_executor.command_sent.connect(self._on_command_sent)
        self.sequence_executor.sequence_finished.connect(
            lambda success, msg: self._on_sequence_finished(success, msg, next_step)
        )
        self.sequence_executor.zone_status_updated.connect(self._on_zone_status_updated)

        # Запускаем
        self.sequence_executor.start()
        self.logger.info(f"Запущена последовательность '{sequence_name}'")

    def _execute_command(self, command: str):
        """Выполнение отдельной команды"""
        if not self.serial_manager.is_connected:
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
        wizard_page = self.pages.get('wizard')
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

        # Записываем мультизональную статистику
        self._record_multizone_execution(success, message)

        # Уведомляем страницу мастера
        wizard_page = self.pages.get('wizard')
        if wizard_page:
            wizard_page.on_sequence_finished(success, next_step)

        if success:
            self.statusBar().showMessage("✓ " + message, 3000)
        else:
            self.statusBar().showMessage("✗ " + message, 5000)

    def _on_zone_status_updated(self, zone_id: int, status: str):
        """Обработка обновления статуса зоны"""
        try:
            self.logger.info(f"Обновление статуса зоны {zone_id}: {status}")
            
            # Обновляем UI зон
            if hasattr(self, 'pages') and 'wizard' in self.pages:
                wizard_page = self.pages['wizard']
                if hasattr(wizard_page, 'update_zone_status'):
                    wizard_page.update_zone_status(zone_id, status)
            
            # Обновляем статус в статусной строке
            zone_names = {1: "Зона 1", 2: "Зона 2", 3: "Зона 3", 4: "Зона 4"}
            zone_name = zone_names.get(zone_id, f"Зона {zone_id}")
            self.statusBar().showMessage(f"{zone_name}: {status}", 3000)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки обновления статуса зоны {zone_id}: {e}")

    def _record_multizone_execution(self, success: bool, message: str):
        """Запись мультизонального выполнения в мониторинг"""
        try:
            if not self.multizone_manager or not self.monitoring_manager:
                return
            
            # Получаем активные зоны
            active_zones = self.multizone_manager.get_active_zones()
            if not active_zones:
                return  # Не мультизональная команда
            
            # Определяем команду из сообщения или контекста
            command = "multizone_command"  # По умолчанию
            if hasattr(self, 'sequence_executor') and self.sequence_executor:
                # Можно попытаться получить команду из исполнителя
                pass
            
            # Записываем в мониторинг
            self.monitoring_manager.record_multizone_execution(
                zones=active_zones,
                command=command,
                success=success,
                execution_time=0.0,  # Можно добавить измерение времени
                error_message=message if not success else None
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка записи мультизонального выполнения: {e}")

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
        """Перезагрузка конфигурации с улучшенной обработкой ошибок"""
        try:
            self.logger.info("Начало перезагрузки конфигурации...")
            
            # Проверяем доступность ConfigLoader
            if not hasattr(self, 'config_loader') or not self.config_loader:
                self.logger.error("ConfigLoader недоступен")
                QMessageBox.critical(self, "Ошибка", "ConfigLoader недоступен")
                return
            
            # Загружаем конфигурацию с обработкой ошибок
            try:
                self.config = self.config_loader.load()
                self.logger.info("Конфигурация загружена")
            except FileNotFoundError as e:
                self.logger.error(f"Файл конфигурации не найден: {e}")
                QMessageBox.critical(self, "Ошибка", f"Файл конфигурации не найден:\n{e}")
                return
            except PermissionError as e:
                self.logger.error(f"Ошибка прав доступа к файлу конфигурации: {e}")
                QMessageBox.critical(self, "Ошибка", f"Нет прав доступа к файлу конфигурации:\n{e}")
                return
            except Exception as e:
                self.logger.error(f"Ошибка загрузки конфигурации: {e}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки конфигурации:\n{e}")
                return
            
            # Обновляем SequenceManager
            try:
                self.sequence_manager = SequenceManager(
                    self.config.get('sequences', {}),
                    self.config.get('buttons', {})
                )
                self.logger.info("SequenceManager обновлен")
            except Exception as e:
                self.logger.error(f"Ошибка обновления SequenceManager: {e}")
                QMessageBox.warning(self, "Предупреждение", f"Ошибка обновления SequenceManager:\n{e}")

            # Обновляем страницы с обработкой ошибок
            if hasattr(self, 'pages'):
                for page_name, page in self.pages.items():
                    try:
                        if hasattr(page, 'refresh'):
                            page.refresh()
                    except Exception as e:
                        self.logger.error(f"Ошибка обновления страницы {page_name}: {e}")
                        # Продолжаем обновление других страниц
            
            # Запускаем recovery стратегию для UI компонентов
            try:
                self._recover_ui_components()
            except Exception as e:
                self.logger.error(f"Ошибка recovery стратегии: {e}")

            self.statusBar().showMessage("Конфигурация перезагружена", 3000)
            self.logger.info("Конфигурация успешно перезагружена")

        except Exception as e:
            self.logger.error(f"Критическая ошибка перезагрузки конфигурации: {e}")
            QMessageBox.critical(
                self,
                "Критическая ошибка",
                f"Критическая ошибка перезагрузки конфигурации:\n{e}"
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

    def _toggle_info_panel(self):
        """Переключение информационной панели"""
        try:
            if hasattr(self, 'info_panel'):
                if self.info_panel.is_open:
                    self.info_panel.hide_panel()
                    self.info_panel_button.setText("📊")
                else:
                    self.info_panel.show_panel()
                    self.info_panel_button.setText("✕")
        except Exception as e:
            self.logger.error(f"Ошибка переключения информационной панели: {e}")

    def _toggle_sidebar(self):
        """Переключение левой панели"""
        try:
            if not hasattr(self, 'sidebar_visible'):
                self.sidebar_visible = False
            
            if self.sidebar_visible:
                # Скрываем левую панель
                self._hide_sidebar()
            else:
                # Показываем левую панель
                self._show_sidebar()
        except Exception as e:
            self.logger.error(f"Ошибка переключения левой панели: {e}")

    def _show_sidebar(self):
        """Показать левую панель"""
        if self.sidebar_visible:
            return

        self.sidebar_visible = True
        self.sidebar.show()

        # Анимация разворачивания
        self.sidebar_animation.setStartValue(0)
        self.sidebar_animation.setEndValue(250)
        self.sidebar_animation.start()

    def _hide_sidebar(self):
        """Скрыть левую панель"""
        if not self.sidebar_visible:
            return

        self.sidebar_visible = False

        # Анимация сворачивания
        self.sidebar_animation.setStartValue(250)
        self.sidebar_animation.setEndValue(0)
        self.sidebar_animation.start()

    def _on_sidebar_animation_finished(self):
        """Обработка завершения анимации левой панели"""
        if not self.sidebar_visible:
            self.sidebar.setFixedWidth(0)
        else:
            self.sidebar.setFixedWidth(250)

    def _show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "<h2>Панель управления устройством</h2>"
            "<p><b>Версия:</b> 2.0 (Рефакторинг)</p>"
            "<p><b>Технологии:</b> Python, PySide6, Serial</p>"
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

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для свайпа"""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                # Проверяем, находится ли курсор в области свайпа (левая часть экрана)
                if event.position().x() < 50:  # Область свайпа 50px от левого края
                    if hasattr(self, 'sidebar'):
                        if not self.sidebar_visible:
                            self._show_sidebar()
                        else:
                            self._hide_sidebar()
                    event.accept()
                    return
                # Проверяем, находится ли курсор в области свайпа (правая часть экрана)
                elif event.position().x() > self.width() - 50:  # Область свайпа 50px от правого края
                    if hasattr(self, 'info_panel') and not self.info_panel.is_open:
                        self.info_panel.show_panel()
                        self.info_panel_button.setText("✕")
                    event.accept()
                    return
        except Exception as e:
            self.logger.error(f"Ошибка обработки нажатия мыши: {e}")
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)
        
        # Обновляем позицию информационной панели при изменении размера окна
        if hasattr(self, 'info_panel'):
            if self.info_panel.is_open:
                self.info_panel.setGeometry(
                    self.width() - self.info_panel.get_panel_width(),
                    0,
                    self.info_panel.get_panel_width(),
                    self.height()
                )
            else:
                self.info_panel.setGeometry(
                    self.width(),
                    0,
                    self.info_panel.get_panel_width(),
                    self.height()
                )

    def closeEvent(self, event):
        """Обработка закрытия окна с proper cleanup и обработкой ошибок"""
        try:
            self.logger.info("Начало процесса закрытия приложения...")
            
            # Останавливаем таймер проверки подключения
            self._cleanup_timers()
            
            # Останавливаем последовательность
            self._cleanup_sequence_executor()
            
            # Отключаемся от порта
            self._cleanup_serial_connection()
            
            # Сохраняем настройки
            self._cleanup_settings()
            
            # Очищаем ресурсы страниц
            self._cleanup_pages()
            
            # Очищаем обработчики сигналов
            self._cleanup_signal_handlers()
            
            # Финальная очистка
            self._final_cleanup()
            
            self.logger.info("Приложение успешно закрыто")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при закрытии приложения: {e}")
            # Даже при ошибке принимаем событие закрытия
            event.accept()

    def _cleanup_timers(self):
        """Очистка таймеров"""
        try:
            if hasattr(self, 'connection_check_timer'):
                self.connection_check_timer.stop()
                self.logger.info("Таймер проверки подключения остановлен")
                
            if hasattr(self, 'monitoring_update_timer'):
                self.monitoring_update_timer.stop()
                self.logger.info("Таймер обновления мониторинга остановлен")
        except Exception as e:
            self.logger.error(f"Ошибка остановки таймера: {e}")

    def _cleanup_sequence_executor(self):
        """Очистка исполнителя последовательности"""
        try:
            if hasattr(self, 'sequence_executor') and self.sequence_executor:
                if self.sequence_executor.isRunning():
                    self.sequence_executor.stop()
                    self.logger.info("Исполнитель последовательности остановлен")
                # Отключаем сигналы
                try:
                    self.sequence_executor.progress_updated.disconnect()
                    self.sequence_executor.command_sent.disconnect()
                    self.sequence_executor.sequence_finished.disconnect()
                except:
                    pass  # Игнорируем ошибки отключения сигналов
        except Exception as e:
            self.logger.error(f"Ошибка очистки исполнителя последовательности: {e}")

    def _cleanup_serial_connection(self):
        """Очистка Serial соединения"""
        try:
            if hasattr(self, 'serial_manager') and self.serial_manager:
                # Отключаем обработчики данных
                if self.serial_manager.reader_thread:
                    try:
                        self.serial_manager.reader_thread.data_received.disconnect()
                        self.serial_manager.reader_thread.error_occurred.disconnect()
                    except:
                        pass  # Игнорируем ошибки отключения
                
                # Отключаемся от порта
                self.serial_manager.disconnect()
                self.logger.info("Serial соединение закрыто")
        except Exception as e:
            self.logger.error(f"Ошибка очистки Serial соединения: {e}")

    def _cleanup_settings(self):
        """Очистка и сохранение настроек"""
        try:
            if hasattr(self, 'settings_manager') and self.settings_manager:
                self.settings_manager.save_all()
                self.logger.info("Настройки сохранены")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек: {e}")

    def _cleanup_pages(self):
        """Очистка ресурсов страниц"""
        try:
            if hasattr(self, 'pages'):
                for page_name, page in self.pages.items():
                    try:
                        if hasattr(page, 'cleanup'):
                            page.cleanup()
                        elif hasattr(page, 'close'):
                            page.close()
                    except Exception as e:
                        self.logger.error(f"Ошибка очистки страницы {page_name}: {e}")
                self.logger.info("Ресурсы страниц очищены")
                
            # Очистка информационной панели
            if hasattr(self, 'info_panel'):
                try:
                    self.info_panel.close()
                    self.logger.info("Информационная панель закрыта")
                except Exception as e:
                    self.logger.error(f"Ошибка закрытия информационной панели: {e}")
                    
            # Остановка системы мониторинга
            if hasattr(self, 'monitoring_manager'):
                try:
                    self.monitoring_manager.stop_monitoring()
                    self.logger.info("Система мониторинга остановлена")
                except Exception as e:
                    self.logger.error(f"Ошибка остановки системы мониторинга: {e}")
                    
        except Exception as e:
            self.logger.error(f"Ошибка очистки страниц: {e}")

    def _cleanup_signal_handlers(self):
        """Очистка обработчиков сигналов"""
        try:
            # Отключаем обработчики от страниц
            if hasattr(self, 'pages'):
                for page_name, page in self.pages.items():
                    try:
                        # Отключаем все сигналы страницы
                        if hasattr(page, 'sequence_requested'):
                            page.sequence_requested.disconnect()
                        if hasattr(page, 'zone_selection_changed'):
                            page.zone_selection_changed.disconnect()
                        if hasattr(page, 'connect_requested'):
                            page.connect_requested.disconnect()
                        if hasattr(page, 'disconnect_requested'):
                            page.disconnect_requested.disconnect()
                        if hasattr(page, 'config_reload_requested'):
                            page.config_reload_requested.disconnect()
                        if hasattr(page, 'status_message'):
                            page.status_message.disconnect()
                        if hasattr(page, 'sequence_execute_requested'):
                            page.sequence_execute_requested.disconnect()
                        if hasattr(page, 'sequence_edited'):
                            page.sequence_edited.disconnect()
                        if hasattr(page, 'command_execute_requested'):
                            page.command_execute_requested.disconnect()
                        if hasattr(page, 'sequence_created'):
                            page.sequence_created.disconnect()
                    except:
                        pass  # Игнорируем ошибки отключения сигналов
            self.logger.info("Обработчики сигналов очищены")
        except Exception as e:
            self.logger.error(f"Ошибка очистки обработчиков сигналов: {e}")

    def _final_cleanup(self):
        """Финальная очистка ресурсов"""
        try:
            # Очищаем ссылки на объекты
            if hasattr(self, 'pages'):
                self.pages.clear()
            
            # Очищаем менеджеры
            if hasattr(self, 'sequence_executor'):
                self.sequence_executor = None
                
            self.logger.info("Финальная очистка завершена")
        except Exception as e:
            self.logger.error(f"Ошибка финальной очистки: {e}")

    def _setup_flag_control_panel(self):
        """Настройка панели управления флагами"""
        try:
            # Создаем группу для управления флагами
            flag_group = QGroupBox("Управление флагами")
            flag_layout = QVBoxLayout()
            
            # Флаг wanted
            wanted_layout = QHBoxLayout()
            wanted_label = QLabel("Флаг 'wanted':")
            self.wanted_checkbox = QCheckBox()
            self.wanted_checkbox.setChecked(self.flag_manager.get_flag('wanted', False))
            self.wanted_checkbox.toggled.connect(self._on_wanted_flag_changed)
            
            wanted_layout.addWidget(wanted_label)
            wanted_layout.addWidget(self.wanted_checkbox)
            wanted_layout.addStretch()
            
            flag_layout.addLayout(wanted_layout)
            
            # Кнопка сброса всех флагов
            reset_flags_button = QPushButton("Сбросить все флаги")
            reset_flags_button.clicked.connect(self._reset_all_flags)
            flag_layout.addWidget(reset_flags_button)
            
            flag_group.setLayout(flag_layout)
            
            # Добавляем группу в основной layout
            if hasattr(self, 'central_widget') and hasattr(self.central_widget, 'layout'):
                self.central_widget.layout().addWidget(flag_group)
            
            self.logger.info("Панель управления флагами добавлена")
            
        except Exception as e:
            self.logger.error(f"Ошибка при настройке панели управления флагами: {e}")
    
    def _on_wanted_flag_changed(self, checked: bool):
        """
        Обработчик изменения флага wanted
        
        Args:
            checked: Новое значение флага
        """
        try:
            self.logger.info(f"Флаг 'wanted' изменен на: {checked}")
            self.flag_manager.set_flag('wanted', checked)
            
        except Exception as e:
            self.logger.error(f"Ошибка при изменении флага 'wanted': {e}")
    
    def _reset_all_flags(self):
        """Сброс всех флагов"""
        try:
            self.logger.info("Сброс всех флагов")
            self.flag_manager.clear_flags()
            
            # Обновляем UI
            self.wanted_checkbox.setChecked(False)
            
            QMessageBox.information(
                self,
                "Флаги сброшены",
                "Все флаги были сброшены к значениям по умолчанию.",
                QMessageBox.Ok
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка при сбросе флагов: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Произошла ошибка при сбросе флагов: {e}",
                QMessageBox.Ok
            )
