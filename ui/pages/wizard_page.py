"""
Страница мастера настройки
"""
from typing import Dict, Optional, Any
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QSizePolicy, QStackedLayout, QGroupBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal as Signal

from .base_page import BasePage
from ..widgets.modern_widgets import ModernCard, ModernButton
from ..widgets.overlay_panel import OverlayPanel

import logging
from core.sequence_manager import SequenceManager
from core.command_executor import CommandExecutorFactory
from core.multizone_manager import MultizoneManager
from core.flag_manager import FlagManager
from core.tag_manager import TagManager
from ui.dialogs.tag_dialogs import TagDialogManager


class WizardPage(BasePage):
    """Страница мастера настройки"""

    # Сигналы
    sequence_requested = Signal(str, int)  # sequence_name, next_step_id
    zone_selection_changed = Signal(dict)  # zones dict

    def __init__(self, wizard_config: Dict, multizone_manager=None, parent=None):
        self.wizard_config = wizard_config
        self.wizard_steps = wizard_config.get('steps', {})
        self.current_step_id = 1
        self.waiting_next_id = None
        self.multizone_manager = multizone_manager
        
        # Старое представление зон (для обратной совместимости)
        self.zone_selected = {
            'left_top': False,
            'left_bottom': False,
            'right_top': False,
            'right_bottom': False,
        }
        
        # Новое представление зон (1-4)
        self.zone_checkboxes = {}
        self.zone_mapping = {
            'left_top': 1,
            'left_bottom': 2,
            'right_top': 3,
            'right_bottom': 4
        }
        
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Получаем сервисы из родительского окна
        self.main_window = parent
        if hasattr(self.main_window, 'sequence_manager'):
            self.sequence_manager = self.main_window.sequence_manager
        if hasattr(self.main_window, 'command_executor_factory'):
            self.command_executor_factory = self.main_window.command_executor_factory
        if hasattr(self.main_window, 'multizone_manager'):
            self.multizone_manager = self.main_window.multizone_manager
        if hasattr(self.main_window, 'flag_manager'):
            self.flag_manager = self.main_window.flag_manager
        if hasattr(self.main_window, 'tag_manager'):
            self.tag_manager = self.main_window.tag_manager
        if hasattr(self.main_window, 'tag_dialog_manager'):
            self.tag_dialog_manager = self.main_window.tag_dialog_manager
        
        # Подключение сигналов для тегов
        self._setup_tag_connections()

    def _setup_tag_connections(self):
        """Настройка соединений для системы тегов"""
        try:
            # Подключаем обработчики для диалогов тегов
            if hasattr(self, 'tag_dialog_manager'):
                # Обработчик для диалога _wanted
                self.tag_dialog_manager.on_wanted_dialog_result = self._on_wanted_dialog_result
                self.logger.info("Обработчики тегов подключены в WizardPage")
        except Exception as e:
            self.logger.error(f"Ошибка при настройке соединений тегов в WizardPage: {e}")
    
    def _on_wanted_dialog_result(self, result: str):
        """
        Обработчик результата диалога _wanted в WizardPage
        
        Args:
            result: Результат диалога ('check_fluids' или 'cancel')
        """
        try:
            self.logger.info(f"WizardPage: Получен результат диалога _wanted: {result}")
            
            if result == 'check_fluids':
                # Пользователь подтвердил проверку жидкостей
                self.logger.info("WizardPage: Пользователь подтвердил проверку жидкостей")
                
                # Устанавливаем флаг wanted в False
                if hasattr(self, 'flag_manager'):
                    self.flag_manager.set_flag('wanted', False)
                    self.logger.info("WizardPage: Флаг 'wanted' установлен в False")
                
                # Показываем уведомление
                QMessageBox.information(
                    self,
                    "Проверка жидкостей",
                    "Спасибо! Выполнение команды будет продолжено.",
                    QMessageBox.Ok
                )
                
                # Возобновляем выполнение команды
                self._resume_command_execution()
                
            elif result == 'cancel':
                # Пользователь отменил операцию
                self.logger.info("WizardPage: Пользователь отменил операцию")
                
                # Показываем уведомление
                QMessageBox.information(
                    self,
                    "Операция отменена",
                    "Операция была отменена пользователем.",
                    QMessageBox.Ok
                )
                
                # Останавливаем выполнение команды
                self._cancel_command_execution()
                
        except Exception as e:
            self.logger.error(f"Ошибка при обработке результата диалога _wanted в WizardPage: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Произошла ошибка при обработке результата диалога: {e}",
                QMessageBox.Ok
            )
    
    def _resume_command_execution(self):
        """Возобновление выполнения команды после обработки тега"""
        try:
            self.logger.info("WizardPage: Возобновление выполнения команды")
            
            # Здесь должна быть логика возобновления выполнения
            # Пока просто логируем
            self.logger.info("WizardPage: Выполнение команды возобновлено")
            
        except Exception as e:
            self.logger.error(f"Ошибка при возобновлении выполнения команды в WizardPage: {e}")
    
    def _cancel_command_execution(self):
        """Отмена выполнения команды"""
        try:
            self.logger.info("WizardPage: Отмена выполнения команды")
            
            # Здесь должна быть логика отмены выполнения
            # Пока просто логируем
            self.logger.info("WizardPage: Выполнение команды отменено")
            
        except Exception as e:
            self.logger.error(f"Ошибка при отмене выполнения команды в WizardPage: {e}")
    
    def execute_command(self, command: str):
        """
        Выполнение команды с поддержкой тегов
        
        Args:
            command: Команда для выполнения
        """
        try:
            self.logger.info(f"Выполнение команды: {command}")
            
            # Создаем контекст выполнения с флагами
            execution_context = self._create_execution_context()
            
            # Проверяем наличие тегов в команде
            if hasattr(self, 'tag_manager') and self.tag_manager._has_tags(command):
                self.logger.info(f"Обнаружены теги в команде: {command}")
                
                # Обрабатываем теги
                if not self._process_tags(command, execution_context):
                    self.logger.warning("Обработка тегов не прошла, команда не выполняется")
                    return False
            
            # Выполняем команду через фабрику исполнителей
            if hasattr(self, 'command_executor_factory'):
                executor = self.command_executor_factory.create_executor(
                    command,
                    tag_manager=self.tag_manager if hasattr(self, 'tag_manager') else None,
                    tag_dialog_manager=self.tag_dialog_manager if hasattr(self, 'tag_dialog_manager') else None
                )
                
                # Передаем контекст в исполнитель
                if hasattr(executor, 'execute'):
                    result = executor.execute(command, **execution_context)
                    self.logger.info(f"Результат выполнения команды: {result}")
                    return result
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении команды: {e}")
            return False
    
    def _create_execution_context(self) -> Dict[str, Any]:
        """
        Создание контекста выполнения с флагами
        
        Returns:
            Контекст выполнения
        """
        context = {}
        
        # Добавляем FlagManager в контекст
        if hasattr(self, 'flag_manager'):
            context['flag_manager'] = self.flag_manager
        
        # Добавляем все флаги в контекст
        if hasattr(self, 'flag_manager'):
            flags = self.flag_manager.get_all_flags()
            context.update(flags)
        
        self.logger.debug(f"Создан контекст выполнения: {context}")
        return context
    
    def _process_tags(self, command: str, context: Dict[str, Any]) -> bool:
        """
        Обработка тегов в команде
        
        Args:
            command: Команда с тегами
            context: Контекст выполнения
            
        Returns:
            True если обработка прошла успешно
        """
        try:
            if not hasattr(self, 'tag_manager'):
                self.logger.warning("TagManager недоступен")
                return True
            
            # Парсим команду
            parsed_command = self.tag_manager.parse_command(command)
            
            if not parsed_command.tags:
                self.logger.debug("Теги не найдены в команде")
                return True
            
            self.logger.info(f"Найдены теги: {[tag.tag_name for tag in parsed_command.tags]}")
            
            # Валидируем теги
            if not self.tag_manager.validate_tags(parsed_command.tags):
                self.logger.error("Валидация тегов не прошла")
                return False
            
            # Обрабатываем теги
            results = self.tag_manager.process_tags(parsed_command.tags, context)
            
            # Проверяем результаты обработки
            for result in results:
                if not result.success:
                    self.logger.error(f"Ошибка обработки тега: {result.message}")
                    return False
                
                if not result.should_continue:
                    self.logger.info(f"Обработка тега остановлена: {result.message}")
                    return False
                
                # Если нужно показать диалог
                if result.data and result.data.get('show_dialog'):
                    dialog_type = result.data.get('dialog_type')
                    if dialog_type and hasattr(self, 'tag_dialog_manager'):
                        self.logger.info(f"Показываем диалог: {dialog_type}")
                        dialog_result = self.tag_dialog_manager.show_tag_dialog(dialog_type, self)
                        
                        if dialog_result == 'cancel':
                            self.logger.info("Пользователь отменил операцию через диалог")
                            return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке тегов: {e}")
            return False

    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Подсказка
        self.hint_label = QLabel("Выберите зоны окраски до начала окраски/промывки")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setObjectName("wizard_hint")
        layout.addWidget(self.hint_label)

        # Заголовок шага
        self.step_title = QLabel()
        self.step_title.setObjectName("wizard_step_title")
        layout.addWidget(self.step_title)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Панели выбора зон
        self._create_zone_panels(layout)

        # Панель управления зонами (мультизональный режим)
        self._create_zone_control_panel(layout)

        # Кнопки действий
        self.buttons_layout = QHBoxLayout()
        layout.addStretch()

        self._create_action_buttons()
        layout.addLayout(self.buttons_layout)

        # Загружаем первый шаг
        self.render_step(self.current_step_id)

    def _create_zone_panels(self, parent_layout):
        """Создание панелей выбора зон"""
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(20)

        # Левая панель
        self.left_panel = OverlayPanel(
            "left", "Верхняя левая", "Нижняя левая",
            self.wizard_config.get('image_dir', 'back'),
            self.multizone_manager
        )
        self.left_panel.state_changed.connect(self._on_zone_changed)
        self.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Правая панель
        self.right_panel = OverlayPanel(
            "right", "Верхняя правая", "Нижняя правая",
            self.wizard_config.get('image_dir', 'back'),
            self.multizone_manager
        )
        self.right_panel.state_changed.connect(self._on_zone_changed)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        panels_layout.addWidget(self.left_panel, 1)
        panels_layout.addWidget(self.right_panel, 1)
        parent_layout.addLayout(panels_layout)

    def _create_zone_control_panel(self, parent_layout):
        """Создание панели управления зонами для мультизонального режима"""
        if not self.multizone_manager:
            return
            
        zone_group = QGroupBox("🎯 Управление зонами (мультизональный режим)")
        zone_group.setObjectName("zone_control_group")
        
        zone_layout = QHBoxLayout(zone_group)
        
        # Чекбоксы для каждой зоны
        zone_names = {
            1: "Зона 1 (Верхняя левая)",
            2: "Зона 2 (Нижняя левая)", 
            3: "Зона 3 (Верхняя правая)",
            4: "Зона 4 (Нижняя правая)"
        }
        
        for zone_id, zone_name in zone_names.items():
            checkbox = QCheckBox(zone_name)
            checkbox.setObjectName(f"zone_{zone_id}_checkbox")
            checkbox.toggled.connect(lambda checked, zid=zone_id: self._on_zone_checkbox_changed(zid, checked))
            self.zone_checkboxes[zone_id] = checkbox
            zone_layout.addWidget(checkbox)
        
        # Информационная панель
        self.zone_info_label = QLabel("Выберите зоны для мультизонального режима")
        self.zone_info_label.setObjectName("zone_info_label")
        zone_layout.addWidget(self.zone_info_label)
        
        parent_layout.addWidget(zone_group)

    def _create_action_buttons(self):
        """Создание кнопок действий"""
        self.buttons_layout.addStretch()

        paint_btn = ModernButton("🎨 Начать окраску", "success")
        paint_btn.clicked.connect(lambda: self._start_sequence("paint"))

        rinse_btn = ModernButton("🧼 Начать промывку", "warning")
        rinse_btn.clicked.connect(lambda: self._start_sequence("rinse"))

        self.buttons_layout.addWidget(paint_btn)
        self.buttons_layout.addWidget(rinse_btn)

    def _on_zone_changed(self, panel_id: str, top: bool, bottom: bool):
        """Обработка изменения выбора зон (старый режим)"""
        if panel_id == 'left':
            self.zone_selected['left_top'] = top
            self.zone_selected['left_bottom'] = bottom
        elif panel_id == 'right':
            self.zone_selected['right_top'] = top
            self.zone_selected['right_bottom'] = bottom

        self.zone_selection_changed.emit(self.zone_selected)
        self.logger.info(f"Выбраны зоны: {self.zone_selected}")
        
        # Синхронизируем с мультизональным менеджером
        self._sync_with_multizone_manager()

    def _on_zone_checkbox_changed(self, zone_id: int, checked: bool):
        """Обработка изменения чекбокса зоны (мультизональный режим)"""
        if not self.multizone_manager:
            return
            
        # Получаем текущие активные зоны
        active_zones = self.multizone_manager.get_active_zones()
        
        if checked:
            if zone_id not in active_zones:
                active_zones.append(zone_id)
        else:
            if zone_id in active_zones:
                active_zones.remove(zone_id)
        
        # Устанавливаем зоны в менеджере
        if active_zones:
            success = self.multizone_manager.set_zones(active_zones)
            if success:
                self._update_zone_info()
                self.logger.info(f"Установлены мультизональные зоны: {active_zones}")
            else:
                # Откатываем изменение чекбокса
                self.zone_checkboxes[zone_id].setChecked(not checked)
                self.logger.warning(f"Не удалось установить зоны: {active_zones}")
        else:
            # Если нет активных зон, сбрасываем менеджер
            self.multizone_manager.reset_zones()
            self._update_zone_info()
            self.logger.info("Все зоны сброшены")

    def _sync_with_multizone_manager(self):
        """Синхронизация с мультизональным менеджером"""
        if not self.multizone_manager:
            return
            
        # Преобразуем старое представление в новое
        active_zones = []
        for zone_name, is_active in self.zone_selected.items():
            if is_active and zone_name in self.zone_mapping:
                active_zones.append(self.zone_mapping[zone_name])
        
        # Устанавливаем зоны в менеджере
        if active_zones:
            self.multizone_manager.set_zones(active_zones)
        else:
            self.multizone_manager.reset_zones()
        
        self._update_zone_info()

    def _update_zone_info(self):
        """Обновление информационной панели зон"""
        if not self.multizone_manager or not hasattr(self, 'zone_info_label'):
            return
            
        active_zones = self.multizone_manager.get_active_zones()
        zone_mask = self.multizone_manager.get_zone_mask()
        
        if active_zones:
            zones_text = ", ".join([f"Зона {z}" for z in active_zones])
            info_text = f"Активные зоны: {zones_text} (маска: {zone_mask:04b})"
        else:
            info_text = "Выберите зоны для мультизонального режима"
        
        self.zone_info_label.setText(info_text)

    def update_zone_status(self, zone_id: int, status: str):
        """Обновление статуса зоны в UI"""
        try:
            if not hasattr(self, 'zone_checkboxes') or zone_id not in self.zone_checkboxes:
                return
            
            checkbox = self.zone_checkboxes[zone_id]
            
            # Обновляем стиль чекбокса в зависимости от статуса
            if status == 'executing':
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: #ffc107;
                        font-weight: bold;
                    }
                    QCheckBox::indicator {
                        background-color: #ffc107;
                    }
                """)
            elif status == 'completed':
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: #28a745;
                        font-weight: bold;
                    }
                    QCheckBox::indicator {
                        background-color: #28a745;
                    }
                """)
            elif status == 'error':
                checkbox.setStyleSheet("""
                    QCheckBox {
                        color: #dc3545;
                        font-weight: bold;
                    }
                    QCheckBox::indicator {
                        background-color: #dc3545;
                    }
                """)
            else:  # inactive или active
                checkbox.setStyleSheet("")
            
            # Обновляем информационную панель
            self._update_zone_info()
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса зоны {zone_id}: {e}")

    def _start_sequence(self, sequence_type: str):
        """Запуск последовательности"""
        # Ищем подходящую последовательность
        sequence_name = self.wizard_config.get(f'{sequence_type}_sequence', '')
        if sequence_name:
            self.sequence_requested.emit(sequence_name, 0)

    def render_step(self, step_id: int):
        """Отрисовка шага мастера"""
        if step_id not in self.wizard_steps:
            return

        step = self.wizard_steps[step_id]
        self.current_step_id = step_id

        # Обновляем заголовок
        self.step_title.setText(step.get('title', ''))

        # Показываем/скрываем панели
        first_step_id = min(self.wizard_steps.keys()) if self.wizard_steps else step_id
        show_panels = (step_id == first_step_id)
        self.left_panel.setVisible(show_panels)
        self.right_panel.setVisible(show_panels)

        # Обновляем прогресс-бар
        self.progress_bar.setVisible(step.get('show_bar', False))
        if step.get('show_bar', False):
            self.progress_bar.setRange(0, 0)  # Неопределенный прогресс

        # Пересоздаем кнопки
        self._update_step_buttons(step)

        # Автозапуск последовательности если указана
        if step.get('sequence'):
            self.sequence_requested.emit(
                step['sequence'],
                step.get('auto_next', 0)
            )

    def _update_step_buttons(self, step: Dict):
        """Обновление кнопок для текущего шага"""
        # Очищаем старые кнопки
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Создаем новые кнопки
        buttons = step.get('buttons', [])
        for btn_config in buttons:
            text = btn_config.get('text', '')
            next_id = btn_config.get('next', 0)

            btn = ModernButton(text, "primary")

            if step.get('sequence') and text.startswith("▶"):
                # Кнопка запуска последовательности
                btn.clicked.connect(
                    lambda checked, seq=step['sequence'], nxt=next_id:
                    self.sequence_requested.emit(seq, nxt)
                )
            else:
                # Кнопка перехода
                btn.clicked.connect(
                    lambda checked, nid=next_id:
                    self.render_step(nid)
                )

            self.buttons_layout.addWidget(btn)

    def update_progress(self, current: int, total: int):
        """Обновление прогресса"""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.progress_bar.setVisible(True)

    def on_sequence_finished(self, success: bool, next_id: int):
        """Обработка завершения последовательности"""
        self.progress_bar.setVisible(False)

        # Разблокируем кнопки
        for i in range(self.buttons_layout.count()):
            widget = self.buttons_layout.itemAt(i).widget()
            if widget:
                widget.setEnabled(True)

        # Переходим к следующему шагу
        if success and next_id > 0:
            self.render_step(next_id)
