# System Architecture: FastAPI RAG System

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER / CLIENT                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST API
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API Layer (app/api/)                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │ /chat       │  │ /documents  │  │ /health         │  │   │
│  │  │ (RAG query) │  │ (CRUD)      │  │ (status check)  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │           Service Layer (app/services/)                   │  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌──────────────────────────────┐   │  │
│  │  │ Ingestion       │  │ Retrieval                    │   │  │
│  │  │ ┌─────────────┐ │  │ ┌─────────────────────────┐  │   │  │
│  │  │ │ OCR         │ │  │ │ Hybrid Retrieval        │  │   │  │
│  │  │ │ Parser      │ │  │ │ ┌─────────┬─────────┐   │  │   │  │
│  │  │ │ Chunker     │ │  │ │ │ Vector  │ BM25    │   │  │   │  │
│  │  │ └─────────────┘ │  │ │ │ Search  │ Search  │   │  │   │  │
│  │  └─────────────────┘  │ │ └─────────┴─────────┘   │  │   │  │
│  │                       │ │ ┌─────────────────────┐  │  │   │  │
│  │  ┌─────────────────┐ │  │ │ Re-ranking          │  │  │   │  │
│  │  │ LLM             │ │  │ │ ┌─────────────────┐ │  │  │   │  │
│  │  │ ┌─────────────┐ │ │  │ │ │ Query overlap   │ │  │  │   │  │
│  │  │ │ Ollama      │ │ │  │ │ │ Length penalty  │ │  │  │   │  │
│  │  │ │ Service     │ │ │  │ │ │ Score fusion    │ │  │  │   │  │
│  │  │ └─────────────┘ │ │  │ │ └─────────────────┘ │  │  │   │  │
│  │  └─────────────────┘ │  │ └─────────────────────┘  │  │   │  │
│  │                       │ │ ┌─────────────────────┐  │  │   │  │
│  │                       │ │ │ Embedding           │  │  │   │  │
│  │                       │ │ │ (Ollama)            │  │  │   │  │
│  │                       │ │ └─────────────────────┘  │  │   │  │
│  │                       │ └──────────────────────────┘  │   │  │
│  │                       └──────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐
│   PostgreSQL    │  │     Qdrant      │  │    Redis     │
│   (Metadata)    │  │  (Vector Store) │  │   (Cache)    │
│                 │  │                 │  │              │
│ - Documents     │  │ - Embeddings    │  │ - Queries    │
│ - Chunks        │  │ - Similarity    │  │ - Embeddings │
│ - Conversations │  │   search        │  │              │
│ - Messages      │  │                 │  │              │
└─────────────────┘  └─────────────────┘  └──────────────┘
```

---

## Data Flow: Chat Query (RAG Pipeline)

```
1. USER QUERY
   │
   │ "What is FastAPI?"
   │
   ▼
2. API ENDPOINT (/api/v1/chat)
   │
   │ Receive request
   │ Extract query, conversation_id, params
   │
   ▼
3. LOAD HISTORY
   │
   │ PostgreSQL ─────┐
   │                 │ SELECT messages
   │                 │ WHERE conversation_id = ?
   │ ◄───────────────┘
   │ [Previous messages]
   │
   ▼
4. EMBEDDING GENERATION
   │
   │ Ollama API ─────┐
   │                 │ POST /api/embeddings
   │                 │ {"model": "nomic-embed-text", "input": "..."}
   │ ◄───────────────┘
   │ [768-dim vector]
   │
   ▼
5. VECTOR SEARCH
   │
   │ Qdrant ─────────┐
   │                 │ POST /collections/{name}/points/search
   │                 │ {"vector": [...], "limit": 20}
   │ ◄───────────────┘
   │ [20 similar chunks with scores]
   │
   ▼
6. BM25 KEYWORD SEARCH
   │
   │ PostgreSQL ─────┐
   │                 │ SELECT * FROM chunks
   │                 │ WHERE content @@ to_tsquery(?)
   │ ◄───────────────┘
   │ [20 keyword matches]
   │
   ▼
7. SCORE FUSION
   │
   │ Normalize scores
   │ Combine: 70% vector + 30% BM25
   │ Merge unique results
   │
   │ [Combined ranked list]
   │
   ▼
8. RE-RANKING
   │
   │ Calculate:
   │ - Query overlap score
   │ - Length penalty
   │ - Final score = 0.7*vector + 0.2*overlap + 0.1*length
   │
   │ [Top 5 re-ranked chunks]
   │
   ▼
9. CONTEXT ASSEMBLY
   │
   │ Build context string:
   │ "[1] {chunk1}\n[2] {chunk2}..."
   │ "Answer based on context above"
   │
   │ [System prompt with context]
   │
   ▼
