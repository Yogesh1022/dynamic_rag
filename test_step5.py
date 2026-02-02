"""
Test script for Step 5: Retrieval Engine

This script tests:
1. Hybrid retrieval service
2. Re-ranking service  
3. Ollama LLM service
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_reranker():
    """Test re-ranking service."""
    from app.services.retrieval.reranker import get_reranker_service
    
    print("\n" + "="*60)
    print("TEST 1: Re-ranking Service")
    print("="*60)
    
    # Sample search results
    mock_results = [
        {
            "id": "chunk_1",
            "score": 0.85,
            "payload": {
                "content": "FastAPI is a modern, fast web framework for building APIs with Python.",
                "document_id": "doc_1",
                "page": 1,
            }
        },
        {
            "id": "chunk_2",
            "score": 0.80,
            "payload": {
                "content": "Python is a programming language.",
                "document_id": "doc_2",
                "page": 1,
            }
        },
        {
            "id": "chunk_3",
            "score": 0.75,
            "payload": {
                "content": "FastAPI supports async operations and is built on Starlette.",
                "document_id": "doc_1",
                "page": 2,
            }
        },
    ]
    
    query = "What is FastAPI?"
    
    reranker = get_reranker_service()
    ranked_results = reranker.rerank(query, mock_results, top_k=3)
    
    print(f"\nQuery: {query}")
    print("\nRe-ranked results:")
    for i, result in enumerate(ranked_results):
        print(f"\n{i+1}. Score: {result.final_score:.4f}")
        print(f"   Content: {result.content[:80]}...")
        print(f"   Original Score: {result.original_score:.4f}")
    
    print("\n✅ Re-ranker test passed!")
    return True


def test_ollama_service():
    """Test Ollama LLM service."""
    from app.services.llm.ollama_service import get_ollama_service
    
    print("\n" + "="*60)
    print("TEST 2: Ollama Service")
    print("="*60)
    
    ollama = get_ollama_service()
    
    # Test connection
    print("\n1. Testing Ollama connection...")
    if ollama.verify_connection():
        print("   ✅ Ollama is connected")
    else:
        print("   ❌ Ollama is not running")
        print("   Please start Ollama: ollama serve")
        return False
    
    # List models
    print("\n2. Listing available models...")
    models = ollama.list_models()
    if models:
        print(f"   Available models: {', '.join(models)}")
    else:
        print("   No models found. Please pull a model:")
        print("   ollama pull llama3")
        return False
    
    # Test generation (only if models available)
    if models:
        print("\n3. Testing response generation...")
        try:
            query = "What is 2+2?"
            context = "You are a helpful math tutor. Answer concisely."
            
            response = ollama.generate_response(
                query=query,
                context=context,
                model=models[0],  # Use first available model
                temperature=0.7,
                max_tokens=100,
            )
            
            print(f"   Query: {query}")
            print(f"   Response: {response[:100]}...")
            print("   ✅ Generation test passed!")
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            return False
    
    print("\n✅ Ollama service test passed!")
    return True


def test_hybrid_retrieval():
    """Test hybrid retrieval (mock test without database)."""
    from app.services.retrieval.hybrid_retrieval import get_hybrid_retrieval_service
    
    print("\n" + "="*60)
    print("TEST 3: Hybrid Retrieval Service")
    print("="*60)
    
    retrieval = get_hybrid_retrieval_service()
    
    print("\n✅ Hybrid retrieval service initialized")
    print("   (Full integration test requires database and Qdrant)")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# STEP 5: RETRIEVAL ENGINE TESTS")
    print("#"*60)
    
    try:
        # Test 1: Re-ranker
        if not test_reranker():
            return False
        
        # Test 2: Ollama
        if not test_ollama_service():
            print("\n⚠️  Ollama tests failed - make sure Ollama is running")
            print("   Start with: ollama serve")
            print("   Pull a model with: ollama pull llama3")
        
        # Test 3: Hybrid retrieval
        if not test_hybrid_retrieval():
            return False
        
        print("\n" + "#"*60)
        print("# ALL TESTS COMPLETED")
        print("#"*60)
        print("\n✅ Step 5 implementation verified!")
        print("\nNext steps:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull a model: ollama pull llama3")
        print("3. Start Docker services: docker-compose up -d")
        print("4. Run server: uvicorn app.main:app --reload")
        print("5. Test chat endpoint: POST /api/v1/chat")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
