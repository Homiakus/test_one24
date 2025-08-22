"""
@file: monitoring_panel.py
@description: Выдвигающаяся панель мониторинга с поддержкой свайпа
@dependencies: PySide6, monitoring
@created: 2024-12-19
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRect, QPoint
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
)

from monitoring import MonitoringManager
from ui.pages.monitoring_page import MonitoringPage


class MonitoringPanel(QWidget):
    """Выдвигающаяся панель мониторинга"""
    
    def __init__(self, monitoring_manager: MonitoringManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.monitoring_manager = monitoring_manager
        
        # Состояние панели
        self.is_open = False
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.panel_width = 400
        
        # Анимация
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Настройка виджета
        self.setup_ui()
        self.setup_animations()
        self.setup_events()
        
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
        self.create_scroll_area(main_layout)
        
        # Установка стилей
        self.setObjectName("monitoring_panel")
        self.setStyleSheet("""
            QWidget#monitoring_panel {
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
        title = QLabel("📊 Мониторинг системы")
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
        
    def create_scroll_area(self, parent_layout):
        """Создание области прокрутки"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для контента
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.scroll_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Добавляем страницу мониторинга
        content_layout = QVBoxLayout(self.scroll_content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.monitoring_page = MonitoringPage(self.monitoring_manager)
        content_layout.addWidget(self.monitoring_page)
        
        self.scroll_area.setWidget(self.scroll_content)
        parent_layout.addWidget(self.scroll_area)
        
    def setup_animations(self):
        """Настройка анимаций"""
        self.animation.finished.connect(self.on_animation_finished)
        
    def setup_events(self):
        """Настройка обработки событий"""
        # Включаем отслеживание мыши для свайпа
        self.setMouseTracking(True)
        
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
            
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка нажатия мыши"""
        # Обрабатываем только клики внутри панели
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Обработка движения мыши"""
        # Обрабатываем только движение внутри панели
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Обработка отпускания мыши"""
        # Обрабатываем только отпускание внутри панели
        super().mouseReleaseEvent(event)
        
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
            
    def get_panel_width(self) -> int:
        """Получить ширину панели"""
        return self.panel_width
        
    def set_panel_width(self, width: int):
        """Установить ширину панели"""
        self.panel_width = max(300, min(600, width))  # Ограничиваем от 300 до 600px
        if self.is_open:
            self.resizeEvent(None)
