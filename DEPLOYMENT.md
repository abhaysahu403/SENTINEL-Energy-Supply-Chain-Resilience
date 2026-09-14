# 🚀 SENTINEL - Complete Deployment Guide

## 📋 Prerequisites

- ✅ Docker Desktop installed and running
- ✅ Docker Compose installed
- ✅ Git installed
- ✅ GitHub account with repository access

---

## 🏃 Quick Start (Local Docker)

### **Option 1: Full Stack (Recommended)**

```bash
# Clone the repository
git clone https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience.git
cd SENTINEL-Energy-Supply-Chain-Resilience

# Start all services
docker-compose up --build

# Access the application
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### **Option 2: Quickstart (Minimal)**

```bash
# Use the quickstart compose file
docker-compose -f docker-compose.quickstart.yml up --build
```

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the project root:

```env
# Security
JWT_SECRET=your-secret-key-here-change-this

# Application
SENTINEL_APP_ENV=development
SENTINEL_LOG_LEVEL=INFO
SENTINEL_AUTOPLAY=1

# Database
SENTINEL_DATABASE_URL=sqlite:////app/sentinel.db
```

### **Generate JWT Secret**

```bash
# Windows PowerShell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)

# Linux/Mac
openssl rand -base64 32
```

---

## 🧪 Testing the Deployment

### **1. Check Services Status**

```bash
docker-compose ps
```

**Expected Output:**
```
NAME                 STATUS        PORTS
sentinel-backend     Up (healthy)  0.0.0.0:8000->8000/tcp
sentinel-frontend    Up (healthy)  0.0.0.0:5173->80/tcp
```

### **2. Test Backend API**

```bash
# Health check
curl http://localhost:8000/health

# Get system status
curl http://localhost:8000/api/system/status

# View API documentation
open http://localhost:8000/docs  # Windows
xdg-open http://localhost:8000/docs  # Linux
```

### **3. Test Frontend**

Open browser: http://localhost:5173

---

## 📊 Viewing Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

---

## 🛑 Stopping the Application

```bash
# Stop services (keep data)
docker-compose stop

# Stop and remove containers (keep data)
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

---

## 🔄 CI/CD Pipeline Setup

### **1. GitHub Secrets Configuration**

Go to: `GitHub Repository → Settings → Secrets and variables → Actions`

Add these secrets:

| Secret Name | Description | Required |
|------------|-------------|----------|
| `DOCKER_USERNAME` | Docker Hub username | Optional* |
| `DOCKER_TOKEN` | Docker Hub access token | Optional* |
| `JWT_SECRET` | JWT secret for backend | No (uses default for CI) |

*Only required if you want to push images to Docker Hub

### **2. Create Docker Hub Token**

1. Login to https://hub.docker.com
2. Go to: `Account Settings → Security → New Access Token`
3. Name: `GitHub Actions SENTINEL`
4. Permissions: `Read, Write, Delete`
5. Copy the token and add to GitHub Secrets as `DOCKER_TOKEN`

### **3. Trigger CI/CD Pipeline**

The pipeline runs automatically on:
- ✅ Push to `main` or `develop` branch
- ✅ Pull Request to `main` or `develop`

**Pipeline Stages:**
1. **Validate** - Linting & Unit Tests
2. **Build** - Docker image builds
3. **Integration Test** - Full stack testing
4. **Push** - Push to Docker Hub (only on main/develop)
5. **Summary** - Deployment report

---

## 🐛 Troubleshooting

### **Problem: Port Already in Use**

```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Backend
  - "5174:80"    # Frontend
```

### **Problem: Container Won't Start**

```bash
# Check logs
docker-compose logs backend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### **Problem: Backend Can't Find Data Files**

```bash
# Ensure data directory exists
ls data/

# Check volume mounts
docker-compose config
```

### **Problem: Frontend Can't Connect to Backend**

1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in backend
3. Check VITE_API_BASE in frontend Dockerfile
4. Clear browser cache

---

## 📈 Monitoring

### **Container Stats**

```bash
# Resource usage
docker stats

# Specific container
docker stats sentinel-backend
```

### **Health Checks**

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:5173
```

---

## 🎯 Production Deployment

For production deployment, see:
- **Azure Kubernetes**: `docs/azure-deployment.md`
- **AWS ECS**: `docs/aws-deployment.md`
- **Kubernetes**: `helm/README.md`

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Project README**: [README.md](README.md)
- **CI/CD Documentation**: [docs/cicd.md](docs/cicd.md)
- **Helm Charts**: [helm/README.md](helm/README.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Push and create a Pull Request
5. Wait for CI/CD pipeline to pass ✅

---

**🎉 Happy Deploying!**
