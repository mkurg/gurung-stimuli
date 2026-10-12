@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_workflow.py --add-recording
) else (
    py run_workflow.py --add-recording
)
pause
