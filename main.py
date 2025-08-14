import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime

import git
import serial
import serial.tools.list_ports
import tomli
from PySide6.QtCore import (
    QThread,
    QTimer,
    QUrl,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QColor, QFont, QIntValidator
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qt_material import apply_stylesheet  # qt-material must be imported after PySide

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
        filemode='a'
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    logging.info("Логирование инициализировано успешно")
except Exception as e:
    print(f"Ошибка при настройке логирования: {str(e)}")

# Путь к файлу с настройками
SETTINGS_FILE = 'serial_settings.json'
# Настройки обновления по умолчанию
DEFAULT_UPDATE_SETTINGS = {
    'enable_auto_update': True,
    'repository_url': 'https://github.com/yourusername/yourrepository.git',
    'update_check_interval': 3600,
    'auto_connect': True,
    'platformio_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arduino'),
    'upload_port': '',
    'theme': 'dark'
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

    def __init__(self, serial_port, commands, keywords=None, parent=None):
        super().__init__(parent)
        self.serial_port = serial_port
        self.commands = commands
        # Словарь ключевых слов для анализа ответов
        self.keywords = keywords or {
            'complete': ['complete', 'completed', 'done'],
            'received': ['received'],
            'error': ['err', 'error', 'fail'],
        }
        # Гарантируем наличие базовых ключевых слов даже при пустом словаре
        self.keywords.setdefault('complete', ['complete', 'completed', 'done','COMPLETE'])
        self.keywords.setdefault('received', ['received'])
        self.keywords.setdefault('error', ['err', 'error', 'fail'])
        self.keywords.setdefault('complete_line', ['complete'])
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

                # Ожидаем завершения команды (COMPLETE). Маркер RECEIVED теперь необязателен
                received = False  # оставляем для логов, но не используем в проверке
                completed = False
                start_time = time.time()
                timeout = 10  # Таймаут в секундах

                # Ждём только until COMPLETE/COMPLETED
                while (not completed) and time.time() - start_time < timeout:
                    if not self.running:
                        self.sequence_finished.emit(False, "Выполнение прервано пользователем")
                        return

                    with self.lock:
                        # Копируем ответы и очищаем буфер, чтобы не обрабатывать их повторно
                        current_responses = self.responses[:]
                        self.responses.clear()

                    for response in current_responses:
                        # Приводим строку к нижнему регистру, чтобы сравнение не зависело от регистра
                        resp_lower = response.lower()

                        # Флаг о получении подтверждения приёма команды
                        if any(re.search(rf"\\b{re.escape(kw)}\\b", resp_lower) for kw in self.keywords.get('received', [])):
                            received = True

                        # Флаг о завершении выполнения -- требуем ОТДЕЛЬНУЮ строку "complete" (или другие ключевые)
                        if (not completed):
                            cleaned = resp_lower.strip()
                            if cleaned in self.keywords.get('complete_line', ['complete']):
                                completed = True

                        # Обрабатываем возможную ошибку
                        if any(re.search(rf"\\b{re.escape(kw)}\\b", resp_lower) for kw in self.keywords.get('error', [])):
                            self.sequence_finished.emit(False, f"Ошибка выполнения команды: {response}")
                            return

                    if not completed:
                        time.sleep(0.1)  # Проверяем каждые 100 мс

                # Проверяем завершение выполнения команды
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
        # Сбрасываем кастомные стили, чтобы применить qt-material
        self.setStyleSheet("")

        # Устанавливаем accent-класс для qt-material, где применимо
        qt_material_class = None
        if self.button_type == "success":
            qt_material_class = "success"
        elif self.button_type == "warning":
            qt_material_class = "warning"
        elif self.button_type == "danger":
            qt_material_class = "danger"

        if qt_material_class:
            self.setProperty('class', qt_material_class)
            # Обновить стиль после изменения property
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            # Сбрасываем класс для обычных/вторичных кнопок
            self.setProperty('class', '')
            self.style().unpolish(self)
            self.style().polish(self)


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
        """Применение темы qt-material"""
        theme_pref = self.update_settings.get('theme', 'dark')

        # Дополнительные акцентные цвета и шрифт для qt-material
        extra = {
            'danger': '#dc3545',
            'warning': '#ffc107',
            'success': '#17a2b8',
            'font_family': 'Segoe UI',
        }

        if theme_pref == 'light':
            apply_stylesheet(QApplication.instance(), theme='light_blue.xml', invert_secondary=True, extra=extra)
            self.current_theme = 'light'
        else:
            apply_stylesheet(QApplication.instance(), theme='dark_teal.xml', extra=extra)
            self.current_theme = 'dark'

        self.update()

    def toggle_theme(self):
        """Переключение светлой/тёмной темы qt-material"""
        new_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.update_settings['theme'] = new_theme
        self.save_update_settings()
        self.apply_theme()
        self.statusBar().showMessage(f"Тема применена: {self.current_theme}", 2000)

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

            # ---------- Новая логика: ключевые слова последовательностей ----------
            self.sequence_keywords = config.get(
                'sequence_keywords',
                {
                    'complete': ['complete', 'completed', 'done'],
                    'received': ['received'],
                    'error': ['err', 'error', 'fail'],
                },
            )
            # --------------------------------------------------------------------

            # Парсим разделы из исходного файла по комментариям
            self.button_groups = self.parse_config_sections(config_path)

            # Загружаем кнопки команд
            self.buttons_config = config.get('buttons', {})

            # Загружаем последовательности
            self.sequences = config.get('sequences', {})

            # Загружаем мастер шаги
            self.wizard_steps = {}
            if 'wizard' in config:
                steps = config['wizard'].get('step', [])
                # tomli может вернуть dict или list; нормализуем
                if isinstance(steps, dict):
                    steps = [steps]
                for s in steps:
                    self.wizard_steps[s['id']] = s
            else:
                self.wizard_steps = {}

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
            with open(config_path, encoding='utf-8') as file:
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
-            #sidebar {
-                background-color: #16151a;
-                border-right: 3px solid #343b48;
-            }
+            /* Стили боковой панели применяются qt-material */
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
            ("wizard", "🪄 Мастер", True),
            ("sequences", "🏠 Главное меню", False),
            ("commands", "⚡ Команды", False),
            ("designer", "🖱️ Конструктор", False),
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
            # Стилями управляет qt-material
            btn.clicked.connect(lambda checked, k=key: self.switch_page(k))
            self.nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        sidebar_layout.addWidget(nav_widget)
        sidebar_layout.addStretch()

        # Информация о подключении
        self.connection_card = ModernCard()
        connection_layout = QVBoxLayout()

        self.connection_status = QLabel("● Отключено")
        # Цвета и виджет стилизуются qt-material
        connection_layout.addWidget(self.connection_status)

        self.connection_card.addLayout(connection_layout)
        sidebar_layout.addWidget(self.connection_card)

    def setup_content_area(self):
        """Настройка основной области контента"""
        self.content_area = QStackedWidget()

        # Создаем страницы
        self.setup_wizard_page()
        self.setup_sequences_page()
        self.setup_commands_page()
        self.setup_designer_page()  # Конструктор последовательностей
        self.setup_settings_page()
        self.setup_firmware_page()  # Новая страница для прошивки

    def setup_wizard_page(self):
        """Настройка страницы мастера"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header = QLabel("🪄 Мастер")
        header.setStyleSheet("color:#568af2;font-size:18pt;font-weight:700;")
        layout.addWidget(header)

        self.wizard_step_title = QLabel()
        self.wizard_step_title.setStyleSheet("color:#dce1ec;font-size:14pt;font-weight:600;")
        layout.addWidget(self.wizard_step_title)

        self.wizard_progress = QProgressBar()
        self.wizard_progress.setVisible(False)
        layout.addWidget(self.wizard_progress)

        self.wizard_buttons_layout = QHBoxLayout()
        layout.addLayout(self.wizard_buttons_layout)

        layout.addStretch()

        self.content_area.addWidget(page)

        # state
        self.current_wizard_id = 1
        self.wizard_waiting_next_id = None

        # initial render
        self.render_wizard_step(self.current_wizard_id)

    # ---------------- Wizard helpers ----------------

    def _normalize_next_id(self, value) -> int:
        """Преобразует значение next/autoNext из конфигурации к целому ID шага.

        Возвращает 0, если переход не задан (false, 0, None или некорректная строка).
        """
        # TOML может парсить `false` в bool, а числа – в int/str
        if value is None:
            return 0
        if isinstance(value, bool):
            # False -> 0, True практически не используется, трактуем как 1
            return 1 if value else 0
        if isinstance(value, int):
            return value
        # Если пришла строка – пытаемся преобразовать в число
        if isinstance(value, str) and value.isdigit():
            return int(value)
        # Всё остальное считаем отсутствием перехода
        return 0

    def render_wizard_step(self, step_id: int):
        if step_id == 0 or step_id not in getattr(self, 'wizard_steps', {}):
            return

        step = self.wizard_steps[step_id]

        # play enter melody
        if step.get('melodyEnter'):
            safe_playsound(step['melodyEnter'])

        self.wizard_step_title.setText(step.get('title', ''))

        # progress bar
        self.wizard_progress.setVisible(step.get('showBar', False))
        if step.get('showBar', False):
            self.wizard_progress.setRange(0, 0)  # indeterminate

        # clear old buttons
        while self.wizard_buttons_layout.count():
            child = self.wizard_buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # create buttons
        buttons_cfg = step.get('buttons', [])
        for btn_cfg in buttons_cfg:
            text = btn_cfg['text']
            next_id = btn_cfg.get('next', 0)
            btn = ModernButton(text, "primary")

            if step.get('sequence') and text.startswith("▶"):
                # кнопка запуска последовательности
                btn.clicked.connect(lambda _=False, seq=step['sequence'], nxt=btn_cfg.get('next', 0): self.wizard_run_sequence(seq, nxt or step.get('autoNext', 0)))
            else:
                btn.clicked.connect(lambda _=False, nid=next_id: self.render_wizard_step(nid))

            self.wizard_buttons_layout.addWidget(btn)

        self.current_wizard_id = step_id

        # Всегда автоматически запускаем последовательность, если она задана.
        if step.get('sequence') and (
            not self.command_sequence_thread or not self.command_sequence_thread.isRunning()
        ):
            self.wizard_run_sequence(step['sequence'], step.get('autoNext', 0))

    def wizard_run_sequence(self, sequence_name: str, next_id_after: int = 0):
        if sequence_name:
            # Нормализуем ID следующего шага (0 означает – без перехода)
            self.wizard_waiting_next_id = self._normalize_next_id(next_id_after)
            self.start_sequence(sequence_name)
        else:
            next_id_norm = self._normalize_next_id(next_id_after)
            if next_id_norm:
                self.render_wizard_step(next_id_norm)

        # Подключаем прогресс бар
        if self.command_sequence_thread:
            total = len(self.command_sequence_thread.commands)
            self.wizard_progress.setRange(0, total)
            self.wizard_progress.setValue(0)
            self.wizard_progress.setVisible(True)
            self.command_sequence_thread.progress_updated.connect(self.update_wizard_progress)
            # блокируем кнопки
            for i in range(self.wizard_buttons_layout.count()):
                w = self.wizard_buttons_layout.itemAt(i).widget()
                if w:
                    w.setEnabled(False)

    def update_wizard_progress(self, current: int, total: int):
        self.wizard_progress.setRange(0, total)
        self.wizard_progress.setValue(current)

    def enable_wizard_buttons(self):
        for i in range(self.wizard_buttons_layout.count()):
            w = self.wizard_buttons_layout.itemAt(i).widget()
            if w:
                w.setEnabled(True)

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

    def setup_designer_page(self):
        """Создаёт базовый UI конструктора последовательностей (Drag & Drop)"""

        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ---------------- Левая колонка: команды ----------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        left_title = QLabel("📦 Доступные команды")
        left_title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 14pt;
                font-weight: 600;
                margin-bottom: 10px;
            }
        """)
        left_layout.addWidget(left_title)

        # Список команд (drag-enabled)
        self.designer_commands_list = QListWidget()
        self.designer_commands_list.setDragEnabled(True)
        self.designer_commands_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Заполняем командами из buttons_config
        for name in self.buttons_config.keys():
            item = QListWidgetItem(name, self.designer_commands_list)
            self.style_command_item(item)

        # Добавляем стандартные команды типа wait
        for wait_val in ["wait 1", "wait 5", "wait 10"]:
            item = QListWidgetItem(wait_val, self.designer_commands_list)
            self.style_command_item(item)

        # Добавляем существующие последовательности как элементы
        if self.sequences:
            for seq in self.sequences.keys():
                if seq == "":
                    continue
                item = QListWidgetItem(seq, self.designer_commands_list)
                self.style_command_item(item)

        left_layout.addWidget(self.designer_commands_list)

        # ---------------- Правая колонка: последовательность ----------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        right_title = QLabel("🧩 Текущая последовательность")
        right_title.setStyleSheet("""
            QLabel {
                color: #568af2;
                font-size: 14pt;
                font-weight: 600;
                margin-bottom: 10px;
            }
        """)
        right_layout.addWidget(right_title)

        # Список всех последовательностей
        self.sequence_names_list = QListWidget()
        self.sequence_names_list.addItems(list(self.sequences.keys()))
        self.sequence_names_list.setFixedHeight(120)
        self.sequence_names_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        right_layout.addWidget(self.sequence_names_list)

        # Список элементов последовательности (drop-enabled)
        self.designer_sequence_list = SequenceListWidget(self)
        self.designer_sequence_list.setAcceptDrops(True)
        self.designer_sequence_list.setDragEnabled(True)
        self.designer_sequence_list.setDefaultDropAction(Qt.CopyAction)
        right_layout.addWidget(self.designer_sequence_list)

        # Кнопки пока-заглушки
        buttons_layout = QHBoxLayout()
        self.save_sequence_btn = ModernButton("💾 Сохранить", "success")
        self.delete_item_btn = ModernButton("🗑️ Удалить элемент", "danger")
        buttons_layout.addWidget(self.save_sequence_btn)
        buttons_layout.addWidget(self.delete_item_btn)
        right_layout.addLayout(buttons_layout)

        # ---------- Поведение ----------
        # Настройка режимов drag & drop
        self.designer_commands_list.setDragDropMode(QAbstractItemView.DragOnly)
        self.designer_sequence_list.setDragDropMode(QAbstractItemView.DragDrop)
        self.designer_sequence_list.setDefaultDropAction(Qt.CopyAction)
        self.designer_sequence_list.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
        )

        # Сигналы
        self.sequence_names_list.itemClicked.connect(self.on_sequence_item_clicked)
        self.sequence_names_list.itemDoubleClicked.connect(self.rename_sequence_item)
        self.save_sequence_btn.clicked.connect(self.save_current_sequence)
        self.delete_item_btn.clicked.connect(self.delete_selected_sequence_item)

        # Подключаем обработку double click/Enter для команд wait
        for lw in (self.designer_commands_list, self.designer_sequence_list):
            lw.itemDoubleClicked.connect(self.edit_wait_item)
            lw.itemActivated.connect(self.edit_wait_item)

        # Загрузить первую последовательность (если есть)
        if self.sequence_names_list.count():
            self.sequence_names_list.setCurrentRow(0)
            self.load_sequence_to_designer(self.sequence_names_list.currentItem().text())

        # ---------------- Сборка в макет ----------------
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 2)

        self.content_area.addWidget(page)

        # Поле для создания новой последовательности
        new_seq_layout = QHBoxLayout()
        self.new_seq_edit = QLineEdit()
        self.new_seq_edit.setPlaceholderText("Новая последовательность")
        self.add_seq_btn = ModernButton("➕", "primary")
        self.add_seq_btn.setFixedWidth(50)
        self.add_seq_btn.clicked.connect(self.create_new_sequence)
        new_seq_layout.addWidget(self.new_seq_edit)
        new_seq_layout.addWidget(self.add_seq_btn)
        right_layout.addLayout(new_seq_layout)

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

        # --- Новая секция Commit & Push ---
        commit_layout = QHBoxLayout()
        commit_layout.addWidget(QLabel("Сообщение коммита:"))

        self.commit_message_edit = QLineEdit()
        self.commit_message_edit.setPlaceholderText("Описание изменений...")
        commit_layout.addWidget(self.commit_message_edit, 1)

        self.commit_push_btn = ModernButton("⬆️ Commit & Push", "warning")
        self.commit_push_btn.clicked.connect(self.commit_and_push_changes)
        commit_layout.addWidget(self.commit_push_btn)

        git_layout.addLayout(commit_layout)
        # --- конец новой секции ---

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

        # Если уже выполняется другая последовательность, корректно завершим её
        # прежде чем запускать новую. Это гарантирует, что только один поток
        # CommandSequenceThread обращается к Serial-порту одновременно и
        # предотвращает возможные гонки и конфликт за ресурсы.
        if self.command_sequence_thread and self.command_sequence_thread.isRunning():
            self.command_sequence_thread.stop()
            self.command_sequence_thread.wait()
            self.command_sequence_thread = None

        # Рекурсивно разворачиваем последовательности в реальные команды
        def expand_item(item, visited):
            if self.is_wait_command(item):
                return [item]

            # Команда
            if item in self.buttons_config:
                return [self.buttons_config[item]]

            # Вложенная последовательность
            if item in self.sequences:
                if item in visited:
                    self.add_terminal_message(f"❌ Обнаружена рекурсия в последовательности '{item}'", "error")
                    return []
                visited.add(item)
                expanded = []
                for sub in self.sequences[item]:
                    expanded.extend(expand_item(sub, visited))
                visited.remove(item)
                return expanded

            # Неизвестное – отправляем как есть
            return [item]

        actual_commands = []
        for cmd in self.sequences[sequence_name]:
            actual_commands.extend(expand_item(cmd, {sequence_name}))

        # Запускаем поток выполнения последовательности
        self.command_sequence_thread = CommandSequenceThread(self.serial_port, actual_commands, self.sequence_keywords, self)
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
            # Скрываем прогресс и разблокируем кнопки
            self.wizard_progress.setVisible(False)
            self.enable_wizard_buttons()
            if self.wizard_waiting_next_id and self.wizard_waiting_next_id != 0:
                self.render_wizard_step(self.wizard_waiting_next_id)
                self.wizard_waiting_next_id = 0
            else:
                # Fallback: используем autoNext текущего шага
                step = self.wizard_steps.get(self.current_wizard_id, {})
                auto_next = self._normalize_next_id(step.get('autoNext', 0))
                if auto_next:
                    self.render_wizard_step(auto_next)
        else:
            self.add_terminal_message(f"❌ {message}", "error")
            # Скрываем прогресс и разблокируем кнопки
            self.wizard_progress.setVisible(False)
            self.enable_wizard_buttons()

        self.command_sequence_thread = None

    def stop_sequence(self):
        """Остановка выполнения последовательности"""
        if self.command_sequence_thread and self.command_sequence_thread.isRunning():
            self.command_sequence_thread.stop()
            # Дожидаемся корректного завершения потока, чтобы освободить ресурсы
            self.command_sequence_thread.wait()
            self.command_sequence_thread = None
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
            for i, (_name, button) in enumerate(self.nav_buttons.items()):
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
            self.setup_wizard_page()
            self.setup_sequences_page()
            self.setup_commands_page()
            self.setup_designer_page()  # Конструктор последовательностей
            self.setup_settings_page()
            self.setup_firmware_page()  # Новая страница для прошивки

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
        page_index = {"wizard": 0, "sequences": 1, "commands": 2, "designer": 3, "settings": 4, "firmware": 5}.get(page_name, 0)
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
            self.add_terminal_message(f"🔗 Подключено к порту {self.serial_settings.get('port', 'COM?')}", "response")
            self.statusBar().showMessage(f"Подключено к порту {self.serial_settings.get('port', 'COM?')}", 3000)

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

    # ================= Designer helpers =================

    def load_sequence_to_designer(self, seq_name):
        """Отображает команды выбранной последовательности в правом списке"""
        self.designer_sequence_list.clear()

        commands = self.sequences.get(seq_name, [])
        for cmd in commands:
            item = QListWidgetItem(cmd, self.designer_sequence_list)
            self.style_command_item(item)

        self.validate_designer_items()

    def on_sequence_item_clicked(self, item):
        """При выборе последовательности загрузить её содержимое"""
        self.load_sequence_to_designer(item.text())

    def rename_sequence_item(self, item):
        """Переименование последовательности"""
        new_name, ok = QInputDialog.getText(self, 'Переименование последовательности', 'Введите новое имя:', text=item.text())
        if ok and new_name:
            item.setText(new_name)
            self.sequences[new_name] = self.sequences.pop(item.text())
            self.sequence_names_list.clear()
            self.sequence_names_list.addItems(list(self.sequences.keys()))
            self.sequence_names_list.setCurrentRow(0)
            self.load_sequence_to_designer(new_name)

    def save_current_sequence(self):
        """Сохраняет текущую последовательность в self.sequences и файл config.toml"""
        seq_name = self.get_current_sequence_name()
        if not seq_name:
            seq_name, ok = QInputDialog.getText(self, 'Имя последовательности', 'Введите имя новой последовательности:')
            if not ok or not seq_name:
                return

        # Сбор команд из списка
        cmds = [self.designer_sequence_list.item(i).text() for i in range(self.designer_sequence_list.count())]

        self.sequences[seq_name] = cmds

        # Обновить список в случае новой последовательности
        if seq_name not in [self.sequence_names_list.item(i).text() for i in range(self.sequence_names_list.count())]:
            self.sequence_names_list.addItem(seq_name)

        # Записать в файл
        success = self.write_sequences_to_config()
        if success:
            self.add_terminal_message(f"💾 Последовательность '{seq_name}' сохранена", "info")
            self.statusBar().showMessage("Последовательности сохранены", 3000)

            # Перезагрузить конфиг для остальной части UI
            self.reload_config()

        self.validate_designer_items()

    def delete_selected_sequence_item(self):
        """Удаляет выбранный элемент из последовательности"""
        row = self.designer_sequence_list.currentRow()
        if row != -1:
            self.designer_sequence_list.takeItem(row)

        self.validate_designer_items()

    def write_sequences_to_config(self):
        """Перезаписывает секцию [sequences] в config.toml, сохраняя остальные секции"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
            if not os.path.exists(config_path):
                QMessageBox.warning(self, "Ошибка", f"Файл конфигурации не найден: {config_path}")
                return False

            with open(config_path, encoding="utf-8") as f:
                lines = f.readlines()

            start_idx = None
            end_idx = None
            for i, line in enumerate(lines):
                if line.strip().lower() == "[sequences]":
                    start_idx = i
                    # поиск конца секции
                    for j in range(i + 1, len(lines)):
                        if re.match(r"^\[.*\]", lines[j]) and lines[j].strip().lower() != "[sequences]":
                            end_idx = j
                            break
                    if end_idx is None:
                        end_idx = len(lines)
                    break

            if start_idx is None:
                # если секция не найдена, добавим в конец
                start_idx = len(lines)
                end_idx = len(lines)
                lines.append("\n")

            # Формируем новую секцию
            new_section_lines = ["[sequences]\n"]
            for seq, cmds in self.sequences.items():
                cmds_str = ", ".join([f'\"{c}\"' for c in cmds])
                new_section_lines.append(f"{seq} = [{cmds_str}]\n")

            # Заменяем старую секцию на новую
            updated_lines = lines[:start_idx] + new_section_lines + lines[end_idx:]

            with open(config_path, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

            return True
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))
            return False

    def is_wait_command(self, text: str) -> bool:
        return text.lower().startswith("wait")

    def is_sequence_name(self, text: str) -> bool:
        return text in self.sequences

    def style_command_item(self, item):
        """Окрашивает команды wait в оранжевый цвет для выделения"""
        if self.is_wait_command(item.text()):
            item.setForeground(QColor("#ffb86c"))  # оранжевый
        elif self.is_sequence_name(item.text()):
            item.setForeground(QColor("#568af2"))  # синий
        else:
            item.setForeground(QColor("#dce1ec"))  # стандартный

    def edit_wait_item(self, item):
        """Открывает диалог целочисленного ввода для команды wait"""
        if not self.is_wait_command(item.text()):
            return

        # Текущее значение (целое)
        parts = item.text().split()
        current_val = 1
        if len(parts) > 1:
            try:
                current_val = int(float(parts[1]))
            except ValueError:
                pass

        dlg = NumericPadDialog(current_val, self)
        if dlg.exec() == QDialog.Accepted:
            new_val = dlg.value()
            item.setText(f"wait {new_val}")
            self.style_command_item(item)

        self.validate_designer_items()

    def validate_designer_items(self):
        """Проверяет элементы последовательности и подсвечивает недействительные красным"""
        current_seq = self.get_current_sequence_name()

        for i in range(self.designer_sequence_list.count()):
            item = self.designer_sequence_list.item(i)

            # Начальная базовая стилизация
            self.style_command_item(item)

            text = item.text()

            # Особые проверки
            if self.is_wait_command(text):
                continue  # wait всегда валиден

            valid = False

            if text in self.buttons_config:  # команда
                valid = True
            elif text in self.sequences:  # последовательность
                if text != current_seq:
                    valid = True

            if not valid:
                # недействительная команда/последовательность или self recursion
                item.setForeground(QColor("#ff5555"))

    def get_current_sequence_name(self):
        item = self.sequence_names_list.currentItem() if hasattr(self, 'sequence_names_list') else None
        return item.text() if item else ""

    def create_new_sequence(self):
        """Создание новой последовательности"""
        new_name, ok = QInputDialog.getText(self, 'Имя новой последовательности', 'Введите имя новой последовательности:')
        if ok and new_name:
            if new_name not in self.sequences:
                self.sequences[new_name] = []
                self.sequence_names_list.addItem(new_name)
                self.add_terminal_message(f"🎉 Новая последовательность '{new_name}' создана", "info")
            else:
                QMessageBox.warning(self, "Ошибка", f"Последовательность '{new_name}' уже существует")

    def commit_and_push_changes(self):
        """Индексирует изменения, создаёт коммит и выполняет push.

        Использует сообщение из поля ввода. Все логи выводятся
        в область «Вывод команд» на странице прошивки.
        """

        # Получаем сообщение коммита
        commit_msg = self.commit_message_edit.text().strip() if hasattr(self, 'commit_message_edit') else ""

        if not commit_msg:
            QMessageBox.warning(self, "Ошибка", "Введите сообщение коммита")
            return

        try:
            repo_path = os.path.dirname(os.path.abspath(__file__))
            repo = git.Repo(repo_path)

            # Индексируем все изменения
            repo.git.add(all=True)

            # Проверяем есть ли что коммитить
            if not repo.is_dirty(untracked_files=True):
                self.add_firmware_message("ℹ️ Нет изменений для коммита", "info")
                return

            # Создаём коммит
            new_commit = repo.index.commit(commit_msg)
            self.add_firmware_message(f"✅ Создан коммит {new_commit.hexsha[:7]}", "response")

            # Push
            origin = repo.remotes.origin
            push_result = origin.push()

            # Отображаем результат push
            if push_result and push_result[0].flags & push_result[0].ERROR:
                self.add_firmware_message(f"❌ Ошибка push: {push_result[0].summary}", "error")
            else:
                self.add_firmware_message("⬆️ Изменения отправлены в удалённый репозиторий", "response")

            # Очищаем поле ввода и обновляем статус
            self.commit_message_edit.clear()
            self.check_git_status()

        except Exception as e:
            self.add_firmware_message(f"❌ Ошибка коммита/push: {str(e)}", "error")


class SequenceListWidget(QListWidget):
    """QListWidget с умным Drop: внешние перетаскивания копируются, внутренние – переносятся.
    После drop уведомляет родительское окно для повторной валидации."""

    def __init__(self, parent_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent_window = parent_window

    def dropEvent(self, event):
        # Если источник тот же виджет – перенос (Move), иначе – копирование
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
        else:
            event.setDropAction(Qt.CopyAction)

        super().dropEvent(event)

        # После изменений валидируем список
        if self._parent_window:
            self._parent_window.validate_designer_items()


class NumericPadDialog(QDialog):
    """Простой цифровой ввод с кнопками 0-9, ← и OK"""

    def __init__(self, initial_value: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введите число")
        self.setModal(True)
        self.setFixedSize(260, 320)

        layout = QVBoxLayout(self)

        # Поле ввода
        self.edit = QLineEdit(str(initial_value))
        self.edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit.setValidator(QIntValidator(0, 9999, self))
        self.edit.setFixedHeight(40)
        layout.addWidget(self.edit)

        # Сетка кнопок
        grid = QGridLayout()
        buttons = [
            "7", "8", "9",
            "4", "5", "6",
            "1", "2", "3",
            "←", "0", "OK",
        ]

        positions = [(i, j) for i in range(4) for j in range(3)]
        for pos, label in zip(positions, buttons):
            btn = QPushButton(label)
            btn.setFixedSize(60, 50)
            btn.clicked.connect(self.handle_button)
            grid.addWidget(btn, *pos)

        layout.addLayout(grid)

    def handle_button(self):
        label = self.sender().text()
        if label == "OK":
            if self.edit.text() == "":
                self.edit.setText("0")
            self.accept()
            return
        elif label == "←":
            self.edit.backspace()
        else:  # digit
            self.edit.insert(label)

    def value(self) -> int:
        text = self.edit.text()
        return int(text) if text.isdigit() else 0


# ---------------- Safe playsound helper ----------------

# Храним активные эффекты, чтобы их не удалил GC до завершения воспроизведения
_active_sounds: list[QSoundEffect] = []


def safe_playsound(path: str):  # type: ignore
    """Воспроизвести WAV/MP3 через QSoundEffect без блокировки UI.

    Файл допускается задавать относительным путём; он будет преобразован
    к абсолютному. Ошибки воспроизведения фиксируются в логах, но не
    мешают работе программы.
    """
    if not path:
        return

    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        logging.warning(f"Файл мелодии не найден: {abs_path}")
        return

    try:
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(abs_path))
        effect.setLoopCount(1)
        effect.setVolume(0.9)
        effect.play()

        _active_sounds.append(effect)

        # Очистим список по завершении звука
        def _cleanup():
            _active_sounds.remove(effect)

        effect.playingChanged.connect(lambda: None if effect.isPlaying() else _cleanup())

    except Exception as exc:  # noqa: BLE001
        logging.warning(f"Не удалось воспроизвести звук '{abs_path}': {exc}")


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
