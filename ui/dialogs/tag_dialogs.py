"""
Диалоги для тегов команд
"""
import logging
from typing import Optional, Callable
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QMessageBox
)
from PySide6.QtGui import QFont, QIcon


class WantedTagDialog(QDialog):
    """Диалог для тега _wanted - проверка жидкостей"""
    
    # Сигналы
    fluid_checked = Signal()  # Пользователь подтвердил проверку жидкостей
    operation_cancelled = Signal()  # Пользователь отменил операцию
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.result_action = None  # Результат действия пользователя
        
        self._setup_ui()
        self._setup_connections()
        
        self.logger.info("Диалог WantedTagDialog создан")
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Проверка жидкостей")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Иконка и заголовок
        self._create_header(main_layout)
        
        # Сообщение
        self._create_message(main_layout)
        
        # Инструкции
        self._create_instructions(main_layout)
        
        # Кнопки
        self._create_buttons(main_layout)
        
        # Стили
        self._apply_styles()
    
    def _create_header(self, parent_layout):
        """Создание заголовка"""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Иконка предупреждения
        icon_label = QLabel("⚠️")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Заголовок
        title_label = QLabel("Проверка жидкостей")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ff6b35;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        parent_layout.addLayout(header_layout)
    
    def _create_message(self, parent_layout):
        """Создание сообщения"""
        message_label = QLabel(
            "Закончилась жидкость.\n"
            "Проверьте жидкости перед продолжением операции."
        )
        message_label.setFont(QFont("Arial", 12))
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                color: #856404;
            }
        """)
        parent_layout.addWidget(message_label)
    
    def _create_instructions(self, parent_layout):
        """Создание инструкций"""
        instructions_text = QTextEdit()
        instructions_text.setPlainText(
            "Инструкции по проверке жидкостей:\n\n"
            "1. Проверьте уровень жидкости в резервуаре\n"
            "2. Убедитесь, что жидкость не загрязнена\n"
            "3. При необходимости замените или долейте жидкость\n"
            "4. Проверьте герметичность соединений\n"
            "5. Убедитесь, что все клапаны закрыты\n\n"
            "После проверки нажмите 'Проверить жидкости' для продолжения."
        )
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(120)
        instructions_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 11px;
            }
        """)
        parent_layout.addWidget(instructions_text)
    
    def _create_buttons(self, parent_layout):
        """Создание кнопок"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Кнопка "Проверить жидкости"
        self.check_fluids_button = QPushButton("Проверить жидкости")
        self.check_fluids_button.setDefault(True)
        self.check_fluids_button.setMinimumHeight(40)
        self.check_fluids_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        button_layout.addWidget(self.check_fluids_button)
        
        # Кнопка "Отмена"
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        parent_layout.addLayout(button_layout)
    
    def _setup_connections(self):
        """Настройка соединений сигналов"""
        self.check_fluids_button.clicked.connect(self._on_fluids_checked)
        self.cancel_button.clicked.connect(self._on_cancelled)
    
    def _apply_styles(self):
        """Применение стилей к диалогу"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
    
    def _on_fluids_checked(self):
        """Обработка нажатия кнопки 'Проверить жидкости'"""
        self.logger.info("Пользователь подтвердил проверку жидкостей")
        self.result_action = "check_fluids"
        self.fluid_checked.emit()
        self.accept()
    
    def _on_cancelled(self):
        """Обработка нажатия кнопки 'Отмена'"""
        self.logger.info("Пользователь отменил операцию")
        self.result_action = "cancel"
        self.operation_cancelled.emit()
        self.reject()
    
    def get_result(self) -> Optional[str]:
        """Получение результата действия пользователя"""
        return self.result_action
    
    def show_dialog(self) -> str:
        """
        Показ диалога и ожидание результата.
        
        Returns:
            'check_fluids' - пользователь подтвердил проверку жидкостей
            'cancel' - пользователь отменил операцию
        """
        self.logger.info("Показ диалога проверки жидкостей")
        result = self.exec()
        
        if result == QDialog.DialogCode.Accepted:
            return "check_fluids"
        else:
            return "cancel"


class TagDialogManager:
    """Менеджер диалогов тегов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._dialogs = {}
        self._register_dialogs()
        self.on_wanted_dialog_result = None  # Callback для результата диалога _wanted
    
    def _register_dialogs(self):
        """Регистрация диалогов"""
        self._dialogs['wanted'] = WantedTagDialog
    
    def show_tag_dialog(self, dialog_type: str, parent=None) -> Optional[str]:
        """
        Показ диалога тега.
        
        Args:
            dialog_type: Тип диалога ('wanted', etc.)
            parent: Родительский виджет
            
        Returns:
            Результат действия пользователя или None
        """
        self.logger.info(f"Показ диалога тега: {dialog_type}")
        
        dialog_class = self._dialogs.get(dialog_type)
        if not dialog_class:
            self.logger.error(f"Неизвестный тип диалога: {dialog_type}")
            return None
        
        try:
            dialog = dialog_class(parent)
            result = dialog.show_dialog()
            
            # Вызываем callback если он установлен
            if dialog_type == 'wanted' and self.on_wanted_dialog_result:
                self.on_wanted_dialog_result(result)
            
            self.logger.info(f"Результат диалога {dialog_type}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка показа диалога {dialog_type}: {e}")
            return None
    
    def get_supported_dialog_types(self) -> list:
        """Получение поддерживаемых типов диалогов"""
        return list(self._dialogs.keys())
