"""
Utility functions for UI components
"""
from typing import Optional, List, Dict, Any, Callable
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QWidget, QFrame, QPushButton, QGridLayout,
    QMessageBox, QInputDialog, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon


def create_page_layout(widget: QWidget, margins: tuple = (20, 20, 20, 20), spacing: int = 20) -> QVBoxLayout:
    """Create standard page layout"""
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def create_title(text: str, object_name: str = "page_title") -> QLabel:
    """Create standard page title"""
    title = QLabel(text)
    title.setObjectName(object_name)
    return title


def create_scroll_area(widget: QWidget = None, frame_shape: QScrollArea.Shape = QScrollArea.Shape.NoFrame) -> QScrollArea:
    """Create scroll area"""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(frame_shape)
    
    if widget:
        scroll.setWidget(widget)
    
    return scroll


def create_card(title: str = "", parent: QWidget = None) -> 'ModernCard':
    """Create modern card"""
    from ..widgets.modern_widgets import ModernCard
    return ModernCard(title, parent)


def create_button(text: str, button_type: str = "primary", 
                 icon: str = None, parent: QWidget = None) -> 'ModernButton':
    """Create modern button"""
    from ..widgets.modern_widgets import ModernButton
    return ModernButton(text, button_type, icon, parent)


def setup_common_styles(widget: QWidget):
    """Setup common styles for widget"""
    widget.setObjectName("modern_widget")


