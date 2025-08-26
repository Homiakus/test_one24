"""
@file: info_panel.py
@description: Информационная панель справа с консолью и диагностикой
@dependencies: PyQt6, monitoring
@created: 2024-12-19
"""

import logging
from typing import Optional, List
from datetime import datetime

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, pyqtSignal as pyqtSignal as Signal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
    QTextEdit, QTabWidget, QSplitter, QGroupBox
)

from monitoring import MonitoringManager
from ui.pages.monitoring_page import MonitoringPage


class ConsoleWidget(QTextEdit):
    """Виджет консоли с поддержкой цветного вывода"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_console()
        
    def setup_console(self):
        """Настройка консоли"""
        # Устанавливаем моноширинный шрифт
        font = QFont("Consolas", 10)
        self.setFont(font)
        
        # Настройка цветов
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor("#1e1e1e"))
        palette.setColor(QPalette.Text, QColor("#ffffff"))
        self.setPalette(palette)
        
        # Настройка стилей
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        # Максимальное количество строк
        self.max_lines = 1000
        
    def add_message(self, message: str, level: str = "INFO"):
        """Добавить сообщение в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Цвета для разных уровней
        colors = {
            "INFO": "#ffffff",
            "WARNING": "#ffaa00",
            "ERROR": "#ff4444",
            "CRITICAL": "#ff0000",
            "DEBUG": "#888888",
            "SUCCESS": "#44ff44"
        }
        
        color = colors.get(level, "#ffffff")
        formatted_message = f'<span style="color: {color}">[{timestamp}] {level}: {message}</span><br>'
        
        # Добавляем сообщение
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
        self.insertHtml(formatted_message)
        
        # Прокручиваем к концу
        self.ensureCursorVisible()
        
        # Ограничиваем количество строк
        self.limit_lines()
        
    def limit_lines(self):
        """Ограничить количество строк"""
        text = self.toPlainText()
        lines = text.split('\n')
        
        if len(lines) > self.max_lines:
            # Удаляем старые строки
            lines = lines[-self.max_lines:]
            self.setPlainText('\n'.join(lines))
            
    def clear_console(self):
        """Очистить консоль"""
        self.clear()


class DiagnosticsWidget(QWidget):
    """Виджет диагностических сообщений"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title = QLabel("🔍 Диагностика системы")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Область диагностических сообщений
        self.diagnostics_area = QTextEdit()
        self.diagnostics_area.setMaximumHeight(200)
        self.diagnostics_area.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.diagnostics_area)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Обновить")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        
        self.clear_button = QPushButton("🗑️ Очистить")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Подключаем сигналы
        self.refresh_button.clicked.connect(self.refresh_diagnostics)
        self.clear_button.clicked.connect(self.clear_diagnostics)
        
    def add_diagnostic_message(self, message: str, level: str = "INFO"):
        """Добавить диагностическое сообщение"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        cursor = self.diagnostics_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.diagnostics_area.setTextCursor(cursor)
        self.diagnostics_area.insertPlainText(formatted_message)
        
        # Прокручиваем к концу
        self.diagnostics_area.ensureCursorVisible()
        
    def refresh_diagnostics(self):
        """Обновить диагностику"""
        # Здесь можно добавить логику обновления диагностики
        self.add_diagnostic_message("Диагностика обновлена", "INFO")
        
    def clear_diagnostics(self):
        """Очистить диагностику"""
        self.diagnostics_area.clear()


