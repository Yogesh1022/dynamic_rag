# Dynamic RAG System - Setup Instructions

## Step 1: Environment Setup ✅

### 1. Install Prerequisites

#### Install uv (Fast Python Package Manager)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Install Ollama (Local LLM Server)
- Download from: https://ollama.com/download
- Install and verify:
```bash
ollama --version
```

#### Install Tesseract (OCR Engine)
- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
- **Linux:** `sudo apt-get install tesseract-ocr`
- **macOS:** `brew install tesseract`

#### Install Docker Desktop
- Download from: https://www.docker.com/products/docker-desktop

### 2. Pull Ollama Models
```bash
# Pull the LLM model
ollama pull llama3

# Pull the embedding model
ollama pull nomic-embed-text
```

### 3. Set Up Environment Variables
```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and update values as needed
```

### 4. Start Docker Services
```bash
# Start PostgreSQL, Qdrant, and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 5. Install Python Dependencies

#### Option A: Using uv (Recommended)
```bash
# Install dependencies
uv pip install -r requirements.txt
```

#### Option B: Using Poetry
```bash
# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

### 6. Verify Setup
```bash
# Check Docker services
docker-compose ps

# Check Ollama
ollama list

# Check Tesseract
tesseract --version

# Check Python packages
uv pip list
```

### 7. Create Upload Directory
```bash
# Windows
mkdir uploads
mkdir logs

# Linux/macOS
mkdir -p uploads logs
```

---

## Next Steps

Step 1 is complete! You can now proceed to:
- **Step 2:** Implement the FastAPI backend
- **Step 3:** Build the ingestion pipeline
- **Step 4:** Set up embedding and vector storage

---

## Quick Start Commands

### Start all services:
```bash
docker-compose up -d
```

### Run the FastAPI server:
```bash
# Using uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Stop all services:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f
```

---

## Troubleshooting

### Docker services won't start
- Check if ports 5432, 6333, 6379 are available
- Run `docker-compose down` and try again

### Ollama connection error
- Ensure Ollama is running: `ollama serve`
- Check URL: http://localhost:11434

### Tesseract not found
- Add Tesseract to PATH
- Update `TESSERACT_CMD` in `.env`

---

## Resources
- [uv Documentation](https://github.com/astral-sh/uv)
- [Ollama Documentation](https://ollama.com/docs)
- [Docker Compose](https://docs.docker.com/compose/)
