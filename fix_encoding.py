#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления проблем с кодировкой main.py
Решает проблему SyntaxError: source code string cannot contain null bytes
"""

import os
import sys

def fix_encoding_issues():
    """Исправляет проблемы с кодировкой в main.py"""
    
    print("🔧 Исправление проблем с кодировкой main.py")
    print("=" * 50)
    
    # Проверяем существование файла
    if not os.path.exists('main.py'):
        print("❌ Файл main.py не найден!")
        return False
    
    try:
        # Читаем файл в бинарном режиме
        print("📖 Читаю файл main.py...")
        with open('main.py', 'rb') as f:
            data = f.read()
        
        print(f"📊 Размер файла: {len(data)} байт")
        
        # Проверяем наличие null bytes
        null_count = data.count(b'\x00')
        print(f"🔍 Найдено null bytes: {null_count}")
        
        if null_count > 0:
            print("⚠️ ВНИМАНИЕ: Обнаружены null bytes!")
            
            # Показываем позиции первых null bytes
            positions = []
            for i, byte in enumerate(data):
                if byte == 0:
                    positions.append(i)
                    if len(positions) >= 5:
                        break
            print(f"📍 Позиции null bytes (первые 5): {positions}")
            
            # Удаляем null bytes
            clean_data = data.replace(b'\x00', b'')
            print(f"🧹 После удаления null bytes: {len(clean_data)} байт")
            
            # Создаем резервную копию
            backup_name = 'main_broken.py'
            with open(backup_name, 'wb') as f:
                f.write(data)
            print(f"💾 Создана резервная копия: {backup_name}")
            
            data = clean_data
        
        # Проверяем и исправляем кодировку
        try:
            # Пытаемся декодировать как UTF-8
            text_content = data.decode('utf-8')
            print("✅ Файл корректно декодируется как UTF-8")
        except UnicodeDecodeError:
            print("⚠️ Проблема с UTF-8, пытаемся другие кодировки...")
            
            # Пробуем другие кодировки
            encodings = ['cp1251', 'cp866', 'latin1', 'utf-8-sig']
            text_content = None
            
            for encoding in encodings:
                try:
                    text_content = data.decode(encoding)
                    print(f"✅ Файл декодирован с кодировкой: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                print("❌ Не удалось декодировать файл!")
                return False
        
        # Записываем исправленный файл
        print("💾 Сохраняю исправленный файл...")
        with open('main.py', 'w', encoding='utf-8', newline='\n') as f:
            f.write(text_content)
        
        print("✅ Файл успешно исправлен!")
        
        # Проверяем что файл можно импортировать
        print("🧪 Проверяю синтаксис...")
        try:
            with open('main.py', 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Компилируем для проверки синтаксиса
            compile(code, 'main.py', 'exec')
            print("✅ Синтаксис корректен!")
            
        except SyntaxError as e:
            print(f"❌ Ошибка синтаксиса: {e}")
            return False
        except Exception as e:
            print(f"⚠️ Предупреждение: {e}")
        
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("Теперь можно запускать: python main.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

def create_requirements_if_missing():
    """Создает requirements.txt если его нет"""
    if not os.path.exists('requirements.txt'):
        print("📝 Создаю requirements.txt...")
        requirements = """PySide6>=6.6.0
pyserial>=3.5
GitPython>=3.1.40
tomli>=2.0.1
ruff>=0.1.8
"""
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(requirements)
        print("✅ Создан requirements.txt")

def create_config_if_missing():
    """Создает config.toml если его нет"""
    if not os.path.exists('config.toml'):
        print("📝 Создаю config.toml...")
        config = """[buttons]
"Тест" = "test"

[sequences]
test = ["Тест"]

[serial_default]
port = "COM1"
baudrate = 115200
"""
        with open('config.toml', 'w', encoding='utf-8') as f:
            f.write(config)
        print("✅ Создан config.toml")

if __name__ == "__main__":
    print("🚀 Утилита исправления проблем с main.py")
    print("Автор: AI Assistant")
    print("Версия: 1.0")
    print()
    
    # Исправляем main.py
    success = fix_encoding_issues()
    
    if success:
        print()
        # Создаем недостающие файлы
        create_requirements_if_missing()
        create_config_if_missing()
        
        print()
        print("📋 ИНСТРУКЦИИ ДЛЯ ЗАПУСКА:")
        print("1. Установите зависимости: pip install -r requirements.txt")
        print("2. Запустите программу: python main.py")
        print()
        print("🐛 Если проблемы продолжаются:")
        print("- Проверьте версию Python (рекомендуется 3.9+)")
        print("- Убедитесь что все зависимости установлены")
        print("- Попробуйте: python -m pip install --upgrade pip")
    else:
        print("\n❌ Не удалось исправить файл автоматически")
        print("Рекомендуется скачать чистую версию проекта") 