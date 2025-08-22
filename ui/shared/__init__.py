"""
Shared utilities for UI components
"""

from .base_classes import *
from .mixins import *
from .utils import *
from .imports import *

__all__ = [
    # Base classes
    'BasePage',
    'BaseDialog', 
    'BaseWidget',
    'BaseMainWindow',
    
    # Mixins
    'LayoutMixin',
    'TitleMixin',
    'ScrollableMixin',
    'CardMixin',
    'SignalMixin',
    'ButtonMixin',
    'ValidationMixin',
    
    # Utils
    'create_page_layout',
    'create_title',
    'create_scroll_area',
    'create_card',
    'create_button',
    'create_button_grid',
    'create_form_layout',
    'create_splitter',
    'create_tab_widget',
    'create_group_box',
    'create_progress_dialog',
    'create_confirmation_dialog',
    'create_input_dialog',
    'create_error_dialog',
    'create_info_dialog',
    'create_warning_dialog',
    'create_tool_tip',
    'create_status_tip',
    'create_whats_this',
    'setup_common_styles',
    
    # Imports and constants
    'DEFAULT_MARGINS',
    'DEFAULT_SPACING',
    'DEFAULT_BUTTON_HEIGHT',
    'DEFAULT_CARD_PADDING',
    'OBJECT_NAMES',
    'BUTTON_TYPES',
    'ICONS',
    
    # Type aliases
    'Widget',
    'Layout',
    'Button',
    'Label',
    'LineEdit',
    'TextEdit',
    'ListWidget',
    'ComboBox',
    'SpinBox',
    'Dialog',
    'MessageBox',
]
