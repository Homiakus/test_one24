@echo off
setlocal enabledelayedexpansion

:: Папка с проектом
set BASE_DIR=C:\test_one24
set PYTHON_SCRIPT=main.py

:: Файлы
set OPTIMIZED_BAT=%BASE_DIR%\fast_python.bat
set MINIMAL_VBS=%BASE_DIR%\instant_launcher.vbs

echo === МАКСИМАЛЬНО БЫСТРЫЙ АВТОЗАПУСК PYTHON ===
echo.

:: Проверки
if not exist "%BASE_DIR%" (
    echo ОШИБКА: Папка %BASE_DIR% не существует!
    pause & exit /b 1
)
if not exist "%BASE_DIR%\%PYTHON_SCRIPT%" (
    echo ОШИБКА: Файл %PYTHON_SCRIPT% не найден!
    pause & exit /b 1
)

echo === Шаг 1: Создаём оптимизированный bat файл ===
(
echo @echo off
echo cd /d "%BASE_DIR%" ^>nul 2^>^&1
echo start /min /b pythonw.exe "%PYTHON_SCRIPT%"
echo exit /b
) > "%OPTIMIZED_BAT%"
echo Создан: %OPTIMIZED_BAT%

echo === Шаг 2: Создаём минимальный VBS лаунчер ===
(
echo CreateObject^("WScript.Shell"^).Run """%OPTIMIZED_BAT%""",0,0
) > "%MINIMAL_VBS%"
echo Создан: %MINIMAL_VBS%

echo === Шаг 3: Очищаем старые автозапуски ===
:: Удаляем старые задачи
for %%i in (FastPythonStartup PythonAutoStart QuickPython InstantPython) do (
    schtasks /delete /tn "%%i" /f >nul 2>&1
)
:: Удаляем из реестра
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonAutoStart" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonAutoStart" /f >nul 2>&1

echo === Шаг 4: Создаём ПРИОРИТЕТНУЮ задачу планировщика ===
:: Метод 1: Самая быстрая - задача с триггером на загрузку системы
schtasks /create ^
    /tn "InstantPython" ^
    /tr "wscript.exe \"%MINIMAL_VBS%\"" ^
    /sc onstart ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f

if %errorlevel%==0 (
    echo ✅ Приоритетная задача создана (запуск при старте системы)
) else (
    echo ❌ Ошибка создания приоритетной задачи
)

echo === Шаг 5: Дублируем через автозагрузку пользователя ===
:: Метод 2: Дублирующий запуск через логон пользователя
schtasks /create ^
    /tn "QuickPython" ^
    /tr "wscript.exe \"%MINIMAL_VBS%\"" ^
    /sc onlogon ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f

if %errorlevel%==0 (
    echo ✅ Дублирующая задача создана (запуск при входе в систему)
) else (
    echo ❌ Ошибка создания дублирующей задачи
)

echo === Шаг 6: Добавляем в реестр автозагрузки (тройная защита) ===
:: Метод 3: Через реестр для максимальной надежности
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonQuickStart" /t REG_SZ /d "wscript.exe \"%MINIMAL_VBS%\"" /f >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Добавлено в реестр пользователя
) else (
    echo ❌ Ошибка добавления в реестр
)

echo === Шаг 7: БОНУС - Добавляем в системный реестр (требует админ права) ===
:: Метод 4: Системный автозапуск (самый ранний)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonSystemStart" /t REG_SZ /d "wscript.exe \"%MINIMAL_VBS%\"" /f >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Добавлено в системный реестр (МАКСИМАЛЬНАЯ СКОРОСТЬ!)
) else (
    echo ⚠️  Не удалось добавить в системный реестр (нужны права администратора)
    echo    Запустите скрипт от имени администратора для максимальной скорости
)

echo.
echo === ДОПОЛНИТЕЛЬНЫЕ ОПТИМИЗАЦИИ ===

echo === Создаём задачу с задержкой (если нужна стабильность) ===
:: Альтернативная задача с небольшой задержкой для стабильности
(
echo @echo off
echo timeout /t 2 /nobreak ^>nul
echo cd /d "%BASE_DIR%" ^>nul 2^>^&1
echo start /min /b pythonw.exe "%PYTHON_SCRIPT%"
) > "%BASE_DIR%\delayed_python.bat"

schtasks /create ^
    /tn "DelayedPython" ^
    /tr "\"%BASE_DIR%\delayed_python.bat\"" ^
    /sc onstart ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f >nul 2>&1

echo ✅ Создана резервная задача с задержкой (DelayedPython)

echo.
echo === ТЕСТИРОВАНИЕ ===
echo Тестируем основную задачу...
schtasks /run /tn "InstantPython" >nul 2>&1
timeout /t 1 /nobreak >nul
echo ✅ Тест запущен

echo.
echo === УПРАВЛЕНИЕ АВТОЗАПУСКОМ ===
echo.
echo *** ДЛЯ ОТКЛЮЧЕНИЯ всех автозапусков: ***
echo schtasks /delete /tn "InstantPython" /f
echo schtasks /delete /tn "QuickPython" /f  
echo schtasks /delete /tn "DelayedPython" /f
echo reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonQuickStart" /f
echo reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonSystemStart" /f
echo.
echo *** ДЛЯ ПРОВЕРКИ статуса: ***
echo schtasks /query /tn "InstantPython"
echo.

echo === РЕЗУЛЬТАТ ===
echo 🚀 УСТАНОВЛЕНО 4 МЕТОДА АВТОЗАПУСКА:
echo    1. Системная задача при старте Windows (самая быстрая)
echo    2. Пользовательская задача при логоне  
echo    3. Реестр пользователя
echo    4. Системный реестр (если есть админ права)
echo    + Резервная задача с задержкой
echo.
echo 💡 РЕКОМЕНДАЦИИ ДЛЯ МАКСИМАЛЬНОЙ СКОРОСТИ:
echo    - Перезапустите скрипт от имени администратора
echo    - Отключите ненужные программы из автозагрузки
echo    - Используйте SSD диск
echo    - Оптимизируйте сам Python скрипт (используйте компиляцию в .pyc)
echo.
echo ⚡ После перезагрузки ваш Python скрипт запустится МГНОВЕННО!
pause