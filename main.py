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
from PyQt5.QtCore import (
    Q_ARG,
    QMetaObject,
    QMutex,
    QThread,
    QTimer,
    QWaitCondition,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
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
)
from qt_material import apply_stylesheet

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
    # Создаем базовый logger, который выводит только в консоль
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.error(f"Не удалось настроить запись логов в файл: {str(e)}")

# Проверка возможности записи в файл логов
try:
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - TEST - Проверка доступа к файлу логов\n")
    logging.info(f"Файл логов доступен для записи: {LOG_FILE}")
except Exception as e:
    logging.error(f"Невозможно записать в файл логов {LOG_FILE}: {str(e)}")

# Темная тема в стиле QSS (на случай если qt-material не установлен)
DARK_STYLE = """
QWidget {
    background-color: #2D2D30;
    color: #FFFFFF;
    font-family: 'Segoe UI', Arial;
}

QMainWindow {
    background-color: #1E1E1E;
}

QGroupBox {
    border: 1px solid #3F3F46;
    border-radius: 6px;
    margin-top: 1em;
    font-weight: bold;
    color: #00A2E8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #0078D7;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1C90F3;
}

QPushButton:pressed {
    background-color: #0063B1;
}

QPushButton:disabled {
    background-color: #3F3F46;
    color: #9D9D9D;
}

QTextEdit {
    background-color: #252526;
    color: #E6E6E6;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    font-family: 'Courier New';
    selection-background-color: #264F78;
}

QComboBox {
    background-color: #333337;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    padding: 4px;
    min-width: 6em;
}

QComboBox:hover {
    border: 1px solid #007ACC;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left: 1px solid #3F3F46;
}

QSpinBox {
    background-color: #333337;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
    border-radius: 4px;
    padding: 4px;
}

QSpinBox:hover {
    border: 1px solid #007ACC;
}

QDialog {
    background-color: #252526;
}

QDialogButtonBox > QPushButton {
    min-width: 80px;
}

QMenu {
    background-color: #1E1E1E;
    color: #FFFFFF;
    border: 1px solid #3F3F46;
}

QMenu::item {
    padding: 6px 25px 6px 25px;
}

QMenu::item:selected {
    background-color: #007ACC;
}

QMenuBar {
    background-color: #1E1E1E;
    color: #FFFFFF;
}

QMenuBar::item {
    spacing: 5px;
    padding: 5px 10px;
    background: transparent;
}

QMenuBar::item:selected {
    background-color: #007ACC;
}
"""

