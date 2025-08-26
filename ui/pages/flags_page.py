"""
Страница управления флагами для условного выполнения последовательностей
"""
import logging
from typing import Dict, Optional, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QGroupBox, QScrollArea,
    QFrame, QSpacerItem, QSizePolicy, QLineEdit, QComboBox,
    QSpinBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

from ui.widgets.modern_widgets import ModernCard
from core.sequence_manager import SequenceManager


class FlagsPage(QWidget):
    """Страница управления флагами"""
    
    flag_changed = Signal(str, bool)  # flag_name, new_value
    
    def __init__(self, sequence_manager: SequenceManager):
        super().__init__()
        self.sequence_manager = sequence_manager
        self.logger = logging.getLogger(__name__)
        
        # Таймер для обновления состояния
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_flags_display)
        self.update_timer.start(1000)  # Обновляем каждую секунду
        
        self._setup_ui()
        self._load_flags()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("Управление флагами")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Описание
        description = QLabel(
            "Флаги используются для условного выполнения последовательностей команд. "
            "Измените состояние флагов для управления логикой выполнения."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #888888; font-size: 14px;")
        layout.addWidget(description)
        
        # Область прокрутки для флагов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #707070;
            }
        """)
        
        # Контейнер для флагов
        self.flags_container = QWidget()
        self.flags_layout = QVBoxLayout(self.flags_container)
        self.flags_layout.setContentsMargins(10, 10, 10, 10)
        self.flags_layout.setSpacing(15)
        
        scroll_area.setWidget(self.flags_container)
        layout.addWidget(scroll_area)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.setFixedSize(120, 40)
        refresh_btn.clicked.connect(self._load_flags)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """)
        buttons_layout.addWidget(refresh_btn)
        
        # Кнопка сброса
        reset_btn = QPushButton("🔄 Сброс")
        reset_btn.setFixedSize(120, 40)
        reset_btn.clicked.connect(self._reset_flags)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B4513;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A0522D;
            }
            QPushButton:pressed {
                background-color: #654321;
            }
        """)
        buttons_layout.addWidget(reset_btn)
        
        layout.addLayout(buttons_layout)
        
        # Статус
        self.status_label = QLabel("Готово")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #00AA00; font-size: 12px;")
        layout.addWidget(self.status_label)
    
    def _load_flags(self):
        """Загрузка флагов из sequence_manager"""
        try:
            # Очищаем старые виджеты
            for i in reversed(range(self.flags_layout.count())):
                widget = self.flags_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Получаем все флаги
            flags = self.sequence_manager.get_all_flags()
            
            if not flags:
                # Создаем группу с флагами по умолчанию
                self._create_default_flags_group()
            else:
                # Создаем группы флагов
                self._create_flags_groups(flags)
            
            self.status_label.setText(f"Загружено {len(flags)} флагов")
            self.status_label.setStyleSheet("color: #00AA00; font-size: 12px;")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки флагов: {e}")
            self.status_label.setText(f"Ошибка загрузки: {e}")
            self.status_label.setStyleSheet("color: #AA0000; font-size: 12px;")
    
    def _create_default_flags_group(self):
        """Создание группы с флагами по умолчанию"""
        group = QGroupBox("Флаги по умолчанию")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                color: #E0E0E0;
                border: 2px solid #505050;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(15)
        
        default_flags = {
            'auto_mode': 'Автоматический режим',
            'safety_check': 'Проверка безопасности',
            'emergency_stop': 'Аварийная остановка',
            'maintenance_mode': 'Режим обслуживания',
            'test_mode': 'Тестовый режим'
        }
        
        row = 0
        for flag_name, description in default_flags.items():
            # Чекбокс
            checkbox = QCheckBox(description)
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(
                lambda state, name=flag_name: self._on_flag_changed(name, state == Qt.CheckState.Checked)
            )
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    color: #E0E0E0;
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #606060;
                    border-radius: 4px;
                    background-color: #404040;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border-color: #4CAF50;
                }
                QCheckBox::indicator:checked::after {
                    content: "✓";
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            
            # Статус
            status_label = QLabel("Выключен")
            status_label.setStyleSheet("color: #FF6B6B; font-size: 12px; font-weight: bold;")
            status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            layout.addWidget(checkbox, row, 0)
            layout.addWidget(status_label, row, 1)
            
            # Сохраняем ссылки для обновления
            checkbox.status_label = status_label
            checkbox.flag_name = flag_name
            
            row += 1
        
        self.flags_layout.addWidget(group)
    
    def _create_flags_groups(self, flags: Dict[str, bool]):
        """Создание групп флагов"""
        # Группируем флаги по категориям
        categories = {
            'Системные флаги': ['auto_mode', 'safety_check', 'emergency_stop'],
            'Режимы работы': ['maintenance_mode', 'test_mode', 'debug_mode'],
            'Пользовательские флаги': []
        }
        
        # Распределяем флаги по категориям
        for flag_name in flags.keys():
            categorized = False
            for category_flags in categories.values():
                if flag_name in category_flags:
                    categorized = True
                    break
            
            if not categorized:
                categories['Пользовательские флаги'].append(flag_name)
        
        # Создаем группы
        for category_name, category_flags in categories.items():
            if not category_flags:
                continue
                
            group = QGroupBox(category_name)
            group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 16px;
                    color: #E0E0E0;
                    border: 2px solid #505050;
                    border-radius: 10px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
            
            layout = QGridLayout(group)
            layout.setSpacing(15)
            
            row = 0
            for flag_name in category_flags:
                if flag_name not in flags:
                    continue
                
                value = flags[flag_name]
                
                # Чекбокс
                checkbox = QCheckBox(flag_name.replace('_', ' ').title())
                checkbox.setChecked(value)
                checkbox.stateChanged.connect(
                    lambda state, name=flag_name: self._on_flag_changed(name, state == Qt.CheckState.Checked)
                )
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font-size: 14px;
                        color: #E0E0E0;
                        spacing: 10px;
                    }
                    QCheckBox::indicator {
                        width: 20px;
                        height: 20px;
                        border: 2px solid #606060;
                        border-radius: 4px;
                        background-color: #404040;
                    }
                    QCheckBox::indicator:checked {
                        background-color: #4CAF50;
                        border-color: #4CAF50;
                    }
                    QCheckBox::indicator:checked::after {
                        content: "✓";
                        color: white;
                        font-weight: bold;
                        font-size: 14px;
                    }
                """)
                
                # Статус
                status_label = QLabel("Включен" if value else "Выключен")
                status_label.setStyleSheet(
                    f"color: {'#4CAF50' if value else '#FF6B6B'}; "
                    f"font-size: 12px; font-weight: bold;"
                )
                status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                layout.addWidget(checkbox, row, 0)
                layout.addWidget(status_label, row, 1)
                
                # Сохраняем ссылки для обновления
                checkbox.status_label = status_label
                checkbox.flag_name = flag_name
                
                row += 1
            
            self.flags_layout.addWidget(group)
    
    def _on_flag_changed(self, flag_name: str, value: bool):
        """Обработка изменения флага"""
        try:
            self.sequence_manager.set_flag(flag_name, value)
            self.flag_changed.emit(flag_name, value)
            
            self.status_label.setText(f"Флаг '{flag_name}' установлен в {value}")
            self.status_label.setStyleSheet("color: #00AA00; font-size: 12px;")
            
            self.logger.info(f"Флаг '{flag_name}' изменен на {value}")
            
        except Exception as e:
            self.logger.error(f"Ошибка изменения флага '{flag_name}': {e}")
            self.status_label.setText(f"Ошибка изменения флага: {e}")
            self.status_label.setStyleSheet("color: #AA0000; font-size: 12px;")
    
    def _update_flags_display(self):
        """Обновление отображения флагов"""
        try:
            current_flags = self.sequence_manager.get_all_flags()
            
            # Обновляем статусы чекбоксов
            for i in range(self.flags_layout.count()):
                item = self.flags_layout.itemAt(i)
                if item and item.widget():
                    group = item.widget()
                    if isinstance(group, QGroupBox):
                        layout = group.layout()
                        if layout:
                            for j in range(layout.count()):
                                item_widget = layout.itemAt(j).widget()
                                if isinstance(item_widget, QCheckBox) and hasattr(item_widget, 'flag_name'):
                                    flag_name = item_widget.flag_name
                                    if flag_name in current_flags:
                                        value = current_flags[flag_name]
                                        if item_widget.isChecked() != value:
                                            item_widget.setChecked(value)
                                        
                                        # Обновляем статус
                                        if hasattr(item_widget, 'status_label'):
                                            status_label = item_widget.status_label
                                            status_label.setText("Включен" if value else "Выключен")
                                            status_label.setStyleSheet(
                                                f"color: {'#4CAF50' if value else '#FF6B6B'}; "
                                                f"font-size: 12px; font-weight: bold;"
                                            )
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления отображения флагов: {e}")
    
    def _reset_flags(self):
        """Сброс всех флагов в значения по умолчанию"""
        try:
            default_flags = {
                'auto_mode': True,
                'safety_check': True,
                'emergency_stop': False,
                'maintenance_mode': False,
                'test_mode': False
            }
            
            for flag_name, default_value in default_flags.items():
                self.sequence_manager.set_flag(flag_name, default_value)
            
            self._load_flags()
            
            self.status_label.setText("Флаги сброшены к значениям по умолчанию")
            self.status_label.setStyleSheet("color: #00AA00; font-size: 12px;")
            
            self.logger.info("Флаги сброшены к значениям по умолчанию")
            
        except Exception as e:
            self.logger.error(f"Ошибка сброса флагов: {e}")
            self.status_label.setText(f"Ошибка сброса: {e}")
            self.status_label.setStyleSheet("color: #AA0000; font-size: 12px;")
    
    def closeEvent(self, event):
        """Обработка закрытия страницы"""
        self.update_timer.stop()
        super().closeEvent(event)