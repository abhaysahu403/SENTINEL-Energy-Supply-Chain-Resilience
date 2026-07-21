# SENTINEL - Energy Supply Chain Resilience Platform

[![PR Validation](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/pr-validation.yml/badge.svg)](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/pr-validation.yml)
[![Production Deployment](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/production.yml/badge.svg)](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/production.yml)

## 🎯 Overview

SENTINEL is an enterprise-grade energy supply chain resilience platform deployed on Azure Kubernetes Service (AKS). The platform provides real-time monitoring, risk assessment, and scenario planning for energy supply chains.

## 🏗️ Architecture

- **Backend**: Python FastAPI application
- **Frontend**: React + Vite application  
- **Infrastructure**: Azure Kubernetes Service (AKS)
- **Container Registry**: Azure Container Registry (ACR)
- **Deployment**: Helm charts with GitOps workflow

## 🚀 CI/CD Pipeline

### GitHub Actions Workflows

| Workflow | Trigger | Status |
|----------|---------|--------|
| **PR Validation** | Pull Request to `main`/`develop` | [![PR Validation](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/pr-validation.yml/badge.svg)](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/pr-validation.yml) |
| **Dev Deployment** | Push to `develop` | [![Dev Deployment](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/dev.yml/badge.svg)](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/dev.yml) |
| **Production Deployment** | Push to `main` | [![Production Deployment](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/production.yml/badge.svg)](https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/actions/workflows/production.yml) |

### Pipeline Features

- ✅ Automated linting and testing
- ✅ Docker image builds for backend and frontend
- ✅ Security scanning with Trivy
- ✅ Helm-based deployments
- ✅ Zero-downtime rolling updates
- ✅ Automatic rollback on failure
- ✅ Health checks and readiness probes

## 📦 Deployment

### Prerequisites

- Azure subscription
- AKS cluster: `aks-sentinel-dev`
- ACR: `acrsentineldev2026.azurecr.io`
- kubectl configured for AKS
- Helm 3.x installed

### Quick Deploy

```bash
# Backend
helm install sentinel-backend ./helm/sentinel-backend \
  --namespace sentinel \
  --create-namespace \
  --set image.tag=latest \
  --set secrets.jwtSecret="${JWT_SECRET}"

# Frontend
helm install sentinel-frontend ./helm/sentinel-frontend \
  --namespace sentinel \
  --set image.tag=latest
```

## 🛠️ Development

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Linting
flake8 backend/app
```

## 📂 Project Structure

```
SENTINEL/
├── backend/                  # FastAPI backend application
│   ├── app/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React frontend application
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── helm/                     # Helm charts
│   ├── sentinel-backend/
│   └── sentinel-frontend/
├── .github/workflows/        # GitHub Actions CI/CD
├── Jenkins/                  # Jenkins pipelines
├── terraform/                # Infrastructure as Code
└── scripts/                  # Deployment scripts
```

## 🔐 Security

- Non-root containers
- Network policies enabled
- Pod security contexts configured
- Container image scanning
- Secrets management via Kubernetes secrets

## 📊 Monitoring

- Application Insights integration
- Log Analytics workspace
- Prometheus metrics
- Health check endpoints

## 📝 Documentation

- [CI/CD Documentation](docs/cicd.md)
- [Helm Charts Guide](helm/README.md)
- [Deployment Guide](helm/DEPLOYMENT.md)
- [Rollback Procedures](docs/rollback.md)

## 🤝 Contributing

1. Create a feature branch from `develop`
2. Make your changes
3. Ensure tests pass and linting is clean
4. Create a Pull Request
5. Wait for PR validation to pass
6. Merge after approval

## 📄 License

Copyright © 2026 SENTINEL Project

---

**Deployed on Azure** | **Powered by Kubernetes** | **Built with ❤️**
