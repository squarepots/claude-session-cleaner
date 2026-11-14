@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" cleaner.py --once --show-browser
pause
