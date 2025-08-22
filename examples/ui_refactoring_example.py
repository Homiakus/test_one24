"""
Пример использования новых UI утилит
"""
import sys
from PySide6.QtWidgets import QApplication

# Импортируем новые утилиты
from ui.shared import (
    BasePage, LayoutMixin, TitleMixin, CardMixin, ButtonMixin,
    create_page_layout, create_title, create_card, create_button,
    DEFAULT_MARGINS, DEFAULT_SPACING, ICONS
)


class ExamplePage(BasePage):
    """Пример страницы с использованием новых утилит"""
    
    def __init__(self, parent=None):
        super().__init__("Пример", parent)
    
    def _get_page_title(self) -> str:
        return f"{ICONS['test']} Пример использования утилит"
    
    def _setup_additional_ui(self):
        """Настройка дополнительных элементов UI"""
        # Создаем карточку с информацией
        info_card = self.create_card("ℹ️ Информация")
        info_layout = self.create_page_layout(margins=(10, 10, 10, 10), spacing=10)
        
        # Добавляем текст
        info_label = self.create_title("Это пример использования новых UI утилит")
        info_layout.addWidget(info_label)
        
        info_card.addLayout(info_layout)
        self.content_layout.addWidget(info_card)
        
        # Создаем карточку с кнопками
        buttons_card = self.create_card("🔘 Кнопки")
        
        # Подготавливаем данные для кнопок
        button_data = [
            {
                'text': f"{ICONS['add']} Добавить",
                'type': 'success',
                'clicked': self._on_add_clicked
            },
            {
                'text': f"{ICONS['edit']} Редактировать", 
                'type': 'primary',
                'clicked': self._on_edit_clicked
            },
            {
                'text': f"{ICONS['remove']} Удалить",
                'type': 'danger',
                'clicked': self._on_remove_clicked
            },
            {
                'text': f"{ICONS['refresh']} Обновить",
                'type': 'secondary',
                'clicked': self._on_refresh_clicked
            }
        ]
        
        # Создаем сетку кнопок
        button_grid = self.create_button_grid(button_data, max_cols=2, spacing=10)
        buttons_card.addLayout(button_grid)
        
        self.content_layout.addWidget(buttons_card)
    
    def _on_add_clicked(self):
        """Обработка нажатия кнопки Добавить"""
        self.show_status_message("Кнопка 'Добавить' нажата")
        self.show_terminal_message("Добавление элемента", "info")
    
    def _on_edit_clicked(self):
        """Обработка нажатия кнопки Редактировать"""
        self.show_status_message("Кнопка 'Редактировать' нажата")
        self.show_terminal_message("Редактирование элемента", "info")
    
    def _on_remove_clicked(self):
        """Обработка нажатия кнопки Удалить"""
        self.show_status_message("Кнопка 'Удалить' нажата")
        self.show_terminal_message("Удаление элемента", "warning")
    
    def _on_refresh_clicked(self):
        """Обработка нажатия кнопки Обновить"""
        self.show_status_message("Кнопка 'Обновить' нажата")
        self.show_terminal_message("Обновление данных", "info")


class StandaloneWidget(BasePage, LayoutMixin, TitleMixin, CardMixin):
    """Пример виджета с использованием только mixins"""
    
    def __init__(self, parent=None):
        super().__init__("Standalone", parent)
    
    def _get_page_title(self) -> str:
        return f"{ICONS['settings']} Standalone виджет"
    
    def _setup_additional_ui(self):
        """Настройка UI с использованием только mixins"""
        # Создаем карточку
        card = self.create_card("📋 Пример")
        
        # Создаем layout
        layout = self.create_page_layout(margins=(10, 10, 10, 10), spacing=10)
        
        # Добавляем заголовок
        title = self.create_title("Это standalone виджет")
        layout.addWidget(title)
        
        # Добавляем layout в карточку
        card.addLayout(layout)
        
        # Добавляем карточку в контент
        self.content_layout.addWidget(card)


def main():
    """Главная функция для демонстрации"""
    app = QApplication(sys.argv)
    
    # Создаем пример страницы
    example_page = ExamplePage()
    example_page.show()
    
    # Создаем standalone виджет
    standalone_widget = StandaloneWidget()
    standalone_widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
