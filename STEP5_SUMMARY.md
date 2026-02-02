# Step 5: Retrieval Engine - Implementation Summary

## ✅ Status: COMPLETED

## Overview
Step 5 implements the retrieval engine with hybrid search combining vector similarity and keyword matching, plus intelligent re-ranking for optimal result quality.

## Components Implemented

### 1. Re-ranking Service (`app/services/retrieval/reranker.py`)

**Purpose:** Re-rank search results to improve relevance

**Features:**
- **Query Overlap Scoring:** Measures term overlap between query and document
- **Length Penalty:** Penalizes very short or very long documents
- **Weighted Scoring:** Combines multiple signals
  - 70% original vector score
  - 20% query overlap score
  - 10% length penalty

**Key Classes:**
- `RankedResult`: Dataclass for ranked results with scores
- `RerankerService`: Main re-ranking logic
- `SimpleReranker`: Fallback reranker

**Usage:**
```python
from app.services.retrieval.reranker import get_reranker_service

reranker = get_reranker_service()
ranked = reranker.rerank(
    query="What is FastAPI?",
    results=search_results,
    top_k=5
)
```

---

### 2. Hybrid Retrieval Service (`app/services/retrieval/hybrid_retrieval.py`)

**Purpose:** Combine vector and keyword search for better retrieval

**Features:**
- **Vector Search:** Semantic similarity via Qdrant + Ollama embeddings
- **BM25 Keyword Search:** Lexical matching for exact terms
- **Score Fusion:** Weighted combination (configurable weights)
  - Default: 70% vector + 30% BM25
- **Automatic Re-ranking:** Applies reranker to combined results

**Search Modes:**
- `use_hybrid=True`: Vector + BM25 combined (recommended)
- `use_hybrid=False`: Vector search only

**Key Methods:**
- `retrieve()`: Main entry point
- `_vector_retrieve()`: Vector search only
- `_hybrid_retrieve()`: Vector + BM25 combined
- `_bm25_search()`: Keyword search using BM25Okapi
- `_combine_results()`: Weighted score fusion

**Usage:**
```python
from app.services.retrieval.hybrid_retrieval import get_hybrid_retrieval_service

retrieval = get_hybrid_retrieval_service()
results = await retrieval.retrieve(
    query="How does FastAPI work?",
    db=db_session,
    vector_store_service=qdrant,
    top_k=5,
    use_hybrid=True
)
```

---

### 3. Ollama LLM Service (`app/services/llm/ollama_service.py`)

**Purpose:** Generate responses using local Ollama LLMs

**Supported Models:**
- **llama3:** Meta's Llama 3 (general purpose)
- **mistral:** Mistral 7B (fast, efficient)
- **codellama:** Code Llama (code-related queries)
- **mixtral:** Mixtral 8x7B (complex reasoning)
- **gemma3:** Google Gemma (lightweight)

**Features:**
- **Chat API:** Multi-turn conversations with history
- **Streaming Support:** Token-by-token generation (future)
- **Connection Verification:** Health checks
- **Model Listing:** Discover available models
- **Timeout Handling:** Configurable timeouts

**Key Methods:**
- `generate_response()`: Generate text response
- `generate_streaming_response()`: Stream response chunks
- `verify_connection()`: Check Ollama server
- `list_models()`: List available models

**Usage:**
```python
from app.services.llm.ollama_service import get_ollama_service

ollama = get_ollama_service()

# Check connection
if ollama.verify_connection():
    # Generate response
    answer = ollama.generate_response(
        query="What is RAG?",
        context="RAG stands for Retrieval-Augmented Generation...",
        model="llama3",
        temperature=0.7
    )
```

---

### 4. Updated Chat Endpoint (`app/api/v1/endpoints/chat.py`)

**Full RAG Pipeline Integration:**

1. **Load Conversation History**
   - Retrieve past messages from PostgreSQL
   - Support multi-turn conversations

2. **Hybrid Retrieval**
   - Vector search (Qdrant)
   - BM25 keyword search (PostgreSQL)
   - Score fusion and re-ranking

3. **Context Assembly**
   - Build context from top-K chunks
   - Include source citations (document ID + page)

4. **LLM Response Generation**
   - Call Ollama with context + query
   - Include conversation history
   - Configurable model and temperature

5. **Conversation Persistence**
   - Save user message
   - Save assistant response
   - Track conversation metadata

**Request Example:**
```json
{
  "query": "What is FastAPI used for?",
  "conversation_id": "conv_abc123",
  "model": "llama3",
  "temperature": 0.7,
  "top_k": 5,
  "use_hybrid": true
}
```

