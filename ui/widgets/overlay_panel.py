"""
Панель с наложенными кнопками поверх изображения
"""
import os
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QStackedLayout, QSizePolicy
)


class OverlayPanel(QWidget):
    """Панель с изображением и невидимыми кнопками-зонами"""

    state_changed = Signal(str, bool, bool)  # panel_id, top_state, bottom_state

    def __init__(self, panel_id: str, top_title: str, bottom_title: str,
                 image_dir: str, parent=None):
        super().__init__(parent)

        self.panel_id = panel_id
        self.top_title = top_title
        self.bottom_title = bottom_title
        self.image_dir = Path(image_dir)

        self._pixmaps: Dict[str, QPixmap] = {}
        self._setup_ui()
        self._load_images()
        self.update_image()

    def _setup_ui(self):
        """Настройка интерфейса"""
        # Используем stacked layout для наложения
        self._stack = QStackedLayout(self)
        self._stack.setStackingMode(QStackedLayout.StackAll)
        self._stack.setContentsMargins(0, 0, 0, 0)

        # Изображение
        self._image_label = QLabel()
        self._image_label.setScaledContents(False)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self._stack.addWidget(self._image_label)

        # Контейнер для кнопок
        self._overlay = QWidget()
        self._overlay.setStyleSheet("background: transparent;")
        self._overlay.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self._stack.addWidget(self._overlay)

        # Кнопки-зоны
        self.top_btn = self._create_zone_button(self.top_title)
        self.bottom_btn = self._create_zone_button(self.bottom_title)

        # Подключаем обработчики
        self.top_btn.toggled.connect(self._on_state_changed)
        self.bottom_btn.toggled.connect(self._on_state_changed)

        # Порядок отображения
        self._image_label.lower()
        self._overlay.raise_()

    def _create_zone_button(self, title: str) -> QPushButton:
        """Создание кнопки-зоны"""
        btn = QPushButton(self._overlay)
        btn.setCheckable(True)
        btn.setAutoExclusive(False)
        btn.setToolTip(title)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 2px solid rgba(128, 128, 128, 0.3);
            }
            QPushButton:hover {
                border: 2px solid rgba(86, 138, 242, 0.5);
                background: rgba(86, 138, 242, 0.1);
            }
            QPushButton:checked {
                border: 2px solid #17a2b8;
                background: rgba(23, 162, 184, 0.2);
            }
        """)
        return btn

    def _load_images(self):
        """Загрузка изображений"""
        if not self.image_dir.exists():
            self.logger.warning(f"Директория изображений не найдена: {self.image_dir}")
            return

        # Ищем файлы с нужными именами
        image_mapping = {
            '0': 'none',      # Ничего не выбрано
            '1': 'top',       # Верхняя зона
            '2': 'bottom',    # Нижняя зона
            '1_2': 'both'     # Обе зоны
        }

        for filename, key in image_mapping.items():
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                path = self.image_dir / f"{filename}{ext}"
                if path.exists():
                    self._pixmaps[key] = QPixmap(str(path))
                    break

        # Загружаем дефолтное изображение если есть
        if not self._pixmaps:
            # Создаем пустое изображение
            self._pixmaps['none'] = QPixmap(400, 600)
            self._pixmaps['none'].fill(Qt.GlobalColor.lightGray)

    def _get_current_state_key(self) -> str:
        """Получение ключа текущего состояния"""
        if self.top_btn.isChecked() and self.bottom_btn.isChecked():
            return 'both'
        elif self.top_btn.isChecked():
            return 'top'
        elif self.bottom_btn.isChecked():
            return 'bottom'
        else:
            return 'none'

    def update_image(self):
        """Обновление изображения в соответствии с выбором"""
        key = self._get_current_state_key()
        pixmap = self._pixmaps.get(key, self._pixmaps.get('none'))

        if pixmap and not pixmap.isNull():
            # Масштабируем изображение
            scaled = self._scale_pixmap(pixmap)
            self._image_label.setPixmap(scaled)

        # Позиционируем кнопки
        self._position_buttons()

    def _scale_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """Масштабирование изображения"""
        if pixmap.isNull():
            return pixmap

        # Масштабируем с сохранением пропорций
        label_size = self._image_label.size()
        return pixmap.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

    def _position_buttons(self):
        """Позиционирование кнопок поверх изображения"""
        pixmap = self._image_label.pixmap()
        if not pixmap or pixmap.isNull():
            return

        # Получаем размеры изображения
        img_rect = self._get_image_rect()

        # Позиционируем кнопки
        self.top_btn.setGeometry(
            img_rect.x(),
            img_rect.y(),
            img_rect.width(),
            img_rect.height() // 2
        )

        self.bottom_btn.setGeometry(
            img_rect.x(),
            img_rect.y() + img_rect.height() // 2,
            img_rect.width(),
            img_rect.height() - img_rect.height() // 2
        )

    def _get_image_rect(self) -> QRect:
        """Получение прямоугольника изображения"""
        pixmap = self._image_label.pixmap()
        if not pixmap or pixmap.isNull():
            return QRect(0, 0, 0, 0)

        # Вычисляем позицию изображения с учетом центрирования
        widget_size = self.size()
        img_size = pixmap.size()

        x = (widget_size.width() - img_size.width()) // 2
        y = (widget_size.height() - img_size.height()) // 2

        return QRect(x, y, img_size.width(), img_size.height())

    def _on_state_changed(self):
        """Обработка изменения состояния"""
        self.update_image()
        self.state_changed.emit(
            self.panel_id,
            self.top_btn.isChecked(),
            self.bottom_btn.isChecked()
        )

    def resizeEvent(self, event):
        """Обработка изменения размера"""
        self.update_image()
        super().resizeEvent(event)
