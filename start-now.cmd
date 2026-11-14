@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" cleaner.py --loop --min-hours 2 --max-hours 6
pause
