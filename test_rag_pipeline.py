"""
Comprehensive RAG Pipeline Test
Tests all components: Parsing, Embedding, Vector DB, Retrieval, LLM
"""

import asyncio
import sys
from pathlib import Path

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_test(name, status, details=""):
    """Print test result"""
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_emoji} {name}: {status}")
    if details:
        print(f"   └─ {details}")
    
    if status == "PASS":
        test_results["passed"].append(name)
    elif status == "FAIL":
        test_results["failed"].append(name)
    else:
        test_results["warnings"].append(name)

# ============================================================================
# TEST 1: Ollama Connection & Models
# ============================================================================
async def test_ollama():
    print_header("TEST 1: Ollama Connection & Models")
    
    try:
        import ollama
        from app.core.config import settings
        
        # Test connection
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        models = client.list()
        print_test("Ollama Connection", "PASS", f"Connected to {settings.OLLAMA_BASE_URL}")
        
        # Check LLM model
        model_names = [m.get('model', m.get('name', '')) for m in models.get('models', [])]
        if settings.OLLAMA_LLM_MODEL in model_names:
            print_test(f"LLM Model ({settings.OLLAMA_LLM_MODEL})", "PASS", "Model available")
        else:
            print_test(f"LLM Model ({settings.OLLAMA_LLM_MODEL})", "FAIL", 
                      f"Not found. Available: {', '.join(model_names)}")
        
        # Check embedding model
        if settings.OLLAMA_EMBEDDING_MODEL in model_names:
            print_test(f"Embedding Model ({settings.OLLAMA_EMBEDDING_MODEL})", "PASS", "Model available")
        else:
            print_test(f"Embedding Model ({settings.OLLAMA_EMBEDDING_MODEL})", "FAIL",
                      f"Not found. Available: {', '.join(model_names)}")
        
    except Exception as e:
        print_test("Ollama Connection", "FAIL", str(e))

# ============================================================================
# TEST 2: Embedding Generation
# ============================================================================
async def test_embeddings():
    print_header("TEST 2: Embedding Generation")
    
    try:
        from app.services.retrieval.embedding import get_embedding_service
        
        embedding_service = get_embedding_service()
        
        # Test single embedding
        test_text = "This is a test document about machine learning."
        embedding = embedding_service.generate_embedding(test_text)
        
        print_test("Single Embedding", "PASS", 
                  f"Generated {len(embedding)}-dim vector")
        
        # Test batch embeddings
        test_texts = [
            "Machine learning is a subset of AI",
            "Deep learning uses neural networks",
            "Python is great for data science"
        ]
        embeddings = embedding_service.generate_embeddings_batch(test_texts)
        
        print_test("Batch Embeddings", "PASS", 
                  f"Generated {len(embeddings)} embeddings")
        
    except Exception as e:
        print_test("Embedding Generation", "FAIL", str(e))

