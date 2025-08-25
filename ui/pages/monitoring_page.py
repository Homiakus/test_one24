"""
@file: monitoring_page.py
@description: Страница мониторинга системы
@dependencies: PySide6, monitoring, ui.shared
@created: 2024-12-19
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QProgressBar, QGroupBox, QGridLayout, QSplitter, QFrame
)
from PySide6.QtCore import QTimer, Qt, Signal, QThread
from PySide6.QtGui import QFont, QPalette, QColor

from ui.shared.base_classes import BasePage
from ui.shared.mixins import LayoutMixin
from ui.shared.utils import create_styled_button, create_styled_label
from monitoring import MonitoringManager


class MonitoringDataThread(QThread):
    """Поток для обновления данных мониторинга"""
    data_updated = Signal(dict)
    
    def __init__(self, monitoring_manager: MonitoringManager):
        super().__init__()
        self.monitoring_manager = monitoring_manager
        self.running = True
        
    def run(self):
        while self.running:
            try:
                # Получаем данные мониторинга
                summary = self.monitoring_manager.get_comprehensive_summary(hours=24)
                current_status = self.monitoring_manager.get_current_status()
                
                data = {
                    "summary": summary,
                    "current_status": current_status
                }
                
                self.data_updated.emit(data)
                
            except Exception as e:
                print(f"Error updating monitoring data: {e}")
                
            self.msleep(5000)  # Обновляем каждые 5 секунд
            
    def stop(self):
        self.running = False


class MonitoringPage(BasePage, LayoutMixin):
    """Страница мониторинга системы"""
    
    def __init__(self, monitoring_manager: Optional[MonitoringManager] = None):
        super().__init__()
        self.monitoring_manager = monitoring_manager
        self.data_thread: Optional[MonitoringDataThread] = None
        
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Мониторинг системы")
        
        # Главный layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Заголовок
        title_label = create_styled_label("Мониторинг системы", "title")
        main_layout.addWidget(title_label)
        
        # Кнопки управления
        control_layout = QHBoxLayout()
        
        self.start_button = create_styled_button("Запустить мониторинг", "success")
        self.start_button.clicked.connect(self.start_monitoring)
        
        self.stop_button = create_styled_button("Остановить мониторинг", "danger")
        self.stop_button.clicked.connect(self.stop_monitoring)
        
        self.refresh_button = create_styled_button("Обновить данные", "info")
        self.refresh_button.clicked.connect(self.refresh_data)
        
        self.export_button = create_styled_button("Экспорт данных", "warning")
        self.export_button.clicked.connect(self.export_data)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.export_button)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # Статус системы
        self.status_frame = self.create_status_frame()
        main_layout.addWidget(self.status_frame)
        
        # Табы с данными
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Создаем вкладки
        self.create_performance_tab()
        self.create_alerts_tab()
        self.create_health_tab()
        self.create_usage_tab()
        
    def create_status_frame(self) -> QFrame:
        """Создание фрейма статуса системы"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        
        layout = QGridLayout()
        frame.setLayout(layout)
        
        # Заголовок
        title = create_styled_label("Статус системы", "heading")
        layout.addWidget(title, 0, 0, 1, 2)
        
        # Статус мониторинга
        self.monitoring_status_label = QLabel("Мониторинг: Не запущен")
        self.monitoring_status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.monitoring_status_label, 1, 0)
        
        # Статус системы
        self.system_status_label = QLabel("Система: Неизвестно")
        layout.addWidget(self.system_status_label, 1, 1)
        
        # Время работы
        self.uptime_label = QLabel("Время работы: --")
        layout.addWidget(self.uptime_label, 2, 0)
        
        # Активные уведомления
        self.alerts_label = QLabel("Активные уведомления: 0")
        layout.addWidget(self.alerts_label, 2, 1)
        
        return frame
        
    def create_performance_tab(self):
        """Создание вкладки производительности"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Системные метрики
        system_group = QGroupBox("Системные ресурсы")
        system_layout = QGridLayout()
        system_group.setLayout(system_layout)
        
        self.cpu_label = QLabel("CPU: --")
        self.memory_label = QLabel("Память: --")
        self.disk_label = QLabel("Диск: --")
        
        system_layout.addWidget(self.cpu_label, 0, 0)
        system_layout.addWidget(self.memory_label, 0, 1)
        system_layout.addWidget(self.disk_label, 0, 2)
        
        layout.addWidget(system_group)
        
        # Производительность команд
        commands_group = QGroupBox("Производительность команд")
        commands_layout = QVBoxLayout()
        commands_group.setLayout(commands_layout)
        
        self.commands_table = QTableWidget()
        self.commands_table.setColumnCount(4)
        self.commands_table.setHorizontalHeaderLabels([
            "Команда", "Количество", "Среднее время", "Успешность"
        ])
        
        commands_layout.addWidget(self.commands_table)
        layout.addWidget(commands_group)
        
        self.tab_widget.addTab(widget, "Производительность")
        
    def create_alerts_tab(self):
        """Создание вкладки уведомлений"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Сводка уведомлений
        summary_group = QGroupBox("Сводка уведомлений")
        summary_layout = QGridLayout()
        summary_group.setLayout(summary_layout)
        
        self.total_alerts_label = QLabel("Всего: 0")
        self.active_alerts_label = QLabel("Активные: 0")
        self.critical_alerts_label = QLabel("Критические: 0")
        
        summary_layout.addWidget(self.total_alerts_label, 0, 0)
        summary_layout.addWidget(self.active_alerts_label, 0, 1)
        summary_layout.addWidget(self.critical_alerts_label, 0, 2)
        
        layout.addWidget(summary_group)
        
        # Таблица уведомлений
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Время", "Уровень", "Источник", "Сообщение", "Статус"
        ])
        
        layout.addWidget(self.alerts_table)
        
        self.tab_widget.addTab(widget, "Уведомления")
        
    def create_health_tab(self):
        """Создание вкладки состояния системы"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Общее состояние
        health_group = QGroupBox("Состояние системы")
        health_layout = QGridLayout()
        health_group.setLayout(health_layout)
        
        self.overall_health_label = QLabel("Общее состояние: --")
        self.health_uptime_label = QLabel("Время работы: --")
        
        health_layout.addWidget(self.overall_health_label, 0, 0)
        health_layout.addWidget(self.health_uptime_label, 0, 1)
        
        layout.addWidget(health_group)
        
        # Проверки состояния
        checks_group = QGroupBox("Проверки состояния")
        checks_layout = QVBoxLayout()
        checks_group.setLayout(checks_layout)
        
        self.health_table = QTableWidget()
        self.health_table.setColumnCount(4)
        self.health_table.setHorizontalHeaderLabels([
            "Проверка", "Статус", "Сообщение", "Время ответа"
        ])
        
        checks_layout.addWidget(self.health_table)
        layout.addWidget(checks_group)
        
        self.tab_widget.addTab(widget, "Состояние")
        
    def create_usage_tab(self):
        """Создание вкладки использования"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Сводка использования
        usage_group = QGroupBox("Сводка использования")
        usage_layout = QGridLayout()
        usage_group.setLayout(usage_layout)
        
        self.total_events_label = QLabel("Всего событий: 0")
        self.total_sessions_label = QLabel("Сессий: 0")
        self.avg_session_label = QLabel("Средняя сессия: --")
        
        usage_layout.addWidget(self.total_events_label, 0, 0)
        usage_layout.addWidget(self.total_sessions_label, 0, 1)
        usage_layout.addWidget(self.avg_session_label, 0, 2)
        
        layout.addWidget(usage_group)
        
        # Популярные страницы
        pages_group = QGroupBox("Популярные страницы")
        pages_layout = QVBoxLayout()
        pages_group.setLayout(pages_layout)
        
        self.pages_table = QTableWidget()
        self.pages_table.setColumnCount(2)
        self.pages_table.setHorizontalHeaderLabels(["Страница", "Посещений"])
        
        pages_layout.addWidget(self.pages_table)
        layout.addWidget(pages_group)
        
        self.tab_widget.addTab(widget, "Использование")
        
    def setup_timers(self):
        """Настройка таймеров"""
        # Таймер для обновления данных
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(10000)  # Обновляем каждые 10 секунд
        
    def start_monitoring(self):
        """Запуск мониторинга"""
        if self.monitoring_manager:
            self.monitoring_manager.start_monitoring()
            self.monitoring_status_label.setText("Мониторинг: Запущен")
            self.monitoring_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Запускаем поток обновления данных
            self.data_thread = MonitoringDataThread(self.monitoring_manager)
            self.data_thread.data_updated.connect(self.update_data)
            self.data_thread.start()
            
    def stop_monitoring(self):
        """Остановка мониторинга"""
        if self.monitoring_manager:
            self.monitoring_manager.stop_monitoring()
            self.monitoring_status_label.setText("Мониторинг: Остановлен")
            self.monitoring_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Останавливаем поток
            if self.data_thread:
                self.data_thread.stop()
                self.data_thread.wait()
                
    def refresh_data(self):
        """Обновление данных"""
        if self.monitoring_manager:
            try:
                summary = self.monitoring_manager.get_comprehensive_summary(hours=24)
                current_status = self.monitoring_manager.get_current_status()
                self.update_data({"summary": summary, "current_status": current_status})
            except Exception as e:
                print(f"Error refreshing data: {e}")
                
    def update_data(self, data: Dict[str, Any]):
        """Обновление данных в интерфейсе"""
        try:
            summary = data.get("summary", {})
            current_status = data.get("current_status", {})
            
            # Обновляем статус
            self.update_status_frame(current_status)
            
            # Обновляем производительность
            self.update_performance_tab(summary)
            
            # Обновляем уведомления
            self.update_alerts_tab(summary)
            
            # Обновляем состояние
            self.update_health_tab(summary)
            
            # Обновляем использование
            self.update_usage_tab(summary)
            
        except Exception as e:
            print(f"Error updating UI data: {e}")
            
    def update_status_frame(self, current_status: Dict[str, Any]):
        """Обновление фрейма статуса"""
        system_health = current_status.get("system_health", {})
        
        # Статус системы
        status = system_health.get("status", "unknown")
        status_text = f"Система: {status}"
        if status == "healthy":
            self.system_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status == "warning":
            self.system_status_label.setStyleSheet("color: orange; font-weight: bold;")
        elif status == "critical":
            self.system_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.system_status_label.setStyleSheet("color: gray; font-weight: bold;")
        self.system_status_label.setText(status_text)
        
        # Время работы
        uptime_seconds = system_health.get("uptime", 0)
        uptime = timedelta(seconds=uptime_seconds)
        self.uptime_label.setText(f"Время работы: {str(uptime).split('.')[0]}")
        
        # Уведомления
        active_alerts = current_status.get("active_alerts", 0)
        critical_alerts = current_status.get("critical_alerts", 0)
        self.alerts_label.setText(f"Активные уведомления: {active_alerts}")
        
    def update_performance_tab(self, summary: Dict[str, Any]):
        """Обновление вкладки производительности"""
        performance = summary.get("performance", {})
        
        # Системные метрики
        cpu = performance.get("cpu", {})
        memory = performance.get("memory", {})
        
        if cpu:
            avg_cpu = cpu.get("avg", 0)
            if avg_cpu is not None:
                self.cpu_label.setText(f"CPU: {avg_cpu:.1f}%")
            else:
                self.cpu_label.setText("CPU: N/A")
            
        if memory:
            avg_memory = memory.get("avg_mb", 0)
            if avg_memory is not None:
                self.memory_label.setText(f"Память: {avg_memory:.1f} MB")
            else:
                self.memory_label.setText("Память: N/A")
            
        # Производительность команд
        command_performance = summary.get("command_performance", {})
        commands = command_performance.get("commands", {})
        
        self.commands_table.setRowCount(len(commands))
        for i, (command, stats) in enumerate(commands.items()):
            self.commands_table.setItem(i, 0, QTableWidgetItem(command))
            self.commands_table.setItem(i, 1, QTableWidgetItem(str(stats.get("count", 0))))
            
            avg_time = stats.get("avg_time", 0)
            if avg_time is not None:
                self.commands_table.setItem(i, 2, QTableWidgetItem(f"{avg_time:.3f}s"))
            else:
                self.commands_table.setItem(i, 2, QTableWidgetItem("N/A"))
                
            success_rate = stats.get("success_rate", 0)
            if success_rate is not None:
                self.commands_table.setItem(i, 3, QTableWidgetItem(f"{success_rate*100:.1f}%"))
            else:
                self.commands_table.setItem(i, 3, QTableWidgetItem("N/A"))
            
    def update_alerts_tab(self, summary: Dict[str, Any]):
        """Обновление вкладки уведомлений"""
        alerts = summary.get("alerts", {})
        
        # Сводка
        total_alerts = alerts.get("total_alerts", 0)
        active_alerts = alerts.get("active_alerts", 0)
        
        self.total_alerts_label.setText(f"Всего: {total_alerts}")
        self.active_alerts_label.setText(f"Активные: {active_alerts}")
        
        # TODO: Добавить отображение таблицы уведомлений
        
    def update_health_tab(self, summary: Dict[str, Any]):
        """Обновление вкладки состояния"""
        health = summary.get("health", {})
        
        # Общее состояние
        current_status = health.get("current_status", "unknown")
        self.overall_health_label.setText(f"Общее состояние: {current_status}")
        
        # TODO: Добавить отображение проверок состояния
        
    def update_usage_tab(self, summary: Dict[str, Any]):
        """Обновление вкладки использования"""
        usage = summary.get("usage", {})
        
        # Сводка
        total_events = usage.get("total_events", 0)
        sessions = usage.get("sessions", {})
        total_sessions = sessions.get("total", 0)
        avg_duration = sessions.get("avg_duration_minutes", 0)
        
        self.total_events_label.setText(f"Всего событий: {total_events}")
        self.total_sessions_label.setText(f"Сессий: {total_sessions}")
        
        if avg_duration is not None:
            self.avg_session_label.setText(f"Средняя сессия: {avg_duration:.1f} мин")
        else:
            self.avg_session_label.setText("Средняя сессия: N/A")
        
        # Популярные страницы
        popular_pages = usage.get("popular_pages", {})
        
        self.pages_table.setRowCount(len(popular_pages))
        for i, (page, visits) in enumerate(popular_pages.items()):
            self.pages_table.setItem(i, 0, QTableWidgetItem(page))
            self.pages_table.setItem(i, 1, QTableWidgetItem(str(visits)))
            
    def export_data(self):
        """Экспорт данных"""
        if self.monitoring_manager:
            try:
                self.monitoring_manager.export_all_data()
                # TODO: Показать уведомление об успешном экспорте
            except Exception as e:
                print(f"Error exporting data: {e}")
                
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.data_thread:
            self.data_thread.stop()
            self.data_thread.wait()
        super().closeEvent(event)
