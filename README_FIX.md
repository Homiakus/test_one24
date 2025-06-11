# 🔧 Исправление проблемы запуска на Python 3.12

## Проблема
При запуске программы на другом компьютере с Python 3.12 возникает ошибка:
```
SyntaxError: source code string cannot contain null bytes
```

## Причина
Ошибка возникает из-за наличия null bytes (нулевых байтов) в файле `main.py`, которые могут появиться при:
- Передаче файла между разными операционными системами
- Проблемах с кодировкой файла
- Копировании через некоторые текстовые редакторы

## 🚀 Автоматическое решение

### Шаг 1: Запустите скрипт исправления
```bash
python fix_encoding.py
```

Этот скрипт автоматически:
- ✅ Обнаружит и удалит null bytes
- ✅ Исправит проблемы с кодировкой
- ✅ Проверит синтаксис Python
- ✅ Создаст резервную копию поврежденного файла
- ✅ Создаст недостающие конфигурационные файлы

### Шаг 2: Установите зависимости
```bash
pip install -r requirements.txt
```

### Шаг 3: Запустите программу
```bash
python main.py
```

## 🛠️ Ручное решение

Если автоматический скрипт не помог:

### Метод 1: Через командную строку
```bash
# Windows
python -c "open('main_clean.py', 'wb').write(open('main.py', 'rb').read().replace(b'\x00', b''))"
move main_clean.py main.py

# Linux/Mac
python3 -c "open('main_clean.py', 'wb').write(open('main.py', 'rb').read().replace(b'\x00', b''))"
mv main_clean.py main.py
```

### Метод 2: Пересоздание файла
1. Откройте `main.py` в текстовом редакторе (например, Notepad++, VS Code)
2. Выделите весь текст (Ctrl+A)
3. Скопируйте (Ctrl+C)
4. Создайте новый файл
5. Вставьте содержимое (Ctrl+V)
6. Сохраните как `main.py` с кодировкой UTF-8

## 📋 Требования системы

- **Python**: 3.9+ (рекомендуется 3.10+)
- **Операционная система**: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- **Память**: Минимум 4 ГБ RAM
- **Диск**: 100 МБ свободного места

## 📦 Зависимости

Файл `requirements.txt` содержит:
```
PySide6>=6.6.0
pyserial>=3.5
GitPython>=3.1.40
tomli>=2.0.1
ruff>=0.1.8
```

## 🐛 Частые проблемы и решения

### Проблема: ModuleNotFoundError
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Проблема: Permission denied
```bash
# Windows (запустите как администратор)
pip install --user -r requirements.txt

# Linux/Mac
sudo pip3 install -r requirements.txt
```

### Проблема: SSL certificate errors
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## 📞 Получение помощи

Если проблемы продолжаются:

1. **Проверьте версию Python**:
   ```bash
   python --version
   ```

2. **Проверьте установку PySide6**:
   ```bash
   python -c "import PySide6; print('PySide6 работает')"
   ```

3. **Запустите диагностику**:
   ```bash
   python fix_encoding.py
   ```

4. **Проверьте логи**:
   - Файл `app.log` содержит детальную информацию об ошибках

## 📄 Структура проекта

```
project/
├── main.py              # Главный файл приложения
├── fix_encoding.py      # Скрипт исправления кодировки
├── requirements.txt     # Зависимости Python
├── config.toml         # Конфигурация команд
├── app.log             # Файл логов
├── docs/               # Документация
│   ├── changelog.md
│   └── tasktracker.md
└── arduino/            # Проект Arduino/PlatformIO
```

## ✅ Успешный запуск

При успешном запуске вы увидите:
- Окно приложения в полноэкранном режиме
- Темную тему PyDracula
- Боковую панель навигации
- Статус "Готов к работе" в строке состояния

## 🔄 Обновления

Приложение поддерживает автоматические обновления через Git:
1. Перейдите на страницу "🔧 Прошивка"
2. Нажмите "🔍 Проверить обновления"
3. При наличии обновлений нажмите "⬇️ Скачать обновления"

---

**Версия инструкции**: 1.0  
**Дата**: 2024-12-28  
**Совместимость**: Python 3.9+ / PySide6 6.6+ 