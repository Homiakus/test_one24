---
title: "Быстрый старт"
description: "Краткое руководство по быстрому запуску приложения"
type: "tutorial"
audience: ["User", "Developer"]
priority: "High"
created: "2024-12-20"
updated: "2024-12-20"
tags: ["tutorial", "quick-start", "fast-setup"]
---

# ⚡ Быстрый старт

Краткое руководство для быстрого запуска приложения управления устройством.

## 🚀 За 5 минут

### 1. Установка
```bash
# Клонировать репозиторий
git clone <repository-url>
cd test_one24

# Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Установить зависимости
pip install -r requirements.txt
```

### 2. Автоматическая настройка
```bash
# Запустить мастер настройки
python docs/tutorials/setup_wizard.py
```

### 3. Запуск приложения
```bash
python main.py
```

## ⚙️ Минимальная настройка

### Конфигурация Serial порта
Отредактируйте `resources/config.toml`:
```toml
[serial_default]
port = "COM4"        # Ваш порт
baudrate = 115200
timeout = 1.0
```

### Проверка портов
```bash
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"
```

## 🎯 Первые команды

1. **Подключение**: Нажмите "Подключиться" в интерфейсе
2. **Тест**: Отправьте команду `status`
3. **Хоминг**: Выполните "Хоминг Multi" и "Хоминг RRight"
4. **Движение**: Попробуйте "Multi → OG"

## 🔧 Быстрая диагностика

### Проверка зависимостей
```bash
python -c "import PyQt6, serial, qt_material; print('Все OK')"
```

### Проверка конфигурации
```bash
python -c "import tomli; print('TOML OK')"
```

### Тест Serial
```bash
python -c "import serial; print('Serial OK')"
```

## 🚨 Частые проблемы

| Проблема | Решение |
|----------|---------|
| "ModuleNotFoundError" | `pip install -r requirements.txt` |
| "Port not found" | Проверьте список портов |
| "Connection failed" | Проверьте baudrate и порт |
| "App won't start" | Проверьте Python 3.8+ |

## 📚 Следующие шаги

- [[docs/tutorials/getting-started|Полное руководство]]
- [[docs/api/examples/index|Примеры API]]
- [[docs/runbooks/troubleshooting|Решение проблем]]

---

**Готово!** Приложение должно работать. Для подробной информации изучите [[docs/tutorials/getting-started|полное руководство]].
