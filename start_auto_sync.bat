@echo off
echo Starting Auto Git Sync for MeMap+...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the auto-sync script
python auto_git_sync.py --interval 30

pause