# Светлая тема в стиле QSS
LIGHT_STYLE = """
QWidget {
    background-color: #F5F5F5;
    color: #212121;
    font-family: 'Segoe UI', Arial;
}

QMainWindow {
    background-color: #FFFFFF;
}

QGroupBox {
    border: 1px solid #BDBDBD;
    border-radius: 6px;
    margin-top: 1em;
    font-weight: bold;
    color: #0078D7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #0078D7;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1C90F3;
}

QPushButton:pressed {
    background-color: #0063B1;
}

QPushButton:disabled {
    background-color: #E0E0E0;
    color: #9E9E9E;
}

QTextEdit {
    background-color: #FFFFFF;
    color: #212121;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    font-family: 'Courier New';
    selection-background-color: #B3D7FF;
}

QComboBox {
    background-color: #FFFFFF;
    color: #212121;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 4px;
    min-width: 6em;
}

QComboBox:hover {
    border: 1px solid #0078D7;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left: 1px solid #BDBDBD;
}

QSpinBox {
    background-color: #FFFFFF;
    color: #212121;
    border: 1px solid #BDBDBD;
    border-radius: 4px;
    padding: 4px;
}

QSpinBox:hover {
    border: 1px solid #0078D7;
}

QDialog {
    background-color: #F5F5F5;
}

QDialogButtonBox > QPushButton {
    min-width: 80px;
}

QMenu {
    background-color: #FFFFFF;
    color: #212121;
    border: 1px solid #BDBDBD;
}

QMenu::item {
    padding: 6px 25px 6px 25px;
}

QMenu::item:selected {
    background-color: #E3F2FD;
}

QMenuBar {
    background-color: #F5F5F5;
    color: #212121;
}

QMenuBar::item {
    spacing: 5px;
    padding: 5px 10px;
    background: transparent;
}

QMenuBar::item:selected {
    background-color: #E3F2FD;
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
    'upload_port': ''  # Порт для загрузки прошивки
}

class SerialThread(QThread):
    """Поток для чтения данных с Serial порта"""
    data_received = pyqtSignal(str)

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


class SerialSettingsDialog(QDialog):
    """Диалог для настройки параметров Serial порта"""
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки Serial порта")
        self.settings = settings or {}

        # Список доступных портов
        self.port_combo = QComboBox()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports if ports else ["COM1", "COM2", "COM3"])

        # Скорость передачи
        self.baudrate_combo = QComboBox()
        baudrates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        self.baudrate_combo.addItems(baudrates)

        # Биты данных
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["5", "6", "7", "8"])

        # Четность
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N", "E", "O", "M", "S"])

        # Стоп-биты
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])

        # Таймаут
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(0, 10)
        self.timeout_spin.setSingleStep(1)

        # Установка значений из настроек
        self.set_values_from_settings()

        # Компоновка
        layout = QFormLayout()
        layout.addRow("Порт:", self.port_combo)
        layout.addRow("Скорость (бод):", self.baudrate_combo)
        layout.addRow("Биты данных:", self.bytesize_combo)
        layout.addRow("Четность:", self.parity_combo)
        layout.addRow("Стоп-биты:", self.stopbits_combo)
        layout.addRow("Таймаут (сек):", self.timeout_spin)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addWidget(buttons)

        self.setLayout(main_layout)

    def set_values_from_settings(self):
        """Установка значений из настроек"""
        if not self.settings:
            return

        # Установка порта
        port = self.settings.get('port', 'COM1')
        index = self.port_combo.findText(port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)

        # Установка скорости
        baudrate = str(self.settings.get('baudrate', 9600))
        index = self.baudrate_combo.findText(baudrate)
        if index >= 0:
            self.baudrate_combo.setCurrentIndex(index)

        # Установка битов данных
        bytesize = str(self.settings.get('bytesize', 8))
        index = self.bytesize_combo.findText(bytesize)
        if index >= 0:
            self.bytesize_combo.setCurrentIndex(index)

        # Установка четности
        parity = self.settings.get('parity', 'N')
        index = self.parity_combo.findText(parity)
        if index >= 0:
            self.parity_combo.setCurrentIndex(index)

        # Установка стоп-битов
        stopbits = str(self.settings.get('stopbits', 1))
        index = self.stopbits_combo.findText(stopbits)
        if index >= 0:
            self.stopbits_combo.setCurrentIndex(index)

        # Установка таймаута
        timeout = int(self.settings.get('timeout', 1))
        self.timeout_spin.setValue(timeout)

    def get_settings(self):
        """Получение настроек из диалога"""
        stopbits_map = {"1": 1, "1.5": 1.5, "2": 2}
        bytesize_map = {"5": 5, "6": 6, "7": 7, "8": 8}

        return {
            'port': self.port_combo.currentText(),
            'baudrate': int(self.baudrate_combo.currentText()),
            'bytesize': bytesize_map[self.bytesize_combo.currentText()],
            'parity': self.parity_combo.currentText(),
            'stopbits': stopbits_map[self.stopbits_combo.currentText()],
            'timeout': self.timeout_spin.value()
        }


class CommandSequenceThread(QThread):
    """Поток для выполнения последовательности команд с ожиданием ответов"""
    progress_updated = pyqtSignal(int, int)  # (текущий_шаг, всего_шагов)
    command_sent = pyqtSignal(str)
    response_received = pyqtSignal(str)
    sequence_finished = pyqtSignal(bool, str)  # (успешно, сообщение)

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Панель управления устройством")
        self.setMinimumSize(1000, 650)  # Увеличиваю начальные размеры окна

        # Инициализация переменных
        self.serial_port = None
        self.serial_thread = None
        self.command_sequence_thread = None
        self.buttons_config = {}
        self.button_groups = {}  # Группы кнопок, инициализируем пустым словарем
        self.sequence_commands = {}  # Для хранения последовательностей команд
        self.is_fullscreen = False  # Флаг для отслеживания полноэкранного режима

        # Загружаем сохраненные настройки Serial порта или используем значения по умолчанию
        self.serial_settings = self.load_serial_settings()

        # Загружаем настройки обновления
        self.update_settings = self.load_update_settings()

        self.dark_theme = True  # По умолчанию - темная тема

        # Создаем статусную строку
        self.status_bar = self.statusBar()

        # Создание меню
        self.create_menu()

        # Загрузка конфигурации
        self.load_config()

        # Настройка интерфейса
        self.setup_ui()

        # Применение темы
        self.apply_theme()

        # Переключаемся на страницу "Главное меню" (бывшая "Работа")
        self.switch_page("sequences")

        # Автоматическое подключение, если это указано в настройках
        if self.update_settings.get('auto_connect', True):
            QTimer.singleShot(1000, self.auto_connect)

        # Запуск таймера для проверки обновлений
        if self.update_settings.get('enable_auto_update', True):
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.check_for_updates)
            # Интервал проверки обновлений (в миллисекундах)
            interval = self.update_settings.get('update_check_interval', 3600) * 1000
            self.update_timer.start(interval)

            # Проверяем обновления при запуске
            QTimer.singleShot(5000, self.check_for_updates)

        # Запуск в полноэкранном режиме
        self.showFullScreen()
        self.is_fullscreen = True

        logging.info("Приложение запущено")

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
            self.status_bar.showMessage(f"Автоподключение к порту {port}", 3000)
        else:
            self.status_bar.showMessage(f"Не удалось автоматически подключиться: порт {port} недоступен", 5000)

    def check_for_updates(self):
        """Проверка наличия обновлений в репозитории"""
        if not self.update_settings.get('enable_auto_update', True):
            return

        repo_url = self.update_settings.get('repository_url', '')
        if not repo_url:
            return

        try:
            self.status_bar.showMessage("Проверка обновлений...", 3000)

            # Путь к текущей директории
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Проверяем, есть ли .git директория для определения локального репозитория
            is_git_repo = os.path.exists(os.path.join(current_dir, '.git'))

            if is_git_repo:
                # Если программа уже является git репозиторием, просто делаем pull
                self.update_from_existing_repo(current_dir)
            else:
                # Если программа не является git репозиторием, клонируем во временную директорию и копируем файлы
                self.update_from_remote_repo(repo_url, current_dir)

        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при проверке обновлений: {str(e)}", 5000)

    def update_from_existing_repo(self, repo_path):
        """Обновление существующего git репозитория"""
        try:
            repo = git.Repo(repo_path)

            # Сохраняем текущий хеш коммита
            current_commit = repo.head.commit.hexsha

            # Получаем изменения с удаленного репозитория
            origin = repo.remotes.origin
            origin.fetch()

            # Проверяем, есть ли изменения
            if current_commit != origin.refs.main.commit.hexsha:
                # Есть новые изменения
                result = QMessageBox.question(
                    self,
                    "Доступны обновления",
                    "Доступны обновления для программы. Обновить сейчас?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if result == QMessageBox.StandardButton.Yes:
                    # Выполняем pull
                    origin.pull()
                    self.status_bar.showMessage("Программа успешно обновлена. Требуется перезапуск.", 5000)

                    # Предлагаем пользователю перезапустить программу
                    restart_result = QMessageBox.question(
                        self,
                        "Требуется перезапуск",
                        "Для применения обновлений необходимо перезапустить программу. Перезапустить сейчас?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if restart_result == QMessageBox.StandardButton.Yes:
                        self.restart_application()
            else:
                self.status_bar.showMessage("Обновлений не найдено", 3000)

        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при обновлении: {str(e)}", 5000)

    def update_from_remote_repo(self, repo_url, target_dir):
        """Обновление из удаленного репозитория"""
        try:
            # Создаем временную директорию для клонирования
            temp_dir = tempfile.mkdtemp()

            # Клонируем репозиторий во временную директорию
            git.Repo.clone_from(repo_url, temp_dir)

            # Проверяем, есть ли новые файлы или изменения
            has_changes = False

            # Сравниваем файлы
            for root, _dirs, files in os.walk(temp_dir):
                for file in files:
                    # Пропускаем .git директорию
                    if '.git' in root:
                        continue

                    # Получаем относительный путь
                    rel_path = os.path.relpath(os.path.join(root, file), temp_dir)
                    target_file = os.path.join(target_dir, rel_path)
                    source_file = os.path.join(root, file)

                    # Проверяем существование и содержимое файла
                    if not os.path.exists(target_file):
                        has_changes = True
                        break

                    # Сравниваем содержимое файлов
                    with open(source_file, 'rb') as src, open(target_file, 'rb') as dst:
                        if src.read() != dst.read():
                            has_changes = True
                            break

            if has_changes:
                # Есть новые изменения
                result = QMessageBox.question(
                    self,
                    "Доступны обновления",
                    "Доступны обновления для программы. Обновить сейчас?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if result == QMessageBox.StandardButton.Yes:
                    # Копируем файлы из временной директории в целевую, исключая .git
                    for root, _dirs, files in os.walk(temp_dir):
                        # Пропускаем .git директорию
                        if '.git' in root:
                            continue

                        # Получаем относительный путь
                        rel_dir = os.path.relpath(root, temp_dir)
                        target_path = os.path.join(target_dir, rel_dir)

                        # Создаем директорию, если не существует
                        os.makedirs(target_path, exist_ok=True)

                        # Копируем файлы
                        for file in files:
                            source_file = os.path.join(root, file)
                            target_file = os.path.join(target_path, file)
                            shutil.copy2(source_file, target_file)

                    self.status_bar.showMessage("Программа успешно обновлена. Требуется перезапуск.", 5000)

                    # Предлагаем пользователю перезапустить программу
                    restart_result = QMessageBox.question(
                        self,
                        "Требуется перезапуск",
                        "Для применения обновлений необходимо перезапустить программу. Перезапустить сейчас?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if restart_result == QMessageBox.StandardButton.Yes:
                        self.restart_application()
            else:
                self.status_bar.showMessage("Обновлений не найдено", 3000)

            # Удаляем временную директорию
            shutil.rmtree(temp_dir)

        except Exception as e:
            self.status_bar.showMessage(f"Ошибка при обновлении: {str(e)}", 5000)

    def restart_application(self):
        """Перезапуск приложения"""
        # Сохраняем настройки перед перезапуском
        self.save_serial_settings()
        self.save_update_settings()

        # Получаем путь к python и текущему скрипту
        python = sys.executable
        script = os.path.abspath(__file__)

        # Отключаемся от устройства
        self.disconnect_serial()

        # Закрываем текущий экземпляр приложения
        QApplication.instance().quit()

        # Запускаем новый экземпляр
        os.execl(python, python, script)

    def load_serial_settings(self):
        """Загрузка сохраненных настроек Serial порта"""
        default_settings = {
            'port': 'COM1',
            'baudrate': 9600,
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

    def create_menu(self):
        """Создание меню приложения"""
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')

        # Действие "Перезагрузить конфигурацию"
        reload_config_action = QAction('Перезагрузить конфигурацию', self)
        reload_config_action.setShortcut('Ctrl+R')
        reload_config_action.setStatusTip('Перезагрузить конфигурацию из файла config.toml')
        reload_config_action.triggered.connect(self.reload_config)
        file_menu.addAction(reload_config_action)

        # Действие "Настройки соединения"
        settings_action = QAction('Настройки соединения', self)
        settings_action.setShortcut('Ctrl+P')
        settings_action.setStatusTip('Открыть диалог настроек соединения')
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        # Действие "Выход"
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Выйти из приложения')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Соединение"
        conn_menu = menubar.addMenu('Соединение')

        # Действие "Подключиться"
        self.connect_action = QAction('Подключиться', self)
        self.connect_action.setShortcut('Ctrl+K')
        self.connect_action.setStatusTip('Подключиться к устройству')
        self.connect_action.triggered.connect(self.connect_device)
        conn_menu.addAction(self.connect_action)

        # Действие "Отключиться"
        self.disconnect_action = QAction('Отключиться', self)
        self.disconnect_action.setShortcut('Ctrl+D')
        self.disconnect_action.setStatusTip('Отключиться от устройства')
        self.disconnect_action.triggered.connect(self.disconnect_device)
        self.disconnect_action.setEnabled(False)
        conn_menu.addAction(self.disconnect_action)

        # Меню "Вид"
        view_menu = menubar.addMenu("Вид")

        # Действие "Переключить тему"
        self.toggle_theme_action = QAction("Светлая тема", self)
        self.toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.toggle_theme_action)

        # Действие "Полноэкранный режим"
        self.toggle_fullscreen_action = QAction("Выйти из полноэкранного режима", self)
        self.toggle_fullscreen_action.setShortcut("F11")
        self.toggle_fullscreen_action.setStatusTip("Переключить полноэкранный режим")
        self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.toggle_fullscreen_action)

        # Меню "Помощь"
        help_menu = menubar.addMenu('Помощь')

        # Действие "О программе"
        about_action = QAction('О программе', self)
        about_action.setStatusTip('Информация о программе')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_config(self):
        """Загрузка конфигурации из TOML файла"""
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

            # Сначала попытаемся прочитать заголовки групп из файла
            self.button_groups = {}
            current_group = "Все команды"  # Группа по умолчанию
            self.button_groups[current_group] = []

            try:
                with open(config_path, encoding='utf-8') as f:
                    in_buttons_section = False
                    for line in f:
                        line = line.strip()

                        # Проверяем секцию
                        if line == "[buttons]":
                            in_buttons_section = True
                            continue
                        elif line.startswith("[") and line.endswith("]"):
                            in_buttons_section = False
                            continue

                        # Пропускаем строки не в секции [buttons]
                        if not in_buttons_section:
                            continue

                        # Если строка является комментарием с названием группы
                        if line.startswith('# ') and line != '# ':
                            current_group = line[2:]  # Удаляем '# ' из начала
                            if current_group not in self.button_groups:
                                self.button_groups[current_group] = []
                        # Если строка содержит определение кнопки
                        elif '=' in line and not line.startswith('[') and not line.startswith('#'):
                            # Разбираем строку кнопки
                            button_parts = line.split('=', 1)
                            if len(button_parts) == 2:
                                button_name = button_parts[0].strip()
                                # Удаляем кавычки, если они есть
                                if button_name.startswith('"') and button_name.endswith('"'):
                                    button_name = button_name[1:-1]

                                if button_name and not button_name.startswith('{'):
                                    self.button_groups[current_group].append(button_name)
            except Exception as e:
                print(f"Ошибка при чтении групп из файла: {e}")
                # В случае ошибки используем группу по умолчанию
                self.button_groups = {"Все команды": []}

            # Загружаем конфигурацию с помощью TOML парсера
            with open(config_path, 'rb') as f:
                config = tomli.load(f)

            # Загружаем конфигурацию кнопок
            if 'buttons' in config:
                self.buttons_config = config['buttons']

                # Если не удалось извлечь группы из комментариев,
                # добавляем все кнопки в группу по умолчанию
                if not any(self.button_groups.values()):
                    self.button_groups = {"Все команды": list(self.buttons_config.keys())}
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка конфигурации",
                    "В файле конфигурации отсутствует секция [buttons].\nБудет использована базовая конфигурация кнопок."
                )
                self.buttons_config = {}
                self.button_groups = {"Все команды": []}

            # Загружаем последовательности команд
            if 'sequences' in config:
                self.sequence_commands = config['sequences']
                # Создаем словарь для последовательностей, совместимый с интерфейсом
                self.sequences = {}
                for seq_name, steps_list in self.sequence_commands.items():
                    steps = []
                    for step in steps_list:
                        if isinstance(step, str):
                            # Если шаг задан как строка, проверяем, является ли это командой wait
                            if step.lower().startswith("wait"):
                                parts = step.split(None, 1)
                                if len(parts) == 2:
                                    try:
                                        wait_time = float(parts[1])
                                        steps.append({"wait": wait_time, "comment": f"Ожидание {wait_time} секунд"})
                                    except ValueError:
                                        steps.append({"command": step, "comment": ""})
                            else:
                                # Если это имя кнопки из buttons, используем соответствующую команду
                                command = None
                                for btn_name, cmd in self.buttons_config.items():
                                    if isinstance(cmd, str) and step == btn_name:
                                        command = cmd
                                        steps.append({"command": command, "comment": f"Кнопка {btn_name}"})
                                        break
                                # Если кнопка не найдена, используем как прямую команду
                                if command is None:
                                    steps.append({"command": step, "comment": ""})
                        elif isinstance(step, dict):
                            # Шаг уже в формате словаря
                            steps.append(step)

                    self.sequences[seq_name] = {
                        "description": f"Последовательность {seq_name}",
                        "steps": steps,
                        "filepath": config_path
                    }
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка конфигурации",
                    "В файле конфигурации отсутствует секция [sequences].\nПоследовательности команд будут недоступны."
                )
                self.sequence_commands = {}
                self.sequences = {}

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки конфигурации",
                f"Не удалось загрузить конфигурацию: {str(e)}"
            )
            self.buttons_config = {}
            self.sequence_commands = {}
            self.sequences = {}
            self.button_groups = {"Все команды": []}

    def create_default_config(self, config_path):
        """Создание файла конфигурации по умолчанию"""
        try:
            # Базовая конфигурация
            default_config = {
                'buttons': {
                    'MOTOR1_ON': {'command': 'MOTOR1 ON', 'comment': 'Включение мотора 1'},
                    'MOTOR1_OFF': {'command': 'MOTOR1 OFF', 'comment': 'Выключение мотора 1'},
                    'MOTOR2_ON': {'command': 'MOTOR2 ON', 'comment': 'Включение мотора 2'},
                    'MOTOR2_OFF': {'command': 'MOTOR2 OFF', 'comment': 'Выключение мотора 2'},
                    'VALVE1_ON': {'command': 'VALVE1 ON', 'comment': 'Открытие клапана 1'},
                    'VALVE1_OFF': {'command': 'VALVE1 OFF', 'comment': 'Закрытие клапана 1'},
                    'VALVE2_ON': {'command': 'VALVE2 ON', 'comment': 'Открытие клапана 2'},
                    'VALVE2_OFF': {'command': 'VALVE2 OFF', 'comment': 'Закрытие клапана 2'},
                    'PUMP_ON': {'command': 'PUMP ON', 'comment': 'Включение насоса'},
                    'PUMP_OFF': {'command': 'PUMP OFF', 'comment': 'Выключение насоса'}
                },
                'sequences': {
                    'coloring': [
                        {'command': 'Valve 1 ON', 'comment': 'Открытие клапана 1'},
                        {'wait': 2, 'comment': 'Ожидание 2 секунды'},
                        {'command': 'Pump ON', 'comment': 'Включение насоса'},
                        {'wait': 5, 'comment': 'Ожидание 5 секунд'},
                        {'command': 'Pump OFF', 'comment': 'Выключение насоса'},
                        {'command': 'Valve 1 OFF', 'comment': 'Закрытие клапана 1'}
                    ],
                    'precipitation': [
                        {'command': 'Valve 1 ON', 'comment': 'Открытие клапана 1'},
                        {'wait': 2, 'comment': 'Ожидание 2 секунды'},
                        {'command': 'Pump ON', 'comment': 'Включение насоса'},
                        {'wait': 10, 'comment': 'Ожидание 10 секунд'},
                        {'command': 'Pump OFF', 'comment': 'Выключение насоса'},
                        {'command': 'Valve 1 OFF', 'comment': 'Закрытие клапана 1'}
                    ],
                    'washing': [
                        {'command': 'Valve 2 ON', 'comment': 'Открытие клапана 2'},
                        {'wait': 2, 'comment': 'Ожидание 2 секунды'},
                        {'command': 'Pump ON', 'comment': 'Включение насоса'},
                        {'wait': 15, 'comment': 'Ожидание 15 секунд'},
                        {'command': 'Pump OFF', 'comment': 'Выключение насоса'},
                        {'command': 'Valve 2 OFF', 'comment': 'Закрытие клапана 2'}
                    ]
                }
            }

            # Определяем группы кнопок
            button_groups = {
                "Двигатели": ["MOTOR1_ON", "MOTOR1_OFF", "MOTOR2_ON", "MOTOR2_OFF"],
                "Клапаны": ["VALVE1_ON", "VALVE1_OFF", "VALVE2_ON", "VALVE2_OFF"],
                "Насосы": ["PUMP_ON", "PUMP_OFF"]
            }
            self.button_groups = button_groups  # Сохраняем группы и для текущего экземпляра

            # Сохраняем конфигурацию в виде строки в формате TOML
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write("[buttons]\n")

                # Записываем кнопки по группам
                for group_name, button_names in button_groups.items():
                    f.write(f"\n# {group_name}\n")  # Добавляем комментарий с названием группы
                    for btn_name in button_names:
                        btn_data = default_config['buttons'][btn_name]
                        f.write(f'{btn_name} = {{ command = "{btn_data["command"]}", comment = "{btn_data["comment"]}" }}\n')

                f.write("\n[sequences]\n")
                # Секция [sequences]
                for seq_name, seq_steps in default_config['sequences'].items():
                    f.write(f"\n# Последовательность {seq_name}\n")
                    f.write(f"{seq_name} = [\n")
                    for step in seq_steps:
                        if 'command' in step:
                            f.write(f'    {{ command = "{step["command"]}", comment = "{step["comment"]}" }},\n')
                        elif 'wait' in step:
                            f.write(f'    {{ wait = {step["wait"]}, comment = "{step["comment"]}" }},\n')
                    f.write("]\n")

            return default_config
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка создания конфигурации",
                f"Не удалось создать файл конфигурации: {str(e)}"
            )
            return {}

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Программа управления стендом")
        self.resize(1200, 800)

        # Создаем статус-бар
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готов к работе")

        # Создаем основное меню
        self.create_menu()

        # Создаем основной виджет и компоновку
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Создаем разделитель для левой и правой панелей
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # Создаем левую панель
        left_panel = QWidget()
        left_layout = QHBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Создаем боковую панель с кнопками
        self.setup_sidebar()

        # Добавляем боковую панель в левую панель
        left_layout.addWidget(self.sidebar)

        # Добавляем стек виджетов в левую панель
        left_layout.addWidget(self.stacked_widget)

        # Настраиваем страницу команд (создание вкладок и кнопок)
        # Создаем вертикальный макет для страницы команд
        commands_layout = QVBoxLayout(self.commands_page)
        commands_layout.setContentsMargins(10, 10, 10, 10)
        commands_layout.setSpacing(10)

        # Создаем таблицу команд вместо вкладок
        commands_group = QGroupBox("Команды управления")
        commands_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3F51B5;
                border-radius: 8px;
                margin-top: 1em;
                font-weight: bold;
                color: #3F51B5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: palette(window);
            }
        """)
        commands_group_layout = QVBoxLayout(commands_group)

        # Создаем прокручиваемую область для команд
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        command_container = QWidget()
        container_layout = QVBoxLayout(command_container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(10)

        # Создаем таблицу для команд
        self.commands_table = QTableWidget()
        self.commands_table.setColumnCount(6)  # 6 колонок для кнопок (больше кнопок в строке)
        self.commands_table.horizontalHeader().setVisible(False)  # Скрываем горизонтальные заголовки
        self.commands_table.verticalHeader().setVisible(False)  # Скрываем вертикальные заголовки
        self.commands_table.setShowGrid(False)  # Скрываем сетку
        self.commands_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Определяем общее количество команд и групп
        total_rows = 0
        for _group_name, button_names in self.button_groups.items():
            if not button_names:  # Пропускаем пустые группы
                continue
            # +1 для заголовка группы и +1 для пустой строки после группы
            total_rows += 1 + (len(button_names) + 5) // 6 + 1  # 6 кнопок в строке

        self.commands_table.setRowCount(total_rows)

        # Добавляем команды в таблицу
        current_row = 0
        for group_name, button_names in self.button_groups.items():
            if not button_names:  # Пропускаем пустые группы
                continue

            # Добавляем заголовок группы
            group_label = QLabel(group_name)
            group_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #3F51B5;")
            group_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.commands_table.setSpan(current_row, 0, 1, 6)  # Объединяем ячейки для заголовка (6 колонок)
            self.commands_table.setCellWidget(current_row, 0, group_label)
            current_row += 1

            # Добавляем кнопки в сетку
            col = 0
            for button_name in button_names:
                if button_name not in self.buttons_config:
                    continue

                button_data = self.buttons_config[button_name]

                # Проверяем тип button_data и получаем command и comment соответственно
                if isinstance(button_data, dict):
                    command = button_data.get('command', '')
                    comment = button_data.get('comment', '')
                elif isinstance(button_data, str):
                    command = button_data
                    comment = f"Команда: {command}"
                else:
                    # Пропускаем, если button_data неизвестного типа
                    continue

                # Создаем кнопку с меньшими размерами
                btn = QPushButton(button_name)
                btn.setMinimumSize(100, 40)
                btn.setMaximumSize(180, 40)
                btn.setFont(QFont("Segoe UI", 12))  # Уменьшаем шрифт

                # Настройка стиля кнопки в зависимости от группы
                if "двигател" in group_name.lower():
                    color = "#4CAF50"  # Зеленый для двигателей
                elif "клапан" in group_name.lower():
                    color = "#2196F3"  # Синий для клапанов
                elif "насос" in group_name.lower():
                    color = "#FFC107"  # Желтый для насосов
                else:
                    color = "#9C27B0"  # Фиолетовый для остальных

                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: white;
                        border: 1px solid #333333;
                        border-radius: 4px;
                        font-weight: bold;
                        padding: 2px;
                        text-align: center;
                    }}
                    QPushButton:hover {{
                        background-color: {color}CC;
                        border: 1px solid #555555;
                    }}
                    QPushButton:pressed {{
                        background-color: {color}99;
                        border: 1px solid #777777;
                    }}
                """)

                # Настройка тултипа с комментарием
                if comment:
                    btn.setToolTip(comment)

                # Подключение обработчика нажатия
                btn.clicked.connect(lambda checked, cmd=command: self.send_command(cmd))

                # Добавление кнопки в таблицу
                self.commands_table.setCellWidget(current_row, col, btn)

                # Перемещение к следующей позиции в сетке
                col += 1
                if col >= 6:  # Максимум 6 кнопок в строке
                    col = 0
                    current_row += 1

            # Если есть неполная строка, переходим к следующей
            if col > 0:
                current_row += 1

            # Добавляем пустую строку после группы
            current_row += 1

        # Устанавливаем высоту строк
        for row in range(self.commands_table.rowCount()):
            self.commands_table.setRowHeight(row, 42)  # Уменьшаем высоту строк

        container_layout.addWidget(self.commands_table)

        # Добавляем контейнер в scroll area
        scroll.setWidget(command_container)

        # Добавляем scroll area в группу
        commands_group_layout.addWidget(scroll)

        # Добавляем группу на страницу команд
        commands_layout.addWidget(commands_group)

        # Правая панель с терминалом и управлением
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # Настройки соединения
        conn_group = QGroupBox("Соединение")
        conn_layout = QHBoxLayout(conn_group)
        conn_layout.setSpacing(10)

        # Добавляем метку для отображения статуса
        self.status_label = QLabel("Статус: Отключено")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")

        # Создаем кнопки для управления соединением
        self.connect_button = QPushButton("Подключиться")
        self.connect_button.setMinimumSize(110, 36)
        self.connect_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_button.clicked.connect(self.toggle_connection)

        self.settings_button = QPushButton("Настройки")
        self.settings_button.setMinimumSize(110, 36)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.clicked.connect(self.show_settings_dialog)

        # Добавляем кнопку для загрузки прошивки
        self.upload_firmware_button = QPushButton("Загрузить прошивку")
        self.upload_firmware_button.setMinimumSize(150, 36)
        self.upload_firmware_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_firmware_button.clicked.connect(self.upload_firmware)
        self.upload_firmware_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: 2px solid #2E7D32;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
                border: 2px solid #388E3C;
            }
            QPushButton:pressed {
                background-color: #43A047;
                border: 2px solid #2E7D32;
            }
            QPushButton:disabled {
                background-color: #A5D6A7;
                color: #E8F5E9;
                border: 2px solid #81C784;
            }
        """)

        conn_layout.addWidget(self.status_label)
        conn_layout.addStretch()
        conn_layout.addWidget(self.connect_button)
        conn_layout.addWidget(self.settings_button)
        conn_layout.addWidget(self.upload_firmware_button)

        right_layout.addWidget(conn_group)

        # Терминал
        terminal_group = QGroupBox("Терминал")
        terminal_layout = QVBoxLayout(terminal_group)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFont(QFont("Consolas", 9))
        self.terminal.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Добавляем кнопку очистки терминала
        clear_btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Очистить терминал")
        clear_btn.setMaximumWidth(150)
        clear_btn.clicked.connect(self.clear_terminal)
        clear_btn_layout.addStretch()
        clear_btn_layout.addWidget(clear_btn)

        terminal_layout.addWidget(self.terminal)
        terminal_layout.addLayout(clear_btn_layout)

        right_layout.addWidget(terminal_group, 1)  # 1 - stretch factor

        # Поле ввода и кнопка отправки
        input_group = QGroupBox("Отправка команды")
        input_layout = QHBoxLayout(input_group)

        self.command_input = QComboBox()
        self.command_input.setEditable(True)
        self.command_input.setMinimumWidth(120)  # Уменьшаем минимальную ширину
        self.command_input.setMaximumWidth(300)  # Ограничиваем максимальную ширину
        self.command_input.lineEdit().setPlaceholderText("Введите команду...")

        self.send_button = QPushButton("Отправить")
        self.send_button.setMinimumSize(100, 32)
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self.send_manual_command)

        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.send_button)

        right_layout.addWidget(input_group)

        # Добавляем панели в разделитель
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)

        # Устанавливаем начальные размеры в соотношении 7:1 (уменьшаем ширину правой панели в 2 раза)
        total_width = self.width()
        self.splitter.setSizes([int(total_width * 4/5), int(total_width * 1/5)])

        # Устанавливаем максимальную ширину для правой панели
        right_panel.setMaximumWidth(300)

        # Добавляем разделитель в основную компоновку
        main_layout.addWidget(self.splitter)

        # Устанавливаем основной виджет
        self.setCentralWidget(main_widget)

        # Обновляем интерфейс в зависимости от состояния подключения
        self.update_ui_connection_state(False)

    def apply_theme(self):
        """Применение текущей темы"""
        try:
            # Пробуем использовать qt-material
            theme = 'dark_blue' if self.dark_theme else 'light_blue'
            apply_stylesheet(self.app, theme=theme)
            self.toggle_theme_action.setText("Светлая тема" if self.dark_theme else "Темная тема")
        except Exception:
            # Если qt-material не установлен, используем собственные QSS стили
            app = QApplication.instance()
            if self.dark_theme:
                app.setStyleSheet(DARK_STYLE)
                self.toggle_theme_action.setText("Светлая тема")
            else:
                app.setStyleSheet(LIGHT_STYLE)
                self.toggle_theme_action.setText("Темная тема")

    def toggle_theme(self):
        """Переключение между светлой и темной темой"""
        self.dark_theme = not self.dark_theme
        self.apply_theme()

    def update_ui_connection_state(self, connected):
        """Обновление интерфейса в соответствии с состоянием подключения"""
        if connected:
            # Обновляем кнопку подключения
            self.connect_button.setText("Отключиться")
            self.connect_button.setStyleSheet("background-color: #D32F2F; color: white;")
            self.settings_button.setEnabled(False)

            # Обновляем статус
            self.status_label.setText(f"Статус: Подключено ({self.serial_settings.get('port', 'COM?')})")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            # Добавляем сообщение в терминал
            self.terminal.append("<span style='color:#4CAF50;'>--- Подключено к порту " +
                                self.serial_settings.get('port', 'COM?') + " ---</span>")

            # Обновляем действия меню
            if hasattr(self, 'connect_action'):
                self.connect_action.setEnabled(False)
            if hasattr(self, 'disconnect_action'):
                self.disconnect_action.setEnabled(True)
        else:
            # Обновляем кнопку подключения
            self.connect_button.setText("Подключиться")
            self.connect_button.setStyleSheet("")  # Возвращаем стиль по умолчанию
            self.settings_button.setEnabled(True)

            # Обновляем статус
            self.status_label.setText("Статус: Отключено")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")

            # Добавляем сообщение в терминал, если было подключение
            if self.serial_port and not self.serial_port.is_open:
                self.terminal.append("<span style='color:#F44336;'>--- Отключено ---</span>")

            # Обновляем действия меню
            if hasattr(self, 'connect_action'):
                self.connect_action.setEnabled(True)
            if hasattr(self, 'disconnect_action'):
                self.disconnect_action.setEnabled(False)

    def show_settings_dialog(self):
        """Показать диалог настроек Serial порта"""
        dialog = SerialSettingsDialog(self, self.serial_settings)
        if dialog.exec():
            self.serial_settings = dialog.get_settings()
            # Сохраняем настройки после изменения
            self.save_serial_settings()

    def toggle_connection(self):
        """Переключение состояния подключения"""
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """Подключение к Serial порту"""
        try:
            # Создание объекта Serial с параметрами из настроек
            self.serial_port = serial.Serial(
                port=self.serial_settings.get('port', 'COM1'),
                baudrate=self.serial_settings.get('baudrate', 9600),
                bytesize=self.serial_settings.get('bytesize', 8),
                parity=self.serial_settings.get('parity', 'N'),
                stopbits=self.serial_settings.get('stopbits', 1),
                timeout=self.serial_settings.get('timeout', 1)
            )

            # Создание и запуск потока для чтения данных
            self.serial_thread = SerialThread(self.serial_port)
            self.serial_thread.data_received.connect(self.on_data_received)
            self.serial_thread.start()

            self.update_ui_connection_state(True)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                f"Не удалось подключиться к порту: {str(e)}"
            )

    def disconnect_serial(self):
        """Отключение от Serial порта"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.update_ui_connection_state(False)

    @pyqtSlot(str)
    def on_data_received(self, data):
        """Обработка полученных данных"""
        message = f"<span style='color:#2196F3;'>&lt;&lt; {data}</span>"
        self.terminal.append(message)

        # Также выводим сообщение в терминал на вкладке "Работа"
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.append(message)

        self.terminal.ensureCursorVisible()
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.ensureCursorVisible()

        # Передаем полученный ответ в поток выполнения последовательности
        if self.command_sequence_thread and self.command_sequence_thread.isRunning():
            self.command_sequence_thread.add_response(data)

    def send_command(self, command):
        """Отправка команды через Serial порт"""
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(
                self,
                "Нет подключения",
                "Необходимо сначала подключиться к устройству."
            )
            return

        try:
            # Добавление символа новой строки к команде
            full_command = command + '\n'
            self.serial_port.write(full_command.encode('utf-8'))

            message = f"<span style='color:#FF9800;'>&gt;&gt; {command}</span>"
            self.terminal.append(message)

            # Также выводим сообщение в терминал на вкладке "Работа"
            if hasattr(self, 'sequence_terminal'):
                self.sequence_terminal.append(message)

            self.terminal.ensureCursorVisible()
            if hasattr(self, 'sequence_terminal'):
                self.sequence_terminal.ensureCursorVisible()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка отправки",
                f"Не удалось отправить команду: {str(e)}"
            )

    def send_manual_command(self):
        """Отправка команды, введенной пользователем вручную"""
        command = self.command_input.currentText().strip()
        if command:
            self.send_command(command)

            # Добавление команды в историю, если её там еще нет
            if self.command_input.findText(command) == -1:
                self.command_input.addItem(command)

            # Очистка текущего ввода
            self.command_input.setCurrentText("")

    def show_about(self):
        """Показать диалог "О программе\""""
        QMessageBox.about(
            self,
            "О программе",
            "<h2>Панель управления Serial</h2>"
            "<p>Версия 1.0</p>"
            "<p>Приложение для отправки команд на устройства через Serial-порт.</p>"
            "<p>© 2024 Все права защищены</p>"
        )

    def clear_terminal(self):
        """Очистка содержимого терминала"""
        self.terminal.clear()

        # Также очищаем терминал на вкладке "Работа"
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.clear()

        message = "<span style='color:#9E9E9E;'>--- Терминал очищен ---</span>"
        self.terminal.append(message)

        # Также выводим сообщение в терминал на вкладке "Работа"
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.append(message)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.disconnect_serial()

        # Сохраняем настройки Serial порта перед закрытием
        self.save_serial_settings()

        event.accept()

    def reload_config(self):
        """Перезагрузка конфигурации и обновление интерфейса"""
        try:
            # Сохраняем текущую вкладку для восстановления
            current_page = None
            # Сохраняем текущие размеры слайдера
            splitter_sizes = None

            if hasattr(self, 'centralWidget'):
                # Ищем QStackedWidget в текущем интерфейсе
                if hasattr(self, 'stacked_widget'):
                    current_page = self.stacked_widget.currentIndex()

                # Ищем QSplitter
                splitter = self.centralWidget().findChild(QSplitter)
                if splitter:
                    # Сохраняем общую ширину
                    splitter_sizes = sum(splitter.sizes())

            # Очищаем текущие конфигурации
            self.buttons_config = {}
            self.button_groups = {}
            self.sequence_commands = {}

            # Загружаем новые конфигурации
            self.load_config()

            # Удаляем текущий центральный виджет
            if hasattr(self, 'centralWidget'):
                current_widget = self.centralWidget()
                self.setCentralWidget(None)
                if current_widget:
                    current_widget.deleteLater()

            # Очищаем список кнопок категорий и страниц
            self.category_buttons = []
            self.category_pages = {}

            # Пересоздаем интерфейс
            self.setup_ui()

            # Восстанавливаем текущую страницу
            if current_page is not None and hasattr(self, 'stacked_widget'):
                if current_page < self.stacked_widget.count():
                    self.stacked_widget.setCurrentIndex(current_page)
                    # Отмечаем соответствующую кнопку в боковом меню
                    if current_page < len(self.category_buttons):
                        self.category_buttons[current_page].setChecked(True)

            # Восстанавливаем размеры слайдера
            if splitter_sizes:
                splitter = self.centralWidget().findChild(QSplitter)
                if splitter:
                    # Устанавливаем размеры в соотношении 2:1
                    splitter.setSizes([int(splitter_sizes * 2/3), int(splitter_sizes * 1/3)])

            # Обновляем состояние подключения в интерфейсе
            is_connected = hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open
            self.update_ui_connection_state(is_connected)

            # Добавляем сообщение в терминал
            self.terminal.append("<span style='color:#4CAF50;'>--- Конфигурация перезагружена ---</span>")

            # Выводим сообщение в статусной строке
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("Конфигурация успешно обновлена", 3000)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка перезагрузки",
                f"Не удалось перезагрузить конфигурацию: {str(e)}"
            )

    def show_connection_settings(self):
        """Показать диалог настроек соединения"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки соединения")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # COM-порт
        port_layout = QHBoxLayout()
        port_combo = QComboBox()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        port_combo.addItems(ports)

        # Если порт из конфигурации есть в списке, выбираем его
        current_port = self.serial_settings.get('port', '')
        if current_port in ports:
            port_combo.setCurrentText(current_port)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(lambda: self.refresh_ports(port_combo))
        port_layout.addWidget(port_combo, 1)
        port_layout.addWidget(refresh_button, 0)
        form_layout.addRow("COM-порт:", port_layout)

        # Скорость
        baud_combo = QComboBox()
        baud_rates = ["9600", "19200", "38400", "57600", "115200"]
        baud_combo.addItems(baud_rates)
        baud_combo.setCurrentText(str(self.serial_settings.get('baudrate', 9600)))
        form_layout.addRow("Скорость:", baud_combo)

        # Биты данных
        data_bits_combo = QComboBox()
        data_bits_combo.addItems(["5", "6", "7", "8"])
        data_bits_combo.setCurrentText(str(self.serial_settings.get('bytesize', 8)))
        form_layout.addRow("Биты данных:", data_bits_combo)

        # Четность
        parity_combo = QComboBox()
        parity_options = {
            "N": "Нет",
            "E": "Четный (Even)",
            "O": "Нечетный (Odd)",
            "M": "Маркер (Mark)",
            "S": "Пробел (Space)"
        }
        parity_combo.addItems(parity_options.values())
        current_parity = self.serial_settings.get('parity', 'N')
        for code, name in parity_options.items():
            if code == current_parity:
                parity_combo.setCurrentText(name)
                break
        form_layout.addRow("Четность:", parity_combo)

        # Стоповые биты
        stop_bits_combo = QComboBox()
        stop_bits_options = {"1": "1", "1.5": "1.5", "2": "2"}
        stop_bits_combo.addItems(stop_bits_options.values())
        current_stop_bits = self.serial_settings.get('stopbits', 1)
        for code, name in stop_bits_options.items():
            if float(code) == float(current_stop_bits):
                stop_bits_combo.setCurrentText(name)
                break
        form_layout.addRow("Стоповые биты:", stop_bits_combo)

        # Таймаут чтения
        timeout_spin = QSpinBox()
        timeout_spin.setRange(0, 10000)
        timeout_spin.setValue(self.serial_settings.get('timeout', 1000))
        timeout_spin.setSuffix(" мс")
        form_layout.addRow("Таймаут чтения:", timeout_spin)

        layout.addLayout(form_layout)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Получаем коды для четности и стоповых бит
            parity_code = 'N'
            for code, name in parity_options.items():
                if name == parity_combo.currentText():
                    parity_code = code
                    break

            stop_bits_code = 1
            for code, name in stop_bits_options.items():
                if name == stop_bits_combo.currentText():
                    stop_bits_code = float(code)
                    break

            # Обновляем настройки
            self.serial_settings = {
                'port': port_combo.currentText(),
                'baudrate': int(baud_combo.currentText()),
                'bytesize': int(data_bits_combo.currentText()),
                'parity': parity_code,
                'stopbits': stop_bits_code,
                'timeout': timeout_spin.value()
            }

            # Если порт подключен, отключаем его и переподключаем с новыми настройками
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                self.disconnect_device()
                self.connect_device()

    def refresh_ports(self, combo_box):
        """Обновление списка доступных COM-портов"""
        combo_box.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        combo_box.addItems(ports)

    def connect_device(self):
        """Подключение к устройству"""
        self.connect_serial()

    def disconnect_device(self):
        """Отключение от устройства"""
        self.disconnect_serial()

    def switch_page(self, page_name):
        """Переключение между страницами"""
        # Проверяем, что self.category_buttons является словарем
        if isinstance(self.category_buttons, dict):
            # Выделяем только активную кнопку
            for name, button in self.category_buttons.items():
                button.setChecked(name == page_name)

            # Переключаемся на выбранную страницу
            if page_name in self.category_pages:
                self.stacked_widget.setCurrentWidget(self.category_pages[page_name])
        else:
            # Если это список, просто переключаем страницу по имени
            page_index = -1
            for _i, (name, idx) in enumerate(self.category_pages.items()):
                if name == page_name:
                    page_index = idx
                    break

            if page_index >= 0:
                self.stacked_widget.setCurrentIndex(page_index)
                # Обновляем состояние кнопок
                for i, btn in enumerate(self.category_buttons):
                    btn.setChecked(i == page_index)

    def maintain_splitter_ratio(self, pos, index):
        """Обработчик изменения размеров слайдера"""
        # Получаем текущие размеры слайдера
        splitter = self.centralWidget().findChild(QSplitter)
        # Принудительно устанавливаем размеры в соотношении 2:1
        total_width = sum(splitter.sizes())
        splitter.setSizes([int(total_width * 2/3), int(total_width * 1/3)])

    def start_sequence(self, sequence_type):
        """Запуск последовательности команд"""
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(
                self,
                "Нет подключения",
                "Необходимо сначала подключиться к устройству."
            )
            return

        # Проверяем, есть ли уже запущенная последовательность
        if hasattr(self, 'command_sequence_thread') and self.command_sequence_thread and self.command_sequence_thread.isRunning():
            QMessageBox.warning(
                self,
                "Последовательность уже запущена",
                "Дождитесь завершения текущей последовательности или остановите её."
            )
            return

        # Получаем список команд для указанного типа последовательности
        commands = self.sequence_commands.get(sequence_type, [])
        if not commands:
            QMessageBox.warning(
                self,
                "Последовательность не найдена",
                f"В конфигурации не найдена последовательность команд для типа '{sequence_type}'."
            )
            return

        # Преобразуем команды в формат для отправки
        send_commands = []
        for item in commands:
            if isinstance(item, str):
                # Если элемент - строка
                if item.lower().startswith("wait"):
                    # Это команда ожидания, оставляем как есть
                    send_commands.append(item)
                else:
                    # Это имя кнопки, получаем соответствующую команду
                    command = None
                    for btn_name, cmd in self.buttons_config.items():
                        if isinstance(cmd, str) and item == btn_name:
                            command = cmd
                            break

                    # Если кнопка не найдена, используем как прямую команду
                    send_commands.append(command if command else item)
            elif isinstance(item, dict) and 'command' in item:
                # Если элемент - словарь с командой
                send_commands.append(item['command'])

        # Создаем и запускаем поток выполнения последовательности
        self.command_sequence_thread = CommandSequenceThread(self.serial_port, send_commands)
        self.command_sequence_thread.progress_updated.connect(self.on_progress_updated)
        self.command_sequence_thread.command_sent.connect(self.on_sequence_command_sent)
        self.command_sequence_thread.response_received.connect(self.on_sequence_response_received)
        self.command_sequence_thread.sequence_finished.connect(self.on_sequence_finished)
        self.command_sequence_thread.start()

        # Обновляем интерфейс
        # Отключаем все кнопки последовательностей
        for btn in self.sequence_buttons:
            btn.setEnabled(False)

        # Активируем кнопку остановки
        self.stop_sequence_button.setEnabled(True)

        # Настраиваем прогресс-бар
        self.sequence_progress.setMaximum(len(send_commands))
        self.sequence_progress.setValue(0)

        # Выводим сообщение о начале выполнения
        sequence_name = sequence_type
        # Обновляем информацию о текущей последовательности
        self.current_sequence_name.setText(f"Выполняется: {sequence_name}")
        self.sequence_info.setText(f"Запущена последовательность {sequence_name}")
        self.sequence_info.setStyleSheet("font-weight: bold; color: #2196F3;")

        # Выводим сообщение в терминал
        message = f"<span style='color:#4CAF50;'>--- Запущена последовательность: {sequence_name} ---</span>"
        if hasattr(self, 'terminal'):
            self.terminal.append(message)

        # Выводим сообщение в терминал на вкладке "Работа"
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.append(message)

        # Обновляем статусную строку
        self.status_bar.showMessage(f"Запущена последовательность '{sequence_name}'", 3000)

    def stop_sequence(self):
        """Остановка выполнения текущей последовательности"""
        if hasattr(self, 'sequence_thread') and self.sequence_thread and self.sequence_thread.isRunning():
            self.sequence_thread.stop()

            # Обновляем информацию в интерфейсе если есть sequence_details
            if hasattr(self, 'sequence_details'):
                self.sequence_details.append("<p><span style='color: red; font-weight: bold;'>Выполнение последовательности остановлено пользователем</span></p>")

            # Деактивируем кнопки управления
            if hasattr(self, 'stop_sequence_button'):
                self.stop_sequence_button.setEnabled(False)

            # Разблокируем кнопки последовательностей
            for btn in self.sequence_buttons:
                btn.setEnabled(True)

            # Обновляем статусную строку
            self.status_bar.showMessage("Выполнение последовательности остановлено", 3000)

    def on_sequence_completed(self, sequence_name, success):
        """Обработка завершения последовательности команд"""
        # Обновляем статус
        status_text = "завершена успешно" if success else "завершена с ошибками"

        # Проверяем существование атрибута перед использованием
        if hasattr(self, 'sequence_status_label'):
            self.sequence_status_label.setText(f"Последовательность {sequence_name} {status_text}")

        # Разблокируем кнопки последовательностей
        for btn in self.sequence_buttons:
            btn.setEnabled(True)

        # Деактивируем кнопки управления
        # Проверяем существование атрибутов перед использованием
        if hasattr(self, 'stop_sequence_button'):
            self.stop_sequence_button.setEnabled(False)

        # Сбрасываем текущую последовательность
        if hasattr(self, 'current_sequence_name'):
            self.current_sequence_name.setText("Нет активной последовательности")

        # Обновляем статусную строку
        message = f"Последовательность '{sequence_name}' {status_text}"
        self.status_bar.showMessage(message, 5000)

    def on_sequence_command_sent(self, command):
        """Обработка отправки команды в последовательности"""
        message = f"<span style='color:#FF9800;'>&gt;&gt; {command}</span>"
        self.terminal.append(message)

        # Также выводим сообщение в терминал на вкладке "Работа"
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.append(message)

        self.terminal.ensureCursorVisible()
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.ensureCursorVisible()

    def on_progress_updated(self, current_step, total_steps):
        """Обработчик сигнала обновления прогресса от CommandSequenceThread"""
        # Обновляем только прогресс-бар
        if hasattr(self, 'sequence_progress'):
            self.sequence_progress.setValue(current_step)

        # Выводим базовую информацию в терминал
        if hasattr(self, 'terminal'):
            self.terminal.append(f"<span style='color:#888;'>[Шаг {current_step}/{total_steps}]</span>")
            self.terminal.ensureCursorVisible()

        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.append(f"<span style='color:#888;'>[Шаг {current_step}/{total_steps}]</span>")
            self.sequence_terminal.ensureCursorVisible()

    @pyqtSlot(str)
    def on_sequence_response_received(self, response):
        """Обработка ответа в последовательности"""
        # Этот метод вызывается из потока выполнения последовательности,
        # ответы уже выводятся в terminal через on_data_received
        pass

    @pyqtSlot(bool, str)
    def on_sequence_finished(self, success, message):
        """Обработка завершения выполнения последовательности"""
        # Обновляем интерфейс
        # Разблокируем кнопки последовательностей
        for btn in self.sequence_buttons:
            btn.setEnabled(True)

        # Деактивируем кнопку остановки
        self.stop_sequence_button.setEnabled(False)

        # Обновляем информацию о статусе
        if success:
            self.sequence_info.setText("Последовательность успешно завершена")
            self.sequence_info.setStyleSheet("font-weight: bold; color: #4CAF50;")

            terminal_message = f"<span style='color:#4CAF50;'>--- {message} ---</span>"
            if hasattr(self, 'terminal'):
                self.terminal.append(terminal_message)

            # Также выводим сообщение в терминал на вкладке "Работа"
            if hasattr(self, 'sequence_terminal'):
                self.sequence_terminal.append(terminal_message)
        else:
            self.sequence_info.setText(f"Ошибка: {message}")
            self.sequence_info.setStyleSheet("font-weight: bold; color: #F44336;")

            terminal_message = f"<span style='color:#F44336;'>--- {message} ---</span>"
            if hasattr(self, 'terminal'):
                self.terminal.append(terminal_message)

            # Также выводим сообщение в терминал на вкладке "Работа"
            if hasattr(self, 'sequence_terminal'):
                self.sequence_terminal.append(terminal_message)

        # Прокручиваем терминалы для отображения последнего сообщения
        if hasattr(self, 'terminal'):
            self.terminal.ensureCursorVisible()
        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.ensureCursorVisible()

        # Сбрасываем заголовок последовательности
        self.current_sequence_name.setText("Нет активной последовательности")

        # Проверяем, не был ли уничтожен поток
        if hasattr(self, 'command_sequence_thread') and self.command_sequence_thread:
            self.command_sequence_thread.wait()
            self.command_sequence_thread = None

        # Обновляем статусную строку
        status_message = "Последовательность успешно завершена" if success else f"Ошибка выполнения последовательности: {message}"
        self.status_bar.showMessage(status_message, 5000)

    def setup_sidebar(self):
        """Настройка боковой панели с кнопками для выбора страниц"""
        # Словарь для хранения категорий кнопок и страниц
        self.category_buttons = {}
        self.category_pages = {}

        # Создание виджета-контейнера для боковых кнопок
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(150)
        self.sidebar.setMaximumWidth(200)

        # Стиль для боковой панели
        self.sidebar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border: none;
            }
            QPushButton {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: none;
                text-align: left;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked, QPushButton:pressed {
                background-color: #3498db;
                color: white;
            }
        """)

        # Создание вертикального лейаута для боковой панели
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Кнопка для страницы последовательностей
        self.sequences_btn = QPushButton("Главное меню")
        self.sequences_btn.setCheckable(True)
        self.sequences_btn.setChecked(True)
        self.sequences_btn.clicked.connect(lambda: self.switch_page("sequences"))
        self.category_buttons["sequences"] = self.sequences_btn
        sidebar_layout.addWidget(self.sequences_btn)

        # Создание кнопок для страниц
        # Кнопка для страницы команд (основная страница)
        self.commands_btn = QPushButton("Команды")
        self.commands_btn.setCheckable(True)
        self.commands_btn.setChecked(False)
        self.commands_btn.clicked.connect(lambda: self.switch_page("commands"))
        self.category_buttons["commands"] = self.commands_btn
        sidebar_layout.addWidget(self.commands_btn)


        # Кнопка для страницы настроек
        self.settings_btn = QPushButton("Настройки")
        self.settings_btn.setCheckable(True)
        self.settings_btn.clicked.connect(lambda: self.switch_page("settings"))
        self.category_buttons["settings"] = self.settings_btn
        sidebar_layout.addWidget(self.settings_btn)

        # Добавление растягивающегося спейсера
        sidebar_layout.addStretch(1)

        # Создание стек-виджета для отображения страниц
        self.stacked_widget = QStackedWidget()

        # Создание страницы команд (страница с табами)
        self.commands_page = QWidget()
        self.category_pages["commands"] = self.commands_page
        self.stacked_widget.addWidget(self.commands_page)

        # Создание страницы последовательностей
        self.sequences_page = QWidget()
        self.setup_sequences_page()
        self.category_pages["sequences"] = self.sequences_page
        self.stacked_widget.addWidget(self.sequences_page)

        # Создание страницы настроек (пока пустая)
        self.settings_page = QWidget()
        self.setup_settings_page()
        self.category_pages["settings"] = self.settings_page
        self.stacked_widget.addWidget(self.settings_page)

        # Создание горизонтального сплиттера для боковой панели и основного контента
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.stacked_widget)
        self.splitter.setSizes([200, 800])  # Установка начальных размеров

        # Устанавливаем сплиттер как центральный виджет
        self.setCentralWidget(self.splitter)

    def setup_sequences_page(self):
        """Настройка страницы для работы с последовательностями команд из секции [sequences]"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Контейнер для кнопок последовательностей
        sequence_group = QGroupBox("Доступные последовательности")
        sequence_layout = QVBoxLayout(sequence_group)

        # Создаем прокручиваемую область для кнопок
        self.sequence_container = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.sequence_container)

        sequence_layout.addWidget(scroll)
        layout.addWidget(sequence_group)

        # Создаем кнопки для последовательностей из [sequences]
        container_layout = QVBoxLayout(self.sequence_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)

        self.sequence_buttons = []

        # Добавляем кнопки для каждой последовательности
        for sequence_name in self.sequence_commands.keys():
            btn = QPushButton(sequence_name)
            btn.setMinimumHeight(40)

            # Применяем стили кнопок последовательностей
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #42A5F5;
                }
                QPushButton:pressed {
                    background-color: #1976D2;
                }
                QPushButton:disabled {
                    background-color: #78909C;
                    color: #CFD8DC;
                }
            """)

            btn.clicked.connect(lambda checked, name=sequence_name: self.start_sequence(name))
            container_layout.addWidget(btn)
            self.sequence_buttons.append(btn)

        # Добавляем растягивающийся элемент в конец
        container_layout.addStretch(1)

        # Область с информацией о текущей последовательности
        current_group = QGroupBox("Текущая последовательность")
        current_layout = QVBoxLayout(current_group)

        # Заголовок с названием последовательности
        self.current_sequence_name = QLabel("Нет активной последовательности")
        self.current_sequence_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.current_sequence_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.current_sequence_name)

        # Информация о ходе выполнения
        self.sequence_info = QLabel("Выберите последовательность для запуска")
        self.sequence_info.setStyleSheet("font-style: italic;")
        self.sequence_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.sequence_info)

        # Прогресс-бар для отображения прогресса выполнения последовательности
        self.sequence_progress = QProgressBar()
        self.sequence_progress.setTextVisible(True)
        self.sequence_progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.sequence_progress)

        # Кнопки управления выполнением последовательности
        control_layout = QHBoxLayout()

        # Кнопка остановки
        self.stop_sequence_button = QPushButton("Остановить")
        self.stop_sequence_button.setMinimumHeight(35)
        self.stop_sequence_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_sequence_button.clicked.connect(self.stop_sequence)
        self.stop_sequence_button.setEnabled(False)
        self.stop_sequence_button.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
            QPushButton:disabled {
                background-color: #78909C;
                color: #CFD8DC;
            }
        """)
        control_layout.addWidget(self.stop_sequence_button)

        current_layout.addLayout(control_layout)
        layout.addWidget(current_group)

        # Убираем терминал для вывода информации о выполнении последовательности
        # так как он дублирует основной терминал справа
        # Создаем скрытый терминал для совместимости с существующим кодом
        self.sequence_terminal = QTextEdit()
        self.sequence_terminal.setVisible(False)

        self.sequences_page.setLayout(layout)

    def setup_settings_page(self):
        """Настройка страницы настроек"""
        layout = QVBoxLayout(self.settings_page)

        # Группа для настроек соединения
        connection_group = QGroupBox("Настройки соединения")
        connection_layout = QFormLayout(connection_group)

        # Порт
        self.port_combo = QComboBox()
        self.refresh_ports(self.port_combo)  # Передаем combo_box как аргумент
        connection_layout.addRow("COM порт:", self.port_combo)

        # Скорость
        self.baud_combo = QComboBox()
        for baud in [9600, 19200, 38400, 57600, 115200]:
            self.baud_combo.addItem(str(baud))
        self.baud_combo.setCurrentText("9600")
        connection_layout.addRow("Скорость:", self.baud_combo)

        # Автоподключение
        self.auto_connect_check = QCheckBox("Автоматически подключаться при запуске")
        self.auto_connect_check.setChecked(self.update_settings.get('auto_connect', True))
        connection_layout.addRow("", self.auto_connect_check)

        # Кнопка обновления портов
        refresh_btn = QPushButton("Обновить список портов")
        refresh_btn.clicked.connect(lambda: self.refresh_ports(self.port_combo))  # Используем лямбда-функцию для передачи аргумента
        connection_layout.addRow("", refresh_btn)

        # Кнопка сохранения настроек соединения
        save_conn_btn = QPushButton("Сохранить настройки соединения")
        save_conn_btn.clicked.connect(self.save_connection_settings)
        connection_layout.addRow("", save_conn_btn)

        layout.addWidget(connection_group)

        # Группа для настроек обновления
        update_group = QGroupBox("Настройки обновления")
        update_layout = QFormLayout(update_group)

        # Включение автообновления
        self.auto_update_check = QCheckBox("Автоматически проверять обновления")
        self.auto_update_check.setChecked(self.update_settings.get('enable_auto_update', True))
        update_layout.addRow("", self.auto_update_check)

        # URL репозитория
        self.repo_url_edit = QLineEdit(self.update_settings.get('repository_url', ''))
        update_layout.addRow("URL репозитория:", self.repo_url_edit)

        # Интервал проверки обновлений
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 24)
        self.update_interval_spin.setValue(int(self.update_settings.get('update_check_interval', 3600) / 3600))
        self.update_interval_spin.setSuffix(" час(ов)")
        update_layout.addRow("Интервал проверки:", self.update_interval_spin)

        # Кнопка для проверки обновлений
        check_updates_btn = QPushButton("Проверить обновления сейчас")
        check_updates_btn.clicked.connect(self.check_for_updates)
        update_layout.addRow("", check_updates_btn)

        # Кнопка сохранения настроек обновления
        save_update_btn = QPushButton("Сохранить настройки обновления")
        save_update_btn.clicked.connect(self.save_update_settings_from_ui)
        update_layout.addRow("", save_update_btn)

        layout.addWidget(update_group)

        # Группа для настроек PlatformIO
        platformio_group = QGroupBox("Настройки PlatformIO")
        platformio_layout = QFormLayout(platformio_group)

        # Путь к проекту PlatformIO
        self.platformio_path_edit = QLineEdit(self.update_settings.get('platformio_path', ''))
        platformio_layout.addRow("Путь к проекту:", self.platformio_path_edit)

        # Кнопка выбора директории проекта
        browse_path_btn = QPushButton("Обзор...")
        browse_path_btn.clicked.connect(self.browse_platformio_path)
        platformio_layout.addRow("", browse_path_btn)

        # Порт для загрузки прошивки
        self.upload_port_combo = QComboBox()
        self.refresh_ports(self.upload_port_combo)
        current_upload_port = self.update_settings.get('upload_port', '')
        if current_upload_port:
            index = self.upload_port_combo.findText(current_upload_port)
            if index >= 0:
                self.upload_port_combo.setCurrentIndex(index)
        platformio_layout.addRow("Порт для загрузки:", self.upload_port_combo)

        # Кнопка обновления списка портов
        refresh_upload_ports_btn = QPushButton("Обновить список портов")
        refresh_upload_ports_btn.clicked.connect(lambda: self.refresh_ports(self.upload_port_combo))
        platformio_layout.addRow("", refresh_upload_ports_btn)

        # Кнопка для тестирования PlatformIO
        test_platformio_btn = QPushButton("Проверить PlatformIO")
        test_platformio_btn.clicked.connect(self.test_platformio)
        platformio_layout.addRow("", test_platformio_btn)

        # Кнопка сохранения настроек PlatformIO
        save_platformio_btn = QPushButton("Сохранить настройки PlatformIO")
        save_platformio_btn.clicked.connect(self.save_platformio_settings)
        platformio_layout.addRow("", save_platformio_btn)

        layout.addWidget(platformio_group)

        # Группа для настроек приложения
        app_group = QGroupBox("Настройки приложения")
        app_layout = QVBoxLayout(app_group)

        # Кнопка для перезагрузки конфигурации
        reload_config_btn = QPushButton("Перезагрузить конфигурацию")
        reload_config_btn.clicked.connect(self.reload_config)
        app_layout.addWidget(reload_config_btn)

        # Чекбокс для авто-прокрутки терминала
        self.autoscroll_check = QCheckBox("Автоматическая прокрутка терминала")
        self.autoscroll_check.setChecked(True)
        app_layout.addWidget(self.autoscroll_check)

        layout.addWidget(app_group)

        # Добавляем растягивающийся спейсер
        layout.addStretch(1)

    def load_sequences(self):
        """Загрузка последовательностей команд из директории sequences"""
        sequences = {}
        sequences_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sequences')

        # Создаем директорию, если она не существует
        if not os.path.exists(sequences_dir):
            try:
                os.makedirs(sequences_dir)
                self.status_bar.showMessage("Создана директория для последовательностей", 3000)
                # Создаем пример последовательности
                example_path = os.path.join(sequences_dir, 'example.toml')
                with open(example_path, 'w', encoding='utf-8') as f:
                    f.write("""# Пример файла последовательности
