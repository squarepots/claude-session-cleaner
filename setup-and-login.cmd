@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv || goto :err
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :err
".venv\Scripts\python.exe" -m playwright install chromium || goto :err
".venv\Scripts\python.exe" cleaner.py --login || goto :err
".venv\Scripts\python.exe" cleaner.py --once --dry-run --show-browser || goto :err
echo Login and dry run done. Use test-once.cmd, then install.ps1.
pause
exit /b 0
:err
echo Setup or dry run failed.
pause
exit /b 1
