@echo off
cd /d "%~dp0trial_reference"
"C:\Users\Sofya\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" launch_workflow.py
if errorlevel 1 pause
