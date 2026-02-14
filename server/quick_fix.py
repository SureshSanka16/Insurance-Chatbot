"""
Quick fix script to restore RAG functionality.
Run this to fix the Q&A system immediately.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return None

def main():
    print("🔬 RAG System Quick Fix")
    print("=" * 40)
    
    # 1. Get correct Python path
    venv_python = Path("venv/Scripts/python.exe")
    if not venv_python.exists():
        print(f"❌ Virtual environment not found at: {venv_python}")
        return False
    
    print(f"✅ Found Python: {venv_python}")
    
    # 2. Install missing packages
    packages = ["faiss-cpu", "sentence-transformers", "PyPDF2", "pydantic-settings"]
    for package in packages:
        cmd = f'"{venv_python}" -m pip install {package}'
        if not run_command(cmd, f"Installing {package}"):
            return False
    
    # 3. Test imports
    test_cmd = f'''"{venv_python}" -c "
import faiss
from sentence_transformers import SentenceTransformer
import os
print('✅ All imports successful')

# Test FAISS data
if os.path.exists('faiss_data/faiss.index'):
    index = faiss.read_index('faiss_data/faiss.index')
    print(f'✅ FAISS index loaded: {{index.ntotal}} vectors')
else:
    print('❌ FAISS index not found')
"'''
    
    if not run_command(test_cmd, "Testing imports"):
        return False
        
    print()
    print("🎉 Quick fix completed! Now restart your backend:")
    print("1. Stop current backend (Ctrl+C)")
    print(f'2. Start with: "{venv_python}" -m uvicorn main:app --reload --port 8000')
    print("3. Test Q&A - it should now work!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)