name = "Пример последовательности"
description = "Это пример последовательности команд для демонстрации"

[[steps]]
command = "MOTOR1_ON"
comment = "Включение мотора 1"

[[steps]]
wait = 2
comment = "Ожидание 2 секунды"

[[steps]]
command = "MOTOR1_OFF"
comment = "Выключение мотора 1"
""")
                self.status_bar.showMessage("Создан пример последовательности commands/example.toml", 5000)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать директорию последовательностей: {str(e)}")
            return sequences

        # Загружаем последовательности из .toml файлов
        try:
            for filename in os.listdir(sequences_dir):
                if filename.endswith('.toml'):
                    filepath = os.path.join(sequences_dir, filename)
                    try:
                        with open(filepath, 'rb') as f:
                            sequence_data = tomli.load(f)

                            # Получаем имя последовательности из файла или из имени файла
                            name = sequence_data.get('name', os.path.splitext(filename)[0])

                            # Собираем данные последовательности
                            sequences[name] = {
                                'description': sequence_data.get('description', ''),
                                'steps': sequence_data.get('steps', []),
                                'filepath': filepath
                            }
                    except Exception as e:
                        self.status_bar.showMessage(f"Ошибка загрузки {filename}: {str(e)}", 5000)
                        print(f"Ошибка при загрузке последовательности {filename}: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить последовательности: {str(e)}")

        return sequences

    def pause_sequence(self):
        """Приостановка выполнения текущей последовательности"""
        if hasattr(self, 'sequence_thread') and self.sequence_thread and self.sequence_thread.isRunning():
            self.sequence_thread.pause()

            # Обновляем информацию в интерфейсе
            if hasattr(self, 'sequence_details'):
                self.sequence_details.append("<p><span style='color: orange; font-weight: bold;'>Выполнение последовательности приостановлено</span></p>")

            # Обновляем статусную строку
            self.status_bar.showMessage("Выполнение последовательности приостановлено", 3000)

    def run_sequence(self, sequence_name):
        """Запуск последовательности действий"""
        # Проверяем, подключено ли устройство
        if not hasattr(self, 'serial_port') or not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Устройство не подключено. Подключите устройство перед запуском последовательности."
            )
            return False

        # Проверяем, существует ли последовательность
        if sequence_name not in self.sequences:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Последовательность '{sequence_name}' не найдена."
            )
            return False

        # Получаем шаги последовательности
        sequence = self.sequences[sequence_name]
        steps = sequence.get('steps', [])

        if not steps:
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Последовательность '{sequence_name}' не содержит шагов."
            )
            return False

        # Очищаем информацию о предыдущей последовательности
        if hasattr(self, 'sequence_details'):
            self.sequence_details.clear()

        # Обновляем текущую последовательность в интерфейсе
        if hasattr(self, 'current_sequence_name'):
            self.current_sequence_name.setText(f"Выполняется: {sequence_name}")

        # Настраиваем прогресс-бар
        if hasattr(self, 'sequence_progress'):
            self.sequence_progress.setMaximum(len(steps))
            self.sequence_progress.setValue(0)

        # Блокируем кнопки последовательностей
        for btn in self.sequence_buttons:
            btn.setEnabled(False)

        # Активируем кнопку остановки
        if hasattr(self, 'stop_sequence_button'):
            self.stop_sequence_button.setEnabled(True)

        # Создаем и запускаем поток выполнения последовательности
        self.sequence_thread = SequenceThread(self, sequence_name, steps)
        self.sequence_thread.step_completed.connect(
            lambda idx, total, step, comment, success: self.update_sequence_progress(
                idx, total, step, comment, success
            )
        )
        self.sequence_thread.sequence_completed.connect(
            lambda success, message: self.on_sequence_completed(sequence_name, success)
        )
        self.sequence_thread.start()

        # Выводим сообщение о запуске
        message = f"<span style='color:#2196F3;'>--- Запущена последовательность: {sequence_name} ---</span>"
        if hasattr(self, 'terminal'):
            self.terminal.append(message)

        if hasattr(self, 'sequence_terminal'):
            self.sequence_terminal.append(message)

        # Обновляем статусную строку
        self.status_bar.showMessage(f"Запущена последовательность '{sequence_name}'", 3000)

        return True

    def update_sequence_progress(self, step_index, total_steps, step, comment, success):
        """Обновление прогресса выполнения последовательности"""
        # Обновляем прогресс-бар
        if hasattr(self, 'sequence_progress'):
            self.sequence_progress.setValue(step_index + 1)

        # Добавляем информацию о шаге
        step_desc = ""
        if 'command' in step:
            step_desc = f"Команда: {step['command']}"
        elif 'wait' in step:
            step_desc = f"Ожидание: {step['wait']} секунд"

        # Добавляем комментарий, если есть
        if comment:
            step_desc += f" - {comment}"

        # Добавляем информацию о результате выполнения
        status_color = "green" if success else "red"
        status_text = "Успешно" if success else "Ошибка"

        # Формируем HTML для вывода в терминал
        html_message = (
            f"<p style='margin:5px 0;'>"
            f"<span style='color:#666;'>[{step_index + 1}/{total_steps}]</span> "
            f"{step_desc} - "
            f"<span style='color:{status_color};font-weight:bold;'>{status_text}</span>"
            f"</p>"
        )

        # Выводим в терминал последовательности, если он существует
        if hasattr(self, 'sequence_details'):
            self.sequence_details.append(html_message)

        # Выводим в основной терминал с другим форматированием
        if hasattr(self, 'terminal'):
            terminal_message = f"<span style='color:#888;'>[Шаг {step_index + 1}/{total_steps}]</span> {step_desc}"
            if success:
                terminal_message += " <span style='color:green;'>✓</span>"
            else:
                terminal_message += " <span style='color:red;'>✗</span>"
            self.terminal.append(terminal_message)

        # Прокручиваем терминалы для отображения последних сообщений
        if hasattr(self, 'sequence_details'):
            self.sequence_details.ensureCursorVisible()

        if hasattr(self, 'terminal'):
            self.terminal.ensureCursorVisible()

    def on_sequence_button_clicked(self):
        """Обработчик нажатия на кнопку запуска последовательности"""
        sender = self.sender()
        sequence_name = sender.text()
        self.run_sequence(sequence_name)

    def setup_sequence_buttons(self):
        """Создание кнопок для запуска последовательностей"""
        # Очищаем существующие кнопки
        self.sequence_buttons = []

        # Очищаем контейнер кнопок
        layout = self.sequence_container.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        else:
            layout = QVBoxLayout(self.sequence_container)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            self.sequence_container.setLayout(layout)

        # Добавляем кнопки для каждой последовательности
        for sequence_name in self.sequences.keys():
            btn = QPushButton(sequence_name)
            btn.setMinimumHeight(40)

            # Применяем стили кнопок
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0f0ff;
                    color: #005594;
                    border: 1px solid #bad4ed;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d0e5fa;
                    border: 1px solid #99c2e5;
                }
                QPushButton:pressed {
                    background-color: #c0dbf5;
                    border: 1px solid #77a5d6;
                }
                QPushButton:disabled {
                    background-color: #f0f0f0;
                    color: #a0a0a0;
                    border: 1px solid #d0d0d0;
                }
            """)

            btn.clicked.connect(self.on_sequence_button_clicked)
            layout.addWidget(btn)
            self.sequence_buttons.append(btn)

        # Добавляем растягивающийся элемент в конец
        layout.addStretch(1)

    def save_connection_settings(self):
        """Сохранение настроек соединения из UI"""
        # Обновляем настройки соединения
        self.serial_settings['port'] = self.port_combo.currentText()
        self.serial_settings['baudrate'] = int(self.baud_combo.currentText())

        # Обновляем настройку автоподключения
        self.update_settings['auto_connect'] = self.auto_connect_check.isChecked()

        # Сохраняем настройки
        self.save_serial_settings()
        self.save_update_settings()

        self.status_bar.showMessage("Настройки соединения сохранены", 3000)

    def save_update_settings_from_ui(self):
        """Сохранение настроек обновления из UI"""
        # Обновляем настройки обновления
        self.update_settings['enable_auto_update'] = self.auto_update_check.isChecked()
        self.update_settings['repository_url'] = self.repo_url_edit.text()
        self.update_settings['update_check_interval'] = self.update_interval_spin.value() * 3600  # переводим часы в секунды

        # Сохраняем настройки
        self.save_update_settings()

        # Обновляем таймер проверки обновлений
        if hasattr(self, 'update_timer'):
            interval = self.update_settings.get('update_check_interval', 3600) * 1000
            self.update_timer.setInterval(interval)

            if self.update_settings.get('enable_auto_update', True):
                if not self.update_timer.isActive():
                    self.update_timer.start(interval)
            else:
                if self.update_timer.isActive():
                    self.update_timer.stop()

        self.status_bar.showMessage("Настройки обновления сохранены", 3000)

    def browse_platformio_path(self):
        """Открыть диалог выбора директории проекта PlatformIO"""
        current_path = self.platformio_path_edit.text()
        start_dir = current_path if os.path.exists(current_path) else os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию проекта PlatformIO",
            start_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )

        if directory:
            self.platformio_path_edit.setText(directory)

    def test_platformio(self):
        """Проверка доступности PlatformIO"""
        try:
            # Проверяем, установлен ли PlatformIO
            result = subprocess.run(
                ["platformio", "--version"],
                capture_output=True,
                text=True,
                shell=True
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                QMessageBox.information(
                    self,
                    "PlatformIO доступен",
                    f"PlatformIO установлен и доступен:\n{version}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "PlatformIO не найден",
                    "PlatformIO не найден или не установлен. Убедитесь, что PlatformIO установлен и доступен в PATH.\n\n"
                    "Вы можете установить PlatformIO командой:\npip install platformio"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка проверки PlatformIO",
                f"Произошла ошибка при проверке PlatformIO:\n{str(e)}"
            )

    def save_platformio_settings(self):
        """Сохранение настроек PlatformIO"""
        self.update_settings['platformio_path'] = self.platformio_path_edit.text()
        self.update_settings['upload_port'] = self.upload_port_combo.currentText()

        # Сохраняем настройки
        self.save_update_settings()

        self.status_bar.showMessage("Настройки PlatformIO сохранены", 3000)

    def upload_firmware(self):
        """Загрузка прошивки через PlatformIO"""
        # Проверяем настройки
        platformio_path = self.update_settings.get('platformio_path', '')

        # Если путь не указан, используем директорию по умолчанию
        if not platformio_path:
            platformio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arduino')
            self.update_settings['platformio_path'] = platformio_path
            self.save_update_settings()

        upload_port = self.update_settings.get('upload_port', '')

        logging.info(f"Подготовка к загрузке прошивки. Путь: {platformio_path}, Порт: {upload_port}")

        # Проверяем существование директории прошивки
        if not os.path.exists(platformio_path):
            # Предлагаем создать директорию
            result = QMessageBox.question(
                self,
                "Директория не существует",
                f"Директория прошивки не существует:\n{platformio_path}\n\nСоздать директорию?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if result == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(platformio_path, exist_ok=True)
                    self.status_bar.showMessage(f"Создана директория прошивки: {platformio_path}", 3000)
                    logging.info(f"Создана директория прошивки: {platformio_path}")
                except Exception as e:
                    error_msg = f"Не удалось создать директорию: {str(e)}"
                    logging.error(error_msg)
                    QMessageBox.critical(
                        self,
                        "Ошибка создания директории",
                        error_msg
                    )
                    return
            else:
                return

        # Проверяем, содержит ли директория файлы прошивки
        if not self.check_firmware_files(platformio_path):
            error_msg = f"В указанной директории не найдены файлы прошивки Arduino/PlatformIO: {platformio_path}"
            logging.error(error_msg)
            QMessageBox.warning(
                self,
                "Файлы прошивки не найдены",
                f"{error_msg}\n\nУбедитесь, что в этой директории содержится корректный проект."
            )
            return

        # Если устройство подключено, отключаем его перед загрузкой прошивки
        was_connected = False
        if self.serial_port and self.serial_port.is_open:
            was_connected = True
            self.disconnect_serial()
            # Даем немного времени на закрытие порта
            time.sleep(1)

        try:
            # Проверяем доступность PlatformIO
            try:
                check_result = subprocess.run(
                    ["platformio", "--version"],
                    capture_output=True,
                    text=True,
                    shell=True,
                    check=False
                )

                if check_result.returncode != 0:
                    error_msg = f"PlatformIO не установлен или недоступен: {check_result.stderr}"
                    logging.error(error_msg)
                    QMessageBox.critical(
                        self,
                        "PlatformIO не доступен",
                        f"{error_msg}\n\nУстановите PlatformIO или проверьте PATH."
                    )
                    return

                logging.info(f"PlatformIO доступен: {check_result.stdout.strip()}")
            except Exception as e:
                error_msg = f"Ошибка при проверке PlatformIO: {str(e)}"
                logging.error(error_msg)
                QMessageBox.critical(
                    self,
                    "Ошибка проверки PlatformIO",
                    error_msg
                )
                return

            # Создаем команду для загрузки прошивки
            cmd = ["platformio", "run", "--target", "upload"]

            # Если указан порт, добавляем его в команду
            if upload_port:
                cmd.extend(["--upload-port", upload_port])

            # Логируем команду
            logging.info(f"Запуск команды: {' '.join(cmd)} в директории {platformio_path}")

            # Показываем прогресс
            self.status_bar.showMessage("Загрузка прошивки...", 0)

            # Отображаем диалог с прогрессом
            progress_dialog = QProgressDialog(
                "Загрузка прошивки...",
                "Отмена",
                0, 0,
                self
            )
            progress_dialog.setWindowTitle("Загрузка прошивки")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.show()

            # Запускаем процесс загрузки прошивки в отдельном потоке
            upload_thread = threading.Thread(
                target=self.run_upload_process,
                args=(cmd, platformio_path, progress_dialog, was_connected)
            )
            upload_thread.daemon = True
            upload_thread.start()

        except Exception as e:
            error_msg = f"Ошибка при загрузке прошивки: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(
                self,
                "Ошибка загрузки прошивки",
                error_msg
            )
            self.status_bar.showMessage("Ошибка загрузки прошивки", 5000)

            # Восстанавливаем подключение, если оно было
            if was_connected:
                QTimer.singleShot(1000, self.connect_serial)

    def check_firmware_files(self, directory):
        """Проверка наличия файлов прошивки в указанной директории"""
        try:
            logging.info(f"Проверка наличия файлов прошивки в директории: {directory}")

            # Проверяем наличие файла platformio.ini (для PlatformIO проектов)
            platformio_ini = os.path.join(directory, 'platformio.ini')
            if os.path.exists(platformio_ini):
                logging.info(f"Найден файл platformio.ini: {platformio_ini}")
                return True

            # Проверяем наличие .ino файлов (для Arduino проектов)
            for file in os.listdir(directory):
                if file.endswith('.ino'):
                    logging.info(f"Найден Arduino файл: {os.path.join(directory, file)}")
                    return True

            # Проверяем наличие директории src с .cpp или .h файлами
            src_dir = os.path.join(directory, 'src')
            if os.path.exists(src_dir) and os.path.isdir(src_dir):
                for file in os.listdir(src_dir):
                    if file.endswith('.cpp') or file.endswith('.h'):
                        logging.info(f"Найдены исходные файлы в директории src: {os.path.join(src_dir, file)}")
                        return True

            # Проверяем наличие директории include с .h файлами
            include_dir = os.path.join(directory, 'include')
            if os.path.exists(include_dir) and os.path.isdir(include_dir):
                for file in os.listdir(include_dir):
                    if file.endswith('.h'):
                        logging.info(f"Найдены заголовочные файлы в директории include: {os.path.join(include_dir, file)}")
                        return True

            logging.warning(f"Файлы прошивки не найдены в директории: {directory}")
            return False
        except Exception as e:
            logging.error(f"Ошибка при проверке файлов прошивки: {str(e)}")
            return False

    def run_upload_process(self, cmd, platformio_path, progress_dialog, reconnect=False):
        """Выполнение процесса загрузки прошивки в отдельном потоке"""
        try:
            logging.info(f"Запуск процесса загрузки прошивки: {' '.join(cmd)}")
            # Запускаем процесс
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                cwd=platformio_path,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0 # Скрываем консольное окно на Windows
            )
            
            # Читаем вывод процесса и обновляем интерфейс
            output = []
            for line in iter(process.stdout.readline, ''):
                if not line: # Пропускаем пустые строки, которые могут возникнуть при завершении потока
                    break
                line = line.strip()
                output.append(line)
                logging.info(f"PlatformIO: {line}")
                # Безопасное обновление LabelText через QMetaObject.invokeMethod
                QMetaObject.invokeMethod(progress_dialog, "setLabelText", 
                                       Qt.ConnectionType.QueuedConnection, 
                                       Q_ARG(str, f"Загрузка прошивки...\n{line}"))
            
            process.stdout.close()
            # Ждем завершения процесса
            return_code = process.wait()
            
            # Проверяем код возврата
            if return_code == 0:
                # Успешная загрузка
                success_message = "Прошивка успешно загружена"
                logging.info(success_message)
                QMetaObject.invokeMethod(self.status_bar, "showMessage",
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(str, success_message),
                                       Q_ARG(int, 5000))
                # Обновляем диалог прогресса
                QMetaObject.invokeMethod(progress_dialog, "setLabelText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Прошивка успешно загружена"))
                QMetaObject.invokeMethod(progress_dialog, "setCancelButtonText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Закрыть"))
                QMetaObject.invokeMethod(progress_dialog, "setMaximum", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
                QMetaObject.invokeMethod(progress_dialog, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
            else:
                # Ошибка загрузки
                error_message = f"Ошибка загрузки прошивки (код {return_code})"
                logging.error(error_message)
                logging.error("\n".join(output))
                
                QMetaObject.invokeMethod(self.status_bar, "showMessage",
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(str, error_message),
                                       Q_ARG(int, 5000))
                # Показываем диалог с ошибкой
                error_output = "\n".join(output)
                QMetaObject.invokeMethod(QMessageBox, "critical",
                                       Qt.ConnectionType.QueuedConnection, # Важно использовать QueuedConnection для диалогов из потоков
                                       Q_ARG(QWidget, self), 
                                       Q_ARG(str, "Ошибка загрузки прошивки"),
                                       Q_ARG(str, f"Процесс загрузки завершился с ошибкой (код {return_code}):\n\n{error_output}"))
                # Обновляем диалог прогресса
                QMetaObject.invokeMethod(progress_dialog, "setLabelText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Ошибка загрузки прошивки"))
                QMetaObject.invokeMethod(progress_dialog, "setCancelButtonText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Закрыть"))
                QMetaObject.invokeMethod(progress_dialog, "setMaximum", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
                QMetaObject.invokeMethod(progress_dialog, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
            
            # Восстанавливаем подключение, если оно было
            if reconnect:
                QTimer.singleShot(2000, self.connect_serial)
                
        except Exception as e:
            # Обрабатываем ошибки
            error_message = f"Ошибка при выполнении процесса: {str(e)}"
            logging.error(error_message)
            QMetaObject.invokeMethod(self.status_bar, "showMessage",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(str, error_message),
                                   Q_ARG(int, 5000))
            # Показываем диалог с ошибкой
            QMetaObject.invokeMethod(QMessageBox, "critical",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(QWidget, self), 
                                   Q_ARG(str, "Ошибка загрузки прошивки"),
                                   Q_ARG(str, error_message))
            # Обновляем диалог прогресса
            # Убедимся, что progress_dialog существует перед тем, как вызывать его методы
            if progress_dialog:
                QMetaObject.invokeMethod(progress_dialog, "setLabelText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Ошибка загрузки прошивки"))
                QMetaObject.invokeMethod(progress_dialog, "setCancelButtonText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Закрыть"))
                QMetaObject.invokeMethod(progress_dialog, "setMaximum", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
                QMetaObject.invokeMethod(progress_dialog, "setValue", Qt.ConnectionType.QueuedConnection, Q_ARG(int, 1))
            
            # Восстанавливаем подключение, если оно было
            if reconnect:
                QTimer.singleShot(2000, self.connect_serial)

    def toggle_fullscreen(self):
        """Переключение между полноэкранным и оконным режимами"""
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            self.toggle_fullscreen_action.setText("Полноэкранный режим")
        else:
            self.showFullScreen()
            self.is_fullscreen = True
            self.toggle_fullscreen_action.setText("Выйти из полноэкранного режима")

        # Обновляем статусную строку
        mode = "полноэкранного" if self.is_fullscreen else "оконного"
        self.status_bar.showMessage(f"Переключение в режим {mode} отображения", 3000)


class SequenceThread(QThread):
    """Поток для выполнения последовательности команд"""
    # Сигналы для обновления интерфейса
    step_completed = pyqtSignal(int, int, dict, str, bool)  # индекс шага, общее количество, шаг, комментарий, успех
    sequence_completed = pyqtSignal(bool, str)  # успех, сообщение

    def __init__(self, parent, sequence_name, steps):
        super().__init__(parent)
        self.parent = parent
        self.sequence_name = sequence_name
        self.steps = steps
        self.should_stop = False
        self.paused = False
        self.pause_condition = QWaitCondition()
        self.mutex = QMutex()

    def run(self):
        """Выполнение последовательности команд"""
        success = True
        error_message = ""
        total_steps = len(self.steps)

        for i, step in enumerate(self.steps):
            # Проверяем флаг остановки
            if self.should_stop:
                success = False
                error_message = "Последовательность остановлена пользователем"
                break

            # Проверяем паузу
            self.mutex.lock()
            while self.paused and not self.should_stop:
                self.pause_condition.wait(self.mutex)
            self.mutex.unlock()

            # Проверяем флаг остановки снова после ожидания
            if self.should_stop:
                success = False
                error_message = "Последовательность остановлена пользователем"
                break

            step_success = True
            comment = step.get('comment', '')

            # Выполняем команду или ожидание
            if 'wait' in step:
                wait_time = step['wait']
                # Разбиваем ожидание на небольшие интервалы для проверки остановки
                for _ in range(int(wait_time * 10)):
                    time.sleep(0.1)  # Ожидание 100 мс

                    # Проверяем флаг остановки
                    if self.should_stop:
                        success = False
                        error_message = "Последовательность остановлена пользователем"
                        break

                    # Проверяем паузу
                    self.mutex.lock()
                    while self.paused and not self.should_stop:
                        self.pause_condition.wait(self.mutex)
                    self.mutex.unlock()

                    # Проверяем флаг остановки после ожидания
                    if self.should_stop:
                        success = False
                        error_message = "Последовательность остановлена пользователем"
                        break

                if self.should_stop:
                    break

            elif 'command' in step:
                command = step['command']
                try:
                    # Отправляем команду через родительский объект
                    self.parent.send_command(command)
                    step_success = True
                except Exception as e:
                    step_success = False
                    error_message = str(e)
                    success = False

            # Эмитируем сигнал о завершении шага
            self.step_completed.emit(i, total_steps, step, comment, step_success)

            # Если шаг не выполнен успешно, прерываем последовательность
            if not step_success:
                success = False
                break

        # Эмитируем сигнал о завершении последовательности
        self.sequence_completed.emit(success, error_message)

    def stop(self):
        """Остановка выполнения последовательности"""
        self.should_stop = True
        self.mutex.lock()
        self.paused = False
        self.pause_condition.wakeAll()
        self.mutex.unlock()

    def pause(self):
        """Приостановка выполнения последовательности"""
        self.mutex.lock()
        self.paused = True
        self.mutex.unlock()

    def resume(self):
        """Возобновление выполнения последовательности"""
        self.mutex.lock()
        self.paused = False
        self.pause_condition.wakeAll()
        self.mutex.unlock()


if __name__ == "__main__":
    # Инициализация логирования
    try:
        logging.info("=" * 80)
        logging.info("Запуск приложения")
        # Выводим информацию о системе
        logging.info(f"Операционная система: {sys.platform}")
        logging.info(f"Версия Python: {sys.version}")
        logging.info(f"Текущая директория: {os.getcwd()}")
        logging.info(f"Файл логов: {LOG_FILE}")
    except Exception as e:
        print(f"Ошибка при логировании запуска: {str(e)}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.app = app  # Передаем ссылку на объект приложения для стилизации
    window.show()

    try:
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Критическая ошибка при выполнении приложения: {str(e)}")
        print(f"Ошибка: {str(e)}")
