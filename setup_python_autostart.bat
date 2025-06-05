@echo off
setlocal enabledelayedexpansion

set BASE_DIR=C:\test_one24
set PYTHON_SCRIPT=main.py

set FAST_BAT=%BASE_DIR%\fast_python.bat
set MINIMAL_VBS=%BASE_DIR%\launcher.vbs

if not exist "%BASE_DIR%" (
    echo ERROR: Folder %BASE_DIR% does not exist!
    pause & exit /b 1
)
if not exist "%BASE_DIR%\%PYTHON_SCRIPT%" (
    echo ERROR: File %PYTHON_SCRIPT% not found!
    pause & exit /b 1
)

echo Step 1: Creating optimized bat file...
(
echo @echo off
echo cd /d "%BASE_DIR%" ^>nul 2^>^&1
echo start /min /b pythonw.exe "%PYTHON_SCRIPT%"
echo exit /b
) > "%FAST_BAT%"

echo Step 2: Creating minimal VBS launcher...
(
echo CreateObject^("WScript.Shell"^).Run """%FAST_BAT%""",0,0
) > "%MINIMAL_VBS%"

echo Step 3: Removing all existing autostart entries...
for %%i in (FastPythonStartup PythonAutoStart QuickPython InstantPython UltraFastPython DelayedPython) do (
    schtasks /delete /tn "%%i" /f >nul 2>&1
)
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonAutoStart" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonQuickStart" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonSystemStart" /f >nul 2>&1

echo Step 4: Creating SINGLE fastest autostart method...
schtasks /create ^
    /tn "FastestPython" ^
    /tr "wscript.exe \"%MINIMAL_VBS%\"" ^
    /sc onstart ^
    /ru "%USERNAME%" ^
    /rl HIGHEST ^
    /f

if %errorlevel%==0 (
    echo SUCCESS: Single fastest task created!
    echo Testing launch...
    schtasks /run /tn "FastestPython" >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo Test completed.
) else (
    echo ERROR: Failed to create task!
)

echo.
echo RESULT: Single autostart method configured
echo Your Python script will launch instantly on Windows boot
echo.
echo To disable: schtasks /delete /tn "FastestPython" /f
echo To check status: schtasks /query /tn "FastestPython"
pause