"""
Современные виджеты для интерфейса
"""
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal as pyqtSignal as Signal
from PyQt6.QtGui import QFont, QColor, QIntValidator
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog, QLineEdit, QGridLayout
)


class ModernCard(QFrame):
    """Современная карточка для группировки элементов"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("modern_card")

        # Основной layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # Заголовок
        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("card_title")
            self.layout.addWidget(self.title_label)

    def addWidget(self, widget):
        """Добавление виджета в карточку"""
        self.layout.addWidget(widget)

    def addLayout(self, layout):
        """Добавление layout в карточку"""
        self.layout.addLayout(layout)

    def setTitle(self, title: str):
        """Установка заголовка"""
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)


class ModernButton(QPushButton):
    """Современная кнопка с различными стилями"""

    BUTTON_TYPES = {
        "primary": "primary_button",
        "secondary": "secondary_button",
        "success": "success_button",
        "warning": "warning_button",
        "danger": "danger_button"
    }

    def __init__(self, text: str = "", button_type: str = "primary",
                 icon=None, parent=None):
        super().__init__(text, parent)

        self.button_type = button_type
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if icon:
            self.setIcon(icon)

        # Применяем стиль через класс объекта
        self.setObjectName(self.BUTTON_TYPES.get(button_type, "primary_button"))


class NumericPadDialog(QDialog):
    """Диалог для ввода чисел с виртуальной клавиатурой"""

    value_changed = Signal(int)

    def __init__(self, initial_value: int = 0, min_value: int = 0,
                 max_value: int = 9999, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введите число")
        self.setModal(True)
        self.setFixedSize(280, 360)

        self.min_value = min_value
        self.max_value = max_value

        self._setup_ui(initial_value)

    def _setup_ui(self, initial_value: int):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)

        # Поле ввода
        self.edit = QLineEdit(str(initial_value))
        self.edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit.setValidator(QIntValidator(self.min_value, self.max_value, self))
        self.edit.setFixedHeight(40)
        self.edit.setObjectName("numeric_input")
        layout.addWidget(self.edit)

        # Сетка кнопок
        grid = QGridLayout()
        grid.setSpacing(5)

        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
            ("←", 3, 0), ("0", 3, 1), ("OK", 3, 2),
        ]

        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFixedSize(80, 60)
            btn.setObjectName("numpad_button")
            btn.clicked.connect(lambda checked, t=text: self._handle_button(t))
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)

    def _handle_button(self, text: str):
        """Обработка нажатия кнопки"""
        if text == "OK":
            if not self.edit.text():
                self.edit.setText("0")
            self.accept()
        elif text == "←":
            self.edit.backspace()
        else:  # Цифра
            current = self.edit.text()
            new_value = current + text

            # Проверяем, не превышает ли значение максимум
            try:
                if int(new_value) <= self.max_value:
                    self.edit.setText(new_value)
            except ValueError:
                pass

    def value(self) -> int:
        """Получение введенного значения"""
        try:
            return int(self.edit.text())
        except ValueError:
            return self.min_value
