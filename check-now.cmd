@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" cleaner.py --check
".venv\Scripts\python.exe" cleaner.py --status
pause
