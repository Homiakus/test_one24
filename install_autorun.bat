@echo off
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_NAME=PythonSilentStartup.vbs
copy "C:\test_one24\silent_launcher.vbs" "%STARTUP_FOLDER%\%SHORTCUT_NAME%"
echo Автозапуск настроен.
pause
