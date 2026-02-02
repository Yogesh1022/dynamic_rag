# 🚀 Quick Reference Guide: FastAPI RAG System

## Table of Contents
1. [Starting the System](#starting-the-system)
2. [API Endpoints](#api-endpoints)
3. [Configuration](#configuration)
4. [Troubleshooting](#troubleshooting)
5. [Common Tasks](#common-tasks)

---

## Starting the System

### 1. Start Infrastructure Services:
```bash
# Start Qdrant, PostgreSQL, Redis
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Start Ollama:
```bash
# Start Ollama server
ollama serve

# Pull required models (in another terminal)
ollama pull llama3
ollama pull nomic-embed-text
```

### 3. Activate Virtual Environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4. Start FastAPI Server:
```bash
uvicorn app.main:app --reload
```

### 5. Verify Everything:
```bash
# Test Ollama
python test_ollama.py

# Test Step 5
python test_step5.py

# Check API health
curl http://localhost:8000/health
```

---

## API Endpoints

### Base URL: `http://localhost:8000`

### 1. Health Check
```bash
GET /health

# Example
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "RAG system is running"
}
```

---

### 2. Upload Document
```bash
POST /api/v1/documents/upload

# Example
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@path/to/document.pdf"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_type": "pdf",
  "file_size": 102400,
  "status": "processing",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### 3. List Documents
```bash
GET /api/v1/documents/

# Example
curl http://localhost:8000/api/v1/documents/
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 102400,
    "status": "completed",
    "total_chunks": 25,
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

---

### 4. Delete Document
```bash
DELETE /api/v1/documents/{document_id}

# Example
curl -X DELETE http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

---

### 5. Chat (RAG Query)
```bash
POST /api/v1/chat

# Example
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is FastAPI?",
    "conversation_id": null,
    "model": "llama3",
    "temperature": 0.7,
    "top_k": 5,
    "use_hybrid": true
  }'
```

**Request Body:**
```json
{
  "query": "What is FastAPI?",           // Required: User question
  "conversation_id": null,               // Optional: For multi-turn chat
  "model": "llama3",                     // Optional: LLM model (default: llama3)
  "temperature": 0.7,                    // Optional: 0.0-1.0 (default: 0.7)
  "top_k": 5,                            // Optional: Number of chunks (default: 5)
  "use_hybrid": true                     // Optional: Hybrid search (default: true)
}
```

**Response:**
```json
{
  "answer": "FastAPI is a modern web framework for building APIs with Python [1].",
  "conversation_id": "conv_abc123",
  "retrieved_documents": [
    {
      "chunk_id": "chunk_1",
      "content": "FastAPI is a modern, fast (high-performance)...",
      "score": 0.95,
      "metadata": {
        "document_id": "doc_123",
        "page": 1,
        "chunk_index": 0
      },
      "source": "doc_123",
      "page": 1
    }
  ],
  "model": "llama3",
  "tokens_used": null,
  "latency_ms": 2345.67
}
```

---

## Configuration

### Environment Variables (`.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=llama3
OLLAMA_TIMEOUT=60

# Retrieval Settings
USE_HYBRID_SEARCH=true
VECTOR_WEIGHT=0.7
BM25_WEIGHT=0.3
RETRIEVAL_TOP_K=20
RERANK_TOP_K=5

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Security
SECRET_KEY=your-secret-key-here
API_KEY_NAME=X-API-Key

# Uploads
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=["pdf","png","jpg","jpeg","tiff"]
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Problem: Ollama connection failed

**Error:**
```
Failed to connect to Ollama
```

**Solution:**
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

---

### Problem: No models available

**Error:**
```
No models found
```

**Solution:**
```bash
# Pull required models
ollama pull llama3
ollama pull nomic-embed-text

# Verify models
ollama list
```

---

### Problem: Database connection error

**Error:**
```
Could not connect to PostgreSQL
```

**Solution:**
```bash
# Check Docker services
docker-compose ps

# Restart if needed
docker-compose restart db

# Check logs
docker-compose logs db
```

---

### Problem: Qdrant connection error

**Error:**
```
Failed to connect to Qdrant
```

**Solution:**
```bash
# Check Qdrant status
docker-compose ps qdrant

# Restart if needed
docker-compose restart qdrant

# Verify connection
curl http://localhost:6333/collections
```

---

### Problem: Slow responses

**Issue:** Chat responses take >10 seconds

**Solutions:**
1. **Use smaller model:**
   ```env
   OLLAMA_LLM_MODEL=mistral  # Faster than llama3
   ```

2. **Reduce retrieval:**
   ```env
   RETRIEVAL_TOP_K=10  # Instead of 20
   RERANK_TOP_K=3      # Instead of 5
   ```

3. **Lower temperature:**
   ```json
   {
     "temperature": 0.3  // More deterministic, faster
   }
   ```

---

### Problem: Out of memory

**Error:**
```
Ollama out of memory
```

**Solution:**
```bash
# Use smaller model
ollama pull gemma3:4b  # 4B parameters instead of 7B

# Update .env
OLLAMA_LLM_MODEL=gemma3:4b
```

---

## Common Tasks

### Task 1: Add a New Document

```bash
# 1. Upload PDF
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@mydocument.pdf"

# 2. Wait for processing (check logs)
# Processing happens in background

# 3. Verify document
curl http://localhost:8000/api/v1/documents/

# 4. Query the document
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the document"}'
```

---

### Task 2: Have a Multi-Turn Conversation

```bash
# 1. First message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}' \
  > response1.json

# 2. Extract conversation_id
CONV_ID=$(cat response1.json | jq -r '.conversation_id')

# 3. Follow-up message (same conversation)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Can you explain more?\",
    \"conversation_id\": \"$CONV_ID\"
  }"
```

---

### Task 3: Switch LLM Models

```bash
# Use different models for different tasks

# Fast responses (mistral)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Quick fact check", "model": "mistral"}'

# Code-related (codellama)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain this code", "model": "codellama"}'

# Complex reasoning (mixtral)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze this pattern", "model": "mixtral"}'
```

---

### Task 4: Debug Retrieval

```bash
# 1. Enable debug logging
# Edit .env:
LOG_LEVEL=DEBUG

# 2. Restart server
# Ctrl+C then:
uvicorn app.main:app --reload

# 3. Make query and check logs
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query"}'

# 4. Check terminal for debug logs
# You'll see:
# - Embedding generation time
# - Vector search results
# - BM25 search results
# - Re-ranking scores
# - LLM generation time
```

---

### Task 5: Backup Data

```bash
# 1. Backup PostgreSQL
docker exec dynamic_rag_db_1 pg_dump -U raguser ragdb > backup.sql

# 2. Backup Qdrant
docker exec dynamic_rag_qdrant_1 tar -czf /tmp/qdrant_backup.tar.gz /qdrant/storage
docker cp dynamic_rag_qdrant_1:/tmp/qdrant_backup.tar.gz ./qdrant_backup.tar.gz

# 3. Backup uploads
tar -czf uploads_backup.tar.gz ./uploads/
```

---

### Task 6: Clean Up

```bash
# Delete all documents
curl -X DELETE http://localhost:8000/api/v1/documents/all

# Or via Docker (nuclear option)
docker-compose down -v  # Removes all data!
docker-compose up -d
python init_db.py       # Reinitialize
```

---

## Python Usage Examples

### Example 1: Upload and Query (Python)

```python
import requests

# Upload document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        files={'file': f}
    )
    doc_id = response.json()['id']

# Wait for processing (poll status)
import time
while True:
    response = requests.get('http://localhost:8000/api/v1/documents/')
    docs = response.json()
    doc = next(d for d in docs if d['id'] == doc_id)
    if doc['status'] == 'completed':
        break
    time.sleep(1)

# Query
response = requests.post(
    'http://localhost:8000/api/v1/chat',
    json={
        'query': 'What is in this document?',
        'top_k': 3
    }
)
print(response.json()['answer'])
```

---

### Example 2: Conversation (Python)

```python
import requests

BASE_URL = 'http://localhost:8000/api/v1/chat'

# First message
response = requests.post(BASE_URL, json={
    'query': 'Explain RAG in simple terms'
})
result = response.json()
conv_id = result['conversation_id']
print(f"Assistant: {result['answer']}\n")

# Follow-up messages
messages = [
    "Can you give an example?",
    "What are the benefits?",
    "Any limitations?"
]

for msg in messages:
    response = requests.post(BASE_URL, json={
        'query': msg,
        'conversation_id': conv_id
    })
    result = response.json()
    print(f"You: {msg}")
    print(f"Assistant: {result['answer']}\n")
```

---

## Advanced Configuration

### Custom Re-ranking Weights

Edit `.env`:
```env
RERANK_VECTOR_WEIGHT=0.6    # 60% vector score
RERANK_OVERLAP_WEIGHT=0.3   # 30% query overlap
RERANK_LENGTH_WEIGHT=0.1    # 10% length penalty
```

### Custom Hybrid Search Weights

```env
VECTOR_WEIGHT=0.8   # 80% semantic
BM25_WEIGHT=0.2     # 20% keyword
```

### Custom Chunking

```env
CHUNK_SIZE=500         # Smaller chunks
CHUNK_OVERLAP=100      # Less overlap
```

---

## Monitoring

### Check Logs

```bash
# FastAPI logs
# In terminal running uvicorn

# Docker service logs
docker-compose logs -f db
docker-compose logs -f qdrant
docker-compose logs -f redis

# Ollama logs
# In terminal running ollama serve
```

### Performance Metrics

All chat responses include:
- `latency_ms`: Total time for the request
- `model`: Which LLM was used
- `retrieved_documents[].score`: Retrieval scores

---

## Need Help?

1. **Check Documentation:**
   - [`README.md`](README.md)
   - [`STATUS.md`](STATUS.md)
   - [`STEP5_SUMMARY.md`](STEP5_SUMMARY.md)

2. **Run Tests:**
   ```bash
   python test_ollama.py
   python test_step5.py
   ```

3. **Check Services:**
   ```bash
   docker-compose ps
   curl http://localhost:11434/api/tags  # Ollama
   curl http://localhost:8000/health     # FastAPI
   ```

4. **Review Logs:**
   - FastAPI terminal output
   - Docker logs
   - Ollama terminal output

---

**Happy RAG-ing! 🚀**
