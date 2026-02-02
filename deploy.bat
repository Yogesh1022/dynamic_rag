@echo off
REM Deployment script for Windows production environment

echo 🚀 Starting RAG System Deployment...
echo.

REM Check if .env.production exists
if not exist .env.production (
    echo ❌ Error: .env.production not found
    echo 📝 Please copy .env.production.example to .env.production and configure it
    exit /b 1
)

REM Check if Ollama is running
echo 🔍 Checking Ollama availability...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Ollama is not running
    echo 📝 Please start Ollama first: ollama serve
    exit /b 1
)

REM Check if required models are available
echo 🔍 Checking Ollama models...
ollama list | findstr "llama3" >nul
if errorlevel 1 (
    echo 📥 Pulling llama3 model...
    ollama pull llama3
)

ollama list | findstr "nomic-embed-text" >nul
if errorlevel 1 (
    echo 📥 Pulling nomic-embed-text model...
    ollama pull nomic-embed-text
)

REM Stop existing containers
echo 🛑 Stopping existing containers...
docker-compose -f docker-compose.prod.yml down

REM Build images
echo 🏗️  Building Docker images...
docker-compose -f docker-compose.prod.yml build

REM Start services
echo 🚀 Starting services...
docker-compose -f docker-compose.prod.yml up -d

REM Wait for services to be healthy
echo ⏳ Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check health
echo 🏥 Checking service health...
docker-compose -f docker-compose.prod.yml ps

REM Initialize database
echo 💾 Initializing database...
docker-compose -f docker-compose.prod.yml exec -T backend python init_db.py

echo.
echo ✅ Deployment complete!
echo.
echo 📊 Service URLs:
echo    Frontend:  http://localhost
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo    Qdrant:    http://localhost:6333/dashboard
echo.
echo 🔧 Useful commands:
echo    View logs:        docker-compose -f docker-compose.prod.yml logs -f
echo    Stop services:    docker-compose -f docker-compose.prod.yml down
echo    Restart service:  docker-compose -f docker-compose.prod.yml restart [service]
echo.