10. LLM GENERATION
   │
   │ Ollama API ─────┐
   │                 │ POST /api/chat
   │                 │ {
   │                 │   "model": "llama3",
   │                 │   "messages": [
   │                 │     {"role": "system", "content": "..."},
   │                 │     {"role": "user", "content": "..."}
   │                 │   ]
   │                 │ }
   │ ◄───────────────┘
   │ [Generated answer]
   │
   ▼
11. SAVE CONVERSATION
   │
   │ PostgreSQL ─────┐
   │                 │ INSERT INTO messages
   │                 │ (conversation_id, role, content)
   │                 │ VALUES (?, 'user', ?)
   │                 │ VALUES (?, 'assistant', ?)
   │ ◄───────────────┘
   │
   ▼
12. RESPONSE
   │
   │ {
   │   "answer": "FastAPI is...",
   │   "conversation_id": "conv_123",
   │   "retrieved_documents": [...],
   │   "latency_ms": 2345.67
   │ }
   │
   ▼
13. USER
```

---

## Data Flow: Document Upload

```
1. USER UPLOAD
   │
   │ File: document.pdf
   │
   ▼
2. API ENDPOINT (/api/v1/documents/upload)
   │
   │ Validate file type
   │ Save to ./uploads/
   │
   ▼
3. CREATE DB RECORD
   │
   │ PostgreSQL ─────┐
   │                 │ INSERT INTO documents
   │                 │ (filename, file_path, status='processing')
   │ ◄───────────────┘
   │ document_id = "doc_123"
   │
   ▼
4. BACKGROUND PROCESSING
   │
   ├─► 5. OCR / PARSING
   │   │
   │   │ Tesseract ─────┐
   │   │                │ Extract text from images
   │   │ ◄──────────────┘
   │   │
   │   │ PyPDF2 ────────┐
   │   │                │ Extract text from PDF
   │   │ ◄──────────────┘
   │   │
   │   │ [Full document text]
   │   │
   │   ▼
   ├─► 6. CHUNKING
   │   │
   │   │ RecursiveCharacterTextSplitter
   │   │ - Chunk size: 1000 chars
   │   │ - Overlap: 200 chars
   │   │
   │   │ [25 text chunks]
   │   │
   │   ▼
   ├─► 7. EMBEDDING
   │   │
   │   │ For each chunk:
   │   │   Ollama API ────┐
   │   │                  │ Generate embedding
   │   │   ◄──────────────┘
   │   │
   │   │ [25 embeddings (768-dim)]
   │   │
   │   ▼
   ├─► 8. STORE VECTORS
   │   │
   │   │ Qdrant ─────────┐
   │   │                 │ POST /collections/{name}/points/upsert
   │   │                 │ {
   │   │                 │   "points": [
   │   │                 │     {
   │   │                 │       "id": "chunk_1",
   │   │                 │       "vector": [...],
   │   │                 │       "payload": {
   │   │                 │         "document_id": "doc_123",
   │   │                 │         "content": "...",
   │   │                 │         "page": 1
   │   │                 │       }
   │   │                 │     }
   │   │                 │   ]
   │   │                 │ }
   │   │ ◄───────────────┘
   │   │
   │   ▼
   └─► 9. STORE CHUNKS
       │
       │ PostgreSQL ─────┐
       │                 │ INSERT INTO chunks
       │                 │ (document_id, content, chunk_index, page_number)
       │                 │ VALUES (?, ?, ?, ?)
       │                 │ ... (25 rows)
       │ ◄───────────────┘
       │
       ▼
   10. UPDATE STATUS
       │
       │ PostgreSQL ─────┐
       │                 │ UPDATE documents
       │                 │ SET status='completed', total_chunks=25
       │                 │ WHERE id='doc_123'
       │ ◄───────────────┘
       │
       ▼
   11. COMPLETE