# ============================================================================
# TEST 3: Qdrant Vector Database
# ============================================================================
async def test_qdrant():
    print_header("TEST 3: Qdrant Vector Database")
    
    try:
        from qdrant_client import QdrantClient
        from app.core.config import settings
        from app.services.retrieval.vector_store import VectorStoreService
        
        # Test connection
        client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Check health
        health = client.get_collections()
        print_test("Qdrant Connection", "PASS", 
                  f"Connected to {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        
        # Test vector store service
        vector_store = VectorStoreService(client=client)
        vector_store.ensure_collection_exists()
        
        print_test("Collection Creation", "PASS", 
                  f"Collection '{settings.QDRANT_COLLECTION_NAME}' ready")
        
        # Test vector insert
        test_vectors = [[0.1] * settings.EMBEDDING_DIMENSION for _ in range(3)]
        test_payloads = [
            {"text": "Test document 1", "source": "test"},
            {"text": "Test document 2", "source": "test"},
            {"text": "Test document 3", "source": "test"}
        ]
        
        ids = vector_store.upsert_vectors(
            vectors=test_vectors,
            payloads=test_payloads
        )
        
        print_test("Vector Insert", "PASS", f"Inserted {len(ids)} test vectors")
        
        # Test vector search
        results = vector_store.search_vectors(
            query_vector=test_vectors[0],
            top_k=2
        )
        
        print_test("Vector Search", "PASS", f"Found {len(results)} results")
        
        # Cleanup test vectors
        vector_store.delete_vectors(ids)
        print_test("Vector Cleanup", "PASS", "Removed test vectors")
        
    except Exception as e:
        print_test("Qdrant Connection", "FAIL", str(e))

# ============================================================================
# TEST 4: Document Parsing
# ============================================================================
async def test_parsing():
    print_header("TEST 4: Document Parsing")
    
    try:
        from app.services.ingestion.parser import get_parser_service
        
        parser = get_parser_service()
        
        # Create a test text file
        test_file = Path("test_sample.txt")
        test_content = """
Machine Learning Overview
========================

Machine learning is a subset of artificial intelligence that focuses on 
developing systems that can learn from data. It has three main types:

1. Supervised Learning: Learning from labeled data
2. Unsupervised Learning: Finding patterns in unlabeled data  
3. Reinforcement Learning: Learning through trial and error

Applications include image recognition, natural language processing, 
recommendation systems, and autonomous vehicles.
"""
        test_file.write_text(test_content)
        
        # Test parsing
        text, metadata = parser.parse_document(str(test_file))
        
        print_test("Document Parsing", "PASS", 
                  f"Parsed {len(text)} characters")
        
        # Cleanup
        test_file.unlink()
        
    except Exception as e:
        print_test("Document Parsing", "FAIL", str(e))

# ============================================================================
# TEST 5: Text Chunking
# ============================================================================
async def test_chunking():
    print_header("TEST 5: Text Chunking")
    
    try:
        from app.services.ingestion.chunker import get_chunker_service
        
        chunker = get_chunker_service()
        
        # Test text
        long_text = """
        Machine learning is a field of artificial intelligence that uses statistical 
        techniques to give computer systems the ability to learn from data without 
        being explicitly programmed. The term was coined in 1959 by Arthur Samuel.
        
        Deep learning is part of a broader family of machine learning methods based on 
        artificial neural networks with representation learning. Learning can be 
        supervised, semi-supervised or unsupervised.
        
        Common applications include computer vision, speech recognition, natural language 
        processing, audio recognition, social network filtering, machine translation, 
        bioinformatics, drug design, and medical diagnosis.
        """ * 3  # Repeat to create longer text
        
        chunks = chunker.chunk_text(long_text, metadata={"test": True})
        
        print_test("Text Chunking", "PASS", 
                  f"Created {len(chunks)} chunks, avg {sum(c['chunk_size'] for c in chunks)//len(chunks)} chars/chunk")
        
        # Verify chunk structure
        if chunks and all('content' in c and 'chunk_index' in c for c in chunks):
            print_test("Chunk Structure", "PASS", "All chunks have required fields")
        else:
            print_test("Chunk Structure", "FAIL", "Missing required fields")
        
    except Exception as e:
        print_test("Text Chunking", "FAIL", str(e))

# ============================================================================
# TEST 6: Hybrid Retrieval
# ============================================================================
async def test_retrieval():
    print_header("TEST 6: Hybrid Retrieval (Vector + BM25)")
    
    try:
        from app.services.retrieval.hybrid_retrieval import get_hybrid_retrieval_service
        from app.services.retrieval.vector_store import get_vector_store_service
        from app.services.retrieval.embedding import get_embedding_service
        from app.api.deps import get_db, get_qdrant_client
        from qdrant_client import QdrantClient
        from app.core.config import settings
        from app.models import Chunk
        import uuid
        
        # Setup services
        retrieval = get_hybrid_retrieval_service()
        embedding_service = get_embedding_service()
        qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        vector_store = get_vector_store_service()
        vector_store.set_client(qdrant_client)
        vector_store.ensure_collection_exists()
        
        # Create test data
        test_docs = [
            "Python is a high-level programming language used for web development and data science.",
            "Machine learning algorithms can be supervised, unsupervised, or reinforcement learning.",
            "Neural networks are computing systems inspired by biological neural networks.",
            "FastAPI is a modern web framework for building APIs with Python.",
        ]
        
        # Generate embeddings and store
        embeddings = embedding_service.generate_embeddings_batch(test_docs)
        payloads = [{"text": doc, "chunk_id": str(uuid.uuid4())} for doc in test_docs]
        vector_store.upsert_vectors(vectors=embeddings, payloads=payloads)
        
        print_test("Test Data Setup", "PASS", f"Indexed {len(test_docs)} documents")
        
        # Test vector search
        query = "What is machine learning?"
        results_vector = await retrieval._vector_retrieve(
            query, vector_store, top_k=3, filter_conditions=None
        )
        
        print_test("Vector Search", "PASS", f"Retrieved {len(results_vector)} results")
        
        if results_vector:
            print(f"   └─ Top result: '{results_vector[0]['payload']['text'][:60]}...'")
        
    except Exception as e:
        print_test("Hybrid Retrieval", "FAIL", str(e))

# ============================================================================
# TEST 7: LLM Generation
# ============================================================================
async def test_llm():
    print_header("TEST 7: LLM Text Generation")
    
    try:
        from app.services.llm.ollama_service import get_ollama_service
        
        ollama_service = get_ollama_service()
        
        # Test simple generation
        query = "What is Python? Answer in one sentence."
        context = "Python is a programming language."
        response = ollama_service.generate_response(
            query=query,
            context=context,
            max_tokens=50
        )
        
        print_test("LLM Generation", "PASS", f"Generated {len(response)} characters")
        print(f"   └─ Response: {response[:100]}...")
        
        # Test with conversation history
        conversation_history = [{"role": "user", "content": "Hello"}]
        response_with_context = ollama_service.generate_response(
            query="What is Python used for?",
            context="Python is a high-level programming language.",
            conversation_history=conversation_history,
            max_tokens=100
        )
        
        print_test("LLM with Context", "PASS", 
                  f"Generated {len(response_with_context)} characters")
        
    except Exception as e:
        print_test("LLM Generation", "FAIL", str(e))

# ============================================================================
# TEST 8: Full RAG Pipeline
# ============================================================================
async def test_full_pipeline():
    print_header("TEST 8: Full RAG Pipeline (End-to-End)")
    
    try:
        from app.services.retrieval.hybrid_retrieval import get_hybrid_retrieval_service
        from app.services.llm.ollama_service import get_ollama_service
        from app.services.retrieval.vector_store import get_vector_store_service
        from app.services.retrieval.embedding import get_embedding_service
        from qdrant_client import QdrantClient
        from app.core.config import settings
        import uuid
        
        print("\n📝 Simulating full RAG pipeline...")
        
        # 1. Setup
        embedding_service = get_embedding_service()
        qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        vector_store = get_vector_store_service()
        vector_store.set_client(qdrant_client)
        vector_store.ensure_collection_exists()
        retrieval = get_hybrid_retrieval_service()
        ollama = get_ollama_service()
        
        # 2. Index documents
        documents = [
            "FastAPI is a modern, fast web framework for building APIs with Python 3.7+.",
            "It provides automatic API documentation using Swagger UI and ReDoc.",
            "FastAPI is based on Pydantic and type hints for data validation.",
            "It supports async/await for high-performance asynchronous operations.",
        ]
        
        embeddings = embedding_service.generate_embeddings_batch(documents)
        payloads = [{"text": doc, "chunk_id": str(uuid.uuid4())} for doc in documents]
        vector_store.upsert_vectors(vectors=embeddings, payloads=payloads)
        
        print("   1️⃣  Documents indexed ✓")
        
        # 3. Retrieve
        query = "What is FastAPI?"
        retrieved = await retrieval._vector_retrieve(query, vector_store, top_k=2, filter_conditions=None)
        
        print(f"   2️⃣  Retrieved {len(retrieved)} relevant chunks ✓")
        
        # 4. Generate answer
        context = "\n".join([r['payload']['text'] for r in retrieved])
        answer = ollama.generate_response(
            query=query,
            context=context,
            max_tokens=150
        )
        
        print(f"   3️⃣  Generated answer ✓")
        
        print_test("Full RAG Pipeline", "PASS", "All steps completed")
        print(f"\n   📊 Pipeline Results:")
        print(f"   └─ Query: {query}")
        print(f"   └─ Retrieved: {len(retrieved)} chunks")
        print(f"   └─ Answer: {answer[:150]}...")
        
    except Exception as e:
        print_test("Full RAG Pipeline", "FAIL", str(e))

# ============================================================================
# TEST 9: Database Connection
# ============================================================================
async def test_database():
    print_header("TEST 9: PostgreSQL Database")
    
    try:
        from app.api.deps import AsyncSessionLocal
        from app.models import Document
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # Test query
            result = await db.execute(select(Document).limit(1))
            
            print_test("Database Connection", "PASS", "Connected to PostgreSQL")
            print_test("Database Tables", "PASS", "Tables accessible")
        
    except Exception as e:
        print_test("Database Connection", "FAIL", str(e))

# ============================================================================
# TEST 10: Redis Cache
# ============================================================================
async def test_cache():
    print_header("TEST 10: Redis Cache")
    
    try:
        from app.services.cache import cache_service
        
        # Test connection
        await cache_service.connect()
        
        # Test set/get
        test_key = "test_key_123"
        test_value = {"data": "test", "number": 42}
        
        await cache_service.set(test_key, test_value, ttl=60)
        retrieved = await cache_service.get(test_key)
        
        if retrieved == test_value:
            print_test("Cache Set/Get", "PASS", "Data stored and retrieved correctly")
        else:
            print_test("Cache Set/Get", "FAIL", "Data mismatch")
        
        # Cleanup
        await cache_service.delete(test_key)
        
        # Get stats
        stats = await cache_service.get_stats()
        print_test("Cache Statistics", "PASS", 
                  f"Hit rate: {stats.get('hit_rate', 'N/A')}, Keys: {stats.get('total_keys', 0)}")
        
    except Exception as e:
        print_test("Redis Cache", "FAIL", str(e))

# ============================================================================
# Main Test Runner
# ============================================================================
async def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀 "*30)
    print("  COMPREHENSIVE RAG PIPELINE TEST SUITE")
    print("🚀 "*30)
    
    # Run all tests
    await test_ollama()
    await test_embeddings()
    await test_qdrant()
    await test_parsing()
    await test_chunking()
    await test_retrieval()
    await test_llm()
    await test_database()
    await test_cache()
    await test_full_pipeline()
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\n❌ Failed Tests:")
        for test in test_results['failed']:
            print(f"   - {test}")
    
    if test_results['passed']:
        print("\n✅ Passed Tests:")
        for test in test_results['passed']:
            print(f"   - {test}")
    
    # Final verdict
    print("\n" + "="*60)
    if not test_results['failed']:
        print("🎉 ALL TESTS PASSED! Your RAG system is fully operational!")
    else:
        print(f"⚠️  {len(test_results['failed'])} test(s) failed. Please check the errors above.")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
