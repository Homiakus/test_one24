@echo off
chcp 65001 > nul
echo.
echo 🔧 Исправление проблем с кодировкой main.py
echo ===============================================
echo.

REM Проверяем наличие Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.9+ с python.org
    pause
    exit /b 1
)

echo ✅ Python найден
python --version

REM Проверяем наличие main.py
if not exist "main.py" (
    echo ❌ Файл main.py не найден в текущей директории!
    echo Убедитесь что вы запускаете скрипт из папки с проектом
    pause
    exit /b 1
)

echo ✅ Файл main.py найден

REM Запускаем скрипт исправления
echo.
echo 🚀 Запуск исправления...
python fix_encoding.py

REM Проверяем результат
if errorlevel 1 (
    echo.
    echo ❌ Ошибка при исправлении файла
    echo Попробуйте ручное исправление или скачайте проект заново
    pause
    exit /b 1
)

echo.
echo ✅ Исправление завершено!
echo.

REM Проверяем зависимости
echo 📦 Проверка зависимостей...
python -c "import PySide6" > nul 2>&1
if errorlevel 1 (
    echo ⚠️ PySide6 не установлен
    echo 📥 Устанавливаю зависимости...
    pip install -r requirements.txt
) else (
    echo ✅ Зависимости установлены
)

echo.
echo 🎉 Готово! Теперь можно запускать программу:
echo    python main.py
echo.
pause 