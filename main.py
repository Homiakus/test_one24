import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime

import git
import serial
import serial.tools.list_ports
import tomli
from PySide6.QtCore import (
    QMetaObject,
    QMutex,
    QThread,
    QTimer,
    QWaitCondition,
    Qt,
    Signal,
    Slot,
    QObject,
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

# Настройка логирования
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')

# Создаем директорию для логов, если она не существует
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Настраиваем формат логов и запись в файл
try:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filemode='a'  # Режим добавления, а не перезаписи
    )
    # Добавляем вывод логов в консоль для отладки
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    logging.info("Логирование инициализировано успешно")
except Exception as e:
    print(f"Ошибка при настройке логирования: {str(e)}")

# Современная темная тема в стиле PyDracula
PYDRACULA_DARK = """
/* PyDracula Dark Theme */
QMainWindow {
    background-color: #1e1d23;
    color: #fff;
}

QWidget {
    background-color: transparent;
    color: #fff;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

/* Боковая панель */
#sidebar {
    background-color: #16151a;
    border-right: 3px solid #343b48;
}

#sidebar QPushButton {
    background-color: transparent;
    border: none;
    padding: 15px 20px;
    text-align: left;
    color: #8a95aa;
    font-weight: 500;
    font-size: 11pt;
    border-radius: 8px;
    margin: 2px 5px;
}

#sidebar QPushButton:hover {
    background-color: #21202e;
    color: #dce1ec;
}

#sidebar QPushButton:checked {
    background-color: #568af2;
    color: #fff;
    font-weight: 600;
}

/* Кнопки */
QPushButton {
    background-color: #568af2;
    color: #fff;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    font-weight: 500;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #6c98f3;
}

QPushButton:pressed {
    background-color: #4a7ce8;
}

QPushButton:disabled {
    background-color: #44475a;
    color: #6272a4;
}

/* Специальные кнопки */
.success-btn {
    background-color: #50fa7b;
    color: #282a36;
}

.success-btn:hover {
    background-color: #5af78e;
}

.warning-btn {
    background-color: #ffb86c;
    color: #282a36;
}

.warning-btn:hover {
    background-color: #ffc382;
}

.danger-btn {
    background-color: #ff5555;
    color: #fff;
}

.danger-btn:hover {
    background-color: #ff6b6b;
}

/* Группы */
QGroupBox {
    background-color: #21202e;
    border: 2px solid #343b48;
    border-radius: 8px;
    margin-top: 1ex;
    color: #dce1ec;
    font-weight: 600;
    padding-top: 15px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 10px;
    color: #568af2;
}

/* Поля ввода */
QLineEdit, QComboBox, QSpinBox {
    background-color: #343b48;
    border: 2px solid #44475a;
    border-radius: 6px;
    padding: 8px;
    color: #fff;
    font-size: 10pt;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #568af2;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #44475a;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzU2OGFmMiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
}

/* Терминал */
QTextEdit {
    background-color: #16151a;
    border: 2px solid #343b48;
    border-radius: 8px;
    padding: 10px;
    color: #dce1ec;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 9pt;
    line-height: 1.4;
}

/* Прогресс-бар */
QProgressBar {
    background-color: #343b48;
    border: 2px solid #44475a;
    border-radius: 8px;
    text-align: center;
    color: #fff;
    font-weight: 500;
}

QProgressBar::chunk {
    background-color: #568af2;
    border-radius: 6px;
}

/* Таблица */
QTableWidget {
    background-color: #21202e;
    border: 2px solid #343b48;
    border-radius: 8px;
    gridline-color: #44475a;
    color: #dce1ec;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #44475a;
}

QTableWidget::item:selected {
    background-color: #568af2;
}

/* Чекбоксы */
QCheckBox {
    spacing: 8px;
    color: #dce1ec;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background-color: #343b48;
    border: 2px solid #44475a;
    border-radius: 4px;
}

QCheckBox::indicator:checked {
    background-color: #568af2;
    border-color: #568af2;
}

QCheckBox::indicator:checked:hover {
    background-color: #6c98f3;
}

/* Скроллбары */
QScrollBar:vertical {
    background-color: #21202e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #568af2;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6c98f3;
}

QScrollBar:horizontal {
    background-color: #21202e;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #568af2;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6c98f3;
}

/* Меню */
QMenuBar {
    background-color: #16151a;
    color: #dce1ec;
    padding: 4px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 12px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background-color: #568af2;
}

QMenu {
    background-color: #21202e;
    border: 2px solid #343b48;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    padding: 8px 12px;
    border-radius: 6px;
    color: #dce1ec;
}

QMenu::item:selected {
    background-color: #568af2;
}

/* Статусная строка */
QStatusBar {
    background-color: #16151a;
    color: #8a95aa;
    border-top: 1px solid #343b48;
    padding: 4px;
}

/* Сплиттер */
QSplitter::handle {
    background-color: #343b48;
    width: 3px;
    height: 3px;
}

QSplitter::handle:hover {
    background-color: #568af2;
}

/* Диалоги */
QDialog {
    background-color: #1e1d23;
    border: 2px solid #343b48;
    border-radius: 12px;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
    padding: 10px 20px;
}
"""

# Путь к файлу с настройками
SETTINGS_FILE = 'serial_settings.json'
# Настройки обновления по умолчанию
DEFAULT_UPDATE_SETTINGS = {
    'enable_auto_update': True,
    'repository_url': 'https://github.com/yourusername/yourrepository.git',
    'update_check_interval': 3600,  # в секундах (1 час)
    'auto_connect': True,
    'platformio_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arduino'),  # Путь к проекту Arduino/PlatformIO
    'upload_port': '',  # Порт для загрузки прошивки
    'theme': 'dark'  # Тема по умолчанию
}

class SerialThread(QThread):
    """Поток для чтения данных с Serial порта"""
    data_received = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True

    def run(self):
        while self.running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data:
                        self.data_received.emit(data)
            except Exception as e:
                self.data_received.emit(f"Ошибка чтения: {str(e)}")
                break
            self.msleep(50)

    def stop(self):
        self.running = False
        self.wait()


class CommandSequenceThread(QThread):
    """Поток для выполнения последовательности команд с ожиданием ответов"""
    progress_updated = Signal(int, int)  # (текущий_шаг, всего_шагов)
    command_sent = Signal(str)
    response_received = Signal(str)
    sequence_finished = Signal(bool, str)  # (успешно, сообщение)

    def __init__(self, serial_port, commands, parent=None):
        super().__init__(parent)
        self.serial_port = serial_port
        self.commands = commands
        self.running = True
        self.responses = []
        self.lock = threading.Lock()

    def run(self):
        if not self.serial_port or not self.serial_port.is_open:
            self.sequence_finished.emit(False, "Устройство не подключено")
            return

        total_steps = len(self.commands)
        current_step = 0

        for i, command in enumerate(self.commands):
            if not self.running:
                self.sequence_finished.emit(False, "Выполнение прервано пользователем")
                return

            # Обновляем прогресс
            current_step = i + 1
            self.progress_updated.emit(current_step, total_steps)

            # Проверяем, является ли команда специальной (wait)
            if command.lower().startswith("wait"):
                try:
                    # Извлекаем время ожидания в секундах
                    wait_time = float(command.split()[1])
                    self.command_sent.emit(f"Ожидание {wait_time} секунд...")
                    # Реализуем прерываемое ожидание
                    start_time = time.time()
                    while time.time() - start_time < wait_time:
                        if not self.running:
                            self.sequence_finished.emit(False, "Выполнение прервано пользователем")
                            return
                        time.sleep(0.1)  # Проверяем флаг прерывания каждые 100 мс
                    continue
                except Exception as e:
                    self.sequence_finished.emit(False, f"Ошибка в команде wait: {str(e)}")
                    return

            # Отправляем команду
            try:
                # Очищаем буфер ответов перед отправкой новой команды
                self.responses.clear()

                # Отправляем команду
                full_command = command + '\n'
                self.serial_port.write(full_command.encode('utf-8'))
                self.command_sent.emit(command)

                # Ожидаем ответ RECEIVED
                received = False
                completed = False
                start_time = time.time()
                timeout = 10  # Таймаут в секундах

                while (not received or not completed) and time.time() - start_time < timeout:
                    if not self.running:
                        self.sequence_finished.emit(False, "Выполнение прервано пользователем")
                        return

                    with self.lock:
                        for response in self.responses:
                            if "RECEIVED" in response:
                                received = True
                            if "COMPLETED" in response:
                                completed = True
                            if "ERR" in response:
                                self.sequence_finished.emit(False, f"Ошибка выполнения команды: {response}")
                                return

                    if not received or not completed:
                        time.sleep(0.1)  # Проверяем каждые 100 мс

                # Проверяем, были ли получены все необходимые ответы
                if not received:
                    self.sequence_finished.emit(False, f"Таймаут ожидания ответа RECEIVED для команды: {command}")
                    return

                if not completed:
                    self.sequence_finished.emit(False, f"Таймаут ожидания ответа COMPLETED для команды: {command}")
                    return

            except Exception as e:
                self.sequence_finished.emit(False, f"Ошибка при отправке команды: {str(e)}")
                return

        # Все команды успешно выполнены
        self.sequence_finished.emit(True, "Последовательность команд выполнена успешно")

    def add_response(self, response):
        """Добавляет полученный ответ в список ответов"""
        with self.lock:
            self.responses.append(response)

    def stop(self):
        """Остановка выполнения последовательности"""
        self.running = False


