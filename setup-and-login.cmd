@echo off
setlocal
cd /d "%~dp0"
py -3 -m venv .venv || goto :err
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :err
".venv\Scripts\python.exe" -m playwright install chromium || goto :err
".venv\Scripts\python.exe" cleaner.py --login || goto :err
".venv\Scripts\python.exe" cleaner.py --once --dry-run --show-browser || goto :err
echo Setup and dry run complete. Run test-once.cmd to request deletion once.
pause
exit /b 0
:err
echo Setup or verification failed. Review the messages above.
pause
exit /b 1
