"""
Страница последовательностей
"""
from typing import List, Dict
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QGroupBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import pyqtSignal as Signal, Qt

from .base_page import BasePage
from ..shared.utils import create_input_dialog, create_confirmation_dialog


class SequencesPage(BasePage):
    """Страница управления последовательностями"""

    # Сигналы
    sequence_selected = Signal(str)  # sequence_name
    sequence_execute_requested = Signal(str)  # sequence_name
    sequence_edited = Signal(str, list)  # sequence_name, commands

    def __init__(self, sequences_config: Dict[str, List[str]], parent=None):
        self.sequences_config = sequences_config or {}
        self.current_sequence = None
        super().__init__("Последовательности", parent)

    def _get_page_title(self) -> str:
        """Получить заголовок страницы"""
        return "📋 Последовательности"

    def _setup_additional_ui(self):
        """Настройка дополнительных элементов UI"""
        # Основная область с разделителем
        main_splitter = self.create_splitter(Qt.Orientation.Horizontal)
        self.content_layout.addWidget(main_splitter)

        # Левая панель - список последовательностей
        left_widget = self._create_sequences_list()
        main_splitter.addWidget(left_widget)

        # Правая панель - детали последовательности
        right_widget = self._create_sequence_details()
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([300, 600])

        # Кнопки действий
        self._create_action_buttons()

    def _create_sequences_list(self):
        """Создание списка последовательностей"""
        card = self.create_card("Последовательности")

        layout = self.create_page_layout(margins=(10, 10, 10, 10), spacing=10)

        # Список последовательностей
        self.sequences_list = QListWidget()
        self.sequences_list.itemClicked.connect(self._on_sequence_selected)
        layout.addWidget(self.sequences_list)

        # Обновляем список
        self._refresh_sequences_list()

        card.addLayout(layout)
        return card

    def _create_sequence_details(self):
        """Создание области деталей последовательности"""
        card = self.create_card("Детали последовательности")

        layout = self.create_page_layout(margins=(10, 10, 10, 10), spacing=10)

        # Название последовательности
        self.sequence_name_label = QLabel("Выберите последовательность")
        self.sequence_name_label.setObjectName("sequence_name")
        layout.addWidget(self.sequence_name_label)

        # Описание команд
        self.commands_text = QTextEdit()
        self.commands_text.setReadOnly(True)
        self.commands_text.setMaximumHeight(200)
        layout.addWidget(self.commands_text)

        # Кнопки управления
        buttons_layout = self.create_horizontal_layout()

        self.execute_btn = self.create_button("▶ Выполнить", "success")
        self.execute_btn.clicked.connect(self._execute_sequence)
        self.execute_btn.setEnabled(False)

        self.edit_btn = self.create_button("✏️ Редактировать", "primary")
        self.edit_btn.clicked.connect(self._edit_sequence)
        self.edit_btn.setEnabled(False)

        buttons_layout.addWidget(self.execute_btn)
        buttons_layout.addWidget(self.edit_btn)

        layout.addLayout(buttons_layout)

        card.addLayout(layout)
        return card

    def _create_action_buttons(self):
        """Создание кнопок действий"""
        card = self.create_card("Действия")
        
        # Подготавливаем данные для кнопок
        button_data = [
            {
                'text': '➕ Добавить',
                'type': 'success',
                'clicked': self._add_sequence
            },
            {
                'text': '➖ Удалить',
                'type': 'danger',
                'clicked': self._remove_sequence
            },
            {
                'text': '🔄 Обновить',
                'type': 'secondary',
                'clicked': self._refresh_sequences_list
            }
        ]
        
        # Создаем layout с кнопками
        buttons_layout = self.create_button_grid(button_data, max_cols=3, spacing=10)
        card.addLayout(buttons_layout)
        
        self.content_layout.addWidget(card)

    def _refresh_sequences_list(self):
        """Обновление списка последовательностей"""
        self.sequences_list.clear()

        for sequence_name in sorted(self.sequences_config.keys()):
            item = QListWidgetItem(sequence_name)
            item.setData(Qt.ItemDataRole.UserRole, sequence_name)
            self.sequences_list.addItem(item)

    def _on_sequence_selected(self, item):
        """Обработка выбора последовательности"""
        sequence_name = item.data(Qt.ItemDataRole.UserRole)
        self.current_sequence = sequence_name
        self.sequence_selected.emit(sequence_name)

        # Обновляем детали
        self._update_sequence_details()

        # Активируем кнопки
        self.execute_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)

    def _update_sequence_details(self):
        """Обновление деталей последовательности"""
        if not self.current_sequence:
            return

        sequence_name = self.current_sequence
        commands = self.sequences_config.get(sequence_name, [])

        self.sequence_name_label.setText(f"Последовательность: {sequence_name}")

        # Формируем текст с командами
        commands_text = ""
        for i, cmd in enumerate(commands, 1):
            commands_text += f"{i}. {cmd}\n"

        self.commands_text.setPlainText(commands_text)

    def _execute_sequence(self):
        """Выполнение выбранной последовательности"""
        if self.current_sequence:
            self.sequence_execute_requested.emit(self.current_sequence)
            self.show_status_message(f"Выполняется последовательность: {self.current_sequence}")

    def _edit_sequence(self):
        """Редактирование последовательности"""
        if not self.current_sequence:
            return

        # Получаем текущие команды
        current_commands = self.sequences_config.get(self.current_sequence, [])

        # Запрашиваем новые команды
        ok, commands_text = create_input_dialog(
            "Редактирование последовательности",
            "Введите команды (по одной на строку):",
            "\n".join(current_commands),
            self
        )

        if ok and commands_text:
            new_commands = [cmd.strip() for cmd in commands_text.split('\n') if cmd.strip()]

            # Обновляем конфигурацию
            self.sequences_config[self.current_sequence] = new_commands

            # Сигнализируем об изменении
            self.sequence_edited.emit(self.current_sequence, new_commands)

            # Обновляем отображение
            self._update_sequence_details()
            
            self.show_status_message(f"Последовательность '{self.current_sequence}' обновлена")

    def _add_sequence(self):
        """Добавление новой последовательности"""
        ok, sequence_name = create_input_dialog(
            "Добавление последовательности",
            "Введите название последовательности:",
            "",
            self
        )

        if ok and sequence_name:
            sequence_name = sequence_name.strip()
            if sequence_name in self.sequences_config:
                self.show_error_message(f"Последовательность '{sequence_name}' уже существует")
                return

            # Добавляем пустую последовательность
            self.sequences_config[sequence_name] = []
            
            # Обновляем список
            self._refresh_sequences_list()
            
            self.show_status_message(f"Последовательность '{sequence_name}' добавлена")

    def _remove_sequence(self):
        """Удаление последовательности"""
        if not self.current_sequence:
            self.show_error_message("Выберите последовательность для удаления")
            return

        # Запрашиваем подтверждение
        if create_confirmation_dialog(
            "Удаление последовательности",
            f"Вы уверены, что хотите удалить последовательность '{self.current_sequence}'?",
            self
        ):
            # Удаляем последовательность
            del self.sequences_config[self.current_sequence]
            
            # Очищаем текущую последовательность
            self.current_sequence = None
            
            # Обновляем интерфейс
            self._refresh_sequences_list()
            self._update_sequence_details()
            
            # Деактивируем кнопки
            self.execute_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            
            self.show_status_message("Последовательность удалена")

    def refresh(self):
        """Обновление страницы"""
        self._refresh_sequences_list()
        self._update_sequence_details()
        super().refresh()