class ModernCard(QFrame):
    """Современная карточка для группировки элементов"""
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ModernCard {
                background-color: #21202e;
                border: 2px solid #343b48;
                border-radius: 12px;
                margin: 5px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)
        
        if title:
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #568af2;
                    font-size: 14pt;
                    font-weight: 600;
                    border: none;
                    background: transparent;
                    padding: 0;
                    margin-bottom: 10px;
                }
            """)
            self.layout.addWidget(self.title_label)

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def addLayout(self, layout):
        self.layout.addLayout(layout)


class ModernButton(QPushButton):
    """Современная кнопка с различными стилями"""
    def __init__(self, text="", button_type="primary", icon=None, parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setMinimumHeight(36)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if icon:
            self.setIcon(icon)
        
        self.apply_style()

    def apply_style(self):
        base_style = """
            ModernButton {
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 10pt;
            }
        """
        
        if self.button_type == "primary":
            style = base_style + """
                ModernButton {
                    background-color: #568af2;
                    color: #fff;
                }
                ModernButton:hover {
                    background-color: #6c98f3;
                }
                ModernButton:pressed {
                    background-color: #4a7ce8;
                }
            """
        elif self.button_type == "success":
            style = base_style + """
                ModernButton {
                    background-color: #50fa7b;
                    color: #282a36;
                }
                ModernButton:hover {
                    background-color: #5af78e;
                }
                ModernButton:pressed {
                    background-color: #3df56b;
                }
            """
        elif self.button_type == "danger":
            style = base_style + """
                ModernButton {
                    background-color: #ff5555;
                    color: #fff;
                }
                ModernButton:hover {
                    background-color: #ff6b6b;
                }
                ModernButton:pressed {
                    background-color: #e74c3c;
                }
            """
        elif self.button_type == "warning":
            style = base_style + """
                ModernButton {
                    background-color: #ffb86c;
                    color: #282a36;
                }
                ModernButton:hover {
                    background-color: #ffc382;
                }
                ModernButton:pressed {
                    background-color: #f39c12;
                }
            """
        else:  # secondary
            style = base_style + """
                ModernButton {
                    background-color: #44475a;
                    color: #dce1ec;
                    border: 2px solid #6272a4;
                }
                ModernButton:hover {
                    background-color: #6272a4;
                    color: #fff;
                }
                ModernButton:pressed {
                    background-color: #383a59;
                }
            """
        
        self.setStyleSheet(style)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель управления устройством")
        self.setMinimumSize(1200, 800)
        
        # Инициализация переменных
        self.serial_port = None
        self.serial_thread = None
        self.command_sequence_thread = None
        self.buttons_config = {}
        self.button_groups = {}
        self.sequence_commands = {}
        self.sequences = {}
        self.is_fullscreen = False
        self.current_theme = "dark"
        
        # Загружаем сохраненные настройки
        self.serial_settings = self.load_serial_settings()
        self.update_settings = self.load_update_settings()
        
        # Загрузка конфигурации
        self.load_config()
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Применение темы
        self.apply_theme()
        
        # Переключаемся на главную страницу
        self.switch_page("sequences")
        
        # Автоматическое подключение
        if self.update_settings.get('auto_connect', True):
            QTimer.singleShot(1000, self.auto_connect)
        
        # Запуск в полноэкранном режиме
        self.showFullScreen()
        self.is_fullscreen = True
        
        logging.info("Приложение запущено с PySide6")

    def apply_theme(self):
        """Применение современной темы"""
        theme = self.update_settings.get('theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet(PYDRACULA_DARK)
            self.current_theme = 'dark'
        else:
            self.setStyleSheet(PYDRACULA_DARK)
            self.current_theme = 'dark'
        
        # Обновляем тему для всех виджетов
        self.update()

    def toggle_theme(self):
        """Переключение темы"""
        new_theme = 'dark'
        self.update_settings['theme'] = new_theme
        self.save_update_settings()
        self.apply_theme()

    def load_serial_settings(self):
        """Загрузка сохраненных настроек Serial порта"""
        default_settings = {
            'port': 'COM1',
            'baudrate': 115200,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': 1
        }

        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE) as file:
                    settings = json.load(file)
                return settings
            else:
                return default_settings
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")
            return default_settings

    def save_serial_settings(self):
        """Сохранение текущих настроек Serial порта"""
        try:
            with open(SETTINGS_FILE, 'w') as file:
                json.dump(self.serial_settings, file)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {str(e)}")

    def load_update_settings(self):
        """Загрузка настроек обновления программы"""
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_settings.json')

        try:
            if os.path.exists(settings_path):
                with open(settings_path) as file:
                    settings = json.load(file)

                # Если platformio_path не указан или пустой, используем директорию по умолчанию
                if not settings.get('platformio_path'):
                    settings['platformio_path'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arduino')

                return settings
            else:
                # Создаем файл с настройками по умолчанию
                with open(settings_path, 'w') as file:
                    json.dump(DEFAULT_UPDATE_SETTINGS, file, indent=4)
                return DEFAULT_UPDATE_SETTINGS.copy()
        except Exception as e:
            print(f"Ошибка загрузки настроек обновления: {str(e)}")
            return DEFAULT_UPDATE_SETTINGS.copy()

    def save_update_settings(self):
        """Сохранение настроек обновления программы"""
        settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_settings.json')

        try:
            with open(settings_path, 'w') as file:
                json.dump(self.update_settings, file, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения настроек обновления: {str(e)}")

    def auto_connect(self):
        """Автоматическое подключение к порту из настроек"""
        # Проверка доступности порта
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        port = self.serial_settings.get('port', 'COM1')

        if port in available_ports:
            self.connect_serial()
            self.statusBar().showMessage(f"Автоподключение к порту {port}", 3000)
        else:
            self.statusBar().showMessage(f"Не удалось автоматически подключиться: порт {port} недоступен", 5000)

    def load_config(self):
        """Загрузка конфигурации из TOML файла с парсингом разделов по комментариям"""
        try:
            # Путь к файлу конфигурации
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.toml')

            if not os.path.exists(config_path):
                QMessageBox.warning(
                    self,
                    "Файл конфигурации не найден",
                    f"Файл конфигурации не найден: {config_path}\nБудет использована базовая конфигурация."
                )
                self.create_default_config(config_path)

            # Загружаем конфигурацию
            with open(config_path, 'rb') as file:
                config = tomli.load(file)

            # Парсим разделы из исходного файла по комментариям
            self.button_groups = self.parse_config_sections(config_path)

            # Загружаем кнопки команд
            self.buttons_config = config.get('buttons', {})
            
            # Загружаем последовательности
            self.sequences = config.get('sequences', {})
            
            # Загружаем настройки serial по умолчанию
            serial_default = config.get('serial_default', {})
            if serial_default:
                # Обновляем настройки serial, если они не установлены
                for key, value in serial_default.items():
                    if key not in self.serial_settings:
                        self.serial_settings[key] = value
            
            logging.info(f"Конфигурация загружена: {len(self.buttons_config)} команд, {len(self.sequences)} последовательностей, {len(self.button_groups)} разделов")

        except Exception as e:
            error_msg = f"Ошибка загрузки конфигурации: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(
                self,
                "Ошибка загрузки конфигурации",
                error_msg
            )
            # Устанавливаем пустые значения по умолчанию
            self.buttons_config = {}
            self.sequences = {}
            self.button_groups = {"Основные команды": []}

    def parse_config_sections(self, config_path):
        """Парсинг разделов из config.toml по комментариям"""
        sections = {}
        current_section = "Основные команды"
        sections[current_section] = []
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            in_buttons_section = False
            
            for line in lines:
                line = line.strip()
                
                # Проверяем, находимся ли в секции [buttons]
                if line == '[buttons]':
                    in_buttons_section = True
                    continue
                elif line.startswith('[') and line != '[buttons]':
                    in_buttons_section = False
                    continue
                
                if not in_buttons_section:
                    continue
                
                # Парсим комментарии как названия разделов
                if line.startswith('#') and line.strip() != '#':
                    section_name = line[1:].strip()
                    if section_name:
                        current_section = section_name
                        if current_section not in sections:
                            sections[current_section] = []
                
                # Парсим команды (строки с кавычками и знаком =)
                elif '"' in line and '=' in line and not line.startswith('#'):
                    try:
                        # Извлекаем название команды из кавычек
                        start_quote = line.find('"')
                        end_quote = line.find('"', start_quote + 1)
                        if start_quote != -1 and end_quote != -1:
                            command_name = line[start_quote + 1:end_quote]
                            if command_name:
                                sections[current_section].append(command_name)
                    except Exception as e:
                        logging.warning(f"Ошибка парсинга строки: {line}, {str(e)}")
            
            # Удаляем пустые разделы
            sections = {k: v for k, v in sections.items() if v}
            
            if not sections:
                sections = {"Основные команды": list(self.buttons_config.keys()) if hasattr(self, 'buttons_config') else []}
            
            logging.info(f"Найдено разделов: {list(sections.keys())}")
            return sections
            
        except Exception as e:
            logging.error(f"Ошибка парсинга разделов: {str(e)}")
            return {"Основные команды": []}

    def create_button_groups(self):
        """Создание групп кнопок по категориям - УСТАРЕЛ, заменен на parse_config_sections"""
        # Этот метод больше не используется, группировка происходит в parse_config_sections
        return self.button_groups if hasattr(self, 'button_groups') else {"Основные команды": list(self.buttons_config.keys())}

    def create_default_config(self, config_path):
        """Создание конфигурации по умолчанию"""
        default_config = """[buttons]
