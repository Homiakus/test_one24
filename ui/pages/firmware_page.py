"""
Страница прошивки
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import pyqtSignal as Signal

from .base_page import BasePage
from ..widgets.modern_widgets import ModernCard, ModernButton


class FirmwarePage(BasePage):
    """Страница управления прошивкой"""

    # Сигналы
    firmware_build_requested = Signal(str)  # project_path
    firmware_upload_requested = Signal(str)  # port
    firmware_clean_requested = Signal(str)  # project_path

    def __init__(self, project_path: str = None, parent=None):
        self.project_path = project_path or "arduino"
        super().__init__(parent)

    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("🔧 Прошивка")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # Информационная карточка
        self._create_info_card(layout)

        # Карточка сборки
        self._create_build_card(layout)

        # Карточка загрузки
        self._create_upload_card(layout)

        # Карточка очистки
        self._create_clean_card(layout)

        # Область логов
        self._create_log_area(layout)

    def _create_info_card(self, parent_layout):
        """Создание информационной карточки"""
        card = ModernCard("ℹ️ Информация о проекте")

        info_text = QLabel(
            f"<b>Путь к проекту:</b> {self.project_path}<br>"
            f"<b>Статус:</b> Готов к работе<br>"
            f"<b>PlatformIO:</b> Требуется для работы с прошивкой"
        )
        info_text.setObjectName("info_text")
        card.addWidget(info_text)

        parent_layout.addWidget(card)

    def _create_build_card(self, parent_layout):
        """Создание карточки сборки"""
        card = ModernCard("🔨 Сборка прошивки")

        layout = QVBoxLayout()

        # Кнопки сборки
        build_btn = ModernButton("🔨 Собрать прошивку", "success")
        build_btn.clicked.connect(self._build_firmware)

        build_env_btn = ModernButton("🎯 Собрать для среды", "primary")
        build_env_btn.clicked.connect(self._build_for_environment)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(build_btn)
        buttons_layout.addWidget(build_env_btn)

        layout.addLayout(buttons_layout)

        # Прогресс-бар
        self.build_progress = QProgressBar()
        self.build_progress.setVisible(False)
        layout.addWidget(self.build_progress)

        card.addLayout(layout)
        parent_layout.addWidget(card)

    def _create_upload_card(self, parent_layout):
        """Создание карточки загрузки"""
        card = ModernCard("📤 Загрузка прошивки")

        layout = QVBoxLayout()

        # Выбор порта
        port_layout = QHBoxLayout()
        port_label = QLabel("Порт:")
        self.port_combo = QComboBox()
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5"])
        self.port_combo.setCurrentText("COM3")

        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)

        # Кнопки загрузки
        upload_btn = ModernButton("📤 Загрузить прошивку", "success")
        upload_btn.clicked.connect(self._upload_firmware)

        upload_monitor_btn = ModernButton("🔍 Загрузить и мониторить", "warning")
        upload_monitor_btn.clicked.connect(self._upload_and_monitor)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(upload_btn)
        buttons_layout.addWidget(upload_monitor_btn)

        layout.addLayout(port_layout)
        layout.addLayout(buttons_layout)

        # Прогресс-бар
        self.upload_progress = QProgressBar()
        self.upload_progress.setVisible(False)
        layout.addWidget(self.upload_progress)

        card.addLayout(layout)
        parent_layout.addWidget(card)

    def _create_clean_card(self, parent_layout):
        """Создание карточки очистки"""
        card = ModernCard("🧹 Очистка проекта")

        layout = QVBoxLayout()

        clean_btn = ModernButton("🧹 Очистить проект", "danger")
        clean_btn.clicked.connect(self._clean_project)

        clean_env_btn = ModernButton("🎯 Очистить среду", "warning")
        clean_env_btn.clicked.connect(self._clean_environment)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(clean_btn)
        buttons_layout.addWidget(clean_env_btn)

        layout.addLayout(buttons_layout)

        card.addLayout(layout)
        parent_layout.addWidget(card)

    def _create_log_area(self, parent_layout):
        """Создание области логов"""
        card = ModernCard("📋 Логи операций")

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)

        card.addWidget(self.log_area)
        parent_layout.addWidget(card)

    def _build_firmware(self):
        """Сборка прошивки"""
        self._show_progress(self.build_progress)
        self._add_log_entry("🔨 Начинается сборка прошивки...")

        # Запрашиваем сборку
        self.firmware_build_requested.emit(self.project_path)

    def _build_for_environment(self):
        """Сборка для конкретной среды"""
        # В будущем можно добавить выбор среды
        self._build_firmware()

    def _upload_firmware(self):
        """Загрузка прошивки"""
        port = self.port_combo.currentText()

        self._show_progress(self.upload_progress)
        self._add_log_entry(f"📤 Начинается загрузка прошивки на порт {port}...")

        # Запрашиваем загрузку
        self.firmware_upload_requested.emit(port)

    def _upload_and_monitor(self):
        """Загрузка и запуск мониторинга"""
        self._upload_firmware()
        # В будущем добавить автоматический запуск мониторинга

    def _clean_project(self):
        """Очистка проекта"""
        self._add_log_entry("🧹 Начинается очистка проекта...")

        # Запрашиваем очистку
        self.firmware_clean_requested.emit(self.project_path)

    def _clean_environment(self):
        """Очистка конкретной среды"""
        self._clean_project()

    def _show_progress(self, progress_bar):
        """Показ прогресса"""
        progress_bar.setVisible(True)
        progress_bar.setRange(0, 0)  # Неопределенный прогресс

    def _hide_progress(self, progress_bar):
        """Скрытие прогресса"""
        progress_bar.setVisible(False)

    def _add_log_entry(self, message: str):
        """Добавление записи в лог"""
        current_text = self.log_area.toPlainText()
        self.log_area.setPlainText(current_text + message + "\n")
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def update_build_progress(self, current: int, total: int):
        """Обновление прогресса сборки"""
        self.build_progress.setRange(0, total)
        self.build_progress.setValue(current)

    def update_upload_progress(self, current: int, total: int):
        """Обновление прогресса загрузки"""
        self.upload_progress.setRange(0, total)
        self.upload_progress.setValue(current)

    def on_build_finished(self, success: bool, message: str):
        """Обработка завершения сборки"""
        self._hide_progress(self.build_progress)

        status = "✅" if success else "❌"
        self._add_log_entry(f"{status} Сборка завершена: {message}")

        if success:
            self.status_message.emit("✅ Сборка прошивки завершена", 3000)
        else:
            self.status_message.emit("❌ Ошибка сборки прошивки", 5000)

    def on_upload_finished(self, success: bool, message: str):
        """Обработка завершения загрузки"""
        self._hide_progress(self.upload_progress)

        status = "✅" if success else "❌"
        self._add_log_entry(f"{status} Загрузка завершена: {message}")

        if success:
            self.status_message.emit("✅ Загрузка прошивки завершена", 3000)
        else:
            self.status_message.emit("❌ Ошибка загрузки прошивки", 5000)

    def on_clean_finished(self, success: bool, message: str):
        """Обработка завершения очистки"""
        status = "✅" if success else "❌"
        self._add_log_entry(f"{status} Очистка завершена: {message}")

        if success:
            self.status_message.emit("✅ Очистка проекта завершена", 3000)
        else:
            self.status_message.emit("❌ Ошибка очистки проекта", 5000)

    def refresh(self):
        """Обновление страницы"""
        # Очищаем логи
        self.log_area.clear()

        # Сбрасываем прогресс
        self._hide_progress(self.build_progress)
        self._hide_progress(self.upload_progress)