```

---

## Component Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ PostgreSQL   │  │ Qdrant       │  │ Redis            │  │
│  │ :5432        │  │ :6333        │  │ :6379            │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Ollama       │  │ Tesseract    │                         │
│  │ :11434       │  │ (local)      │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    DEPENDENCY INJECTION                      │
│                    (app/api/deps.py)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  get_db() ────────────► AsyncSession                         │
│  get_qdrant_client() ─► QdrantClient                         │
│  get_redis_client() ──► Redis                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌────────────────────────────┴────────────────────────────────┐
│                    SINGLETON SERVICES                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  get_embedding_service() ──────────► EmbeddingService        │
│  get_reranker_service() ───────────► RerankerService         │
│  get_hybrid_retrieval_service() ───► HybridRetrievalService  │
│  get_ollama_service() ─────────────► OllamaService           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌────────────────────────────┴────────────────────────────────┐
│                       API ENDPOINTS                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  POST /api/v1/chat ──────────────► Chat with RAG            │
│  POST /api/v1/documents/upload ──► Upload document          │
│  GET  /api/v1/documents/ ─────────► List documents          │
│  DELETE /api/v1/documents/{id} ──► Delete document          │
│  GET  /health ────────────────────► Health check            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                        PostgreSQL                            │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│    documents     │
├──────────────────┤
│ id (UUID) PK     │
│ filename         │
│ file_path        │
│ file_type        │
│ file_size        │
│ status           │  ◄─── 'processing', 'completed', 'failed'
│ total_chunks     │
│ doc_metadata     │  ◄─── Renamed from 'metadata' (reserved keyword)
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │ 1:N
         │
┌────────▼─────────┐
│     chunks       │
├──────────────────┤
│ id (UUID) PK     │
│ document_id FK   │  ───┐
│ content          │      │ References documents(id)
│ chunk_index      │      │ ON DELETE CASCADE
│ page_number      │  ◄───┘
│ created_at       │
└──────────────────┘

┌──────────────────┐
│  conversations   │
├──────────────────┤
│ id (UUID) PK     │
│ title            │
│ user_id          │  ◄─── TODO: Add user authentication
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │ 1:N
         │
┌────────▼─────────┐
│    messages      │
├──────────────────┤
│ id (UUID) PK     │
│ conversation_id  │  ───┐
│ role             │      │ References conversations(id)
│ content          │      │ ON DELETE CASCADE
│ created_at       │  ◄───┘
└──────────────────┘
```

---

## Qdrant Collections

```
┌─────────────────────────────────────────────────────────────┐
│                          Qdrant                              │
└─────────────────────────────────────────────────────────────┘

Collection: "documents" (from QDRANT_COLLECTION_NAME)

┌──────────────────────────────────────────────────────────┐
│                         Point                             │
├──────────────────────────────────────────────────────────┤
│ id: "chunk_uuid"                                         │
│ vector: [0.123, -0.456, ..., 0.789]  (768 dimensions)   │
│ payload: {                                               │
│   "chunk_id": "chunk_uuid",                              │
│   "content": "FastAPI is a modern web framework...",     │
│   "document_id": "doc_uuid",                             │
│   "chunk_index": 0,                                      │
│   "page": 1                                              │
│ }                                                        │
└──────────────────────────────────────────────────────────┘

Vector Config:
- Size: 768 (Ollama nomic-embed-text)
- Distance: COSINE
- On-disk storage: true
```

---

## Request Flow Timing

```
┌─────────────────────────────────────────────────────────────┐
│           Typical Chat Query Timeline (3.5s total)          │
└─────────────────────────────────────────────────────────────┘

0ms    ├─► Request received
       │
50ms   ├─► Embedding generated (Ollama)
       │   Time: 50ms
       │
100ms  ├─► Vector search complete (Qdrant)
       │   Time: 50ms
       │
180ms  ├─► BM25 search complete (PostgreSQL)
       │   Time: 80ms
       │
200ms  ├─► Re-ranking complete
       │   Time: 20ms
       │
210ms  ├─► Context assembled
       │   Time: 10ms
       │
3500ms ├─► LLM generation complete (Ollama)
       │   Time: 3290ms
       │
3520ms ├─► Conversation saved
       │   Time: 20ms
       │
3530ms └─► Response sent
           Total: 3530ms

Breakdown:
- Retrieval: 200ms (5.7%)
- LLM: 3290ms (93.2%)
- Storage: 40ms (1.1%)
```

---

## Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Sources                     │
└─────────────────────────────────────────────────────────────┘

Priority (highest to lowest):

1. Request Parameters
   ├─ model: "mistral"
   ├─ temperature: 0.5
   ├─ top_k: 3
   └─ use_hybrid: false

2. Environment Variables (.env)
   ├─ OLLAMA_LLM_MODEL=llama3
   ├─ USE_HYBRID_SEARCH=true
   ├─ RERANK_TOP_K=5
   └─ ...

3. Default Values (app/core/config.py)
   ├─ OLLAMA_LLM_MODEL="llama3"
   ├─ USE_HYBRID_SEARCH=True
   └─ RERANK_TOP_K=5

Final values used = Request > .env > Defaults
```

---

**For more details, see:**
- [STATUS.md](STATUS.md) - Project status
- [STEP5_SUMMARY.md](STEP5_SUMMARY.md) - Implementation details
- [QUICKSTART.md](QUICKSTART.md) - Quick reference
