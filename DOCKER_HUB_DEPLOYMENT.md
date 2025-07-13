# Docker Hub Deployment Guide

## Step-by-Step Instructions

### 1. Prerequisites

- Docker installed and running on your machine
- Docker Hub account (create one at https://hub.docker.com)
- Render account (create one at https://render.com)

### 2. Build and Push to Docker Hub

#### Option A: Using the automated script (Windows)
```bash
scripts\build-and-push.bat
```

#### Option B: Using the automated script (macOS/Linux)
```bash
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh
```GROQ_API_KEY = your_groq_api_key_hereGROQ_API_KEY = your_groq_api_key_hereGROQ_API_KEY = your_groq_api_key_here

#### Option C: Manual commands
```bash
# Build the image
docker build -t ananthakr1shnan/researchmate:latest .

# Login to Docker Hub
docker login

# Push the image
docker push ananthakr1shnan/researchmate:latest
```

### 3. Deploy on Render

1. **Go to Render Dashboard**:
   - Visit https://dashboard.render.com
   - Click "New +" → "Web Service"

2. **Choose Deployment Method**:
   - Select "Deploy an existing image from a registry"
   - **NOT** "Build and deploy from a Git repository"

3. **Configure the Service**:
   - **Image URL**: `ananthakr1shnan/researchmate:latest`
   - **Name**: `researchmate-app` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: Not applicable (using Docker image)

4. **Set Environment Variables**:
   ```
   GROQ_API_KEY = your_groq_api_key_here
   PORT = 8000
   ```

5. **Configure Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Port**: `8000` (should auto-detect)
   - **Build Command**: Leave empty (not needed for Docker images)
   - **Start Command**: Leave empty (Dockerfile handles this)

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete

### 4. Verify Deployment

Once deployed, you should see:
- ✅ Health checks passing
- ✅ Service status: "Live"
- 🌐 Your app accessible at: `https://your-service-name.onrender.com`

### 5. Update Deployment

To update your app:

1. **Make changes to your code**
2. **Rebuild and push new image**:
   ```bash
   # Build with new tag
   docker build -t ananthakr1shnan/researchmate:v1.1 .
   docker push ananthakr1shnan/researchmate:v1.1
   
   # Or update latest
   docker build -t ananthakr1shnan/researchmate:latest .
   docker push ananthakr1shnan/researchmate:latest
   ```

3. **Update Render service**:
   - Go to your service in Render dashboard
   - Go to "Settings"
   - Update "Image URL" if using versioned tags
   - Click "Save Changes"
   - Service will automatically redeploy

### 6. Benefits of Docker Hub Deployment

✅ **Faster deployments** (no build time on Render)
✅ **More reliable** (pre-built, tested image)
✅ **Version control** (tagged images)
✅ **Rollback capability** (use previous image tags)
✅ **Consistent environment** (same image everywhere)

### 7. Troubleshooting

#### Build Issues:
```bash
# Check Docker is running
docker --version

# Clean build (if needed)
docker system prune -f
docker build --no-cache -t ananthakr1shnan/researchmate:latest .
```

#### Push Issues:
```bash
# Re-login to Docker Hub
docker logout
docker login

# Check image exists locally
docker images | grep researchmate
```

#### Render Issues:
- Check logs in Render dashboard
- Verify environment variables are set
- Ensure health check endpoint `/health` is accessible
- Check that port 8000 is exposed and used

### 8. Image Tags Strategy

You can use different tagging strategies:

```bash
# Development
docker build -t ananthakr1shnan/researchmate:dev .
docker push ananthakr1shnan/researchmate:dev

# Staging
docker build -t ananthakr1shnan/researchmate:staging .
docker push ananthakr1shnan/researchmate:staging

# Production
docker build -t ananthakr1shnan/researchmate:latest .
docker build -t ananthakr1shnan/researchmate:v1.0 .
docker push ananthakr1shnan/researchmate:latest
docker push ananthakr1shnan/researchmate:v1.0
```

### 9. Security Considerations

- ✅ Never include secrets in Dockerfile
- ✅ Use environment variables for API keys
- ✅ Keep Docker image updated
- ✅ Use specific Python version (3.11-slim)
- ✅ Remove unnecessary packages

### 10. Monitoring

After deployment, monitor:
- Application logs in Render dashboard
- Health check status
- Response times
- Resource usage

---

## Quick Commands Reference

```bash
# Build
docker build -t ananthakr1shnan/researchmate:latest .

# Test locally
docker run -p 8000:8000 -e GROQ_API_KEY=your_key ananthakr1shnan/researchmate:latest

# Push to Docker Hub
docker login
docker push ananthakr1shnan/researchmate:latest

# Deploy on Render
# Use Docker Hub image: ananthakr1shnan/researchmate:latest
```
