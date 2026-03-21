@echo off
REM Start Request Capture Tool (Windows)
REM Usage: start_capture.bat [options]
REM
REM Options:
REM   --project, -P   Project name (skips interactive selection)
REM   --new, -n       Create new project if doesn't exist
REM   --port, -p      Proxy port (default: 8080)
REM   --verbose, -v   Show headers and bodies
REM   --all, -a       Capture all including static assets
REM   --web           Use mitmproxy web UI

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    .venv\Scripts\pip.exe install -r requirements.txt
)

REM Run capture with project management
.venv\Scripts\python.exe run_capture.py %*

pause
