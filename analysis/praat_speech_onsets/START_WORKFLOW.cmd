@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_workflow.py %*
) else (
    py run_workflow.py %*
)
if errorlevel 1 pause