class InfoPanel(QWidget):
    """Информационная панель справа"""

    def __init__(self, monitoring_manager: MonitoringManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.monitoring_manager = monitoring_manager

        # Состояние панели
        self.is_open = False
        self.panel_width = 450

        # Анимация
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Настройка виджета
        self.setup_ui()
        self.setup_animations()
        self.setup_console_logging()

        # Начальное состояние - скрыта
        self.hide_panel()

    def setup_ui(self):
        """Настройка интерфейса"""
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Заголовок панели
        self.create_header(main_layout)

        # Область прокрутки для контента
        self.create_content_area(main_layout)

        # Установка стилей
        self.setObjectName("info_panel")
        self.setStyleSheet("""
            QWidget#info_panel {
                background-color: #2b2b2b;
                border-left: 1px solid #404040;
            }

            QLabel#panel_title {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }

            QPushButton#close_button {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 18px;
                padding: 5px;
                border-radius: 3px;
            }

            QPushButton#close_button:hover {
                background-color: #404040;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QWidget#scroll_content {
                background-color: transparent;
            }
        """)

        # Добавляем тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(-5, 0)
        self.setGraphicsEffect(shadow)

    def create_header(self, parent_layout):
        """Создание заголовка панели"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Заголовок
        title = QLabel("📊 Информационная панель")
        title.setObjectName("panel_title")

        # Кнопка закрытия
        close_button = QPushButton("×")
        close_button.setObjectName("close_button")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.hide_panel)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_button)

        parent_layout.addWidget(header_widget)

    def create_content_area(self, parent_layout):
        """Создание области контента"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Контейнер для контента
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.scroll_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Добавляем контент
        content_layout = QVBoxLayout(self.scroll_content)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Создаем табы
        self.tab_widget = QTabWidget()
        
        # Вкладка мониторинга
        self.monitoring_page = MonitoringPage(self.monitoring_manager)
        self.tab_widget.addTab(self.monitoring_page, "📈 Мониторинг")
        
        # Вкладка консоли
        self.console_widget = ConsoleWidget()
        self.tab_widget.addTab(self.console_widget, "💻 Консоль")
        
        # Вкладка диагностики
        self.diagnostics_widget = DiagnosticsWidget()
        self.tab_widget.addTab(self.diagnostics_widget, "🔍 Диагностика")

        content_layout.addWidget(self.tab_widget)

        self.scroll_area.setWidget(self.scroll_content)
        parent_layout.addWidget(self.scroll_area)

    def setup_animations(self):
        """Настройка анимаций"""
        self.animation.finished.connect(self.on_animation_finished)
        
        # Устанавливаем начальную позицию (скрыта справа)
        if self.parent():
            self.setGeometry(
                self.parent().width(),
                0,
                self.panel_width,
                self.parent().height()
            )

    def setup_console_logging(self):
        """Настройка логирования в консоль"""
        # Создаем кастомный обработчик для консоли
        class ConsoleHandler(logging.Handler):
            def __init__(self, console_widget):
                super().__init__()
                self.console_widget = console_widget
                
            def emit(self, record):
                msg = self.format(record)
                level = record.levelname
                self.console_widget.add_message(msg, level)
        
        # Добавляем обработчик к корневому логгеру
        console_handler = ConsoleHandler(self.console_widget)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Получаем корневой логгер и добавляем обработчик
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)

    def show_panel(self):
        """Показать панель"""
        if self.is_open:
            return

        self.is_open = True
        self.show()

        # Анимация появления
        start_rect = self.geometry()
        end_rect = QRect(
            start_rect.x() - self.panel_width,
            start_rect.y(),
            self.panel_width,
            start_rect.height()
        )

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def hide_panel(self):
        """Скрыть панель"""
        if not self.is_open:
            return

        self.is_open = False
        
        # Анимация скрытия
        start_rect = self.geometry()
        end_rect = QRect(
            start_rect.x() + self.panel_width,
            start_rect.y(),
            self.panel_width,
            start_rect.height()
        )

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def on_animation_finished(self):
        """Обработка завершения анимации"""
        if not self.is_open:
            self.hide()

    def resizeEvent(self, event):
        """Обработка изменения размера"""
        super().resizeEvent(event)

        # Обновляем позицию панели при изменении размера
        if self.is_open:
            self.setGeometry(
                self.parent().width() - self.panel_width,
                0,
                self.panel_width,
                self.parent().height()
            )
        else:
            self.setGeometry(
                self.parent().width(),
                0,
                self.panel_width,
                self.parent().height()
            )

    def update_monitoring_data(self):
        """Обновить данные мониторинга"""
        if hasattr(self, 'monitoring_page'):
            self.monitoring_page.refresh_data()

    def add_console_message(self, message: str, level: str = "INFO"):
        """Добавить сообщение в консоль"""
        if hasattr(self, 'console_widget'):
            self.console_widget.add_message(message, level)

    def add_diagnostic_message(self, message: str, level: str = "INFO"):
        """Добавить диагностическое сообщение"""
        if hasattr(self, 'diagnostics_widget'):
            self.diagnostics_widget.add_diagnostic_message(message, level)

    def get_panel_width(self) -> int:
        """Получить ширину панели"""
        return self.panel_width

    def set_panel_width(self, width: int):
        """Установить ширину панели"""
        self.panel_width = max(400, min(800, width))  # Ограничиваем от 400 до 800px
        if self.is_open:
            self.resizeEvent(None)
