# 🚀 Deployment Guide

Complete guide for deploying the RAG system to production.

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Docker Architecture](#docker-architecture)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

---

## 🔧 Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Docker:** 20.10+ with Docker Compose
- **RAM:** Minimum 8GB (16GB recommended for Llama3)
- **Storage:** 20GB+ free space
- **Ollama:** Installed and running

### Required Software
```bash
# Docker & Docker Compose
docker --version   # Should be 20.10+
docker-compose --version

# Ollama
ollama --version
ollama list  # Should show llama3 and nomic-embed-text
```

### Pull Ollama Models
```bash
# Start Ollama service
ollama serve

# Pull required models
ollama pull llama3
ollama pull nomic-embed-text
```

---

## ⚡ Quick Deployment

### Option 1: Automated Script (Recommended)

#### Linux/Mac:
```bash
# 1. Configure environment
cp .env.production.example .env.production
# Edit .env.production with your values

# 2. Make script executable
chmod +x deploy.sh

# 3. Run deployment
./deploy.sh
```

#### Windows:
```powershell
# 1. Configure environment
copy .env.production.example .env.production
# Edit .env.production with your values

# 2. Run deployment
deploy.bat
```

The script will:
- ✅ Check prerequisites (Ollama, models)
- ✅ Build Docker images
- ✅ Start all services
- ✅ Initialize database
- ✅ Display service URLs

### Option 2: Docker Compose

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Initialize database
docker-compose -f docker-compose.prod.yml exec backend python init_db.py
```

---

## 📝 Manual Deployment

### Step 1: Configure Environment

```bash
# Copy and edit production environment
cp .env.production.example .env.production
nano .env.production
```

**Critical settings to change:**
- `POSTGRES_PASSWORD` - Set a strong password
- `SECRET_KEY` - Generate random 32+ character string
- `API_KEY` - Set your API authentication key
- `CORS_ORIGINS` - Set your domain(s)

### Step 2: Build Backend Image

```bash
# Build FastAPI backend
docker build -t rag-backend:latest .
```

**Backend Dockerfile features:**
- Multi-stage build for smaller image size
- Tesseract OCR + Poppler for PDF processing
- Python 3.11 slim base
- Health check endpoint
- Optimized layer caching

### Step 3: Build Frontend Image

```bash
# Build React dashboard
cd dashboard
docker build -t rag-frontend:latest .
cd ..
```

**Frontend Dockerfile features:**
- Multi-stage build (Node builder + Nginx runtime)
- Production-optimized React build
- Nginx with caching and compression
- Reverse proxy to backend
- Static asset serving

### Step 4: Start Infrastructure

```bash
# Start databases and cache
docker-compose -f docker-compose.prod.yml up -d postgres qdrant redis

# Wait for services to be healthy
docker-compose -f docker-compose.prod.yml ps
```

### Step 5: Start Application

```bash
# Start backend
docker-compose -f docker-compose.prod.yml up -d backend

# Initialize database
docker-compose -f docker-compose.prod.yml exec backend python init_db.py

# Start frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Step 6: Verify Deployment

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost
```

---

## 🔐 Environment Configuration

### Backend Environment (.env.production)

```bash
# Database
POSTGRES_USER=raguser
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=ragdb
DATABASE_URL=postgresql+asyncpg://raguser:your_secure_password_here@postgres:5432/ragdb

# Vector DB
QDRANT_URL=http://qdrant:6333

# Cache
REDIS_URL=redis://redis:6379

# Ollama (running on host)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_LLM_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Security
SECRET_KEY=generate_random_32_plus_character_string
API_KEY=your_api_key_for_authentication
CORS_ORIGINS=http://yourdomain.com,https://yourdomain.com

# App Config
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Frontend Environment (dashboard/.env.production)

```bash
# API endpoint (change for remote deployment)
VITE_API_URL=http://localhost:8000
```

**For remote deployment:**
```bash
VITE_API_URL=https://api.yourdomain.com
```

---

## 🏗️ Docker Architecture

### Container Network

```
┌─────────────────────────────────────────────────┐
│              rag_network (bridge)               │
│                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │PostgreSQL│   │  Qdrant  │   │  Redis   │   │
│  │  :5432   │   │  :6333   │   │  :6379   │   │
│  └─────┬────┘   └─────┬────┘   └─────┬────┘   │
│        │              │              │         │
│        └──────────────┴──────────────┘         │
│                       │                        │
│                ┌──────▼──────┐                 │
│                │   Backend   │                 │
│                │ FastAPI     │                 │
│                │   :8000     │◄────────┐       │
│                └──────┬──────┘         │       │
│                       │                │       │
│                ┌──────▼──────┐         │       │
│                │  Frontend   │         │       │
│                │Nginx+React  │─────────┘       │
│                │    :80      │   (proxy)       │
│                └─────────────┘                 │
└─────────────────────────────────────────────────┘
         │                        │
         ▼                        ▼
    Ollama (host)          User Browser
  :11434 (LLM)            http://localhost
```

### Service Dependencies

```yaml
frontend → backend → postgres + qdrant + redis
backend → ollama (host machine)
```

---

## 📊 Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Service Management

```bash
# Restart a service
docker-compose -f docker-compose.prod.yml restart backend

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (⚠️ deletes data)
docker-compose -f docker-compose.prod.yml down -v

# View resource usage
docker stats
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Qdrant health
curl http://localhost:6333/healthz

# PostgreSQL health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Redis health
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Database Backup

```bash
# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U raguser ragdb > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U raguser ragdb < backup_20260201.sql

# Backup Qdrant (copy volume)
docker run --rm -v rag_qdrant_data:/data -v $(pwd):/backup ubuntu tar czf /backup/qdrant_backup_$(date +%Y%m%d).tar.gz /data
```

### Update Deployment

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Or rebuild specific service
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

---

## 🐛 Troubleshooting

### Issue: Backend can't connect to Ollama

**Error:** `Connection refused to localhost:11434`

**Solution:**
```bash
# Check Ollama is running
ollama list

# Start Ollama if needed
ollama serve

# Verify OLLAMA_BASE_URL in .env.production
# Should be: http://host.docker.internal:11434 (for Docker)
```

### Issue: Frontend can't reach backend

**Error:** `Network Error` or `502 Bad Gateway`

**Solution:**
```bash
# 1. Check backend is running
docker-compose -f docker-compose.prod.yml ps backend

# 2. Check backend logs
docker-compose -f docker-compose.prod.yml logs backend

# 3. Test backend directly
curl http://localhost:8000/health

# 4. Verify nginx proxy config in dashboard/nginx.conf
# Should proxy /api to http://backend:8000
```

### Issue: Database connection errors

**Error:** `could not connect to server`

**Solution:**
```bash
# 1. Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# 2. Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# 3. Verify DATABASE_URL in .env.production
# Format: postgresql+asyncpg://user:pass@postgres:5432/db

# 4. Restart PostgreSQL
docker-compose -f docker-compose.prod.yml restart postgres
```

### Issue: Out of memory

**Error:** Container keeps restarting

**Solution:**
```bash
# 1. Check memory usage
docker stats

# 2. Add memory limits to docker-compose.prod.yml
services:
  backend:
    mem_limit: 2g
    mem_reservation: 1g

# 3. Use lighter models
# In .env.production:
OLLAMA_LLM_MODEL=mistral  # or gemma3:4b
```

### Issue: Slow responses

**Solution:**
```bash
# 1. Check if hybrid search is needed
# In chat settings, toggle USE_HYBRID to false for speed

# 2. Reduce top_k value
# In chat settings, set top_k to 3 instead of 5

# 3. Use faster model
# Switch from llama3 to mistral or gemma3

# 4. Enable Redis caching
# Verify REDIS_URL is set correctly
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
- ✅ Never commit `.env.production` to git
- ✅ Use strong passwords (16+ characters)
- ✅ Rotate API keys regularly
- ✅ Use different credentials for dev/prod

### 2. Network Security
```bash
# In production, don't expose database ports
# Remove from docker-compose.prod.yml:
# ports:
#   - "5432:5432"  # Remove this
```

### 3. API Security
```python
# Add rate limiting (future enhancement)
# Add authentication middleware
# Use HTTPS in production
# Set CORS_ORIGINS to specific domains only
```

### 4. Docker Security
```bash
# Run as non-root user (add to Dockerfile)
USER appuser

# Scan images for vulnerabilities
docker scan rag-backend:latest

# Keep images updated
docker-compose -f docker-compose.prod.yml pull
```

### 5. File Upload Security
```bash
# Set upload limits in .env.production
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,png,jpg,jpeg,tiff

# Scan uploaded files (future enhancement)
# Add virus scanning
# Validate file types
```

---

## 🌐 Production Deployment (Remote Server)

### Deploy to Cloud VM (AWS/GCP/Azure)

#### 1. Prepare Server
```bash
# SSH into server
ssh user@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

#### 2. Clone Repository
```bash
git clone https://github.com/yourusername/dynamic_rag.git
cd dynamic_rag
```

#### 3. Configure for Production
```bash
# Edit environment
cp .env.production.example .env.production
nano .env.production

# Update CORS_ORIGINS with your domain
CORS_ORIGINS=https://yourdomain.com

# Update frontend API URL
cd dashboard
nano .env.production
# VITE_API_URL=https://api.yourdomain.com
```

#### 4. Setup HTTPS (with Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Update nginx.conf to use SSL
```

#### 5. Deploy
```bash
./deploy.sh
```

#### 6. Setup Firewall
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Don't expose database ports publicly
sudo ufw deny 5432/tcp
sudo ufw deny 6333/tcp
sudo ufw deny 6379/tcp
```

---

## 📈 Performance Optimization

### 1. Enable Caching
```python
# Already configured in backend
# Verify REDIS_URL is set
# Cache will store:
# - Embeddings for queries
# - Frequent search results
# - Document metadata
```

### 2. Optimize Docker Images
```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.prod.yml build

# Clean up unused images
docker system prune -a
```

### 3. Database Optimization
```sql
-- Add indexes (future enhancement)
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

### 4. Nginx Optimization
```nginx
# Already configured in dashboard/nginx.conf:
# - Gzip compression
# - Static asset caching (1 year)
# - Connection pooling
```

---

## 📦 Service URLs (After Deployment)

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | React dashboard |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Qdrant UI** | http://localhost:6333/dashboard | Vector DB admin |
| **PostgreSQL** | localhost:5432 | SQL database |
| **Redis** | localhost:6379 | Cache |

---

## ✅ Post-Deployment Checklist

- [ ] All services are healthy (`docker-compose ps`)
- [ ] Backend health check passes (`curl http://localhost:8000/health`)
- [ ] Frontend loads in browser (`http://localhost`)
- [ ] Can upload a document
- [ ] Document processing completes
- [ ] Can query uploaded document in chat
- [ ] Source citations appear correctly
- [ ] Logs are clean (no errors)
- [ ] Database backup configured
- [ ] Monitoring setup (optional)

---

## 🎯 Next Steps

1. **Monitor Performance:**
   - Set up Prometheus + Grafana (optional)
   - Configure log aggregation (ELK stack)
   - Add error tracking (Sentry)

2. **Scale Horizontally:**
   - Add multiple backend replicas
   - Use load balancer (Nginx/HAProxy)
   - Separate vector DB to dedicated server

3. **Enhance Security:**
   - Implement user authentication (JWT)
   - Add rate limiting (Redis)
   - Enable HTTPS (Certbot)
   - Scan dependencies for vulnerabilities

4. **Optimize Costs:**
   - Use smaller models for dev (gemma3:4b)
   - Implement query caching
   - Auto-scale based on load

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review [Troubleshooting](#troubleshooting) section
3. Check GitHub issues
4. Open new issue with logs and config

---

**🎉 Congratulations! Your RAG system is now deployed in production!**
