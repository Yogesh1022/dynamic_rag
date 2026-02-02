# 🚀 Step-by-Step Guide to Run Dynamic RAG System

## 📋 Prerequisites

Before starting, ensure you have the following installed:

### Required Software
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 20+** - [Download](https://nodejs.org/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Ollama** - [Download](https://ollama.ai/download)
- **Git** (optional) - [Download](https://git-scm.com/)

### Optional (for OCR)
- **Tesseract OCR** - [Download](https://github.com/tesseract-ocr/tesseract)
- **Poppler** (for PDF to image) - [Download](https://poppler.freedesktop.org/)

---

## 🎯 Quick Start (5 Steps)

### **Step 1: Install Ollama Models**

Open a terminal and run:

```bash
# Install LLM model (llama3)
ollama pull llama3

# Install embedding model (nomic-embed-text)
ollama pull nomic-embed-text

# Verify installation
ollama list
```

**Expected output:**
```
NAME                    ID              SIZE
llama3:latest           xxxxx           4.7 GB
nomic-embed-text:latest xxxxx           274 MB
```

---

### **Step 2: Start Docker Services**

Open a terminal in the project root directory:

```bash
# Navigate to project directory
cd C:\Users\ASUS\Desktop\yogesh_p\dynamic_rag

# Start PostgreSQL, Qdrant, and Redis
docker-compose up -d

# Verify services are running
docker ps
```

**Expected output:**
```
CONTAINER ID   IMAGE                    STATUS
xxxxx          postgres:15-alpine       Up (healthy)
xxxxx          qdrant/qdrant:latest     Up (healthy)
xxxxx          redis:7-alpine           Up (healthy)
```

**Verify services:**
- PostgreSQL: `http://localhost:5432`
- Qdrant Dashboard: `http://localhost:6333/dashboard`
- Redis: `http://localhost:6379`

---

### **Step 3: Setup Python Backend**

#### 3.1 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (CMD):
.\venv\Scripts\activate.bat

# On Linux/Mac:
source venv/bin/activate
```

#### 3.2 Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**This installs:**
- FastAPI, Uvicorn (web framework)
- Ollama, Qdrant, Redis clients
- SQLAlchemy, PostgreSQL driver
- OCR libraries (Tesseract, PDF2Image)
- Chunking, embeddings, retrieval libraries

#### 3.3 Create Environment File

Create a `.env` file in the project root:

```bash
# Copy example file
copy .env.example .env    # Windows
cp .env.example .env      # Linux/Mac
```

**Edit `.env` file** with your settings:
```env
# Application
APP_NAME=Dynamic RAG System
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secret-api-key-change-in-production

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpass
POSTGRES_DB=ragdb
DATABASE_URL=postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=documents

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# File Upload
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,tiff
UPLOAD_DIR=./uploads
```

#### 3.4 Initialize Database

```bash
# Create database tables
python init_db.py
```

**Expected output:**
```
✅ Database tables created successfully!
```

#### 3.5 Start Backend Server

```bash
# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting up Dynamic RAG System...
📦 Environment: development
🔧 Debug mode: True
✅ Cache service connected
✅ Startup complete!
INFO:     Application startup complete.
```

**Verify backend:**
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

### **Step 4: Setup React Frontend**

**Open a NEW terminal** (keep backend running):

#### 4.1 Navigate to Dashboard

```bash
cd C:\Users\ASUS\Desktop\yogesh_p\dynamic_rag\dashboard
```

#### 4.2 Install Dependencies

```bash
# Install Node.js packages
npm install
```

**Expected output:**
```
added 141 packages, and audited 142 packages in 10s
```

#### 4.3 Create Environment File

Create `.env` file in the dashboard directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_API_KEY=your-secret-api-key-change-in-production
```

#### 4.4 Start Development Server

```bash
# Start Vite dev server
npm run dev
```

**Expected output:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

**Open browser:** `http://localhost:5173`

---

### **Step 5: Test the System**

#### 5.1 Verify All Services

Open these URLs in your browser:

✅ **Frontend Dashboard:** `http://localhost:5173`
✅ **Backend API Docs:** `http://localhost:8000/docs`
✅ **Backend Health:** `http://localhost:8000/health`
✅ **Qdrant Dashboard:** `http://localhost:6333/dashboard`

#### 5.2 Upload a Document

1. Go to `http://localhost:5173`
2. Click **"Documents"** in the sidebar
3. Click **"Upload Document"**
4. Select a PDF or image file
5. Wait for processing (status will change to "completed")

#### 5.3 Chat with Your Documents

1. Click **"Chat"** in the sidebar
2. Type a question about your uploaded document
3. Click **"Send"** or press Enter
4. View AI response with source citations

**Example queries:**
- "What is this document about?"
- "Summarize the main points"
- "What are the key findings?"

---

## 🔍 Troubleshooting

### Problem: Backend won't start

**Check:**
```bash
# Verify Docker services are running
docker ps

# Check if services are healthy
docker-compose ps

# Restart services if needed
docker-compose restart
```

### Problem: Ollama not found

**Solution:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service (if needed)
# Windows: Run Ollama app
# Linux/Mac: ollama serve
```

### Problem: Database connection error

**Solution:**
```bash
# Stop all services
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d

# Recreate database
python init_db.py
```

### Problem: Port already in use

**Solution:**
```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :8000

# Linux/Mac:
lsof -i :8000

# Kill the process or change port in .env
```

### Problem: Frontend can't connect to backend

**Check:**
1. Backend is running on `http://localhost:8000`
2. `.env` in dashboard has correct `VITE_API_URL`
3. API_KEY matches in both `.env` files
4. CORS is enabled (should be by default)

### Problem: Cache not working

**Check:**
```bash
# Verify Redis is running
docker exec -it rag_redis redis-cli ping
# Should return: PONG

# Check cache stats in health endpoint
curl http://localhost:8000/health
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard                       │
│                  (http://localhost:5173)                 │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│                (http://localhost:8000)                   │
│  • REST API endpoints                                    │
│  • Redis caching (400x faster)                           │
│  • Structured JSON logging                               │
│  • Performance monitoring                                │
└──────┬──────────┬───────────┬──────────┬────────────────┘
       │          │           │          │
       ▼          ▼           ▼          ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌───────────┐
  │PostgreSQL│ │ Qdrant │ │ Redis  │ │  Ollama   │
  │  :5432  │ │ :6333  │ │ :6379  │ │  :11434   │
  │         │ │        │ │        │ │           │
  │Metadata │ │Vectors │ │ Cache  │ │   LLM     │
  │Convers. │ │Search  │ │Results │ │Embeddings │
  └─────────┘ └────────┘ └────────┘ └───────────┘
```

---

## 🎯 Common Commands

### Start Everything

```bash
# Terminal 1 - Docker services
docker-compose up -d

# Terminal 2 - Backend
cd C:\Users\ASUS\Desktop\yogesh_p\dynamic_rag
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Terminal 3 - Frontend
cd C:\Users\ASUS\Desktop\yogesh_p\dynamic_rag\dashboard
npm run dev
```

### Stop Everything

```bash
# Stop frontend: Press Ctrl+C in Terminal 3
# Stop backend: Press Ctrl+C in Terminal 2

# Stop Docker services
docker-compose down
```

### View Logs

```bash
# Backend logs (in Terminal 2)
# Already visible in console

# Docker service logs
docker-compose logs -f postgres
docker-compose logs -f qdrant
docker-compose logs -f redis

# All logs
docker-compose logs -f
```

### Reset Everything

```bash
# Stop all services
docker-compose down -v

# Clean Python cache
rm -rf venv
rm -rf __pycache__
rm -rf app/__pycache__

# Clean uploads and logs
rm -rf uploads/*
rm -rf logs/*

# Reinstall
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker-compose up -d
python init_db.py
```

---

## 📁 Project Structure

```
dynamic_rag/
├── app/                          # Backend application
│   ├── api/                      # API endpoints
│   │   └── v1/endpoints/
│   │       ├── chat.py          # RAG chat endpoint
│   │       └── documents.py     # Document upload
│   ├── core/                     # Core configuration
│   │   ├── config.py            # Settings
│   │   ├── middleware.py        # Error handling
│   │   └── security.py          # Authentication
│   ├── services/                 # Business logic
│   │   ├── cache/               # Redis caching
│   │   ├── ingestion/           # Document parsing
│   │   ├── llm/                 # Ollama integration
│   │   └── retrieval/           # Hybrid search
│   ├── utils/                    # Utilities
│   │   └── json_logger.py       # Structured logging
│   └── main.py                   # FastAPI app
├── dashboard/                    # React frontend
│   ├── src/
│   │   ├── pages/               # UI pages
│   │   │   ├── ChatPage.jsx
│   │   │   ├── DocumentsPage.jsx
│   │   │   └── DashboardPage.jsx
│   │   └── api/client.js        # API integration
│   └── package.json
├── docker-compose.yml            # Docker services
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
└── RUN_PROJECT.md               # This file
```

---

## 🎉 Success Checklist

After following all steps, you should have:

- ✅ Docker services running (PostgreSQL, Qdrant, Redis)
- ✅ Ollama models installed (llama3, nomic-embed-text)
- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend running on `http://localhost:5173`
- ✅ API docs accessible at `http://localhost:8000/docs`
- ✅ Health check showing cache connected
- ✅ Can upload documents
- ✅ Can chat with documents
- ✅ Cache working (400x faster responses)

---

## 🚀 Performance Features

### Caching System
- **Query Results:** 30min TTL - instant responses for repeated queries
- **Embeddings:** 24hr TTL - avoid regenerating embeddings
- **Conversations:** 30min TTL - fast conversation loading
- **Performance:** 400x faster (10ms vs 4000ms)

### Monitoring
- Structured JSON logs in `./logs/app.log`
- Request/response tracking
- Performance metrics (LLM, retrieval, DB)
- Slow request detection (>1 second)
- X-Process-Time header on all responses

### Production Ready
- ✅ Error handling middleware
- ✅ API key authentication
- ✅ Rate limiting ready
- ✅ Health checks
- ✅ Auto-restart on failure
- ✅ Graceful shutdown

---

## 📚 Additional Resources

- **API Documentation:** `http://localhost:8000/docs`
- **Qdrant Dashboard:** `http://localhost:6333/dashboard`
- **Ollama Models:** `https://ollama.ai/library`
- **FastAPI Docs:** `https://fastapi.tiangolo.com/`
- **React Docs:** `https://react.dev/`

---

## 🆘 Need Help?

1. **Check logs:** Backend console and `./logs/app.log`
2. **Verify services:** `docker ps` and `docker-compose ps`
3. **Health check:** `http://localhost:8000/health`
4. **Restart services:** `docker-compose restart`
5. **Clear cache:** `docker exec -it rag_redis redis-cli FLUSHALL`

---

## 🎊 You're Ready!

Your Dynamic RAG System is now running! Upload documents and start chatting with your AI assistant powered by Llama3.

**Happy Coding! 🚀**
