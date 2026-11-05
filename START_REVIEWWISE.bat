@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=false"
title ReviewWise - local startup
pushd "%~dp0"
if errorlevel 1 goto folder_error

if not exist "scripts\manage.py" goto extract_first
if exist "runtime\python.exe" goto portable_launch
echo.
echo ReviewWise - local review analysis
echo First launch checks your existing Python and Ollama, then prepares the app.
echo Keep this window open. The application will open in your browser.
echo.

set "REVIEWWISE_ACTION=launch"
if /i "%~1"=="setup" set "REVIEWWISE_ACTION=setup"
call :find_python
if defined REVIEWWISE_PYTHON goto launch

where winget >nul 2>nul
if errorlevel 1 goto python_help
echo No compatible 64-bit Python 3.11-3.15 was found.
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $answer = [System.Windows.Forms.MessageBox]::Show('ReviewWise could not find an installed 64-bit Python 3.11-3.15. Would you like to install Python 3.12 for your Windows account?', 'ReviewWise - Python not found', 'YesNo', 'Question', 'Button2'); if ($answer -eq 'Yes') { exit 0 } else { exit 1 }"
if errorlevel 1 goto python_help
echo Installing 64-bit Python 3.12 for your Windows account...
winget install --id Python.Python.3.12 --exact --source winget --scope user --architecture x64 --accept-package-agreements --accept-source-agreements --disable-interactivity
if errorlevel 1 goto python_install_failed
call :find_python
if not defined REVIEWWISE_PYTHON goto python_help

:portable_launch
echo ReviewWise - ready-to-run Windows edition
echo Python and app packages are included. No package installation is needed.
echo Local AI is prepared in the background. Keep this window open.
"runtime\python.exe" -X utf8 "scripts\manage.py" portable %*
goto launch_result

:launch
"%REVIEWWISE_PYTHON%" -X utf8 "scripts\manage.py" %REVIEWWISE_ACTION%
:launch_result
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
call :accept_python ".venv\Scripts\python.exe"
if defined REVIEWWISE_PYTHON exit /b 0
for /f "delims=" %%P in ('where python.exe 2^>nul ^| findstr /i /v "WindowsApps"') do call :accept_python "%%P"
if defined REVIEWWISE_PYTHON exit /b 0
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*") do call :accept_python "%%~fD\python.exe"
if defined REVIEWWISE_PYTHON exit /b 0
for /f "delims=" %%P in ('py -c "import sys; print(sys.executable)" 2^>nul') do call :accept_python "%%P"
if defined REVIEWWISE_PYTHON exit /b 0
for /f "delims=" %%P in ('powershell -NoProfile -Command "Get-AppxPackage -Name PythonSoftwareFoundation.Python.3* | ForEach-Object { Join-Path $_.InstallLocation 'python.exe' }" 2^>nul') do call :accept_python "%%P"
exit /b 0

:accept_python
if defined REVIEWWISE_PYTHON exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import struct,sys; sys.exit(0 if (3,11) <= sys.version_info[:2] < (3,16) and struct.calcsize('P') == 8 else 1)" >nul 2>nul
if not errorlevel 1 set "REVIEWWISE_PYTHON=%~1"
exit /b 0

:python_install_failed
echo.
echo Windows could not install Python. Check internet access and installation permissions.
goto python_help

:python_help
echo.
echo A compatible installed 64-bit Python 3.11-3.15 could not be detected.
echo Automatic installation needs Windows App Installer / WinGet and your approval.
echo Supported Python downloads: https://www.python.org/downloads/windows/
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
