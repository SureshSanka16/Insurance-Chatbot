#!/usr/bin/env python3
"""
Quick test script to verify RAG dependencies and data
"""
import sys
import os

def test_imports():
    """Test critical imports"""
    print("🧪 Testing Dependencies...")
    
    try:
        import faiss
        print("✅ FAISS imported successfully")
        print(f"   FAISS version: {faiss.__version__}")
    except ImportError as e:
        print(f"❌ FAISS import failed: {e}")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ SentenceTransformer imported successfully")
    except ImportError as e:
        print(f"❌ SentenceTransformer import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    return True

def test_data_files():
    """Test if data files exist"""
    print("📁 Checking Data Files...")
    
    faiss_index = "faiss_data/faiss.index"
    metadata_file = "faiss_data/metadata.json"
    
    if os.path.exists(faiss_index):
        size = os.path.getsize(faiss_index)
        print(f"✅ FAISS index exists: {size:,} bytes")
    else:
        print("❌ FAISS index missing")
        return False
    
    if os.path.exists(metadata_file):
        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"✅ Metadata exists: {len(metadata)} chunks")
        
        # Show sample documents
        sources = set()
        for meta in metadata:
            if 'metadata' in meta and 'source' in meta['metadata']:
                sources.add(meta['metadata']['source'])
        
        print(f"   Document sources: {list(sources)}")
        return True
    else:
        print("❌ Metadata file missing")
        return False

def test_faiss_loading():
    """Test loading FAISS index"""
    print("🔍 Testing FAISS Index Loading...")
    
    try:
        import faiss
        import json
        
        if not os.path.exists("faiss_data/faiss.index"):
            print("❌ Index file missing")
            return False
        
        index = faiss.read_index("faiss_data/faiss.index")
        print(f"✅ FAISS index loaded: {index.ntotal} vectors")
        
        with open("faiss_data/metadata.json", 'r') as f:
            metadata = json.load(f)
        print(f"✅ Metadata loaded: {len(metadata)} entries")
        
        if index.ntotal != len(metadata):
            print(f"⚠️  Index/metadata mismatch: {index.ntotal} vectors vs {len(metadata)} metadata")
        
        return index.ntotal > 0
    except Exception as e:
        print(f"❌ FAISS loading failed: {e}")
        return False

def test_embedding_model():
    """Test sentence transformer model"""
    print("🤖 Testing Embedding Model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder="faiss_data/model_cache")
        test_text = "What does vehicle insurance cover?"
        embedding = model.encode([test_text])
        
        print(f"✅ Model loaded and working")
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   Sample values: {embedding[0][:5]}")
        
        return True
    except Exception as e:
        print(f"❌ Embedding model failed: {e}")
        return False

if __name__ == "__main__":
    print("🔬 RAG System Diagnostic Test")
    print("=" * 40)
    
    all_passed = True
    
    all_passed &= test_imports()
    print()
    
    all_passed &= test_data_files()  
    print()
    
    all_passed &= test_faiss_loading()
    print()
    
    all_passed &= test_embedding_model()
    print()
    
    if all_passed:
        print("🎉 All tests passed! RAG system should be working.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    sys.exit(0 if all_passed else 1)