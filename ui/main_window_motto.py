"""
Главное окно приложения с интеграцией MOTTO

Модифицированная версия main_window.py с поддержкой MOTTO конфигурации
"""
import logging
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QToolButton, QMenu, QMessageBox, QApplication,
    QProgressBar, QTextEdit
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QInputDialog

from config.settings import SettingsManager
from core.motto.ui_integration import MOTTOConfigLoader
from core.serial_manager import SerialManager
from core.sequence_manager import SequenceManager, CommandSequenceExecutor
from monitoring import MonitoringManager
from ui.pages.wizard_page import WizardPage
from ui.pages.settings_page import SettingsPage
from ui.pages.sequences_page import SequencesPage
from ui.pages.commands_page import CommandsPage
from ui.pages.designer_page import DesignerPage
from ui.pages.firmware_page import FirmwarePage
from ui.widgets.modern_widgets import ModernCard
from ui.widgets.info_panel import InfoPanel


class MainWindowMOTTO(QMainWindow):
    """Главное окно приложения с поддержкой MOTTO"""

    # Сигналы для MOTTO
    motto_sequence_progress = Signal(int, str)  # progress, message
    motto_sequence_completed = Signal(str)  # sequence_name
    motto_sequence_error = Signal(str, str)  # sequence_name, error
    motto_info_updated = Signal(dict)  # motto_info

    def __init__(self, config_file: str = 'config_motto_fixed.toml'):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file

        try:
            # Инициализация менеджеров
            self.logger.info("Инициализация SettingsManager...")
            self.settings_manager = SettingsManager()
            self.logger.info("SettingsManager инициализирован")
            
            self.logger.info("Инициализация MOTTOConfigLoader...")
            self.config_loader = MOTTOConfigLoader(config_file)
            self.logger.info("MOTTOConfigLoader инициализирован")
            
            self.logger.info("Инициализация SerialManager...")
            self.serial_manager = SerialManager()
            self.logger.info("SerialManager инициализирован")

            # Инициализация системы мониторинга
            self.logger.info("Инициализация MonitoringManager...")
            self.monitoring_manager = MonitoringManager(self.logger)
            self.logger.info("MonitoringManager инициализирован")

            # Загрузка конфигурации
            self.logger.info("Загрузка конфигурации...")
            self.config = self.config_loader.load()
            
            # Проверяем, что конфигурация загружена
            if self.config is None:
                self.logger.warning("Конфигурация не загружена, создаем пустую")
                self.config = {}
            
            self.logger.info("Конфигурация загружена")
            
            self.logger.info("Инициализация SequenceManager...")
            self.sequence_manager = SequenceManager(
                self.config.get('sequences', {}),
                self.config.get('buttons', {})
            )
            self.logger.info("SequenceManager инициализирован")

            # Текущий исполнитель последовательности
            self.sequence_executor: Optional[CommandSequenceExecutor] = None

            # MOTTO информация
            self.motto_info = self.config_loader.get_motto_info()
            if self.motto_info:
                self.logger.info(f"MOTTO конфигурация загружена: {self.motto_info}")

            # Настройка UI
            self.logger.info("Настройка UI...")
            self._setup_ui()
            self.logger.info("UI настроен")

            # Настройка соединений
            self.logger.info("Настройка соединений...")
            self._setup_connections()
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

        except Exception as e:
            self.logger.error(f"Ошибка инициализации MainWindow: {e}")
            raise

    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основная настройка окна
        self.setWindowTitle("Лабораторное оборудование - MOTTO")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель с навигацией
        self._setup_left_panel(main_layout)
        
        # Центральная область с контентом
        self._setup_central_area(main_layout)
        
        # Правая панель с информацией
        self._setup_right_panel(main_layout)
        
        # Настройка меню
        self._setup_menu()

    def _setup_left_panel(self, main_layout):
        """Настройка левой панели"""
        left_panel = QFrame()
        left_panel.setMaximumWidth(200)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        
        left_layout = QVBoxLayout(left_panel)
        
        # Заголовок
        title = QLabel("MOTTO")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        left_layout.addWidget(title)
        
        # Кнопки навигации
        self.nav_buttons = {}
        nav_items = [
            ("wizard", "🎯 Wizard", "Мастер настройки"),
            ("sequences", "📋 Последовательности", "Управление последовательностями"),
            ("commands", "🔧 Команды", "Отдельные команды"),
            ("settings", "⚙️ Настройки", "Настройки системы"),
            ("designer", "🎨 Дизайнер", "Конструктор последовательностей"),
            ("firmware", "💾 Прошивка", "Управление прошивкой")
        ]
        
        for key, text, tooltip in nav_items:
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: none;
                    padding: 10px;
                    text-align: left;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #3498db;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self._switch_page(k))
            self.nav_buttons[key] = btn
            left_layout.addWidget(btn)
        
        # MOTTO информация
        if self.motto_info:
            motto_info_widget = self._create_motto_info_widget()
            left_layout.addWidget(motto_info_widget)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)

    def _create_motto_info_widget(self) -> QWidget:
        """Создание виджета с информацией о MOTTO"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #27ae60;
                border-radius: 5px;
                margin: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        
        # Заголовок
        title = QLabel("MOTTO v1.1")
        title.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(title)
        
        # Информация
        info_text = f"""