"Тест" = "test"

[sequences]
test = ["test"]

[serial_default]
port = "COM1"
baudrate = 115200
"""
        try:
            with open(config_path, 'w', encoding='utf-8') as file:
                file.write(default_config)
        except Exception as e:
            logging.error(f"Ошибка создания конфигурации по умолчанию: {str(e)}")

    def setup_ui(self):
        """Настройка современного пользовательского интерфейса"""
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной горизонтальный layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Создаем боковую панель
        self.setup_sidebar()
        
        # Создаем основную область контента
        self.setup_content_area()
        
        # Добавляем в основной layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)
        
        # Создаем меню и статусную строку
        self.create_menu()
        self.statusBar().showMessage("Готов к работе")

    def setup_sidebar(self):
        """Настройка современной боковой панели"""
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("""
            #sidebar {
                background-color: #16151a;
                border-right: 3px solid #343b48;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(5)
        
        # Логотип и заголовок
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 20)
        
        title_label = QLabel("Панель управления")
        title_label.setStyleSheet("""
            QLabel {
                color: #dce1ec;
                font-size: 16pt;
                font-weight: 700;
                margin-bottom: 5px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Система контроля")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #8a95aa;
                font-size: 10pt;
                font-weight: 400;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        sidebar_layout.addWidget(header_widget)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #343b48; height: 1px; margin: 0 20px;")
        sidebar_layout.addWidget(separator)
        
        # Кнопки навигации
        self.nav_buttons = {}
        nav_data = [
            ("sequences", "🏠 Главное меню", True),
            ("commands", "⚡ Команды", False),
            ("settings", "⚙️ Настройки", False),
            ("firmware", "🔧 Прошивка", False),
        ]
        
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)
        
        for key, text, checked in nav_data:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.setObjectName("nav_button")
            btn.setStyleSheet("""
                #nav_button {
                    background-color: transparent;
                    border: none;
                    padding: 15px 20px;
                    text-align: left;
                    color: #8a95aa;
                    font-weight: 500;
                    font-size: 11pt;
                    border-radius: 8px;
                    margin: 2px 5px;
                }
                #nav_button:hover {
                    background-color: #21202e;
                    color: #dce1ec;
                }
                #nav_button:checked {
                    background-color: #568af2;
                    color: #fff;
                    font-weight: 600;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self.switch_page(k))
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)
        
        sidebar_layout.addWidget(nav_widget)
        sidebar_layout.addStretch()
        
        # Информация о подключении
        self.connection_card = ModernCard()
        connection_layout = QVBoxLayout()
        
        self.connection_status = QLabel("● Отключено")
        self.connection_status.setStyleSheet("""
            QLabel {
                color: #ff5555;
                font-weight: 600;
                font-size: 11pt;
                padding: 8px;
                background-color: #2d1b1b;
                border-radius: 6px;
                border: 1px solid #ff5555;
            }
        """)
        connection_layout.addWidget(self.connection_status)
        
        self.connection_card.addLayout(connection_layout)
        sidebar_layout.addWidget(self.connection_card)

    def setup_content_area(self):
        """Настройка основной области контента"""
        self.content_area = QStackedWidget()
        
        # Создаем страницы
        self.setup_sequences_page()
        self.setup_commands_page()
        self.setup_settings_page()
        self.setup_firmware_page()  # Новая страница для прошивки

    def setup_sequences_page(self):
        """Настройка страницы последовательностей с терминалом"""
        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Левая часть - последовательности
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("🚀 Автоматические последовательности")
        title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 18pt;
                font-weight: 700;
                margin-bottom: 20px;
            }
        """)
        left_layout.addWidget(title)
        
        # Карточка с последовательностями
        sequences_card = ModernCard("📋 Доступные последовательности")
        sequences_layout = QVBoxLayout()
        
        # Создаем кнопки последовательностей
        self.sequence_buttons = {}
        for seq_name, commands in self.sequences.items():
            btn = ModernButton(f"▶ {seq_name.replace('_', ' ').title()}", "primary")
            btn.clicked.connect(lambda checked, name=seq_name: self.start_sequence(name))
            sequences_layout.addWidget(btn)
            self.sequence_buttons[seq_name] = btn
            
            # Добавляем описание
            desc_label = QLabel(f"Команд: {len(commands)}")
            desc_label.setStyleSheet("color: #8a95aa; font-size: 9pt; margin-bottom: 10px;")
            sequences_layout.addWidget(desc_label)
        
        if not self.sequences:
            no_sequences_label = QLabel("Последовательности не найдены в конфигурации")
            no_sequences_label.setStyleSheet("color: #8a95aa; font-style: italic;")
            sequences_layout.addWidget(no_sequences_label)
        
        # Кнопка остановки
        stop_btn = ModernButton("⏹ Остановить выполнение", "danger")
        stop_btn.clicked.connect(self.stop_sequence)
        sequences_layout.addWidget(stop_btn)
        
        sequences_card.addLayout(sequences_layout)
        left_layout.addWidget(sequences_card)
        left_layout.addStretch()
        
        # Правая часть - терминал
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок терминала
        terminal_title = QLabel("📟 Терминал")
        terminal_title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 14pt;
                font-weight: 600;
                margin-bottom: 10px;
            }
        """)
        right_layout.addWidget(terminal_title)
        
        # Терминал
        self.terminal = QTextEdit()
        self.terminal.setMinimumHeight(400)
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #16151a;
                border: 2px solid #343b48;
                border-radius: 8px;
                padding: 10px;
                color: #dce1ec;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 9pt;
                line-height: 1.4;
            }
        """)
        right_layout.addWidget(self.terminal)
        
        # Поле ввода команды
        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Введите команду...")
        self.command_input.returnPressed.connect(self.send_manual_command)
        
        send_btn = ModernButton("Отправить", "primary")
        send_btn.clicked.connect(self.send_manual_command)
        
        clear_btn = ModernButton("Очистить", "secondary")
        clear_btn.clicked.connect(self.clear_terminal)
        
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(clear_btn)
        right_layout.addLayout(input_layout)
        
        # Добавляем в основной layout
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 1)
        
        # Добавляем в стек
        self.content_area.addWidget(page)

    def setup_commands_page(self):
        """Настройка страницы команд с кнопками из конфигурации и терминалом"""
        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Левая часть - команды
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("⚡ Команды управления")
        title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 18pt;
                font-weight: 700;
                margin-bottom: 20px;
            }
        """)
        left_layout.addWidget(title)
        
        # Создаем прокручиваемую область для команд
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        
        # Создаем карточки для каждой группы команд
        for group_name, commands in self.button_groups.items():
            if not commands:
                continue
                
            group_card = ModernCard(f"📂 {group_name}")
            group_layout = QGridLayout()
            group_layout.setSpacing(10)
            
            # Размещаем кнопки в сетке (2 в строке для экономии места)
            row, col = 0, 0
            for command_name in commands:
                if command_name in self.buttons_config:
                    command = self.buttons_config[command_name]
                    
                    # Определяем тип кнопки по команде
                    if any(keyword in command_name.lower() for keyword in ['zero', 'stop', 'off']):
                        btn_type = "warning"
                    elif any(keyword in command_name.lower() for keyword in ['on', 'включить']):
                        btn_type = "success"
                    elif any(keyword in command_name.lower() for keyword in ['датчик', 'вес', 'состояние']):
                        btn_type = "secondary"
                    else:
                        btn_type = "primary"
                    
                    btn = ModernButton(command_name, btn_type)
                    btn.clicked.connect(lambda checked, cmd=command: self.send_command(cmd))
                    btn.setMinimumHeight(40)
                    
                    group_layout.addWidget(btn, row, col)
                    
                    col += 1
                    if col >= 2:  # 2 кнопки в строке
                        col = 0
                        row += 1
            
            group_card.addLayout(group_layout)
            scroll_layout.addWidget(group_card)
        
        if not self.buttons_config:
            no_commands_label = QLabel("Команды не найдены в конфигурации")
            no_commands_label.setStyleSheet("color: #8a95aa; font-style: italic; text-align: center;")
            scroll_layout.addWidget(no_commands_label)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        left_layout.addWidget(scroll)
        
        # Правая часть - терминал (используем тот же, что на странице последовательностей)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок терминала
        terminal_title = QLabel("📟 Терминал команд")
        terminal_title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 14pt;
                font-weight: 600;
                margin-bottom: 10px;
            }
        """)
        right_layout.addWidget(terminal_title)
        
        # Используем общий терминал или создаем дублированный
        if not hasattr(self, 'terminal'):
            # Если терминал еще не создан, создаем его
            self.terminal = QTextEdit()
            self.terminal.setMinimumHeight(400)
            self.terminal.setReadOnly(True)
            self.terminal.setStyleSheet("""
                QTextEdit {
                    background-color: #16151a;
                    border: 2px solid #343b48;
                    border-radius: 8px;
                    padding: 10px;
                    color: #dce1ec;
                    font-family: "Consolas", "Monaco", monospace;
                    font-size: 9pt;
                    line-height: 1.4;
                }
            """)
        
        # Создаем второй терминал для команд (чтобы не конфликтовать)
        self.commands_terminal = QTextEdit()
        self.commands_terminal.setMinimumHeight(400)
        self.commands_terminal.setReadOnly(True)
        self.commands_terminal.setStyleSheet("""
            QTextEdit {
                background-color: #16151a;
                border: 2px solid #343b48;
                border-radius: 8px;
                padding: 10px;
                color: #dce1ec;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 9pt;
                line-height: 1.4;
            }
        """)
        right_layout.addWidget(self.commands_terminal)
        
        # Поле ввода команды для команд
        input_layout = QHBoxLayout()
        self.commands_input = QLineEdit()
        self.commands_input.setPlaceholderText("Введите команду...")
        self.commands_input.returnPressed.connect(self.send_manual_command_from_commands)
        
        send_btn = ModernButton("Отправить", "primary")
        send_btn.clicked.connect(self.send_manual_command_from_commands)
        
        clear_btn = ModernButton("Очистить", "secondary")
        clear_btn.clicked.connect(self.clear_commands_terminal)
        
        input_layout.addWidget(self.commands_input)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(clear_btn)
        right_layout.addLayout(input_layout)
        
        # Добавляем в основной layout (левая часть чуть больше)
        main_layout.addWidget(left_widget, 3)  # 60% ширины
        main_layout.addWidget(right_widget, 2)  # 40% ширины
        
        # Добавляем в стек
        self.content_area.addWidget(page)

    def setup_settings_page(self):
        """Настройка страницы настроек с портами и параметрами"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("⚙️ Настройки")
        title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 18pt;
                font-weight: 700;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Создаем прокручиваемую область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # Карточка подключения
        connection_card = ModernCard("🔌 Подключение")
        connection_layout = QFormLayout()
        
        # Порт
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.port_combo.setCurrentText(self.serial_settings.get('port', 'COM1'))
        connection_layout.addRow("Порт:", self.port_combo)
        
        # Скорость
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200', '230400', '460800', '921600'])
        self.baud_combo.setCurrentText(str(self.serial_settings.get('baudrate', 115200)))
        connection_layout.addRow("Скорость:", self.baud_combo)
        
        # Кнопки управления подключением
        connection_buttons = QHBoxLayout()
        
        self.connect_btn = ModernButton("🔗 Подключиться", "success")
        self.connect_btn.clicked.connect(self.connect_serial)
        
        self.disconnect_btn = ModernButton("📴 Отключиться", "danger") 
        self.disconnect_btn.clicked.connect(self.disconnect_serial)
        
        refresh_btn = ModernButton("🔄 Обновить порты", "secondary")
        refresh_btn.clicked.connect(self.refresh_ports)
        
        connection_buttons.addWidget(self.connect_btn)
        connection_buttons.addWidget(self.disconnect_btn)
        connection_buttons.addWidget(refresh_btn)
        
        connection_layout.addRow("", connection_buttons)
        connection_card.addLayout(connection_layout)
        scroll_layout.addWidget(connection_card)
        
        # Карточка настроек приложения
        app_card = ModernCard("🎨 Интерфейс")
        app_layout = QFormLayout()
        
        # Автоподключение
        self.auto_connect_check = QCheckBox("Автоматически подключаться при запуске")
        self.auto_connect_check.setChecked(self.update_settings.get('auto_connect', True))
        app_layout.addRow("", self.auto_connect_check)
        
        app_card.addLayout(app_layout)
        scroll_layout.addWidget(app_card)
        
        # Карточка информации
        info_card = ModernCard("ℹ️ Информация")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            f"<b>Версия:</b> 2.0 (PySide6)<br>"
            f"<b>Команд загружено:</b> {len(self.buttons_config)}<br>"
            f"<b>Последовательностей:</b> {len(self.sequences)}<br>"
            f"<b>Файл конфигурации:</b> config.toml"
        )
        info_text.setStyleSheet("color: #dce1ec; line-height: 1.6;")
        info_layout.addWidget(info_text)
        
        info_card.addLayout(info_layout)
        scroll_layout.addWidget(info_card)
        
        # Кнопки действий
        actions_card = ModernCard("🛠️ Действия")
        actions_layout = QHBoxLayout()
        
        save_btn = ModernButton("💾 Сохранить настройки", "success")
        save_btn.clicked.connect(self.save_connection_settings)
        
        reload_btn = ModernButton("🔄 Перезагрузить конфигурацию", "warning")
        reload_btn.clicked.connect(self.reload_config)
        
        about_btn = ModernButton("ℹ️ О программе", "secondary")
        about_btn.clicked.connect(self.show_about)
        
        actions_layout.addWidget(save_btn)
        actions_layout.addWidget(reload_btn)
        actions_layout.addWidget(about_btn)
        
        actions_card.addLayout(actions_layout)
        scroll_layout.addWidget(actions_card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Добавляем в стек
        self.content_area.addWidget(page)

    def setup_firmware_page(self):
        """Настройка страницы работы с прошивкой и Git"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Заголовок
        title = QLabel("🔧 Прошивка и обновления")
        title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 18pt;
                font-weight: 700;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Создаем прокручиваемую область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # Карточка Git
        git_card = ModernCard("📡 Git Repository")
        git_layout = QVBoxLayout()
        
        # Информация о репозитории
        self.repo_info_label = QLabel("Статус репозитория: Проверяется...")
        self.repo_info_label.setStyleSheet("color: #dce1ec; margin-bottom: 10px;")
        git_layout.addWidget(self.repo_info_label)
        
        # Кнопки Git
        git_buttons_layout = QHBoxLayout()
        
        self.check_updates_btn = ModernButton("🔍 Проверить обновления", "primary")
        self.check_updates_btn.clicked.connect(self.check_git_updates)
        
        self.pull_updates_btn = ModernButton("⬇️ Скачать обновления", "success")
        self.pull_updates_btn.clicked.connect(self.pull_git_updates)
        self.pull_updates_btn.setEnabled(False)
        
        self.view_commits_btn = ModernButton("📜 История изменений", "secondary")
        self.view_commits_btn.clicked.connect(self.view_git_commits)
        
        git_buttons_layout.addWidget(self.check_updates_btn)
        git_buttons_layout.addWidget(self.pull_updates_btn)
        git_buttons_layout.addWidget(self.view_commits_btn)
        
        git_layout.addLayout(git_buttons_layout)
        git_card.addLayout(git_layout)
        scroll_layout.addWidget(git_card)
        
        # Карточка PlatformIO
        pio_card = ModernCard("⚡ PlatformIO")
        pio_layout = QVBoxLayout()
        
        # Путь к проекту Arduino
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Путь к проекту:"))
        
        self.arduino_path_edit = QLineEdit()
        self.arduino_path_edit.setText(self.update_settings.get('platformio_path', ''))
        self.arduino_path_edit.setPlaceholderText("Путь к папке с проектом Arduino/PlatformIO")
        
        browse_btn = ModernButton("📁", "secondary")
        browse_btn.clicked.connect(self.browse_arduino_path)
        browse_btn.setMaximumWidth(50)
        
        path_layout.addWidget(self.arduino_path_edit)
        path_layout.addWidget(browse_btn)
        pio_layout.addLayout(path_layout)
        
        # Порт для загрузки
        upload_port_layout = QHBoxLayout()
        upload_port_layout.addWidget(QLabel("Порт загрузки:"))
        
        self.upload_port_combo = QComboBox()
        self.refresh_upload_ports()
        upload_port_layout.addWidget(self.upload_port_combo)
        
        refresh_ports_btn = ModernButton("🔄", "secondary")
        refresh_ports_btn.clicked.connect(self.refresh_upload_ports)
        refresh_ports_btn.setMaximumWidth(50)
        upload_port_layout.addWidget(refresh_ports_btn)
        
        pio_layout.addLayout(upload_port_layout)
        
        # Кнопки PlatformIO
        pio_buttons_layout = QHBoxLayout()
        
        self.compile_btn = ModernButton("🔨 Компилировать", "warning")
        self.compile_btn.clicked.connect(self.compile_firmware)
        
        self.upload_btn = ModernButton("⬆️ Загрузить прошивку", "success")
        self.upload_btn.clicked.connect(self.upload_firmware)
        
        self.compile_upload_btn = ModernButton("🚀 Компилировать и загрузить", "primary")
        self.compile_upload_btn.clicked.connect(self.compile_and_upload_firmware)
        
        pio_buttons_layout.addWidget(self.compile_btn)
        pio_buttons_layout.addWidget(self.upload_btn)
        pio_buttons_layout.addWidget(self.compile_upload_btn)
        
        pio_layout.addLayout(pio_buttons_layout)
        pio_card.addLayout(pio_layout)
        scroll_layout.addWidget(pio_card)
        
        # Карточка вывода
        output_card = ModernCard("📟 Вывод команд")
        output_layout = QVBoxLayout()
        
        self.firmware_output = QTextEdit()
        self.firmware_output.setMinimumHeight(300)
        self.firmware_output.setReadOnly(True)
        self.firmware_output.setStyleSheet("""
            QTextEdit {
                background-color: #16151a;
                border: 2px solid #343b48;
                border-radius: 8px;
                padding: 10px;
                color: #dce1ec;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 9pt;
                line-height: 1.4;
            }
        """)
        output_layout.addWidget(self.firmware_output)
        
        # Кнопка очистки вывода
        clear_output_btn = ModernButton("🧹 Очистить вывод", "secondary")
        clear_output_btn.clicked.connect(lambda: self.firmware_output.clear())
        output_layout.addWidget(clear_output_btn)
        
        output_card.addLayout(output_layout)
        scroll_layout.addWidget(output_card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Добавляем в стек
        self.content_area.addWidget(page)
        
        # Проверяем статус Git при загрузке
        QTimer.singleShot(1000, self.check_git_status)

    def refresh_ports(self):
        """Обновление списка доступных портов"""
        if hasattr(self, 'port_combo'):
            current_port = self.port_combo.currentText()
            self.port_combo.clear()
            
            # Получаем список доступных портов
            ports = [port.device for port in serial.tools.list_ports.comports()]
            if ports:
                self.port_combo.addItems(ports)
                # Восстанавливаем выбранный порт, если он есть в списке
                if current_port in ports:
                    self.port_combo.setCurrentText(current_port)
            else:
                self.port_combo.addItem("Нет доступных портов")

    def set_theme(self, theme_name):
        """Установка темы"""
        self.update_settings['theme'] = theme_name
        self.save_update_settings()
        self.apply_theme()
        
        # Обновляем состояние кнопок
        self.theme_dark_btn.setEnabled(theme_name != 'dark')
        self.theme_light_btn.setEnabled(theme_name != 'dark')
        
        self.add_terminal_message(f"🎨 Тема изменена на: {theme_name}", "info")

    def save_connection_settings(self):
        """Сохранение настроек подключения"""
        if hasattr(self, 'port_combo') and hasattr(self, 'baud_combo'):
            self.serial_settings['port'] = self.port_combo.currentText()
            self.serial_settings['baudrate'] = int(self.baud_combo.currentText())
        
        if hasattr(self, 'auto_connect_check'):
            self.update_settings['auto_connect'] = self.auto_connect_check.isChecked()
        
        self.save_serial_settings()
        self.save_update_settings()
        
        self.add_terminal_message("💾 Настройки сохранены", "info")
        self.statusBar().showMessage("Настройки сохранены", 3000)

    def send_manual_command(self):
        """Отправка команды из поля ввода"""
        if hasattr(self, 'command_input'):
            command = self.command_input.text().strip()
            if command:
                self.send_command(command)
                self.command_input.clear()

    def clear_terminal(self):
        """Очистка терминала"""
        if hasattr(self, 'terminal'):
            self.terminal.clear()
            self.add_terminal_message("🧹 Терминал очищен", "info")

    def send_command(self, command):
        """Отправка команды в Serial порт"""
        if not self.serial_port or not self.serial_port.is_open:
            self.add_terminal_message("❌ Устройство не подключено", "error")
            if hasattr(self, 'commands_terminal'):
                self.add_commands_terminal_message("❌ Устройство не подключено", "error")
            return

        try:
            # Отправляем команду
            full_command = command + '\n'
            self.serial_port.write(full_command.encode('utf-8'))
            
            # Добавляем в терминалы
            self.add_terminal_message(f"➤ {command}", "command")
            if hasattr(self, 'commands_terminal'):
                self.add_commands_terminal_message(f"➤ {command}", "command")
            
            logging.info(f"Отправлена команда: {command}")

        except Exception as e:
            error_msg = f"Ошибка отправки команды: {str(e)}"
            logging.error(error_msg)
            self.add_terminal_message(f"❌ {error_msg}", "error")
            if hasattr(self, 'commands_terminal'):
                self.add_commands_terminal_message(f"❌ {error_msg}", "error")

    def add_terminal_message(self, message, msg_type="info"):
        """Добавление сообщения в терминал"""
        if hasattr(self, 'terminal'):
            # Добавляем временную метку
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Цветовое кодирование по типу сообщения
            if msg_type == "command":
                formatted_msg = f'<span style="color: #6c98f3;">[{timestamp}] {message}</span>'
            elif msg_type == "response":
                formatted_msg = f'<span style="color: #50fa7b;">[{timestamp}] {message}</span>'
            elif msg_type == "error":
                formatted_msg = f'<span style="color: #ff5555;">[{timestamp}] {message}</span>'
            elif msg_type == "warning":
                formatted_msg = f'<span style="color: #ffb86c;">[{timestamp}] {message}</span>'
            else:
                formatted_msg = f'<span style="color: #dce1ec;">[{timestamp}] {message}</span>'
            
            # Добавляем сообщение в терминал
            self.terminal.append(formatted_msg)
            
            # Прокручиваем в конец
            scrollbar = self.terminal.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def disconnect_serial(self):
        """Отключение от Serial порта"""
        try:
            if self.serial_thread:
                self.serial_thread.stop()
                self.serial_thread = None

            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.serial_port = None

            # Обновляем статус
            self.connection_status.setText("● Отключено")
            self.connection_status.setStyleSheet("""
                QLabel {
                    color: #ff5555;
                    font-weight: 600;
                    font-size: 11pt;
                    padding: 8px;
                    background-color: #2d1b1b;
                    border-radius: 6px;
                    border: 1px solid #ff5555;
                }
            """)
            
            self.add_terminal_message("📴 Устройство отключено", "warning")
            self.statusBar().showMessage("Отключено", 3000)

        except Exception as e:
            error_msg = f"Ошибка при отключении: {str(e)}"
            logging.error(error_msg)
            self.add_terminal_message(f"❌ {error_msg}", "error")

    def start_sequence(self, sequence_name):
        """Запуск последовательности команд"""
        if sequence_name not in self.sequences:
            self.add_terminal_message(f"❌ Последовательность '{sequence_name}' не найдена", "error")
            return

        if not self.serial_port or not self.serial_port.is_open:
            self.add_terminal_message("❌ Устройство не подключено", "error")
            return

        # Получаем команды последовательности
        sequence_commands = self.sequences[sequence_name]
        
        # Преобразуем названия команд в actual команды
        actual_commands = []
        for cmd in sequence_commands:
            if cmd in self.buttons_config:
                actual_commands.append(self.buttons_config[cmd])
            else:
                actual_commands.append(cmd)  # Возможно, это уже команда, а не название

        # Запускаем поток выполнения последовательности
        self.command_sequence_thread = CommandSequenceThread(self.serial_port, actual_commands, self)
        self.command_sequence_thread.progress_updated.connect(self.on_sequence_progress)
        self.command_sequence_thread.command_sent.connect(self.on_sequence_command_sent)
        self.command_sequence_thread.sequence_finished.connect(self.on_sequence_finished)
        self.command_sequence_thread.start()

        self.add_terminal_message(f"🚀 Запущена последовательность '{sequence_name}' ({len(actual_commands)} команд)", "info")

    @Slot(int, int)
    def on_sequence_progress(self, current, total):
        """Обновление прогресса выполнения последовательности"""
        self.add_terminal_message(f"⏳ Выполнение: {current}/{total}", "info")

    @Slot(str)
    def on_sequence_command_sent(self, command):
        """Команда последовательности отправлена"""
        self.add_terminal_message(f"➤ {command}", "command")

    @Slot(bool, str)
    def on_sequence_finished(self, success, message):
        """Последовательность завершена"""
        if success:
            self.add_terminal_message(f"✅ {message}", "response")
        else:
            self.add_terminal_message(f"❌ {message}", "error")
        
        self.command_sequence_thread = None

    def stop_sequence(self):
        """Остановка выполнения последовательности"""
        if self.command_sequence_thread and self.command_sequence_thread.isRunning():
            self.command_sequence_thread.stop()
            self.add_terminal_message("⏹️ Последовательность остановлена", "warning")

    def show_about(self):
        """Показать диалог О программе"""
        QMessageBox.about(
            self,
            "О программе",
            "<h2>Панель управления устройством</h2>"
            "<p><b>Версия:</b> 2.0 (PySide6)</p>"
            "<p><b>Описание:</b> Современное приложение для управления устройствами через Serial-порт.</p>"
            "<p><b>Технологии:</b> Python, PySide6, Serial</p>"
            "<p>© 2024 Все права защищены</p>"
        )

    def reload_config(self):
        """Перезагрузка конфигурации с обновлением интерфейса"""
        try:
            # Сохраняем текущую страницу
            current_page = 0
            for i, (name, button) in enumerate(self.nav_buttons.items()):
                if button.isChecked():
                    current_page = i
                    break
            
            # Перезагружаем конфигурацию
            self.load_config()
            
            # Пересоздаем страницы с новой конфигурацией
            # Очищаем содержимое
            while self.content_area.count():
                widget = self.content_area.widget(0)
                self.content_area.removeWidget(widget)
                widget.deleteLater()
            
            # Пересоздаем страницы
            self.setup_sequences_page()
            self.setup_commands_page() 
            self.setup_settings_page()
            self.setup_firmware_page()
            
            # Возвращаемся на текущую страницу
            self.content_area.setCurrentIndex(current_page)
            
            self.add_terminal_message("🔄 Конфигурация перезагружена", "info")
            self.statusBar().showMessage("Конфигурация перезагружена", 3000)
            
        except Exception as e:
            error_msg = f"Не удалось перезагрузить конфигурацию: {str(e)}"
            logging.error(error_msg)
            self.add_terminal_message(f"❌ {error_msg}", "error")
            QMessageBox.critical(
                self,
                "Ошибка",
                error_msg
            )

    def switch_page(self, page_name):
        """Переключение между страницами"""
        # Обновляем состояние кнопок навигации
        for name, button in self.nav_buttons.items():
            button.setChecked(name == page_name)
        
        # Переключаем страницу
        page_index = {"sequences": 0, "commands": 1, "settings": 2, "firmware": 3}.get(page_name, 0)
        self.content_area.setCurrentIndex(page_index)

    def connect_serial(self):
        """Подключение к Serial порту"""
        try:
            # Создание объекта Serial с параметрами из настроек
            self.serial_port = serial.Serial(
                port=self.serial_settings.get('port', 'COM1'),
                baudrate=self.serial_settings.get('baudrate', 115200),
                bytesize=self.serial_settings.get('bytesize', 8),
                parity=self.serial_settings.get('parity', 'N'),
                stopbits=self.serial_settings.get('stopbits', 1),
                timeout=self.serial_settings.get('timeout', 1)
            )

            # Создание и запуск потока для чтения данных
            self.serial_thread = SerialThread(self.serial_port)
            self.serial_thread.data_received.connect(self.on_data_received)
            self.serial_thread.start()

            # Обновляем статус подключения
            self.connection_status.setText("● Подключено")
            self.connection_status.setStyleSheet("""
                QLabel {
                    color: #50fa7b;
                    font-weight: 600;
                    font-size: 11pt;
                    padding: 8px;
                    background-color: #1b2d1b;
                    border-radius: 6px;
                    border: 1px solid #50fa7b;
                }
            """)

            port_name = self.serial_settings.get('port', 'COM?')
            self.add_terminal_message(f"🔗 Подключено к порту {port_name}", "response")
            self.statusBar().showMessage(f"Подключено к порту {port_name}", 3000)

        except Exception as e:
            error_msg = f"Не удалось подключиться к порту: {str(e)}"
            self.add_terminal_message(f"❌ {error_msg}", "error")
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                error_msg
            )

    @Slot(str)
    def on_data_received(self, data):
        """Обработка полученных данных"""
        self.add_terminal_message(f"◄ {data}", "response")
        
        # Дублируем в терминал команд, если он существует
        if hasattr(self, 'commands_terminal'):
            self.add_commands_terminal_message(f"◄ {data}", "response")
        
        # Передаем ответ в поток последовательности, если он активен
        if self.command_sequence_thread and self.command_sequence_thread.isRunning():
            self.command_sequence_thread.add_response(data)
        
        logging.info(f"Получены данные: {data}")

    def create_menu(self):
        """Создание современного меню"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu('📁 Файл')
        
        reload_action = QAction('🔄 Перезагрузить конфигурацию', self)
        reload_action.setShortcut('Ctrl+R')
        reload_action.triggered.connect(self.reload_config)
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('❌ Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Вид"
        view_menu = menubar.addMenu('👁️ Вид')
        
        fullscreen_action = QAction('📺 Полноэкранный режим', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        theme_action = QAction('🎨 Переключить тему', self)
        theme_action.setShortcut('Ctrl+T')
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Меню "Подключение"
        connection_menu = menubar.addMenu('🔌 Подключение')
        
        connect_action = QAction('🔗 Подключиться', self)
        connect_action.setShortcut('Ctrl+Shift+C')
        connect_action.triggered.connect(self.connect_serial)
        connection_menu.addAction(connect_action)
        
        disconnect_action = QAction('📴 Отключиться', self)
        disconnect_action.setShortcut('Ctrl+Shift+D')
        disconnect_action.triggered.connect(self.disconnect_serial)
        connection_menu.addAction(disconnect_action)
        
        # Меню "Помощь"
        help_menu = menubar.addMenu('💡 Помощь')
        
        about_action = QAction('ℹ️ О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            self.add_terminal_message("🪟 Оконный режим", "info")
        else:
            self.showFullScreen()
            self.is_fullscreen = True
            self.add_terminal_message("📺 Полноэкранный режим", "info")

    # Git методы
    def check_git_status(self):
        """Проверка статуса Git репозитория"""
        try:
            repo_path = os.path.dirname(os.path.abspath(__file__))
            repo = git.Repo(repo_path)
            
            # Получаем информацию о текущей ветке
            current_branch = repo.active_branch.name
            last_commit = repo.head.commit.hexsha[:7]
            last_commit_msg = repo.head.commit.message.strip()
            
            # Проверяем состояние
            if repo.is_dirty():
                status = "🔸 Есть несохраненные изменения"
            else:
                status = "✅ Репозиторий чистый"
            
            info_text = f"{status}\nВетка: {current_branch}\nКоммит: {last_commit}\nСообщение: {last_commit_msg}"
            self.repo_info_label.setText(info_text)
            
            self.add_firmware_message(f"📡 Статус Git: {status}", "info")
            
        except Exception as e:
            error_msg = f"❌ Ошибка Git: {str(e)}"
            self.repo_info_label.setText(error_msg)
            self.add_firmware_message(error_msg, "error")

    def check_git_updates(self):
        """Проверка обновлений в удаленном репозитории"""
        try:
            self.add_firmware_message("🔍 Проверка обновлений...", "info")
            
            repo_path = os.path.dirname(os.path.abspath(__file__))
            repo = git.Repo(repo_path)
            
            # Получаем информацию о remote
            origin = repo.remotes.origin
            origin.fetch()
            
            # Сравниваем локальные и удаленные коммиты
            local_commit = repo.head.commit.hexsha
            remote_commit = origin.refs[repo.active_branch.name].commit.hexsha
            
            if local_commit == remote_commit:
                self.add_firmware_message("✅ Обновления не найдены", "response")
                self.pull_updates_btn.setEnabled(False)
            else:
                self.add_firmware_message("🆕 Найдены обновления!", "warning")
                self.pull_updates_btn.setEnabled(True)
                
                # Показываем количество коммитов
                commits_behind = list(repo.iter_commits(f'{local_commit}..{remote_commit}'))
                self.add_firmware_message(f"📊 Доступно коммитов: {len(commits_behind)}", "info")
                
        except Exception as e:
            error_msg = f"❌ Ошибка проверки обновлений: {str(e)}"
            self.add_firmware_message(error_msg, "error")

    def pull_git_updates(self):
        """Скачивание обновлений из репозитория"""
        try:
            self.add_firmware_message("⬇️ Скачивание обновлений...", "info")
            
            repo_path = os.path.dirname(os.path.abspath(__file__))
            repo = git.Repo(repo_path)
            
            # Выполняем git pull
            origin = repo.remotes.origin
            origin.pull()
            
            self.add_firmware_message("✅ Обновления успешно скачаны!", "response")
            self.pull_updates_btn.setEnabled(False)
            
            # Обновляем статус
            self.check_git_status()
            
            # Предлагаем перезапустить приложение
            reply = QMessageBox.question(
                self,
                "Обновление завершено",
                "Обновления скачаны успешно.\nХотите перезапустить приложение для применения изменений?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.restart_application()
                
        except Exception as e:
            error_msg = f"❌ Ошибка скачивания обновлений: {str(e)}"
            self.add_firmware_message(error_msg, "error")

    def view_git_commits(self):
        """Просмотр истории коммитов"""
        try:
            repo_path = os.path.dirname(os.path.abspath(__file__))
            repo = git.Repo(repo_path)
            
            # Получаем последние 10 коммитов
            commits = list(repo.iter_commits(max_count=10))
            
            self.add_firmware_message("📜 Последние коммиты:", "info")
            for commit in commits:
                commit_info = f"  {commit.hexsha[:7]} - {commit.message.strip()} ({commit.author.name})"
                self.add_firmware_message(commit_info, "info")
                
        except Exception as e:
            error_msg = f"❌ Ошибка получения истории: {str(e)}"
            self.add_firmware_message(error_msg, "error")

    def restart_application(self):
        """Перезапуск приложения"""
        try:
            # Сохраняем настройки
            self.save_serial_settings()
            self.save_update_settings()
            
            # Перезапускаем приложение
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        except Exception as e:
            error_msg = f"❌ Ошибка перезапуска: {str(e)}"
            self.add_firmware_message(error_msg, "error")

    # PlatformIO методы
    def browse_arduino_path(self):
        """Выбор папки с проектом Arduino/PlatformIO"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с проектом Arduino/PlatformIO",
            self.update_settings.get('platformio_path', '')
        )
        
        if path:
            self.arduino_path_edit.setText(path)
            self.update_settings['platformio_path'] = path
            self.save_update_settings()
            self.add_firmware_message(f"📁 Путь к проекту обновлен: {path}", "info")

    def refresh_upload_ports(self):
        """Обновление списка портов для загрузки"""
        if hasattr(self, 'upload_port_combo'):
            current_port = self.upload_port_combo.currentText()
            self.upload_port_combo.clear()
            
            # Получаем список доступных портов
            ports = [port.device for port in serial.tools.list_ports.comports()]
            if ports:
                self.upload_port_combo.addItems(ports)
                # Восстанавливаем выбранный порт
                if current_port in ports:
                    self.upload_port_combo.setCurrentText(current_port)
                else:
                    # Если предыдущий порт недоступен, используем из настроек
                    settings_port = self.update_settings.get('upload_port', '')
                    if settings_port in ports:
                        self.upload_port_combo.setCurrentText(settings_port)
            else:
                self.upload_port_combo.addItem("Нет доступных портов")

    def compile_firmware(self):
        """Компиляция прошивки"""
        arduino_path = self.arduino_path_edit.text().strip()
        if not arduino_path or not os.path.exists(arduino_path):
            QMessageBox.warning(self, "Ошибка", "Укажите корректный путь к проекту Arduino/PlatformIO")
            return
        
        self.add_firmware_message("🔨 Начало компиляции...", "info")
        self.run_platformio_command(arduino_path, ["run"])

    def upload_firmware(self):
        """Загрузка прошивки"""
        arduino_path = self.arduino_path_edit.text().strip()
        upload_port = self.upload_port_combo.currentText()
        
        if not arduino_path or not os.path.exists(arduino_path):
            QMessageBox.warning(self, "Ошибка", "Укажите корректный путь к проекту Arduino/PlatformIO")
            return
        
        if not upload_port or upload_port == "Нет доступных портов":
            QMessageBox.warning(self, "Ошибка", "Выберите порт для загрузки")
            return
        
        self.add_firmware_message(f"⬆️ Загрузка на порт {upload_port}...", "info")
        self.run_platformio_command(arduino_path, ["run", "--target", "upload", "--upload-port", upload_port])

    def compile_and_upload_firmware(self):
        """Компиляция и загрузка прошивки"""
        arduino_path = self.arduino_path_edit.text().strip()
        upload_port = self.upload_port_combo.currentText()
        
        if not arduino_path or not os.path.exists(arduino_path):
            QMessageBox.warning(self, "Ошибка", "Укажите корректный путь к проекту Arduino/PlatformIO")
            return
        
        if not upload_port or upload_port == "Нет доступных портов":
            QMessageBox.warning(self, "Ошибка", "Выберите порт для загрузки")
            return
        
        self.add_firmware_message(f"🚀 Компиляция и загрузка на порт {upload_port}...", "info")
        self.run_platformio_command(arduino_path, ["run", "--target", "upload", "--upload-port", upload_port])

    def run_platformio_command(self, project_path, args):
        """Выполнение команды PlatformIO"""
        try:
            # Формируем команду
            cmd = ["pio"] + args
            
            self.add_firmware_message(f"💻 Команда: {' '.join(cmd)}", "info")
            
            # Выполняем команду
            process = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 минут таймаут
            )
            
            # Выводим результат
            if process.stdout:
                for line in process.stdout.split('\n'):
                    if line.strip():
                        self.add_firmware_message(f"📄 {line}", "info")
            
            if process.stderr:
                for line in process.stderr.split('\n'):
                    if line.strip():
                        self.add_firmware_message(f"⚠️ {line}", "warning")
            
            if process.returncode == 0:
                self.add_firmware_message("✅ Команда выполнена успешно!", "response")
            else:
                self.add_firmware_message(f"❌ Команда завершена с ошибкой (код {process.returncode})", "error")
                
        except subprocess.TimeoutExpired:
            self.add_firmware_message("⏰ Команда прервана по таймауту (5 минут)", "error")
        except FileNotFoundError:
            self.add_firmware_message("❌ PlatformIO не найден! Установите PlatformIO CLI", "error")
        except Exception as e:
            self.add_firmware_message(f"❌ Ошибка выполнения команды: {str(e)}", "error")

    def add_firmware_message(self, message, msg_type="info"):
        """Добавление сообщения в вывод прошивки"""
        if hasattr(self, 'firmware_output'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Цветовое кодирование
            if msg_type == "command":
                formatted_msg = f'<span style="color: #6c98f3;">[{timestamp}] {message}</span>'
            elif msg_type == "response":
                formatted_msg = f'<span style="color: #50fa7b;">[{timestamp}] {message}</span>'
            elif msg_type == "error":
                formatted_msg = f'<span style="color: #ff5555;">[{timestamp}] {message}</span>'
            elif msg_type == "warning":
                formatted_msg = f'<span style="color: #ffb86c;">[{timestamp}] {message}</span>'
            else:
                formatted_msg = f'<span style="color: #dce1ec;">[{timestamp}] {message}</span>'
            
            self.firmware_output.append(formatted_msg)
            
            # Прокручиваем в конец
            scrollbar = self.firmware_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def send_manual_command_from_commands(self):
        """Отправка команды из поля ввода на странице команд"""
        if hasattr(self, 'commands_input'):
            command = self.commands_input.text().strip()
            if command:
                self.send_command_to_commands_terminal(command)
                self.commands_input.clear()

    def clear_commands_terminal(self):
        """Очистка терминала команд"""
        if hasattr(self, 'commands_terminal'):
            self.commands_terminal.clear()
            self.add_commands_terminal_message("🧹 Терминал команд очищен", "info")

    def send_command_to_commands_terminal(self, command):
        """Отправка команды в Serial порт с дублированием в терминал команд"""
        if not self.serial_port or not self.serial_port.is_open:
            self.add_commands_terminal_message("❌ Устройство не подключено", "error")
            return

        try:
            # Отправляем команду
            full_command = command + '\n'
            self.serial_port.write(full_command.encode('utf-8'))
            
            # Добавляем в оба терминала
            self.add_terminal_message(f"➤ {command}", "command")
            self.add_commands_terminal_message(f"➤ {command}", "command")
            
            logging.info(f"Отправлена команда: {command}")

        except Exception as e:
            error_msg = f"Ошибка отправки команды: {str(e)}"
            logging.error(error_msg)
            self.add_terminal_message(f"❌ {error_msg}", "error")
            self.add_commands_terminal_message(f"❌ {error_msg}", "error")

    def add_commands_terminal_message(self, message, msg_type="info"):
        """Добавление сообщения в терминал команд"""
        if hasattr(self, 'commands_terminal'):
            # Добавляем временную метку
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Цветовое кодирование по типу сообщения
            if msg_type == "command":
                formatted_msg = f'<span style="color: #6c98f3;">[{timestamp}] {message}</span>'
            elif msg_type == "response":
                formatted_msg = f'<span style="color: #50fa7b;">[{timestamp}] {message}</span>'
            elif msg_type == "error":
                formatted_msg = f'<span style="color: #ff5555;">[{timestamp}] {message}</span>'
            elif msg_type == "warning":
                formatted_msg = f'<span style="color: #ffb86c;">[{timestamp}] {message}</span>'
            else:
                formatted_msg = f'<span style="color: #dce1ec;">[{timestamp}] {message}</span>'
            
            # Добавляем сообщение в терминал
            self.commands_terminal.append(formatted_msg)
            
            # Прокручиваем в конец
            scrollbar = self.commands_terminal.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())


if __name__ == "__main__":
    # Инициализация логирования
    try:
        logging.info("=" * 80)
        logging.info("Запуск приложения с PySide6")
        # Выводим информацию о системе
        logging.info(f"Операционная система: {sys.platform}")
        logging.info(f"Версия Python: {sys.version}")
        logging.info(f"Текущая директория: {os.getcwd()}")
        logging.info(f"Файл логов: {LOG_FILE}")
    except Exception as e:
        print(f"Ошибка при логировании запуска: {str(e)}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Критическая ошибка при выполнении приложения: {str(e)}")
        print(f"Ошибка: {str(e)}") 