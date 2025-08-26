"""
Базовые классы для UI компонентов
"""
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMainWindow
from PyQt6.QtCore import pyqtSignal as Signal, Qt


class BaseWidget(QWidget):
    """Base widget class with common functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()
    
    @abstractmethod
    def _setup_ui(self):
        """Setup the widget UI - must be implemented by subclasses"""
        pass
    
    def refresh(self):
        """Refresh widget content"""
        pass
    
    def cleanup(self):
        """Cleanup resources"""
        pass


class BasePage(BaseWidget):
    """Base class for all application pages"""
    
    # Common signals for all pages
    status_message = Signal(str, int)  # message, timeout
    terminal_message = Signal(str, str)  # message, type
    page_loaded = Signal(str)  # page_name
    page_closed = Signal(str)  # page_name
    
    def __init__(self, page_name: str = "", parent=None):
        self.page_name = page_name or self.__class__.__name__
        super().__init__(parent)
        self.page_loaded.emit(self.page_name)
    
    def closeEvent(self, event):
        """Handle page close event"""
        self.page_closed.emit(self.page_name)
        self.cleanup()
        super().closeEvent(event)
    
    def showEvent(self, event):
        """Handle page show event"""
        self.refresh()
        super().showEvent(event)


class BaseDialog(QDialog):
    """Base dialog class with common functionality"""
    
    dialog_accepted = Signal(dict)  # result_data
    dialog_rejected = Signal()
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()
    
    @abstractmethod
    def _setup_ui(self):
        """Setup the dialog UI - must be implemented by subclasses"""
        pass
    
    def get_result(self) -> Dict[str, Any]:
        """Get dialog result data"""
        return {}
    
    def accept(self):
        """Accept dialog with result data"""
        result = self.get_result()
        self.dialog_accepted.emit(result)
        super().accept()
    
    def reject(self):
        """Reject dialog"""
        self.dialog_rejected.emit()
        super().reject()


class BaseMainWindow(QMainWindow):
    """Base main window class with common functionality"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_ui()
        self._setup_connections()
    
    @abstractmethod
    def _setup_ui(self):
        """Setup the main window UI"""
        pass
    
    def _setup_connections(self):
        """Setup signal connections"""
        pass
    
    def closeEvent(self, event):
        """Handle application close event"""
        self.logger.info("Application closing")
        super().closeEvent(event)
