# Test Ollama Connection Script

import sys
sys.path.insert(0, ".")

from app.services.retrieval.embedding import get_embedding_service
import logging

logging.basicConfig(level=logging.INFO)

def test_ollama():
    """Test Ollama embedding service connection."""
    try:
        print("🔄 Testing Ollama connection...")
        
        embedding_service = get_embedding_service()
        
        # Verify connection
        if embedding_service.verify_connection():
            print("✅ Ollama connection successful!")
            
            # Get embedding dimension
            dim = embedding_service.get_embedding_dimension()
            print(f"📊 Embedding dimension: {dim}")
            
            # Test embedding
            test_text = "This is a test document for RAG system."
            embedding = embedding_service.generate_embedding(test_text)
            print(f"✅ Generated test embedding with {len(embedding)} dimensions")
            
            return True
        else:
            print("❌ Ollama connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure Ollama is running:")
        print("   - Start Ollama: ollama serve")
        print("   - Pull model: ollama pull nomic-embed-text")
        return False


if __name__ == "__main__":
    success = test_ollama()
    sys.exit(0 if success else 1)
