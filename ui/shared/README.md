# UI Shared Module

Модуль с общими утилитами для UI компонентов приложения.

## Структура модуля

```
ui/shared/
├── __init__.py          # Основные импорты и экспорты
├── base_classes.py      # Базовые классы для UI компонентов
├── mixins.py           # Mixins для общего поведения
├── utils.py            # Утилиты для создания UI элементов
├── imports.py          # Оптимизированные импорты и константы
└── README.md           # Документация модуля
```

## Базовые классы

### BasePage
Базовый класс для всех страниц приложения с расширенной функциональностью.

```python
from ui.shared import BasePage

class MyPage(BasePage):
    def __init__(self, parent=None):
        super().__init__("Моя страница", parent)
    
    def _get_page_title(self) -> str:
        return "📄 Моя страница"
    
    def _setup_additional_ui(self):
        # Настройка дополнительных элементов UI
        pass
```

### BaseDialog
Базовый класс для диалоговых окон.

```python
from ui.shared import BaseDialog

class MyDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__("Мой диалог", parent)
    
    def _setup_ui(self):
        # Настройка UI диалога
        pass
    
    def get_result(self) -> Dict[str, Any]:
        return {"key": "value"}
```

## Mixins

### LayoutMixin
Предоставляет методы для создания layouts.

```python
class MyWidget(QWidget, LayoutMixin):
    def __init__(self):
        super().__init__()
        layout = self.create_page_layout()
        # или
        h_layout = self.create_horizontal_layout()
        grid = self.create_grid_layout()
```

### TitleMixin
Методы для работы с заголовками.

```python
class MyPage(BasePage, TitleMixin):
    def setup_ui(self):
        title = self.create_title("Заголовок")
        # или
        self.add_title_to_layout(layout, "Заголовок")
```

### CardMixin
Создание карточек для группировки элементов.

```python
class MyPage(BasePage, CardMixin):
    def setup_ui(self):
        card = self.create_card("Название карточки")
        # или
        card = self.create_card_with_layout("Название", layout)
```

### ButtonMixin
Создание кнопок и сеток кнопок.

```python
class MyPage(BasePage, ButtonMixin):
    def setup_ui(self):
        button = self.create_button("Текст", "primary")
        
        # Создание сетки кнопок
        button_data = [
            {'text': 'Кнопка 1', 'type': 'primary', 'clicked': self.on_click1},
            {'text': 'Кнопка 2', 'type': 'success', 'clicked': self.on_click2}
        ]
        grid = self.create_button_grid(button_data, max_cols=2)
```

### SignalMixin
Общие сигналы для UI компонентов.

```python
class MyPage(BasePage, SignalMixin):
    def show_message(self):
        self.emit_status("Сообщение", 3000)
        self.emit_terminal("Лог", "info")
        self.emit_error("Ошибка", "error")
```

### ValidationMixin
Методы валидации полей ввода.

```python
class MyPage(BasePage, ValidationMixin):
    def validate_form(self):
        if not self.validate_required_field(self.name_input.text(), "Имя"):
            return False
        
        if not self.validate_numeric_field(self.age_input.text(), "Возраст", 0, 120):
            return False
        
        return True
```

## Утилиты

### Создание UI элементов

```python
from ui.shared import (
    create_page_layout, create_title, create_card, create_button,
    create_button_grid, create_scroll_area
)

# Создание layout
layout = create_page_layout(widget, margins=(20, 20, 20, 20), spacing=20)

# Создание заголовка
title = create_title("Заголовок", "page_title")

# Создание карточки
card = create_card("Название карточки")

# Создание кнопки
button = create_button("Текст", "primary")

# Создание сетки кнопок
button_data = [
    {'text': 'Кнопка 1', 'type': 'primary', 'clicked': callback1},
    {'text': 'Кнопка 2', 'type': 'success', 'clicked': callback2}
]
grid = create_button_grid(button_data, max_cols=2)

# Создание scroll area
scroll = create_scroll_area(widget)
```

### Диалоги

```python
from ui.shared import (
    create_confirmation_dialog, create_input_dialog,
    create_error_dialog, create_info_dialog, create_warning_dialog
)

# Диалог подтверждения
if create_confirmation_dialog("Заголовок", "Сообщение", parent):
    # Пользователь подтвердил
    pass

# Диалог ввода
ok, text = create_input_dialog("Заголовок", "Подсказка", "Значение по умолчанию", parent)

# Информационные диалоги
create_error_dialog("Ошибка", "Сообщение об ошибке", parent)
create_info_dialog("Информация", "Информационное сообщение", parent)
create_warning_dialog("Предупреждение", "Предупреждающее сообщение", parent)
```

## Константы

```python
from ui.shared import (
    DEFAULT_MARGINS, DEFAULT_SPACING, DEFAULT_BUTTON_HEIGHT,
    OBJECT_NAMES, BUTTON_TYPES, ICONS
)

# Использование констант
layout.setContentsMargins(*DEFAULT_MARGINS)
layout.setSpacing(DEFAULT_SPACING)

# Объектные имена для стилизации
widget.setObjectName(OBJECT_NAMES['page_title'])

# Типы кнопок
button.setObjectName(BUTTON_TYPES['primary'])

# Иконки
title = f"{ICONS['settings']} Настройки"
```

## Пример использования

```python
from ui.shared import BasePage, LayoutMixin, TitleMixin, CardMixin, ButtonMixin

class ExamplePage(BasePage):
    def _get_page_title(self) -> str:
        return "📄 Пример страницы"
    
    def _setup_additional_ui(self):
        # Создаем карточку с информацией
        info_card = self.create_card("ℹ️ Информация")
        info_layout = self.create_page_layout(margins=(10, 10, 10, 10))
        
        title = self.create_title("Пример использования утилит")
        info_layout.addWidget(title)
        
        info_card.addLayout(info_layout)
        self.content_layout.addWidget(info_card)
        
        # Создаем карточку с кнопками
        buttons_card = self.create_card("🔘 Кнопки")
        
        button_data = [
            {'text': '➕ Добавить', 'type': 'success', 'clicked': self.on_add},
            {'text': '✏️ Редактировать', 'type': 'primary', 'clicked': self.on_edit},
            {'text': '➖ Удалить', 'type': 'danger', 'clicked': self.on_remove}
        ]
        
        button_grid = self.create_button_grid(button_data, max_cols=3)
        buttons_card.addLayout(button_grid)
        
        self.content_layout.addWidget(buttons_card)
    
    def on_add(self):
        self.show_status_message("Добавление элемента")
    
    def on_edit(self):
        self.show_status_message("Редактирование элемента")
    
    def on_remove(self):
        self.show_status_message("Удаление элемента")
```

## Преимущества использования

1. **Уменьшение дублирования кода** - общие паттерны вынесены в утилиты
2. **Единообразие интерфейса** - все компоненты используют одинаковые стили
3. **Улучшенная типизация** - все функции имеют типы
4. **Легкость поддержки** - изменения в одном месте применяются везде
5. **Быстрая разработка** - готовые утилиты для создания UI элементов
6. **Консистентность** - единые константы и объектные имена
