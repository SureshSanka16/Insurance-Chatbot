@echo off
cd /d "%~dp0"
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   Vantage Insurance - One-Click App Launcher
echo ============================================================
echo.

:: ---------------------------------------------------------------------------
:: 1. Python: ensure virtual environment exists
:: ---------------------------------------------------------------------------
echo [1/5] Checking Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo        Creating .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create venv. Ensure Python 3.10+ is installed.
        pause
        exit /b 1
    )
)
echo        OK .venv found.
echo.

:: ---------------------------------------------------------------------------
:: 2. Install / upgrade backend dependencies (server/requirements.txt)
:: ---------------------------------------------------------------------------
echo [2/5] Installing backend dependencies (this may take a few minutes)...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --no-input -r server\requirements.txt
if errorlevel 1 (
    echo [ERROR] Backend dependency install failed.
    pause
    exit /b 1
)
echo        OK Backend dependencies installed.
echo.

:: ---------------------------------------------------------------------------
:: 3. Node: ensure frontend dependencies exist
:: ---------------------------------------------------------------------------
echo [3/5] Checking frontend dependencies...
if not exist "node_modules" (
    echo        Running npm install...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Ensure Node.js is installed.
        pause
        exit /b 1
    )
) else (
    echo        OK node_modules found.
)
echo.

:: ---------------------------------------------------------------------------
:: 4. Start backend (new window)
:: ---------------------------------------------------------------------------
echo [4/5] Starting backend server (port 8000)...
start "Vantage Backend" cmd /k "cd /d "%~dp0server" && "%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul
echo        Backend window opened.
echo.

:: ---------------------------------------------------------------------------
:: 5. Start frontend (new window)
:: ---------------------------------------------------------------------------
echo [5/5] Starting frontend server (port 3000)...
start "Vantage Frontend" cmd /k "cd /d "%~dp0" && npm run dev"
timeout /t 2 /nobreak >nul
echo        Frontend window opened.
echo.

:: ---------------------------------------------------------------------------
:: Done
:: ---------------------------------------------------------------------------
echo ============================================================
echo   App started.
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:3000
echo   API docs: http://127.0.0.1:8000/docs
echo ============================================================
echo.
echo Keep the two opened windows running. Close them to stop the app.
echo.
echo Optional: Add OPENROUTER_API_KEY in server\.env for AI copilot.
echo.
pause
