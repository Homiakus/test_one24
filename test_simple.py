#!/usr/bin/env python3
"""
Простой тест PyQt6 приложения
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal as Signal
from PyQt6.QtGui import QFont

class TestWindow(QMainWindow):
    """Тестовое окно"""
    
    test_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест PyQt6")
        self.setGeometry(100, 100, 800, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title = QLabel("🎉 PyQt6 работает!")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Информация
        info = QLabel("Приложение успешно запущено с PyQt6")
        info.setFont(QFont("Arial", 14))
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        # Размеры окна
        size_info = QLabel(f"Размер окна: {self.width()}x{self.height()}")
        size_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(size_info)
        
        # Золотое сечение
        golden_ratio = 1.618033988749895
        recommended_width = int(self.height() * golden_ratio)
        golden_info = QLabel(f"Рекомендуемая ширина по золотому сечению: {recommended_width}")
        golden_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(golden_info)

def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль
    app.setStyle('Fusion')
    
    # Создаем окно
    window = TestWindow()
    window.show()
    
    # Запускаем приложение
    sys.exit(app.exec())

if __name__ == "__main__":
    main()