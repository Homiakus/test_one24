"""
Страница команд
"""
from typing import Dict
from PySide6.QtWidgets import (
    QHBoxLayout, QLineEdit, QTextEdit, QMessageBox
)
from PySide6.QtCore import Signal

from .base_page import BasePage
from ..shared.utils import create_confirmation_dialog


class CommandsPage(BasePage):
    """Страница управления командами"""

    # Сигналы
    command_execute_requested = Signal(str)  # command
    command_edited = Signal(str, str)  # button_name, command

    def __init__(self, buttons_config: Dict[str, str], parent=None):
        self.buttons_config = buttons_config or {}
        self.button_groups = self._group_buttons()
        super().__init__("Команды", parent)

    def _get_page_title(self) -> str:
        """Получить заголовок страницы"""
        return "⚡ Команды"

    def _setup_additional_ui(self):
        """Настройка дополнительных элементов UI"""
        # Создаем группы команд
        self._create_command_groups()
        
        # Создаем панель тестирования
        self._create_test_panel()

    def _group_buttons(self) -> Dict[str, Dict[str, str]]:
        """Группировка кнопок по категориям"""
        groups = {}

        for button_name, command in self.buttons_config.items():
            # Определяем группу по префиксу или используем "Основные"
            if ":" in button_name:
                group_name = button_name.split(":")[0]
            else:
                group_name = "Основные команды"

            if group_name not in groups:
                groups[group_name] = {}

            groups[group_name][button_name] = command

        return groups

    def _create_command_groups(self):
        """Создание групп команд"""
        for group_name, buttons in self.button_groups.items():
            # Создаем карточку для группы
            card = self.create_card(group_name)
            
            # Подготавливаем данные для кнопок
            button_data = []
            for button_name, command in buttons.items():
                button_data.append({
                    'text': button_name,
                    'type': 'primary',
                    'clicked': lambda checked, cmd=command: self._execute_command(cmd)
                })
            
            # Создаем сетку кнопок
            grid = self.create_button_grid(button_data, max_cols=3, spacing=10)
            card.addLayout(grid)
            
            # Добавляем карточку в layout
            self.content_layout.addWidget(card)

    def _create_test_panel(self):
        """Создание панели тестирования"""
        card = self.create_card("🧪 Тестирование команд")
        
        layout = self.create_horizontal_layout(spacing=10)
        
        # Поле ввода команды
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Введите команду...")
        layout.addWidget(self.command_input)
        
        # Кнопка выполнения
        execute_btn = self.create_button("Выполнить", "success")
        execute_btn.clicked.connect(self._execute_custom_command)
        layout.addWidget(execute_btn)
        
        # Добавляем layout в карточку
        card.addLayout(layout)
        
        # Область вывода результатов
        self.output_area = QTextEdit()
        self.output_area.setMaximumHeight(150)
        self.output_area.setReadOnly(True)
        card.addWidget(self.output_area)
        
        # Добавляем карточку в layout
        self.content_layout.addWidget(card)

    def _execute_command(self, command: str):
        """Выполнение команды"""
        self.command_execute_requested.emit(command)
        self.logger.info(f"Выполнение команды: {command}")
        self.show_status_message(f"Выполняется команда: {command}")

    def _execute_custom_command(self):
        """Выполнение пользовательской команды"""
        command = self.command_input.text().strip()
        if not command:
            self.show_error_message("Введите команду", "validation_error")
            return

        self._execute_command(command)
        self.command_input.clear()

    def add_command_output(self, output: str):
        """Добавление вывода команды"""
        current_text = self.output_area.toPlainText()
        self.output_area.setPlainText(current_text + output + "\n")
        self.output_area.verticalScrollBar().setValue(
            self.output_area.verticalScrollBar().maximum()
        )

    def refresh(self):
        """Обновление страницы"""
        # Перегруппировываем кнопки
        self.button_groups = self._group_buttons()
        
        # Очищаем контент
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Пересоздаем интерфейс
        self._setup_additional_ui()
        
        super().refresh()
