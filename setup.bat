@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -X utf8 scripts\manage.py setup
) else (
    python -X utf8 scripts\manage.py setup
)
set "result=%errorlevel%"
if not "%result%"=="0" echo Setup did not finish. Read the message above. Install 64-bit Python 3.12 and Ollama if missing.
pause
exit /b %result%
