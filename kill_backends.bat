@echo off
echo Killing all Python processes to clear zombie servers...
taskkill /F /IM python.exe
taskkill /F /IM uvicorn.exe
echo.
echo All processes killed. 
echo Now you can run 'run_backend.bat' cleanly.
pause
