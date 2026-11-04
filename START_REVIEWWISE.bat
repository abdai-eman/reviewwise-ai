@echo off
setlocal EnableExtensions DisableDelayedExpansion
title ReviewWise - local startup
pushd "%~dp0"
if errorlevel 1 goto folder_error

if not exist "scripts\manage.py" goto extract_first
echo.
echo ReviewWise - local review analysis
echo First launch prepares Python, Ollama, packages and the model.
echo Keep this window open. The application will open in your browser.
echo.

set "REVIEWWISE_ACTION=launch"
if /i "%~1"=="setup" set "REVIEWWISE_ACTION=setup"
call :find_python
if defined REVIEWWISE_PYTHON goto launch

where winget >nul 2>nul
if errorlevel 1 goto python_help
echo Installing 64-bit Python 3.12 for your Windows account...
winget install --id Python.Python.3.12 --exact --source winget --scope user --architecture x64 --accept-package-agreements --accept-source-agreements --disable-interactivity
if errorlevel 1 goto python_install_failed
call :find_python
if not defined REVIEWWISE_PYTHON goto python_help

:launch
"%REVIEWWISE_PYTHON%" -X utf8 "scripts\manage.py" %REVIEWWISE_ACTION%
set "REVIEWWISE_RESULT=%errorlevel%"
if "%REVIEWWISE_RESULT%"=="0" goto done
if "%REVIEWWISE_RESULT%"=="130" goto done
echo.
echo ReviewWise could not finish. Read the message above and retry this launcher.
pause
:done
popd
exit /b %REVIEWWISE_RESULT%

:find_python
set "REVIEWWISE_PYTHON="
for %%P in ("%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe" ".venv\Scripts\python.exe") do call :accept_python "%%~P"
if defined REVIEWWISE_PYTHON exit /b 0
for /f "delims=" %%P in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do call :accept_python "%%P"
if defined REVIEWWISE_PYTHON exit /b 0
for /f "delims=" %%P in ('where python.exe 2^>nul ^| findstr /i /v "WindowsApps"') do call :accept_python "%%P"
exit /b 0

:accept_python
if defined REVIEWWISE_PYTHON exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import struct,sys; sys.exit(0 if sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8 else 1)" >nul 2>nul
if not errorlevel 1 set "REVIEWWISE_PYTHON=%~1"
exit /b 0

:python_install_failed
echo.
echo Windows could not install Python. Check internet access and installation permissions.
goto python_help

:python_help
echo.
echo Automatic installation needs Windows App Installer / WinGet.
echo Install 64-bit Python 3.12 from https://www.python.org/downloads/windows/
echo Include pip and the Python launcher. Also install Ollama from https://ollama.com/download/windows
echo Then double-click START_REVIEWWISE.bat again.
pause
popd
exit /b 1

:extract_first
echo First extract the ENTIRE project ZIP: right-click it, then choose Extract All.
echo Open the extracted folder and double-click START_REVIEWWISE.bat there.
pause
popd
exit /b 1

:folder_error
echo Extract the project into a writable folder, such as Downloads or Desktop.
pause
exit /b 1
