"""
Улучшенное главное окно с правильными пропорциями золотого сечения
"""
import logging
import math
from typing import Dict, Optional, Any
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal, QPropertyAnimation, QRect, QEasingCurve, QSize
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QAction, QFont, QPalette, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QToolButton, QMenu, QMessageBox, QApplication,
    QGroupBox, QCheckBox, QSizePolicy, QScrollArea
)

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


class GoldenRatioCalculator:
    """Калькулятор золотого сечения для размеров окон"""
    
    GOLDEN_RATIO = 1.618033988749895
    
    @classmethod
    def calculate_window_size(cls, base_height: int = 800) -> tuple[int, int]:
        """Вычисляет размеры окна по золотому сечению"""
        width = int(base_height * cls.GOLDEN_RATIO)
        return width, base_height
    
    @classmethod
    def calculate_sidebar_width(cls, window_height: int) -> int:
        """Вычисляет ширину боковой панели по золотому сечению"""
        return int(window_height / cls.GOLDEN_RATIO)
    
    @classmethod
    def calculate_content_width(cls, window_width: int, sidebar_width: int) -> int:
        """Вычисляет ширину области контента"""
        return window_width - sidebar_width


class ModernMainWindow(QMainWindow):
    """Современное главное окно с правильными пропорциями"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Вычисляем размеры по золотому сечению
        self.window_width, self.window_height = GoldenRatioCalculator.calculate_window_size(800)
        self.sidebar_width = GoldenRatioCalculator.calculate_sidebar_width(self.window_height)
        self.content_width = GoldenRatioCalculator.calculate_content_width(self.window_width, self.sidebar_width)
        
        try:
            # Создаем сервисы
            self.logger.info("Создание сервисов...")
            self._create_services_directly()

            # Загрузка конфигурации
            self.logger.info("Загрузка конфигурации...")
            self.config = self.config_loader.load()
            
            if self.config is None:
                self.logger.warning("Конфигурация не загружена, создаем пустую")
                self.config = {}
            
            # Загружаем флаги из конфигурации
            flags = self.config.get('flags', {})
            for flag_name, value in flags.items():
                self.sequence_manager.set_flag(flag_name, value)
            
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

            # Автоподключение
            if self.settings_manager.update_settings.auto_connect:
                self.logger.info("Настройка автоподключения...")
                QTimer.singleShot(2000, self._safe_auto_connect)
            
            # Периодическая проверка состояния подключения
            self.connection_check_timer = QTimer()
            self.connection_check_timer.timeout.connect(self._check_connection_status)
            self.connection_check_timer.start(5000)

            # Включаем отслеживание мыши для свайпа
            self.setMouseTracking(True)

            # Показ окна
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
        
        self.signal_manager = SignalManager(flag_manager=None)
        
        # Создаем SerialManager с интеграцией SignalManager
        self.serial_manager = SerialManager(signal_manager=self.signal_manager)
        
        self.multizone_manager = MultizoneManager()
        self.flag_manager = FlagManager()
        
        # Устанавливаем flag_manager в signal_manager
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
            config={},
            buttons_config={},
            flag_manager=self.flag_manager
        )
        
        self.logger.info("Сервисы созданы напрямую")

    def _setup_ui(self):
        """Настройка интерфейса с правильными пропорциями"""
        self.setWindowTitle("Система управления устройством")
        
        # Устанавливаем размеры по золотому сечению
        self.setMinimumSize(self.window_width, self.window_height)
        self.resize(self.window_width, self.window_height)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Левая панель навигации
        self._create_sidebar()
        main_layout.addWidget(self.sidebar, 0)

        # Область контента
        self._create_content_area()
        main_layout.addWidget(self.content_area, 1)

        # Информационная панель
        self._create_info_panel()

        # Статусная строка
        self.statusBar().showMessage("Готов к работе")

        # Добавляем панель управления флагами
        self._setup_flag_control_panel()

    def _create_sidebar(self):
        """Создание левой панели навигации с правильными пропорциями"""
        self.logger.info("Создание левой панели навигации...")
        
        # Создаем левую панель с шириной по золотому сечению
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(self.sidebar_width)
        
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
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
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

    def _toggle_sidebar(self):
        """Переключение видимости боковой панели"""
        if self.sidebar_visible:
            self._hide_sidebar()
        else:
            self._show_sidebar()

    def _show_sidebar(self):
        """Показать боковую панель"""
        if not self.sidebar_visible:
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(self.sidebar_width)
            self.sidebar_animation.start()
            self.sidebar_visible = True

    def _hide_sidebar(self):
        """Скрыть боковую панель"""
        if self.sidebar_visible:
            self.sidebar_animation.setStartValue(self.sidebar_width)
            self.sidebar_animation.setEndValue(0)
            self.sidebar_animation.start()
            self.sidebar_visible = False

    def _on_sidebar_animation_finished(self):
        """Обработчик завершения анимации боковой панели"""
        if not self.sidebar_visible:
            self.sidebar.hide()

    def _toggle_info_panel(self):
        """Переключение информационной панели"""
        if hasattr(self, 'info_panel'):
            if self.info_panel.isVisible():
                self.info_panel.hide()
            else:
                self.info_panel.show()

    def _reload_config(self):
        """Перезагрузка конфигурации"""
        try:
            self.config = self.config_loader.load()
            self.logger.info("Конфигурация перезагружена")
            self.statusBar().showMessage("Конфигурация перезагружена", 3000)
        except Exception as e:
            self.logger.error(f"Ошибка перезагрузки конфигурации: {e}")
            self.statusBar().showMessage(f"Ошибка перезагрузки конфигурации: {e}", 5000)

    def _toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        if self.isFullScreen():
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True

    def _toggle_theme(self):
        """Переключение темы"""
        # Здесь будет логика переключения темы
        self.logger.info("Переключение темы")

    def _show_about(self):
        """Показать информацию о программе"""
        QMessageBox.about(
            self,
            "О программе",
            "Система управления устройством\nВерсия 1.0.0\n\nРазработано с использованием PyQt6"
        )

    def _setup_flag_control_panel(self):
        """Настройка панели управления флагами"""
        # Здесь будет логика настройки панели управления флагами
        pass

    def _safe_auto_connect(self):
        """Безопасное автоматическое подключение при запуске"""
        try:
            self.logger.info("Начало безопасного автоподключения...")
            
            if not hasattr(self, 'settings_manager') or not self.settings_manager:
                self.logger.error("SettingsManager недоступен")
                self.statusBar().showMessage("Ошибка: SettingsManager недоступен", 5000)
                return
            
            port = self.settings_manager.serial_settings.port
            self.logger.info(f"Попытка подключения к порту: {port}")
            
            if not port or port.strip() == '':
                self.logger.warning("Порт не указан в настройках")
                self.statusBar().showMessage("Порт не указан в настройках", 5000)
                return
            
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
                self.logger.error(f"Ошибка доступа к порту: {e}")
                self.statusBar().showMessage(f"Ошибка доступа к порту: {e}", 5000)
            except Exception as e:
                self.logger.error(f"Неожиданная ошибка при автоподключении: {e}")
                self.statusBar().showMessage(f"Ошибка автоподключения: {e}", 5000)
                
        except Exception as e:
            self.logger.error(f"Критическая ошибка в _safe_auto_connect: {e}")
            self.statusBar().showMessage(f"Критическая ошибка автоподключения: {e}", 5000)

    def _safe_connect_serial(self, port: str):
        """Безопасное подключение к последовательному порту"""
        try:
            self.logger.info(f"Попытка подключения к порту {port}...")
            
            # Получаем настройки из settings_manager
            baudrate = self.settings_manager.serial_settings.baudrate
            timeout = self.settings_manager.serial_settings.timeout
            
            # Подключаемся
            success = self.serial_manager.connect(port, baudrate, timeout)
            
            if success:
                self.logger.info(f"Успешное подключение к порту {port}")
                self.statusBar().showMessage(f"Подключено к {port}", 3000)
                self._update_connection_status(True, port)
            else:
                self.logger.error(f"Не удалось подключиться к порту {port}")
                self.statusBar().showMessage(f"Не удалось подключиться к {port}", 5000)
                self._update_connection_status(False, port)
                
        except Exception as e:
            self.logger.error(f"Ошибка при подключении к порту {port}: {e}")
            self.statusBar().showMessage(f"Ошибка подключения: {e}", 5000)
            self._update_connection_status(False, port)

    def _update_connection_status(self, connected: bool, port: str = ""):
        """Обновление статуса подключения"""
        if connected:
            self.connection_status.setText(f"● Подключено к {port}")
            self.connection_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.connection_status.setText("● Отключено")
            self.connection_status.setStyleSheet("color: #f44336; font-weight: bold;")

    def _check_connection_status(self):
        """Проверка статуса подключения"""
        try:
            if hasattr(self, 'serial_manager'):
                is_connected = self.serial_manager.is_connected()
                if is_connected:
                    port = self.serial_manager.port
                    self._update_connection_status(True, port)
                else:
                    self._update_connection_status(False)
        except Exception as e:
            self.logger.error(f"Ошибка проверки статуса подключения: {e}")

    def _update_monitoring_data(self):
        """Обновление данных мониторинга"""
        try:
            if hasattr(self, 'info_panel'):
                self.info_panel.update_monitoring_data()
        except Exception as e:
            self.logger.error(f"Ошибка обновления данных мониторинга: {e}")

    def _on_data_received(self, data: str):
        """Обработчик получения данных"""
        self.logger.debug(f"Получены данные: {data}")

    def _on_serial_error(self, error: str):
        """Обработчик ошибки последовательного порта"""
        self.logger.error(f"Ошибка последовательного порта: {error}")
        self.statusBar().showMessage(f"Ошибка порта: {error}", 5000)

    def _on_signal_processed(self, signal_data: dict):
        """Обработчик обработанного сигнала"""
        self.logger.debug(f"Обработан сигнал: {signal_data}")

    def _start_sequence(self, sequence_name: str, next_step_id: int = None):
        """Запуск последовательности"""
        try:
            self.logger.info(f"Запуск последовательности: {sequence_name}")
            # Здесь будет логика запуска последовательности
        except Exception as e:
            self.logger.error(f"Ошибка запуска последовательности: {e}")

    def _on_zone_changed(self, zones: dict):
        """Обработчик изменения зон"""
        self.logger.info(f"Изменены зоны: {zones}")

    def _connect_serial(self, port: str, baudrate: int, timeout: float):
        """Подключение к последовательному порту"""
        try:
            success = self.serial_manager.connect(port, baudrate, timeout)
            if success:
                self._update_connection_status(True, port)
            else:
                self._update_connection_status(False, port)
        except Exception as e:
            self.logger.error(f"Ошибка подключения: {e}")

    def _disconnect_serial(self):
        """Отключение от последовательного порта"""
        try:
            self.serial_manager.disconnect()
            self._update_connection_status(False)
        except Exception as e:
            self.logger.error(f"Ошибка отключения: {e}")

    def _on_sequence_edited(self, sequence_data: dict):
        """Обработчик редактирования последовательности"""
        self.logger.info(f"Последовательность отредактирована: {sequence_data}")

    def _execute_command(self, command: str):
        """Выполнение команды"""
        try:
            self.logger.info(f"Выполнение команды: {command}")
            # Здесь будет логика выполнения команды
        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды: {e}")

    def _on_sequence_created(self, sequence_data: dict):
        """Обработчик создания последовательности"""
        self.logger.info(f"Создана последовательность: {sequence_data}")

    def _on_wanted_dialog_result(self, result: str):
        """Обработчик результата диалога _wanted"""
        try:
            self.logger.info(f"Получен результат диалога _wanted: {result}")
            
            if result == 'check_fluids':
                self.logger.info("Пользователь подтвердил проверку жидкостей")
                
                if hasattr(self, 'flag_manager'):
                    self.flag_manager.set_flag('wanted', False)
                    self.logger.info("Флаг 'wanted' установлен в False")
                
                QMessageBox.information(
                    self,
                    "Проверка жидкостей",
                    "Спасибо! Выполнение команды будет продолжено.",
                    QMessageBox.StandardButton.Ok
                )
                
                self._resume_command_execution()
                
            elif result == 'cancel':
                self.logger.info("Пользователь отменил операцию")
                
                QMessageBox.information(
                    self,
                    "Операция отменена",
                    "Операция была отменена пользователем.",
                    QMessageBox.StandardButton.Ok
                )
                
                self._cancel_command_execution()
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке результата диалога _wanted: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Произошла ошибка при обработке результата диалога: {e}",
                QMessageBox.StandardButton.Ok
            )

    def _resume_command_execution(self):
        """Возобновление выполнения команды после обработки тега"""
        try:
            self.logger.info("Возобновление выполнения команды")
            self.logger.info("Выполнение команды возобновлено")
        except Exception as e:
            self.logger.error(f"Ошибка при возобновлении выполнения команды: {e}")

    def _cancel_command_execution(self):
        """Отмена выполнения команды"""
        try:
            self.logger.info("Отмена выполнения команды")
            self.logger.info("Выполнение команды отменено")
        except Exception as e:
            self.logger.error(f"Ошибка при отмене выполнения команды: {e}")

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        
        # Обновляем размеры по золотому сечению при изменении размера окна
        new_width = event.size().width()
        new_height = event.size().height()
        
        # Пересчитываем пропорции
        self.sidebar_width = GoldenRatioCalculator.calculate_sidebar_width(new_height)
        self.content_width = GoldenRatioCalculator.calculate_content_width(new_width, self.sidebar_width)
        
        # Обновляем размеры виджетов
        if hasattr(self, 'sidebar'):
            self.sidebar.setFixedWidth(self.sidebar_width)
        
        # Обновляем позицию информационной панели
        if hasattr(self, 'info_panel') and self.info_panel.isVisible():
            self.info_panel.setGeometry(
                new_width - self.info_panel.get_panel_width(),
                0,
                self.info_panel.get_panel_width(),
                new_height
            )

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        try:
            # Останавливаем мониторинг
            if hasattr(self, 'monitoring_manager'):
                self.monitoring_manager.stop_monitoring()
            
            # Отключаемся от порта
            if hasattr(self, 'serial_manager'):
                self.serial_manager.disconnect()
            
            self.logger.info("Приложение закрывается")
            event.accept()
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {e}")
            event.accept()