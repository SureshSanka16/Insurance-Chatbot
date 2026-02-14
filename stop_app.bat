@echo off
echo ==========================================
echo   Vantage Insurance - App Stopper
echo ==========================================
echo.
echo Killing all running processes...

taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo.
echo All processes stopped.
pause
