# Документация проекта

Этот каталог содержит документацию для приложения управления устройством.

## Структура документации

- `index.rst` - Главная страница документации
- `conf.py` - Конфигурация Sphinx
- `Makefile` - Команды для генерации документации
- `api/` - Автогенерированная API документация
- `_build/` - Сгенерированные файлы документации

## Генерация документации

### Автоматическая генерация

Используйте скрипт для полной генерации:

```bash
python scripts/generate_docs.py
```

### Ручная генерация

1. **Очистка старых файлов:**
   ```bash
   cd docs
   make clean
   ```

2. **Генерация HTML документации:**
   ```bash
   make html
   ```

3. **Генерация PDF документации:**
   ```bash
   make pdf
   ```

4. **Запуск локального сервера для просмотра:**
   ```bash
   make serve
   ```

## Проверка типов

### Автоматическая проверка

```bash
mypy core ui utils main.py
```

### Настройка IDE

Для лучшей поддержки типов в IDE:

1. Установите mypy: `pip install mypy`
2. Настройте IDE для использования mypy
3. Включите проверку типов в реальном времени

## Структура кода

### Type Hints

Все функции и методы должны иметь аннотации типов:

```python
def process_data(data: List[str], config: Dict[str, Any]) -> bool:
    """
    Обработка данных.
    
    Args:
        data: Список строк для обработки
        config: Конфигурация обработки
        
    Returns:
        True если обработка успешна
    """
    pass
```

### Docstrings

Используйте Google/Sphinx формат для документации:

```python
def calculate_sum(a: int, b: int) -> int:
    """
    Вычисляет сумму двух чисел.
    
    Args:
        a: Первое число
        b: Второе число
        
    Returns:
        Сумма a и b
        
    Raises:
        ValueError: Если числа отрицательные
        
    Example:
        >>> calculate_sum(2, 3)
        5
    """
    return a + b
```

## Инструменты разработки

### Pre-commit hooks

Установите pre-commit hooks для автоматической проверки:

```bash
pip install pre-commit
pre-commit install
```

### Форматирование кода

Используйте black для форматирования:

```bash
black core ui utils main.py
```

### Линтинг

Используйте flake8 для проверки стиля:

```bash
flake8 core ui utils main.py
```

## Покрытие документацией

Для проверки покрытия документацией:

```bash
cd docs
make doc-coverage
```

## Обновление документации

При изменении кода:

1. Обновите docstrings
2. Добавьте type hints
3. Запустите генерацию документации
4. Проверьте типы с mypy

## Полезные команды

```bash
# Полная проверка проекта
mypy core ui utils main.py && flake8 core ui utils main.py && black --check core ui utils main.py

# Генерация документации с проверкой типов
python scripts/generate_docs.py

# Запуск всех тестов
python -m pytest tests/

# Форматирование всего проекта
black .
isort .
```
