@echo off
cd /d "%~dp0"
echo ==========================================
echo   Vantage Insurance - Backend Launcher
echo ==========================================
echo.
echo 1. Checking environment...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv
    echo Please run: python -m venv .venv
    pause
    exit /b
)

echo 2. Installing/Verifying dependencies...
".venv\Scripts\python.exe" -m pip install --no-input -r server\requirements.txt

echo.
echo 3. Starting Uvicorn Server...
cd server
"..\.venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000

pause