def create_confirmation_dialog(title: str, message: str, parent: QWidget = None) -> bool:
    """Create confirmation dialog"""
    reply = QMessageBox.question(
        parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes


def create_input_dialog(title: str, label: str, text: str = "", parent: QWidget = None) -> tuple[bool, str]:
    """Create input dialog"""
    return QInputDialog.getText(parent, title, label, text=text)


def create_error_dialog(title: str, message: str, parent: QWidget = None):
    """Create error dialog"""
    QMessageBox.critical(parent, title, message)


def create_info_dialog(title: str, message: str, parent: QWidget = None):
    """Create info dialog"""
    QMessageBox.information(parent, title, message)


def create_warning_dialog(title: str, message: str, parent: QWidget = None):
    """Create warning dialog"""
    QMessageBox.warning(parent, title, message)


def create_button_grid(buttons: List[Dict[str, Any]], 
                      max_cols: int = 3, spacing: int = 10) -> QGridLayout:
    """Create grid of buttons"""
    grid = QGridLayout()
    grid.setSpacing(spacing)
    
    row, col = 0, 0
    for button_data in buttons:
        btn = create_button(
            text=button_data.get('text', ''),
            button_type=button_data.get('type', 'primary'),
            icon=button_data.get('icon')
        )
        
        if 'clicked' in button_data:
            btn.clicked.connect(button_data['clicked'])
        
        grid.addWidget(btn, row, col)
        
        col += 1
        if col >= max_cols:
            col = 0
            row += 1
    
    return grid


def create_form_layout(fields: List[Dict[str, Any]], spacing: int = 10) -> QVBoxLayout:
    """Create form layout with fields"""
    layout = QVBoxLayout()
    layout.setSpacing(spacing)
    
    for field_data in fields:
        field_type = field_data.get('type', 'line_edit')
        label_text = field_data.get('label', '')
        field_name = field_data.get('name', '')
        
        # Create label
        if label_text:
            label = QLabel(label_text)
            layout.addWidget(label)
        
        # Create field based on type
        if field_type == 'line_edit':
            from PySide6.QtWidgets import QLineEdit
            field = QLineEdit()
            field.setObjectName(field_name)
            layout.addWidget(field)
        
        elif field_type == 'text_edit':
            from PySide6.QtWidgets import QTextEdit
            field = QTextEdit()
            field.setObjectName(field_name)
            layout.addWidget(field)
        
        elif field_type == 'combo_box':
            from PySide6.QtWidgets import QComboBox
            field = QComboBox()
            field.setObjectName(field_name)
            items = field_data.get('items', [])
            field.addItems(items)
            layout.addWidget(field)
        
        elif field_type == 'spin_box':
            from PySide6.QtWidgets import QSpinBox
            field = QSpinBox()
            field.setObjectName(field_name)
            field.setRange(
                field_data.get('min', 0),
                field_data.get('max', 100)
            )
            field.setValue(field_data.get('value', 0))
            layout.addWidget(field)
    
    return layout


def create_splitter(orientation: Qt.Orientation = Qt.Orientation.Horizontal, 
                   widgets: List[QWidget] = None) -> QSplitter:
    """Create splitter with widgets"""
    splitter = QSplitter(orientation)
    
    if widgets:
        for widget in widgets:
            splitter.addWidget(widget)
    
    return splitter


def create_tab_widget(tabs: List[Dict[str, Any]]) -> 'QTabWidget':
    """Create tab widget with tabs"""
    from PySide6.QtWidgets import QTabWidget
    
    tab_widget = QTabWidget()
    
    for tab_data in tabs:
        title = tab_data.get('title', '')
        widget = tab_data.get('widget')
        icon = tab_data.get('icon')
        
        if widget:
            if icon:
                tab_widget.addTab(widget, QIcon(icon), title)
            else:
                tab_widget.addTab(widget, title)
    
    return tab_widget


def create_group_box(title: str, widget: QWidget = None) -> 'QGroupBox':
    """Create group box"""
    from PySide6.QtWidgets import QGroupBox
    
    group_box = QGroupBox(title)
    
    if widget:
        layout = QVBoxLayout(group_box)
        layout.addWidget(widget)
    
    return group_box


def create_progress_dialog(title: str, label: str, parent: QWidget = None) -> 'QProgressDialog':
    """Create progress dialog"""
    from PySide6.QtWidgets import QProgressDialog
    
    progress = QProgressDialog(label, "Отмена", 0, 100, parent)
    progress.setWindowTitle(title)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setAutoClose(True)
    progress.setAutoReset(True)
    
    return progress


def create_tool_tip(widget: QWidget, text: str, rich_text: bool = False):
    """Create tool tip for widget"""
    if rich_text:
        widget.setToolTip(f"<html><body>{text}</body></html>")
    else:
        widget.setToolTip(text)


def create_status_tip(widget: QWidget, text: str):
    """Create status tip for widget"""
    widget.setStatusTip(text)


def create_whats_this(widget: QWidget, text: str):
    """Create what's this help for widget"""
    widget.setWhatsThis(text)


def create_styled_button(text: str, button_type: str = "primary", 
                        icon: str = None, parent: QWidget = None) -> QPushButton:
    """Create styled button with modern appearance"""
    button = QPushButton(text, parent)
    
    # Устанавливаем стили в зависимости от типа
    if button_type == "primary":
        button.setObjectName("primary_button")
    elif button_type == "secondary":
        button.setObjectName("secondary_button")
    elif button_type == "success":
        button.setObjectName("success_button")
    elif button_type == "warning":
        button.setObjectName("warning_button")
    elif button_type == "danger":
        button.setObjectName("danger_button")
    else:
        button.setObjectName("default_button")
    
    # Добавляем иконку если указана
    if icon:
        button.setIcon(QIcon(icon))
    
    return button


def create_styled_label(text: str, label_type: str = "default", 
                       parent: QWidget = None) -> QLabel:
    """Create styled label with modern appearance"""
    label = QLabel(text, parent)
    
    # Устанавливаем стили в зависимости от типа
    if label_type == "title":
        label.setObjectName("title_label")
    elif label_type == "subtitle":
        label.setObjectName("subtitle_label")
    elif label_type == "heading":
        label.setObjectName("heading_label")
    elif label_type == "status":
        label.setObjectName("status_label")
    elif label_type == "error":
        label.setObjectName("error_label")
    elif label_type == "success":
        label.setObjectName("success_label")
    else:
        label.setObjectName("default_label")
    
    return label
