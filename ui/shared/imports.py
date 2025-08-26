"""
Общие импорты для UI модулей
"""
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
    QGroupBox, QFrame, QScrollArea, QTabWidget, QSplitter,
    QGridLayout, QFormLayout, QStackedWidget, QListWidget,
    QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QSlider, QDial, QMenu,
    QMenuBar, QToolBar, QStatusBar, QMessageBox, QDialog,
    QInputDialog, QFileDialog, QColorDialog, QFontDialog
)

from PyQt6.QtCore import (
    Qt, QTimer, QThread, QObject, QEvent, QSize, QPoint,
    QRect, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, Signal, Slot, QUrl, QDir, QFile,
    QFileInfo, QDateTime, QDate, QTime, QLocale, QTranslator
)

from PyQt6.QtGui import (
    QFont, QFontMetrics, QFontInfo, QPalette, QColor,
    QPixmap, QIcon, QPainter, QPen, QBrush, QLinearGradient,
    QRadialGradient, QConicalGradient, QTransform, QMatrix,
    QKeySequence, QShortcut, QCursor, QDrag, QDropEvent,
    QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent
)

# Standard library imports
import logging
import sys
import os
from typing import (
    Optional, List, Dict, Any, Callable, Union,
    Tuple, TypeVar, Generic
)
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Type aliases for better readability
Widget = QWidget
Layout = Union[QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout]
Button = QPushButton
Label = QLabel
LineEdit = QLineEdit
TextEdit = QTextEdit
ListWidget = QListWidget
ComboBox = QComboBox
SpinBox = QSpinBox
Dialog = QDialog
MessageBox = QMessageBox

# Common constants
DEFAULT_MARGINS = (20, 20, 20, 20)
DEFAULT_SPACING = 20
DEFAULT_BUTTON_HEIGHT = 36
DEFAULT_CARD_PADDING = 15

# Common object names for styling
OBJECT_NAMES = {
    'page_title': 'page_title',
    'card_title': 'card_title',
    'modern_card': 'modern_card',
    'primary_button': 'primary_button',
    'secondary_button': 'secondary_button',
    'success_button': 'success_button',
    'warning_button': 'warning_button',
    'danger_button': 'danger_button',
    'modern_widget': 'modern_widget'
}

# Button types
BUTTON_TYPES = {
    'primary': 'primary_button',
    'secondary': 'secondary_button', 
    'success': 'success_button',
    'warning': 'warning_button',
    'danger': 'danger_button'
}

# Common icons
ICONS = {
    'add': '➕',
    'remove': '➖',
    'edit': '✏️',
    'execute': '▶',
    'refresh': '🔄',
    'settings': '⚙️',
    'commands': '⚡',
    'sequences': '🏠',
    'firmware': '🔧',
    'designer': '🎨',
    'wizard': '🧙',
    'test': '🧪'
}
