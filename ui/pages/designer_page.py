"""
Страница конструктора
"""
from typing import List, Dict
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QTextEdit, QSplitter, QInputDialog,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import Signal, Qt

from .base_page import BasePage
from ..widgets.modern_widgets import ModernCard, ModernButton


class DesignerPage(BasePage):
    """Страница конструктора последовательностей"""

    # Сигналы
    sequence_created = Signal(str, list)  # sequence_name, commands
    sequence_updated = Signal(str, list)  # sequence_name, commands

    def __init__(self, buttons_config: Dict[str, str], parent=None):
        self.buttons_config = buttons_config or {}
        self.current_sequence = []
        self.current_sequence_name = None
        super().__init__(parent)

    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("🔧 Конструктор последовательностей")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # Основная область
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        # Левая панель - доступные команды
        left_widget = self._create_available_commands()
        main_splitter.addWidget(left_widget)

        # Центральная панель - текущая последовательность
        center_widget = self._create_current_sequence()
        main_splitter.addWidget(center_widget)

        # Правая панель - настройки
        right_widget = self._create_settings()
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([250, 400, 250])

        # Кнопки действий
        self._create_action_buttons(layout)

    def _create_available_commands(self):
        """Создание панели доступных команд"""
        card = ModernCard("Доступные команды")

        layout = QVBoxLayout()

        # Список команд
        self.available_commands = QListWidget()
        self.available_commands.itemDoubleClicked.connect(self._add_command_to_sequence)

        # Добавляем стандартные команды
        standard_commands = [
            "wait 1", "wait 2", "wait 5",
            "test", "stop", "reset"
        ]

        for cmd in standard_commands:
            item = QListWidgetItem(cmd)
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.available_commands.addItem(item)

        # Добавляем команды из конфигурации
        for name, cmd in self.buttons_config.items():
            item = QListWidgetItem(f"{name} ({cmd})")
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.available_commands.addItem(item)

        layout.addWidget(self.available_commands)

        # Кнопка добавления пользовательской команды
        add_custom_btn = ModernButton("➕ Добавить команду", "secondary")
        add_custom_btn.clicked.connect(self._add_custom_command)
        layout.addWidget(add_custom_btn)

        card.addLayout(layout)
        return card

    def _create_current_sequence(self):
        """Создание панели текущей последовательности"""
        card = ModernCard("Текущая последовательность")

        layout = QVBoxLayout()

        # Список команд последовательности
        self.sequence_list = QListWidget()
        self.sequence_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        layout.addWidget(self.sequence_list)

        # Кнопки управления последовательностью
        seq_btns_layout = QHBoxLayout()

        move_up_btn = ModernButton("↑", "secondary")
        move_up_btn.clicked.connect(self._move_command_up)

        move_down_btn = ModernButton("↓", "secondary")
        move_down_btn.clicked.connect(self._move_command_down)

        remove_btn = ModernButton("✖", "danger")
        remove_btn.clicked.connect(self._remove_command)

        seq_btns_layout.addWidget(move_up_btn)
        seq_btns_layout.addWidget(move_down_btn)
        seq_btns_layout.addWidget(remove_btn)

        layout.addLayout(seq_btns_layout)

        # Предварительный просмотр
        preview_label = QLabel("Предварительный просмотр:")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        layout.addWidget(self.preview_text)

        card.addLayout(layout)
        return card

    def _create_settings(self):
        """Создание панели настроек"""
        card = ModernCard("Настройки последовательности")

        layout = QVBoxLayout()

        # Название последовательности
        name_layout = QHBoxLayout()
        name_label = QLabel("Название:")
        self.sequence_name_edit = QLineEdit()
        self.sequence_name_edit.setPlaceholderText("Введите название...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.sequence_name_edit)
        layout.addLayout(name_layout)

        # Описание
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Описание:")
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Введите описание...")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_edit)
        layout.addLayout(desc_layout)

        # Статистика
        self.stats_label = QLabel("Команд: 0\nВремя выполнения: ~0 сек")
        self.stats_label.setObjectName("stats_label")
        layout.addWidget(self.stats_label)

        card.addLayout(layout)
        return card

    def _create_action_buttons(self, parent_layout):
        """Создание кнопок действий"""
        card = ModernCard("Действия")
        buttons_layout = QHBoxLayout()

        save_btn = ModernButton("💾 Сохранить", "success")
        save_btn.clicked.connect(self._save_sequence)

        load_btn = ModernButton("📂 Загрузить", "primary")
        load_btn.clicked.connect(self._load_sequence)

        clear_btn = ModernButton("🗑️ Очистить", "danger")
        clear_btn.clicked.connect(self._clear_sequence)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(load_btn)
        buttons_layout.addWidget(clear_btn)

        card.addLayout(buttons_layout)
        parent_layout.addWidget(card)

    def _add_command_to_sequence(self, item):
        """Добавление команды в последовательность"""
        command = item.data(Qt.ItemDataRole.UserRole)

        # Добавляем в список
        list_item = QListWidgetItem(command)
        list_item.setData(Qt.ItemDataRole.UserRole, command)
        self.sequence_list.addItem(list_item)

        # Обновляем последовательность
        self.current_sequence.append(command)
        self._update_preview()
        self._update_stats()

    def _add_custom_command(self):
        """Добавление пользовательской команды"""
        command, ok = QInputDialog.getText(
            self,
            "Добавить команду",
            "Введите команду:"
        )

        if ok and command.strip():
            # Добавляем в доступные команды
            item = QListWidgetItem(command.strip())
            item.setData(Qt.ItemDataRole.UserRole, command.strip())
            self.available_commands.addItem(item)

            self.logger.info(f"Добавлена пользовательская команда: {command}")

    def _move_command_up(self):
        """Перемещение команды вверх"""
        current_row = self.sequence_list.currentRow()
        if current_row > 0:
            # Меняем местами в списке
            current_item = self.sequence_list.takeItem(current_row)
            self.sequence_list.insertItem(current_row - 1, current_item)
            self.sequence_list.setCurrentRow(current_row - 1)

            # Меняем местами в последовательности
            self.current_sequence[current_row], self.current_sequence[current_row - 1] = \
                self.current_sequence[current_row - 1], self.current_sequence[current_row]

            self._update_preview()

    def _move_command_down(self):
        """Перемещение команды вниз"""
        current_row = self.sequence_list.currentRow()
        if current_row < self.sequence_list.count() - 1:
            # Меняем местами в списке
            current_item = self.sequence_list.takeItem(current_row)
            self.sequence_list.insertItem(current_row + 1, current_item)
            self.sequence_list.setCurrentRow(current_row + 1)

            # Меняем местами в последовательности
            self.current_sequence[current_row], self.current_sequence[current_row + 1] = \
                self.current_sequence[current_row + 1], self.current_sequence[current_row]

            self._update_preview()

    def _remove_command(self):
        """Удаление команды"""
        current_row = self.sequence_list.currentRow()
        if current_row >= 0:
            self.sequence_list.takeItem(current_row)
            del self.current_sequence[current_row]
            self._update_preview()
            self._update_stats()

    def _update_preview(self):
        """Обновление предварительного просмотра"""
        preview_text = ""
        for i, cmd in enumerate(self.current_sequence, 1):
            preview_text += f"{i}. {cmd}\n"

        self.preview_text.setPlainText(preview_text)

    def _update_stats(self):
        """Обновление статистики"""
        command_count = len(self.current_sequence)

        # Приблизительное время выполнения
        estimated_time = 0
        for cmd in self.current_sequence:
            if cmd.startswith("wait "):
                try:
                    wait_time = float(cmd.split()[1])
                    estimated_time += wait_time
                except (IndexError, ValueError):
                    pass
            else:
                estimated_time += 1  # Предполагаем 1 секунду на команду

        self.stats_label.setText(f"Команд: {command_count}\nВремя выполнения: ~{estimated_time} сек")

    def _save_sequence(self):
        """Сохранение последовательности"""
        sequence_name = self.sequence_name_edit.text().strip()
        if not sequence_name:
            QMessageBox.warning(self, "Ошибка", "Введите название последовательности")
            return

        if not self.current_sequence:
            QMessageBox.warning(self, "Ошибка", "Последовательность пуста")
            return

        self.current_sequence_name = sequence_name
        self.sequence_created.emit(sequence_name, self.current_sequence.copy())

        QMessageBox.information(
            self,
            "Успех",
            f"Последовательность '{sequence_name}' сохранена"
        )

        self.logger.info(f"Сохранена последовательность: {sequence_name}")

    def _load_sequence(self):
        """Загрузка последовательности"""
        # В реальной реализации здесь будет диалог выбора
        QMessageBox.information(self, "Информация", "Функция загрузки пока не реализована")

    def _clear_sequence(self):
        """Очистка последовательности"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Очистить текущую последовательность?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.sequence_list.clear()
            self.current_sequence.clear()
            self.current_sequence_name = None
            self.sequence_name_edit.clear()
            self.description_edit.clear()
            self._update_preview()
            self._update_stats()

    def refresh(self):
        """Обновление страницы"""
        # Перезагружаем доступные команды
        self.available_commands.clear()

        # Стандартные команды
        standard_commands = ["wait 1", "wait 2", "wait 5", "test", "stop", "reset"]
        for cmd in standard_commands:
            item = QListWidgetItem(cmd)
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.available_commands.addItem(item)

        # Команды из конфигурации
        for name, cmd in self.buttons_config.items():
            item = QListWidgetItem(f"{name} ({cmd})")
            item.setData(Qt.ItemDataRole.UserRole, cmd)
            self.available_commands.addItem(item)
