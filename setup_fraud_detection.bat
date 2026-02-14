@echo off
echo ========================================
echo  FRAUD DETECTION SYSTEM - QUICK START
echo ========================================
echo.

echo [1/3] Running database migration...
cd server
alembic upgrade head
if errorlevel 1 (
    echo ❌ Migration failed! Check the error above.
    pause
    exit /b 1
)

echo.
echo ✅ Migration complete!
echo.
echo [2/3] Checking fraud detection status...
python test_auto_fraud_detection.py

echo.
echo [3/3] Ready to start!
echo.
echo ========================================
echo  NEXT STEPS:
echo ========================================
echo 1. Start Backend:  run_backend.bat
echo 2. Start Frontend: run_frontend.bat  
echo 3. Login as User and submit a claim
echo 4. Upload documents to trigger fraud detection
echo 5. Login as Admin to see "IN REVIEW" status
echo 6. Wait 30-60 seconds and refresh to see risk score
echo.
echo Full documentation: FRAUD_DETECTION_IMPLEMENTATION.md
echo ========================================
pause
