"""
Страница настроек
"""
from typing import List
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QScrollArea, QFormLayout, QWidget
)
from PyQt6.QtCore import pyqtSignal as Signal

from .base_page import BasePage
from ..widgets.modern_widgets import ModernCard, ModernButton


class SettingsPage(BasePage):
    """Страница настроек приложения"""

    # Сигналы
    connect_requested = Signal()
    disconnect_requested = Signal()
    settings_changed = Signal(dict)
    config_reload_requested = Signal()

    def __init__(self, settings_manager, parent=None):
        self.settings_manager = settings_manager
        super().__init__(parent)

    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("⚙️ Настройки")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName("transparent_scroll")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(20)

        # Карточка подключения
        self._create_connection_card(scroll_layout)

        # Карточка настроек приложения
        self._create_app_settings_card(scroll_layout)

        # Карточка информации
        self._create_info_card(scroll_layout)

        # Кнопки действий
        self._create_action_buttons(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

    def _create_connection_card(self, parent_layout):
        """Создание карточки подключения"""
        card = ModernCard("🔌 Подключение")
        form_layout = QFormLayout()

        # Порт
        self.port_combo = QComboBox()
        self.port_combo.currentTextChanged.connect(self._on_port_changed)
        form_layout.addRow("Порт:", self.port_combo)

        # Скорость
        self.baud_combo = QComboBox()
        bauds = ['9600', '19200', '38400', '57600',
                '115200', '230400', '460800', '921600']
        self.baud_combo.addItems(bauds)
        self.baud_combo.setCurrentText(
            str(self.settings_manager.serial_settings.baudrate)
        )
        self.baud_combo.currentTextChanged.connect(self._on_baud_changed)
        form_layout.addRow("Скорость:", self.baud_combo)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        connect_btn = ModernButton("🔗 Подключиться", "success")
        connect_btn.clicked.connect(self.connect_requested.emit)

        disconnect_btn = ModernButton("📴 Отключиться", "danger")
        disconnect_btn.clicked.connect(self.disconnect_requested.emit)

        refresh_btn = ModernButton("🔄 Обновить", "secondary")
        refresh_btn.clicked.connect(self.refresh_ports)

        buttons_layout.addWidget(connect_btn)
        buttons_layout.addWidget(disconnect_btn)
        buttons_layout.addWidget(refresh_btn)

        form_layout.addRow("", buttons_layout)
        card.addLayout(form_layout)
        parent_layout.addWidget(card)

        # Инициализация портов
        self.refresh_ports()

    def _create_app_settings_card(self, parent_layout):
        """Создание карточки настроек приложения"""
        card = ModernCard("🎨 Интерфейс")
        form_layout = QFormLayout()

        # Автоподключение
        self.auto_connect_check = QCheckBox("Автоматически подключаться при запуске")
        self.auto_connect_check.setChecked(
            self.settings_manager.update_settings.auto_connect
        )
        self.auto_connect_check.toggled.connect(self._on_auto_connect_changed)
        form_layout.addRow("", self.auto_connect_check)

        card.addLayout(form_layout)
        parent_layout.addWidget(card)

    def _create_info_card(self, parent_layout):
        """Создание карточки информации"""
        card = ModernCard("ℹ️ Информация")

        info_text = QLabel(
            f"<b>Версия:</b> 2.0 (PySide6)<br>"
            f"<b>Файл конфигурации:</b> config.toml"
        )
        info_text.setObjectName("info_text")
        card.addWidget(info_text)

        parent_layout.addWidget(card)

    def _create_action_buttons(self, parent_layout):
        """Создание кнопок действий"""
        card = ModernCard("🛠️ Действия")
        buttons_layout = QHBoxLayout()

        save_btn = ModernButton("💾 Сохранить", "success")
        save_btn.clicked.connect(self._save_settings)

        reload_btn = ModernButton("🔄 Перезагрузить конфигурацию", "warning")
        reload_btn.clicked.connect(self.config_reload_requested.emit)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(reload_btn)

        card.addLayout(buttons_layout)
        parent_layout.addWidget(card)

    def refresh_ports(self):
        """Обновление списка портов"""
        from core.serial_manager import SerialManager

        current = self.port_combo.currentText()
        self.port_combo.clear()

        ports = SerialManager.get_available_ports()
        if ports:
            self.port_combo.addItems(ports)
            if current in ports:
                self.port_combo.setCurrentText(current)
            else:
                saved_port = self.settings_manager.serial_settings.port
                if saved_port in ports:
                    self.port_combo.setCurrentText(saved_port)
        else:
            self.port_combo.addItem("Нет доступных портов")

    def _on_port_changed(self, port: str):
        """Обработка изменения порта"""
        if port and port != "Нет доступных портов":
            self.settings_manager.serial_settings.port = port

    def _on_baud_changed(self, baud: str):
        """Обработка изменения скорости"""
        try:
            self.settings_manager.serial_settings.baudrate = int(baud)
        except ValueError:
            pass

    def _on_auto_connect_changed(self, checked: bool):
        """Обработка изменения автоподключения"""
        self.settings_manager.update_settings.auto_connect = checked

    def _save_settings(self):
        """Сохранение настроек"""
        self.settings_manager.save_all()
        self.status_message.emit("💾 Настройки сохранены", 3000)
        self.logger.info("Настройки сохранены")
