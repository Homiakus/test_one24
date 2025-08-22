"""
Страница мастера настройки
"""
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QSizePolicy, QStackedLayout
)
from PySide6.QtCore import Qt, Signal

from .base_page import BasePage
from ..widgets.modern_widgets import ModernCard, ModernButton
from ..widgets.overlay_panel import OverlayPanel


class WizardPage(BasePage):
    """Страница мастера настройки"""

    # Сигналы
    sequence_requested = Signal(str, int)  # sequence_name, next_step_id
    zone_selection_changed = Signal(dict)  # zones dict

    def __init__(self, wizard_config: Dict, parent=None):
        self.wizard_config = wizard_config
        self.wizard_steps = wizard_config.get('steps', {})
        self.current_step_id = 1
        self.waiting_next_id = None
        self.zone_selected = {
            'left_top': False,
            'left_bottom': False,
            'right_top': False,
            'right_bottom': False,
        }
        super().__init__(parent)

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
            self.wizard_config.get('image_dir', 'back')
        )
        self.left_panel.state_changed.connect(self._on_zone_changed)
        self.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Правая панель
        self.right_panel = OverlayPanel(
            "right", "Верхняя правая", "Нижняя правая",
            self.wizard_config.get('image_dir', 'back')
        )
        self.right_panel.state_changed.connect(self._on_zone_changed)
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        panels_layout.addWidget(self.left_panel, 1)
        panels_layout.addWidget(self.right_panel, 1)
        parent_layout.addLayout(panels_layout)

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
        """Обработка изменения выбора зон"""
        if panel_id == 'left':
            self.zone_selected['left_top'] = top
            self.zone_selected['left_bottom'] = bottom
        elif panel_id == 'right':
            self.zone_selected['right_top'] = top
            self.zone_selected['right_bottom'] = bottom

        self.zone_selection_changed.emit(self.zone_selected)

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
