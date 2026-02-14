@echo off
echo 🔄 Restarting RAG System...
echo.

cd /d "%~dp0server"

echo 📦 Installing dependencies...
venv\Scripts\pip install faiss-cpu sentence-transformers PyPDF2 pydantic-settings --quiet

echo.
echo 🧪 Testing dependencies...
venv\Scripts\python -c "import faiss; from sentence_transformers import SentenceTransformer; print('✅ Dependencies OK')"

if %errorlevel% neq 0 (
    echo ❌ Dependencies failed to install
    pause
    exit /b 1
)

echo.
echo 🚀 Starting backend server...
echo Press Ctrl+C to stop the server
echo.
venv\Scripts\python -m uvicorn main:app --reload --port 8000

pause