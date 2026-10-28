@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\start-dev.py %*
) else (
  python scripts\start-dev.py %*
)
set "velaExit=%errorlevel%"
if not "%velaExit%"=="0" pause
exit /b %velaExit%
