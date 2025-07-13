# ResearchMate Deployment Guide 🐳

This guide covers deploying ResearchMate using Docker for production or development environments.

## Prerequisites 📋

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Groq API Key** ([Get yours here](https://console.groq.com/keys))

## Quick Deploy 🚀

### Windows
```bash
# Run the deployment script
deploy.bat
```

### Linux/macOS
```bash
# Make script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

## Manual Deployment 🔧

### 1. Environment Setup
Create a `.env` file in the project root:
```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 2. Build and Run
```bash
# Create data directories
mkdir -p data logs uploads chroma_persist

# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Access Application
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Docker Configuration 🐋

### Services
- **researchmate**: Main application container
- **Port**: 8000 (mapped to host)
- **Volumes**: Persistent data storage
- **Health Check**: Automatic health monitoring

### Volumes
- `./data` → Application data
- `./logs` → Application logs  
- `./uploads` → User uploads
- `./chroma_persist` → Vector database

### Networks
- **researchmate-network**: Isolated bridge network

## Management Commands 📋

### Viewing Logs
```bash
# Follow logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f researchmate
```

### Service Control
```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# Stop and remove everything
docker-compose down -v
```

### Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Production Considerations 🏭

### Security
1. **Environment Variables**: Use Docker secrets or external secret management
2. **Network**: Use reverse proxy (nginx) for HTTPS
3. **API Keys**: Rotate regularly and store securely

### Performance
1. **Resources**: Allocate sufficient CPU/Memory
2. **Storage**: Use fast SSD for vector database
3. **Monitoring**: Set up health checks and logging

### Scaling
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  researchmate:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Troubleshooting 🔍

### Common Issues

**Container won't start**
```bash
# Check logs
docker-compose logs

# Check system resources
docker system df
```

**API Key issues**
```bash
# Verify environment
docker-compose exec researchmate env | grep GROQ
```

**Port conflicts**
```bash
# Use different port
docker-compose up -d -p 8080:8000
```

**Permission issues**
```bash
# Fix permissions
sudo chown -R $(whoami):$(whoami) data logs uploads chroma_persist
```

## Development Setup 🛠️

### Hot Reload
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  researchmate:
    volumes:
      - .:/app
    environment:
      - RELOAD=true
```

### Debug Mode
```bash
# Run with debug
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Backup & Recovery 💾

### Backup Data
```bash
# Create backup
tar -czf researchmate-backup-$(date +%Y%m%d).tar.gz data logs chroma_persist
```

### Restore Data
```bash
# Stop services
docker-compose down

# Restore backup
tar -xzf researchmate-backup-YYYYMMDD.tar.gz

# Start services
docker-compose up -d
```

## Monitoring 📊

### Health Checks
```bash
# Manual health check
curl http://localhost:8000/health

# Container health
docker-compose ps
```

### Resource Usage
```bash
# Container stats
docker stats

# System usage
docker system df
```

---

For support, check the [main documentation](README.md) or open an issue on GitHub.
