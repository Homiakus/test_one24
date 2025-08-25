#!/usr/bin/env python3
"""
Страница управления сигналами UART
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QTextEdit,
    QSplitter, QFrame, QMessageBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from core.signal_types import SignalType
from core.signal_manager import SignalManager
from core.flag_manager import FlagManager
from config.config_loader import ConfigLoader


class SignalConfigWidget(QWidget):
    """Виджет для настройки конфигурации сигналов"""
    
    signal_config_changed = Signal()
    
    def __init__(self, config_loader: ConfigLoader, parent=None):
        super().__init__(parent)
        self.config_loader = config_loader
        self._setup_ui()
        self._load_current_config()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Настройка сигналов UART")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Форма добавления сигнала
        form_group = QGroupBox("Добавить новый сигнал")
        form_layout = QGridLayout(form_group)
        
        # Поля ввода
        self.signal_name_edit = QLineEdit()
        self.signal_name_edit.setPlaceholderText("Имя сигнала (например: TEMP)")
        form_layout.addWidget(QLabel("Имя сигнала:"), 0, 0)
        form_layout.addWidget(self.signal_name_edit, 0, 1)
        
        self.variable_name_edit = QLineEdit()
        self.variable_name_edit.setPlaceholderText("Имя переменной (например: temperature)")
        form_layout.addWidget(QLabel("Переменная:"), 1, 0)
        form_layout.addWidget(self.variable_name_edit, 1, 1)
        
        self.signal_type_combo = QComboBox()
        self.signal_type_combo.addItems([t.value for t in SignalType])
        form_layout.addWidget(QLabel("Тип данных:"), 2, 0)
        form_layout.addWidget(self.signal_type_combo, 2, 1)
        
        # Кнопки
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить сигнал")
        self.add_button.clicked.connect(self._add_signal)
        button_layout.addWidget(self.add_button)
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self._clear_form)
        button_layout.addWidget(self.clear_button)
        
        form_layout.addLayout(button_layout, 3, 0, 1, 2)
        layout.addWidget(form_group)
        
        # Таблица текущих сигналов
        table_group = QGroupBox("Текущие сигналы")
        table_layout = QVBoxLayout(table_group)
        
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(4)
        self.signals_table.setHorizontalHeaderLabels([
            "Сигнал", "Переменная", "Тип", "Действия"
        ])
        self.signals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.signals_table)
        
        # Кнопки управления таблицей
        table_buttons = QHBoxLayout()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self._load_current_config)
        table_buttons.addWidget(self.refresh_button)
        
        self.save_button = QPushButton("Сохранить конфигурацию")
        self.save_button.clicked.connect(self._save_config)
        table_buttons.addWidget(self.save_button)
        
        table_layout.addLayout(table_buttons)
        layout.addWidget(table_group)
    
    def _load_current_config(self):
        """Загрузка текущей конфигурации сигналов"""
        try:
            signal_mappings = self.config_loader.get_signal_mappings()
            self.signals_table.setRowCount(len(signal_mappings))
            
            for row, (signal_name, mapping) in enumerate(signal_mappings.items()):
                # Сигнал
                signal_item = QTableWidgetItem(signal_name)
                signal_item.setFlags(signal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signals_table.setItem(row, 0, signal_item)
                
                # Переменная
                var_item = QTableWidgetItem(mapping.variable_name)
                var_item.setFlags(var_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signals_table.setItem(row, 1, var_item)
                
                # Тип
                type_item = QTableWidgetItem(mapping.signal_type.value)
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signals_table.setItem(row, 2, type_item)
                
                # Кнопка удаления
                delete_button = QPushButton("Удалить")
                delete_button.clicked.connect(lambda checked, name=signal_name: self._delete_signal(name))
                self.signals_table.setCellWidget(row, 3, delete_button)
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить конфигурацию: {e}")
    
    def _add_signal(self):
        """Добавление нового сигнала"""
        signal_name = self.signal_name_edit.text().strip().upper()
        variable_name = self.variable_name_edit.text().strip()
        signal_type = self.signal_type_combo.currentText()
        
        if not signal_name or not variable_name:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        
        try:
            # Добавляем в конфигурацию
            signal_mappings = self.config_loader.get_signal_mappings()
            signal_mappings[signal_name] = {
                "variable_name": variable_name,
                "signal_type": signal_type
            }
            
            # Обновляем таблицу
            self._load_current_config()
            
            # Очищаем форму
            self._clear_form()
            
            # Уведомляем об изменении
            self.signal_config_changed.emit()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить сигнал: {e}")
    
    def _delete_signal(self, signal_name: str):
        """Удаление сигнала"""
        try:
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Удалить сигнал '{signal_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                signal_mappings = self.config_loader.get_signal_mappings()
                if signal_name in signal_mappings:
                    del signal_mappings[signal_name]
                    self._load_current_config()
                    self.signal_config_changed.emit()
                    
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить сигнал: {e}")
    
    def _clear_form(self):
        """Очистка формы"""
        self.signal_name_edit.clear()
        self.variable_name_edit.clear()
        self.signal_type_combo.setCurrentIndex(0)
    
    def _save_config(self):
        """Сохранение конфигурации"""
        try:
            self.config_loader.save_signal_mappings()
            QMessageBox.information(self, "Успех", "Конфигурация сохранена")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить конфигурацию: {e}")


class SignalMonitorWidget(QWidget):
    """Виджет для мониторинга сигналов в реальном времени"""
    
    def __init__(self, signal_manager: SignalManager, flag_manager: FlagManager, parent=None):
        super().__init__(parent)
        self.signal_manager = signal_manager
        self.flag_manager = flag_manager
        self._setup_ui()
        self._setup_timer()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("Мониторинг сигналов UART")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Статистика
        stats_group = QGroupBox("Статистика")
        stats_layout = QGridLayout(stats_group)
        
        self.total_signals_label = QLabel("0")
        self.processed_signals_label = QLabel("0")
        self.errors_label = QLabel("0")
        self.last_signal_label = QLabel("Нет")
        
        stats_layout.addWidget(QLabel("Всего сигналов:"), 0, 0)
        stats_layout.addWidget(self.total_signals_label, 0, 1)
        stats_layout.addWidget(QLabel("Обработано:"), 1, 0)
        stats_layout.addWidget(self.processed_signals_label, 1, 1)
        stats_layout.addWidget(QLabel("Ошибок:"), 2, 0)
        stats_layout.addWidget(self.errors_label, 2, 1)
        stats_layout.addWidget(QLabel("Последний сигнал:"), 3, 0)
        stats_layout.addWidget(self.last_signal_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # Таблица значений сигналов
        values_group = QGroupBox("Текущие значения")
        values_layout = QVBoxLayout(values_group)
        
        self.values_table = QTableWidget()
        self.values_table.setColumnCount(4)
        self.values_table.setHorizontalHeaderLabels([
            "Сигнал", "Переменная", "Значение", "Тип"
        ])
        self.values_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        values_layout.addWidget(self.values_table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.clicked.connect(self._update_values)
        buttons_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("Очистить")
        self.clear_button.clicked.connect(self._clear_values)
        buttons_layout.addWidget(self.clear_button)
        
        values_layout.addLayout(buttons_layout)
        layout.addWidget(values_group)
        
        # Лог сигналов
        log_group = QGroupBox("Лог сигналов")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
    
    def _setup_timer(self):
        """Настройка таймера для обновления данных"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_data)
        self.update_timer.start(1000)  # Обновление каждую секунду
    
    def _update_data(self):
        """Обновление данных"""
        self._update_statistics()
        self._update_values()
    
    def _update_statistics(self):
        """Обновление статистики"""
        try:
            stats = self.signal_manager.get_statistics()
            
            self.total_signals_label.setText(str(stats.get('total_signals', 0)))
            self.processed_signals_label.setText(str(stats.get('processed_signals', 0)))
            self.errors_label.setText(str(stats.get('errors', 0)))
            
            last_signal = stats.get('last_signal', 'Нет')
            self.last_signal_label.setText(str(last_signal))
            
        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
    
    def _update_values(self):
        """Обновление значений сигналов"""
        try:
            signal_mappings = self.signal_manager.get_signal_mappings()
            
            self.values_table.setRowCount(len(signal_mappings))
            
            for row, (signal_name, mapping) in enumerate(signal_mappings.items()):
                # Сигнал
                signal_item = QTableWidgetItem(signal_name)
                signal_item.setFlags(signal_item.flags() & ~Qt.ItemIsEditable)
                self.values_table.setItem(row, 0, signal_item)
                
                # Переменная
                var_item = QTableWidgetItem(mapping.variable_name)
                var_item.setFlags(var_item.flags() & ~Qt.ItemIsEditable)
                self.values_table.setItem(row, 1, var_item)
                
                # Значение
                value = self.flag_manager.get_flag(mapping.variable_name)
                value_item = QTableWidgetItem(str(value) if value is not None else "Не установлено")
                value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
                
                # Цветовое выделение
                if value is not None:
                    value_item.setBackground(QColor(200, 255, 200))  # Зеленый
                else:
                    value_item.setBackground(QColor(255, 200, 200))  # Красный
                
                self.values_table.setItem(row, 2, value_item)
                
                # Тип
                type_item = QTableWidgetItem(mapping.signal_type.value)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.values_table.setItem(row, 3, type_item)
                
        except Exception as e:
            print(f"Ошибка обновления значений: {e}")
    
    def _clear_values(self):
        """Очистка значений"""
        try:
            signal_mappings = self.signal_manager.get_signal_mappings()
            for mapping in signal_mappings.values():
                self.flag_manager.set_flag(mapping.variable_name, None)
            
            self._update_values()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось очистить значения: {e}")
    
    def add_log_entry(self, signal_name: str, variable_name: str, value: str):
        """Добавление записи в лог"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {signal_name} -> {variable_name} = {value}"
        
        self.log_text.append(log_entry)
        
        # Ограничиваем количество строк в логе
        lines = self.log_text.toPlainText().split('\n')
        if len(lines) > 100:
            self.log_text.setPlainText('\n'.join(lines[-100:]))


class SignalsPage(QWidget):
    """Страница управления сигналами UART"""
    
    def __init__(self, signal_manager: SignalManager, flag_manager: FlagManager, 
                 config_loader: ConfigLoader, parent=None):
        super().__init__(parent)
        self.signal_manager = signal_manager
        self.flag_manager = flag_manager
        self.config_loader = config_loader
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Создаем вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка конфигурации
        self.config_widget = SignalConfigWidget(self.config_loader)
        self.tab_widget.addTab(self.config_widget, "Конфигурация")
        
        # Вкладка мониторинга
        self.monitor_widget = SignalMonitorWidget(self.signal_manager, self.flag_manager)
        self.tab_widget.addTab(self.monitor_widget, "Мониторинг")
        
        layout.addWidget(self.tab_widget)
    
    def _setup_connections(self):
        """Настройка соединений"""
        self.config_widget.signal_config_changed.connect(self._on_config_changed)
    
    def _on_config_changed(self):
        """Обработка изменения конфигурации"""
        try:
            # Перезагружаем сигналы в менеджере
            signal_mappings = self.config_loader.get_signal_mappings()
            self.signal_manager.register_signals(signal_mappings)
            
            # Обновляем отображение
            self.monitor_widget._update_values()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить конфигурацию: {e}")
    
    def on_signal_processed(self, signal_name: str, variable_name: str, value: str):
        """Обработка обработанного сигнала"""
        self.monitor_widget.add_log_entry(signal_name, variable_name, value)
        self.monitor_widget._update_values()
