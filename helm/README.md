# SENTINEL Helm Charts

Enterprise-grade Kubernetes deployment for the SENTINEL Energy Supply Chain Resilience Platform.

## Overview

This directory contains production-ready Helm charts for deploying SENTINEL on Azure Kubernetes Service (AKS):

- **sentinel-backend**: FastAPI backend API with AI-powered risk analysis
- **sentinel-frontend**: React/Vite frontend application

## Quick Start

```bash
# Create namespace
kubectl create namespace sentinel

# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Deploy backend
helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --set secrets.jwtSecret="$JWT_SECRET" \
  --set ingress.hosts[0].host=api.sentinel.yourdomain.com

# Deploy frontend
helm install sentinel-frontend ./sentinel-frontend \
  --namespace sentinel \
  --set config.apiBaseUrl=https://api.sentinel.yourdomain.com \
  --set ingress.hosts[0].host=sentinel.yourdomain.com
```

## Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide with prerequisites, troubleshooting, and best practices
- **[sentinel-backend/README.md](./sentinel-backend/README.md)** - Backend chart documentation
- **[sentinel-frontend/README.md](./sentinel-frontend/README.md)** - Frontend chart documentation

## Chart Structure

Each chart follows Helm best practices:

```
sentinel-backend/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default configuration values
├── values-dev.yaml         # Development environment overrides
├── values-prod.yaml        # Production environment overrides
└── templates/
    ├── deployment.yaml     # Main deployment manifest
    ├── service.yaml        # ClusterIP service
    ├── ingress.yaml        # Ingress configuration
    ├── configmap.yaml      # Application configuration
    ├── secret.yaml         # Sensitive configuration
    ├── serviceaccount.yaml # Service account
    ├── hpa.yaml           # Horizontal Pod Autoscaler
    ├── networkpolicy.yaml  # Network security policies
    ├── poddisruptionbudget.yaml  # PDB for HA
    ├── _helpers.tpl       # Template helpers
    └── NOTES.txt          # Post-installation notes
```

## Environment-Specific Deployments

### Development

```bash
helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel-dev \
  --create-namespace \
  --values ./sentinel-backend/values-dev.yaml
```

### Production

```bash
helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel-prod \
  --create-namespace \
  --values ./sentinel-backend/values-prod.yaml \
  --set secrets.jwtSecret="$PROD_JWT_SECRET"
```

## Key Features

### High Availability
- Pod anti-affinity rules
- Horizontal Pod Autoscaling (HPA)
- Pod Disruption Budgets (PDB)
- Rolling updates with zero downtime

### Security
- Non-root containers
- Read-only root filesystems
- Security contexts and pod security standards
- Network policies for traffic control
- TLS/SSL with cert-manager integration
- Secrets management

### Observability
- Health check probes (liveness, readiness, startup)
- Structured logging
- Resource limits and requests
- Azure Monitor integration ready

### Production-Ready
- Follows Kubernetes best practices
- Azure AKS optimized
- CI/CD friendly
- Environment-specific configurations
- Comprehensive documentation

## Configuration

### Backend Values

Key configuration options:

```yaml
image:
  repository: acrsentineldev2026.azurecr.io/sentinel-backend
  tag: "v1.0.0"

replicaCount: 2

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10

config:
  appEnv: "production"
  logLevel: "INFO"
  autoplay: "0"

secrets:
  jwtSecret: ""  # Required
```

### Frontend Values

Key configuration options:

```yaml
image:
  repository: acrsentineldev2026.azurecr.io/sentinel-frontend
  tag: "v1.0.0"

replicaCount: 2

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

config:
  apiBaseUrl: "https://api.sentinel.example.com"
```

## Prerequisites

1. **Kubernetes cluster** (AKS 1.24+)
2. **Helm** (3.8+)
3. **kubectl** (configured)
4. **NGINX Ingress Controller**
5. **cert-manager** (optional, for TLS)
6. **Azure Container Registry** (ACR)

## Validation

```bash
# Lint charts
helm lint ./sentinel-backend
helm lint ./sentinel-frontend

# Template rendering
helm template sentinel-backend ./sentinel-backend --namespace sentinel

# Dry-run install
helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --dry-run \
  --debug
```

## Upgrading

```bash
# Upgrade with new version
helm upgrade sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --set image.tag=v1.1.0

# Upgrade with new values
helm upgrade sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --values ./sentinel-backend/values-prod.yaml
```

## Rollback

```bash
# View history
helm history sentinel-backend -n sentinel

# Rollback to previous
helm rollback sentinel-backend -n sentinel

# Rollback to specific revision
helm rollback sentinel-backend 3 -n sentinel
```

## Monitoring

```bash
# Check deployments
kubectl get deployments -n sentinel

# Check pods
kubectl get pods -n sentinel

# Check HPA
kubectl get hpa -n sentinel

# View logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend -f
```

## Uninstall

```bash
# Uninstall releases
helm uninstall sentinel-backend -n sentinel
helm uninstall sentinel-frontend -n sentinel

# Delete namespace
kubectl delete namespace sentinel
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/abhaysahu/sentinel/issues
- Documentation: See [DEPLOYMENT.md](./DEPLOYMENT.md)

## License

See the main project repository for license information.
