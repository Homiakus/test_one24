@echo off
setlocal

set BASE_DIR=C:\test_one24
set PYTHON_SCRIPT=main.py

echo Step 1: Creating instant launcher...
(
echo CreateObject^("WScript.Shell"^).Run "pythonw.exe ""%BASE_DIR%\%PYTHON_SCRIPT%""",0,0
) > "%BASE_DIR%\instant.vbs"

echo Step 2: Removing all old autostart entries...
for %%i in (FastPythonStartup PythonAutoStart QuickPython InstantPython UltraFastPython DelayedPython FastestPython) do (
    schtasks /delete /tn "%%i" /f >nul 2>&1
)
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonAutoStart" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonQuickStart" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "PythonSystemStart" /f >nul 2>&1

echo Step 3: Adding to registry autostart (fastest method)...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "InstantPython" /t REG_SZ /d "wscript.exe \"%BASE_DIR%\instant.vbs\"" /f

if %errorlevel%==0 (
    echo SUCCESS: Added to system registry autostart
    echo This is the fastest possible method - launches immediately
) else (
    echo Trying user registry...
    reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "InstantPython" /t REG_SZ /d "wscript.exe \"%BASE_DIR%\instant.vbs\"" /f
    if !errorlevel!==0 (
        echo SUCCESS: Added to user registry autostart
    ) else (
        echo ERROR: Failed to add autostart
    )
)

echo.
echo RESULT: Zero-delay autostart configured
echo Python will launch instantly when Windows starts
echo.
echo To remove: reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "InstantPython" /f
echo Or: reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "InstantPython" /f
pause