Команд: {self.motto_info.get('commands_count', 0)}
Последовательностей: {self.motto_info.get('sequences_count', 0)}
Условий: {self.motto_info.get('conditions_count', 0)}
Гвардов: {self.motto_info.get('guards_count', 0)}
        """
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: white; font-size: 10px;")
        layout.addWidget(info_label)
        
        return widget

    def _setup_central_area(self, main_layout):
        """Настройка центральной области"""
        self.stacked_widget = QStackedWidget()
        
        # Создание страниц
        self.pages = {}
        
        # Wizard страница
        self.pages['wizard'] = WizardPage(self.config.get('wizard', {}))
        self.stacked_widget.addWidget(self.pages['wizard'])
        
        # Последовательности
        self.pages['sequences'] = SequencesPage(
            self.config.get('sequences', {}),
            self.sequence_manager
        )
        self.stacked_widget.addWidget(self.pages['sequences'])
        
        # Команды
        self.pages['commands'] = CommandsPage(
            self.config.get('buttons', {}),
            self.serial_manager
        )
        self.stacked_widget.addWidget(self.pages['commands'])
        
        # Настройки
        self.pages['settings'] = SettingsPage(self.settings_manager)
        self.stacked_widget.addWidget(self.pages['settings'])
        
        # Дизайнер
        self.pages['designer'] = DesignerPage()
        self.stacked_widget.addWidget(self.pages['designer'])
        
        # Прошивка
        self.pages['firmware'] = FirmwarePage()
        self.stacked_widget.addWidget(self.pages['firmware'])
        
        main_layout.addWidget(self.stacked_widget)

    def _setup_right_panel(self, main_layout):
        """Настройка правой панели"""
        right_panel = QFrame()
        right_panel.setMaximumWidth(300)
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        
        right_layout = QVBoxLayout(right_panel)
        
        # Информационная панель
        self.info_panel = InfoPanel()
        right_layout.addWidget(self.info_panel)
        
        # Прогресс-бар для MOTTO последовательностей
        self.motto_progress = QProgressBar()
        self.motto_progress.setVisible(False)
        self.motto_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        right_layout.addWidget(self.motto_progress)
        
        # Лог MOTTO операций
        self.motto_log = QTextEdit()
        self.motto_log.setMaximumHeight(200)
        self.motto_log.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        self.motto_log.setPlaceholderText("MOTTO операции...")
        right_layout.addWidget(self.motto_log)
        
        right_layout.addStretch()
        main_layout.addWidget(right_panel)

    def _setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu('Файл')
        
        # Действие для переключения конфигурации
        switch_config_action = QAction('Переключить конфигурацию', self)
        switch_config_action.triggered.connect(self._switch_config)
        file_menu.addAction(switch_config_action)
        
        # Выход
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # MOTTO
        if self.motto_info:
            motto_menu = menubar.addMenu('MOTTO')
            
            # Информация о MOTTO
            motto_info_action = QAction('Информация', self)
            motto_info_action.triggered.connect(self._show_motto_info)
            motto_menu.addAction(motto_info_action)
            
            # Выполнить последовательность
            execute_seq_action = QAction('Выполнить последовательность', self)
            execute_seq_action.triggered.connect(self._execute_motto_sequence)
            motto_menu.addAction(execute_seq_action)

    def _setup_connections(self):
        """Настройка соединений сигналов"""
        # Соединения для MOTTO
        self.motto_sequence_progress.connect(self._update_motto_progress)
        self.motto_sequence_completed.connect(self._on_motto_sequence_completed)
        self.motto_sequence_error.connect(self._on_motto_sequence_error)
        self.motto_info_updated.connect(self._update_motto_info)

    def _switch_page(self, page_name: str):
        """Переключение страницы"""
        if page_name in self.pages:
            self.stacked_widget.setCurrentWidget(self.pages[page_name])
            
            # Обновляем стиль кнопок
            for key, btn in self.nav_buttons.items():
                if key == page_name:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            border: none;
                            padding: 10px;
                            text-align: left;
                            border-radius: 3px;
                        }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #34495e;
                            color: white;
                            border: none;
                            padding: 10px;
                            text-align: left;
                            border-radius: 3px;
                        }
                        QPushButton:hover {
                            background-color: #3498db;
                        }
                        QPushButton:pressed {
                            background-color: #2980b9;
                        }
                    """)

    def _switch_config(self):
        """Переключение конфигурации"""
        if self.config_file == 'config_motto_fixed.toml':
            new_config = 'config.toml'
        else:
            new_config = 'config_motto_fixed.toml'
        
        try:
            # Перезагружаем конфигурацию
            self.config_loader = MOTTOConfigLoader(new_config)
            self.config = self.config_loader.load()
            self.config_file = new_config
            
            # Обновляем информацию
            self.motto_info = self.config_loader.get_motto_info()
            
            # Обновляем UI
            self._update_ui_for_config()
            
            self.logger.info(f"Конфигурация переключена на: {new_config}")
            
        except Exception as e:
            self.logger.error(f"Ошибка переключения конфигурации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось переключить конфигурацию: {e}")

    def _update_ui_for_config(self):
        """Обновление UI для новой конфигурации"""
        # Обновляем заголовок окна
        if self.motto_info:
            self.setWindowTitle("Лабораторное оборудование - MOTTO")
        else:
            self.setWindowTitle("Лабораторное оборудование")
        
        # Обновляем страницы
        if 'sequences' in self.pages:
            self.pages['sequences'].update_sequences(self.config.get('sequences', {}))
        
        if 'commands' in self.pages:
            self.pages['commands'].update_commands(self.config.get('buttons', {}))

    def _show_motto_info(self):
        """Показать информацию о MOTTO"""
        if self.motto_info:
            info_text = f"""
MOTTO Конфигурация v{self.motto_info.get('version', '1.1')}

Команд: {self.motto_info.get('commands_count', 0)}
Последовательностей: {self.motto_info.get('sequences_count', 0)}
Условий: {self.motto_info.get('conditions_count', 0)}
Гвардов: {self.motto_info.get('guards_count', 0)}
Политик: {self.motto_info.get('policies_count', 0)}
Ресурсов: {self.motto_info.get('resources_count', 0)}
Событий: {self.motto_info.get('events_count', 0)}
Обработчиков: {self.motto_info.get('handlers_count', 0)}

Файл конфигурации: {self.config_file}
            """
            
            QMessageBox.information(self, "MOTTO Информация", info_text)
        else:
            QMessageBox.information(self, "MOTTO Информация", "MOTTO конфигурация не загружена")

    def _execute_motto_sequence(self):
        """Выполнить MOTTO последовательность"""
        if not self.motto_info:
            QMessageBox.warning(self, "MOTTO", "MOTTO конфигурация не загружена")
            return
        
        # Получаем список последовательностей
        sequences = list(self.config.get('sequences', {}).keys())
        
        if not sequences:
            QMessageBox.warning(self, "MOTTO", "Нет доступных последовательностей")
            return
        
        # Показываем диалог выбора
        sequence_name, ok = QInputDialog.getItem(
            self, "Выбор последовательности", 
            "Выберите последовательность для выполнения:",
            sequences, 0, False
        )
        
        if ok and sequence_name:
            self._run_motto_sequence(sequence_name)

    def _run_motto_sequence(self, sequence_name: str):
        """Запуск MOTTO последовательности"""
        try:
            # Показываем прогресс
            self.motto_progress.setVisible(True)
            self.motto_progress.setValue(0)
            
            # Добавляем в лог
            self.motto_log.append(f"🚀 Запуск последовательности: {sequence_name}")
            
            # Выполняем последовательность
            success = self.config_loader.execute_sequence_with_motto(
                sequence_name,
                self.sequence_executor,
                self._motto_progress_callback
            )
            
            if success:
                self.motto_log.append(f"✅ Последовательность '{sequence_name}' завершена успешно")
            else:
                self.motto_log.append(f"❌ Ошибка выполнения последовательности '{sequence_name}'")
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения MOTTO последовательности: {e}")
            self.motto_log.append(f"❌ Ошибка: {e}")
        finally:
            # Скрываем прогресс
            self.motto_progress.setVisible(False)

    def _motto_progress_callback(self, progress: int, message: str):
        """Callback для прогресса MOTTO последовательности"""
        self.motto_sequence_progress.emit(progress, message)

    def _update_motto_progress(self, progress: int, message: str):
        """Обновление прогресса MOTTO"""
        self.motto_progress.setValue(progress)
        self.motto_log.append(f"📋 {message}")

    def _on_motto_sequence_completed(self, sequence_name: str):
        """Обработка завершения MOTTO последовательности"""
        self.motto_log.append(f"✅ Последовательность '{sequence_name}' завершена")

    def _on_motto_sequence_error(self, sequence_name: str, error: str):
        """Обработка ошибки MOTTO последовательности"""
        self.motto_log.append(f"❌ Ошибка в последовательности '{sequence_name}': {error}")

    def _update_motto_info(self, info: dict):
        """Обновление информации о MOTTO"""
        self.motto_info = info

    def _safe_auto_connect(self):
        """Безопасное автоподключение"""
        try:
            if self.serial_manager.connect():
                self.logger.info("Автоподключение выполнено успешно")
            else:
                self.logger.warning("Автоподключение не удалось")
        except Exception as e:
            self.logger.error(f"Ошибка автоподключения: {e}")

    def _check_connection_status(self):
        """Проверка статуса подключения"""
        try:
            is_connected = self.serial_manager.is_connected()
            # Обновляем информацию в UI
            if hasattr(self, 'info_panel'):
                self.info_panel.update_connection_status(is_connected)
        except Exception as e:
            self.logger.error(f"Ошибка проверки статуса подключения: {e}")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            # Отключаемся от устройства
            if self.serial_manager.is_connected():
                self.serial_manager.disconnect()
            
            # Останавливаем таймеры
            if hasattr(self, 'connection_check_timer'):
                self.connection_check_timer.stop()
            
            self.logger.info("Приложение закрыто")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {e}")
            event.accept()