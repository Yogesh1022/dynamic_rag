#!/bin/bash
# Deployment script for production environment

set -e

echo "🚀 Starting RAG System Deployment..."

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production not found"
    echo "📝 Please copy .env.production.example to .env.production and configure it"
    exit 1
fi

# Check if Ollama is running
echo "🔍 Checking Ollama availability..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Error: Ollama is not running"
    echo "📝 Please start Ollama first: ollama serve"
    exit 1
fi

# Check if required models are available
echo "🔍 Checking Ollama models..."
if ! ollama list | grep -q "llama3"; then
    echo "📥 Pulling llama3 model..."
    ollama pull llama3
fi

if ! ollama list | grep -q "nomic-embed-text"; then
    echo "📥 Pulling nomic-embed-text model..."
    ollama pull nomic-embed-text
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.prod.yml build

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose -f docker-compose.prod.yml ps

# Initialize database
echo "💾 Initializing database..."
docker-compose -f docker-compose.prod.yml exec -T backend python init_db.py

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Qdrant:    http://localhost:6333/dashboard"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:        docker-compose -f docker-compose.prod.yml logs -f"
echo "   Stop services:    docker-compose -f docker-compose.prod.yml down"
echo "   Restart service:  docker-compose -f docker-compose.prod.yml restart [service]"
echo ""
