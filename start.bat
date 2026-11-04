@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.bat first. It creates the Python environment and downloads the model.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -X utf8 scripts\manage.py start
set "result=%errorlevel%"
if not "%result%"=="0" pause
exit /b %result%
