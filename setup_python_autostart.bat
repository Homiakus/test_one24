@echo off
setlocal

:: Папка с проектом
set BASE_DIR=C:\test_one24

:: Файлы
set BAT_FILE=%BASE_DIR%\run_python.bat
set VBS_FILE=%BASE_DIR%\silent_launcher.vbs

echo === Шаг 1: Создаём run_python.bat ===
(
echo @echo off
echo cd /d "%BASE_DIR%"
echo start "" "pythonw.exe" main.py
echo exit
) > "%BAT_FILE%"
echo Создан: %BAT_FILE%
echo.

echo === Шаг 2: Создаём silent_launcher.vbs ===
(
echo Set WshShell = CreateObject("WScript.Shell")
echo WshShell.Run """%BAT_FILE%""", 0, False
) > "%VBS_FILE%"
echo Создан: %VBS_FILE%
echo.

echo === Шаг 3: Удаляем ярлык из папки Startup (если был) ===
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=PythonSilentStartup.vbs

if exist "%STARTUP_FOLDER%\%SHORTCUT_NAME%" (
    del "%STARTUP_FOLDER%\%SHORTCUT_NAME%"
    echo Удалён: %SHORTCUT_NAME%
) else (
    echo Ярлык не найден — пропускаем
)
echo.

echo === Шаг 4: Создаём задачу в планировщике задач (SYSTEM) ===
schtasks /create ^
    /tn "FastPythonStartup" ^
    /tr "wscript.exe \"%VBS_FILE%\"" ^
    /sc onlogon ^
    /ru SYSTEM ^
    /rl HIGHEST ^
    /f

if %errorlevel%==0 (
    echo ✅ Задача FastPythonStartup успешно создана!
) else (
    echo ❌ ОШИБКА при создании задачи!
)
echo.
echo === УСПЕХ ===
echo Скрипт %BASE_DIR%\main.py будет запускаться БЕЗ ОКНА при старте Windows, до рабочего стола.
pause
