"""
Миксины для UI компонентов
"""
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QWidget, QFrame, QPushButton, QGridLayout, QSplitter
)
from PyQt6.QtCore import pyqtSignal as Signal, Qt


class LayoutMixin:
    """Mixin for common layout functionality"""
    
    def create_page_layout(self, margins: tuple = (20, 20, 20, 20), spacing: int = 20) -> QVBoxLayout:
        """Create standard page layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout
    
    def create_horizontal_layout(self, spacing: int = 10) -> QHBoxLayout:
        """Create horizontal layout"""
        layout = QHBoxLayout()
        layout.setSpacing(spacing)
        return layout
    
    def create_grid_layout(self, spacing: int = 10) -> QGridLayout:
        """Create grid layout"""
        layout = QGridLayout()
        layout.setSpacing(spacing)
        return layout
    
    def create_splitter(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal, 
                       widgets: List[QWidget] = None) -> QSplitter:
        """Create splitter with widgets"""
        splitter = QSplitter(orientation)
        
        if widgets:
            for widget in widgets:
                splitter.addWidget(widget)
        
        return splitter


class TitleMixin:
    """Mixin for title functionality"""
    
    def create_title(self, text: str, object_name: str = "page_title") -> QLabel:
        """Create standard page title"""
        title = QLabel(text)
        title.setObjectName(object_name)
        return title
    
    def add_title_to_layout(self, layout: QVBoxLayout, text: str, object_name: str = "page_title") -> QLabel:
        """Add title to layout"""
        title = self.create_title(text, object_name)
        layout.addWidget(title)
        return title


class ScrollableMixin:
    """Mixin for scrollable content"""
    
    def create_scroll_area(self, widget: QWidget = None, frame_shape: QScrollArea.Shape = QScrollArea.Shape.NoFrame) -> QScrollArea:
        """Create scroll area"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(frame_shape)
        
        if widget:
            scroll.setWidget(widget)
        
        return scroll
    
    def create_scrollable_widget(self, layout: QVBoxLayout = None) -> QWidget:
        """Create widget for scroll area"""
        widget = QWidget()
        if layout:
            widget.setLayout(layout)
        return widget


class CardMixin:
    """Mixin for card functionality"""
    
    def create_card(self, title: str = "", parent: QWidget = None) -> 'ModernCard':
        """Create modern card"""
        from ..widgets.modern_widgets import ModernCard
        return ModernCard(title, parent)
    
    def create_card_with_layout(self, title: str, layout: QVBoxLayout) -> 'ModernCard':
        """Create card with layout"""
        card = self.create_card(title)
        card.addLayout(layout)
        return card


class SignalMixin:
    """Mixin for common signals"""
    
    # Common signals that can be used by any widget
    status_message = Signal(str, int)  # message, timeout
    terminal_message = Signal(str, str)  # message, type
    error_occurred = Signal(str, str)  # error_message, error_type
    
    def emit_status(self, message: str, timeout: int = 3000):
        """Emit status message"""
        self.status_message.emit(message, timeout)
    
    def emit_terminal(self, message: str, message_type: str = "info"):
        """Emit terminal message"""
        self.terminal_message.emit(message, message_type)
    
    def emit_error(self, error_message: str, error_type: str = "error"):
        """Emit error message"""
        self.error_occurred.emit(error_message, error_type)


class ButtonMixin:
    """Mixin for button functionality"""
    
    def create_button(self, text: str, button_type: str = "primary", 
                     icon: str = None, parent: QWidget = None) -> 'ModernButton':
        """Create modern button"""
        from ..widgets.modern_widgets import ModernButton
        return ModernButton(text, button_type, icon, parent)
    
    def create_button_grid(self, buttons: List[Dict[str, Any]], 
                          max_cols: int = 3, spacing: int = 10) -> QGridLayout:
        """Create grid of buttons"""
        grid = QGridLayout()
        grid.setSpacing(spacing)
        
        row, col = 0, 0
        for button_data in buttons:
            btn = self.create_button(
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


class ValidationMixin:
    """Mixin for input validation"""
    
    def validate_required_field(self, value: str, field_name: str) -> bool:
        """Validate required field"""
        if not value or not value.strip():
            self.emit_error(f"Поле '{field_name}' обязательно для заполнения")
            return False
        return True
    
    def validate_numeric_field(self, value: str, field_name: str, 
                             min_value: float = None, max_value: float = None) -> bool:
        """Validate numeric field"""
        try:
            num_value = float(value)
            if min_value is not None and num_value < min_value:
                self.emit_error(f"Значение поля '{field_name}' должно быть не менее {min_value}")
                return False
            if max_value is not None and num_value > max_value:
                self.emit_error(f"Значение поля '{field_name}' должно быть не более {max_value}")
                return False
            return True
        except ValueError:
            self.emit_error(f"Поле '{field_name}' должно содержать числовое значение")
            return False
