"""
Quick fix script to install missing dependencies and test RAG.
Run this to solve the immediate Q&A issue.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"   Error: {e.stderr.strip()}")
        return False

def main():
    print("🚀 Vantage RAG Quick Fix Script")
    print("================================")
    
    # Check if we're in the right directory
    if not Path("server").exists():
        print("❌ Error: Run this from the project root (where 'server' folder is)")
        return
    
    os.chdir("server")
    
    # Install missing dependencies
    packages = [
        "faiss-cpu",
        "sentence-transformers", 
        "PyPDF2",
        "pydantic-settings"
    ]
    
    venv_pip = Path(".venv/Scripts/pip.exe")
    if not venv_pip.exists():
        print("❌ Virtual environment not found. Please create it first:")
        print("   python -m venv .venv")
        return
    
    for package in packages:
        success = run_command(
            f'"{venv_pip}" install "{package}"',
            f"Installing {package}"
        )
        if not success:
            print(f"⚠️  Warning: Failed to install {package}")
    
    # Test imports
    print(f"\n🧪 Testing imports...")
    test_script = '''
try:
    import faiss
    print("✅ FAISS imported successfully")
except ImportError as e:
    print("❌ FAISS import failed:", e)

try:
    from sentence_transformers import SentenceTransformer
    print("✅ SentenceTransformers imported successfully")
except ImportError as e:
    print("❌ SentenceTransformers import failed:", e)

try:
    import PyPDF2
    print("✅ PyPDF2 imported successfully")
except ImportError as e:
    print("❌ PyPDF2 import failed:", e)

try:
    from pydantic_settings import BaseSettings
    print("✅ Pydantic-settings imported successfully")
except ImportError as e:
    print("❌ Pydantic-settings import failed:", e)
    '''
    
    success = run_command(
        f'"{Path(".venv/Scripts/python.exe")}" -c "{test_script}"',
        "Testing package imports"
    )
    
    if success:
        print(f"\n🎉 Dependencies installed successfully!")
        print(f"\nNext steps:")
        print(f"1. Restart your backend server")
        print(f"2. Test the Q&A functionality")
        print(f"3. Follow MIGRATION_PLAN.md for full clean architecture")
    else:
        print(f"\n⚠️  Some packages may not be installed correctly.")
        print(f"   Try manual installation:")
        print(f"   .venv\\Scripts\\pip install faiss-cpu sentence-transformers PyPDF2")

if __name__ == "__main__":
    main()