**Response Example:**
```json
{
  "answer": "FastAPI is a modern web framework for building APIs with Python [1]. It supports async operations and is built on Starlette [2].",
  "conversation_id": "conv_abc123",
  "retrieved_documents": [
    {
      "chunk_id": "chunk_1",
      "content": "FastAPI is a modern, fast web framework...",
      "score": 0.95,
      "metadata": {
        "document_id": "doc_123",
        "page": 1
      },
      "source": "doc_123",
      "page": 1
    }
  ],
  "model": "llama3",
  "tokens_used": null,
  "latency_ms": 1234.56
}
```

---

## Configuration (in `.env`)

```env
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3
OLLAMA_TIMEOUT=60

# Retrieval
USE_HYBRID_SEARCH=true
VECTOR_WEIGHT=0.7
BM25_WEIGHT=0.3
RETRIEVAL_TOP_K=20
RERANK_TOP_K=5

# Re-ranking weights
RERANK_VECTOR_WEIGHT=0.7
RERANK_OVERLAP_WEIGHT=0.2
RERANK_LENGTH_WEIGHT=0.1
```

---

## Testing

### Run Step 5 Tests:
```bash
python test_step5.py
```

**Tests cover:**
1. ✅ Re-ranker service (query overlap, length penalty, scoring)
2. ✅ Ollama service (connection, model listing, generation)
3. ✅ Hybrid retrieval service (initialization)

### Manual Testing:

1. **Start Ollama:**
   ```bash
   ollama serve
   ```

2. **Pull a model:**
   ```bash
   ollama pull llama3
   ```

3. **Start Docker services:**
   ```bash
   docker-compose up -d
   ```

4. **Start FastAPI server:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Test chat endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is FastAPI?",
       "use_hybrid": true,
       "top_k": 3
     }'
   ```

---

## Dependencies Added

```txt
rank-bm25>=0.2.2  # BM25 keyword search
```

---

## Architecture Decisions

### Why Hybrid Search?
- **Vector Search:** Great for semantic similarity (conceptual matches)
- **BM25 Search:** Excellent for exact keyword matches (technical terms, names)
- **Combined:** Best of both worlds - handles both "what is AI?" and "find references to 'FastAPI'"

### Why Re-ranking?
- Initial search returns many candidates
- Re-ranking refines results using multiple signals
- Improves precision without sacrificing recall

### Why Ollama?
- **Local:** No API costs, no data sent to cloud
- **Fast:** Optimized inference on consumer hardware
- **Flexible:** Multiple models for different use cases
- **Private:** Data stays on your machine

---

## Performance Considerations

### Latency Breakdown:
1. **Embedding Generation:** ~50-200ms (Ollama)
2. **Vector Search:** ~10-50ms (Qdrant)
3. **BM25 Search:** ~20-100ms (PostgreSQL)
4. **Re-ranking:** ~5-20ms (CPU)
5. **LLM Generation:** ~1-5s (depends on model and length)

**Total:** ~1.5-6s per query

### Optimization Tips:
- Cache query embeddings in Redis (upcoming)
- Use smaller models for faster responses (gemma3, mistral)
- Reduce `top_k` for faster retrieval
- Use streaming for better UX during generation

---

## Next Steps (Step 6)

1. **Add Redis Caching:**
   - Cache query embeddings
   - Cache frequent queries
   - LRU eviction policy

2. **Query Expansion:**
   - LLM-powered query rewriting
   - Generate multiple query variations
   - Search with all variations

3. **Advanced Re-ranking:**
   - Cross-encoder models (Cohere, FlashRank)
   - Context-aware scoring
   - User feedback integration

4. **React Dashboard:**
   - Chat interface
   - Document upload
   - Conversation history
   - Metrics visualization

---

## Troubleshooting

### Ollama Not Connected
```
Error: Failed to connect to Ollama
Solution: Start Ollama with `ollama serve`
```

### No Models Available
```
Error: No models found
Solution: Pull a model with `ollama pull llama3`
```

### BM25 Search Failing
```
Error: BM25 search failed
Solution: Check PostgreSQL connection in docker-compose
```

### Slow Response Times
```
Issue: Responses taking >10s
Solutions:
- Use smaller model (gemma3:4b instead of llama3)
- Reduce context window
- Reduce top_k retrieval
```

---

## Summary

**Step 5 delivers:**
- ✅ Hybrid retrieval (vector + BM25)
- ✅ Intelligent re-ranking
- ✅ Ollama LLM integration
- ✅ Full RAG pipeline in chat endpoint
- ✅ Conversation history tracking
- ✅ Source citation

**Ready for production:**
- Modular, testable code
- Error handling
- Logging and monitoring
- Configurable parameters
- Fallback mechanisms

**Next:** Step 6 - React Dashboard + Advanced Features
