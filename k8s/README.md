# SENTINEL Kubernetes Deployment Guide

This directory contains production-ready Kubernetes manifests for deploying the SENTINEL Energy Supply Chain Resilience Platform on Azure Kubernetes Service (AKS).

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates the `sentinel` namespace with resource quotas and limits |
| `configmap.yaml` | Non-sensitive configuration values |
| `secrets.yaml.example` | Template for creating secrets (DO NOT commit actual secrets!) |
| `postgres-deployment.yaml` | PostgreSQL StatefulSet and Service |
| `neo4j-deployment.yaml` | Neo4j graph database StatefulSet and Service |
| `backend-deployment.yaml` | Backend API deployment with health checks and autoscaling |
| `backend-service.yaml` | Backend service, HPA, and PDB configurations |
| `frontend-deployment.yaml` | Frontend Nginx deployment |
| `frontend-service.yaml` | Frontend service, Ingress, HPA, and PDB |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      INGRESS (NGINX)                         │
│  sentinel.yourdomain.com → Frontend                          │
│  api.sentinel.yourdomain.com → Backend                       │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              │                            │
    ┌─────────▼────────┐        ┌─────────▼────────┐
    │    FRONTEND      │        │     BACKEND      │
    │   (2-6 pods)     │        │   (3-10 pods)    │
    │  Nginx + React   │        │  FastAPI Python  │
    └──────────────────┘        └─────────┬────────┘
                                          │
                        ┌─────────────────┼─────────────────┐
                        │                 │                 │
                ┌───────▼─────┐  ┌────────▼────────┐  ┌────▼────┐
                │  PostgreSQL  │  │     Neo4j       │  │  Kafka  │
                │ (StatefulSet)│  │  (StatefulSet)  │  │(Optional)│
                └──────────────┘  └─────────────────┘  └─────────┘
```

## 🚀 Deployment Steps

### Prerequisites

1. **Azure CLI and kubectl installed**
   ```bash
   az --version
   kubectl version --client
   ```

2. **AKS Cluster created**
   ```bash
   az aks create \
     --resource-group sentinel-rg \
     --name sentinel-aks \
     --node-count 3 \
     --node-vm-size Standard_D4s_v3 \
     --enable-managed-identity \
     --generate-ssh-keys
   ```

3. **Get AKS credentials**
   ```bash
   az aks get-credentials --resource-group sentinel-rg --name sentinel-aks
   ```

4. **Docker images pushed to registry**
   ```bash
   # Tag images
   docker tag sentinel-backend:latest abhaysahu403/sentinel-backend:latest
   docker tag sentinel-frontend:latest abhaysahu403/sentinel-frontend:latest
   
   # Push to Docker Hub
   docker login
   docker push abhaysahu403/sentinel-backend:latest
   docker push abhaysahu403/sentinel-frontend:latest
   ```

### Step 1: Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### Step 2: Create Secrets

**IMPORTANT:** Never commit secrets to git!

```bash
# Method 1: Create from command line
kubectl create secret generic sentinel-secrets \
  --namespace=sentinel \
  --from-literal=database-url='postgresql://sentinel:YOUR_PASSWORD@postgres.sentinel.svc.cluster.local:5432/sentinel' \
  --from-literal=neo4j-user='neo4j' \
  --from-literal=neo4j-password='YOUR_NEO4J_PASSWORD' \
  --from-literal=neo4j-auth='neo4j/YOUR_NEO4J_PASSWORD' \
  --from-literal=postgres-password='YOUR_POSTGRES_PASSWORD' \
  --from-literal=jwt-secret='YOUR_JWT_SECRET' \
  --from-literal=eia-api-key='' \
  --from-literal=marinetraffic-api-key=''

# Method 2: Use Azure Key Vault (Recommended)
# See secrets.yaml.example for detailed instructions
```

### Step 3: Create ConfigMap

```bash
# Edit configmap.yaml first to set your domain names
kubectl apply -f configmap.yaml
```

### Step 4: Deploy Databases

```bash
# PostgreSQL
kubectl apply -f postgres-deployment.yaml

# Neo4j
kubectl apply -f neo4j-deployment.yaml

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l component=postgres -n sentinel --timeout=300s
kubectl wait --for=condition=ready pod -l component=neo4j -n sentinel --timeout=300s
```

### Step 5: Deploy Backend

```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# Wait for backend to be ready
kubectl wait --for=condition=ready pod -l component=backend -n sentinel --timeout=300s
```

### Step 6: Deploy Frontend

```bash
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
```

### Step 7: Verify Deployment

```bash
# Check all pods
kubectl get pods -n sentinel

# Check services
kubectl get services -n sentinel

# Check ingress
kubectl get ingress -n sentinel

# View logs
kubectl logs -f deployment/sentinel-backend -n sentinel
kubectl logs -f deployment/sentinel-frontend -n sentinel
```

## 🔍 Monitoring and Health Checks

### Health Endpoints

- Backend: `http://sentinel-backend:8000/health`
- Frontend: `http://sentinel-frontend/`

### Check Pod Status

```bash
# Get pod status
kubectl get pods -n sentinel -o wide

# Describe pod for details
kubectl describe pod <pod-name> -n sentinel

# Get events
kubectl get events -n sentinel --sort-by='.lastTimestamp'
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/sentinel-backend -n sentinel --tail=100

# Frontend logs
kubectl logs -f deployment/sentinel-frontend -n sentinel --tail=100

# Previous container logs (if pod crashed)
kubectl logs <pod-name> -n sentinel --previous
```

## 📈 Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment sentinel-backend --replicas=5 -n sentinel

# Scale frontend
kubectl scale deployment sentinel-frontend --replicas=4 -n sentinel
```

### Auto-scaling (HPA)

Auto-scaling is configured in the service YAML files:

- **Backend**: 3-10 pods based on CPU (70%) and Memory (80%)
- **Frontend**: 2-6 pods based on CPU (70%) and Memory (80%)

Check HPA status:
```bash
kubectl get hpa -n sentinel
kubectl describe hpa sentinel-backend-hpa -n sentinel
```

## 🔒 Security Best Practices

1. **Use Azure Key Vault** for secrets management
2. **Enable Pod Security Standards** in namespace
3. **Use Network Policies** to restrict traffic
4. **Enable RBAC** for fine-grained access control
5. **Scan images** for vulnerabilities before deployment
6. **Use private container registry** (Azure Container Registry)
7. **Enable audit logging** on AKS cluster

## 🔄 Updates and Rollbacks

### Rolling Update

```bash
# Update image
kubectl set image deployment/sentinel-backend backend=abhaysahu403/sentinel-backend:v2.0.0 -n sentinel

# Check rollout status
kubectl rollout status deployment/sentinel-backend -n sentinel
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/sentinel-backend -n sentinel

# Rollback to previous version
kubectl rollout undo deployment/sentinel-backend -n sentinel

# Rollback to specific revision
kubectl rollout undo deployment/sentinel-backend --to-revision=2 -n sentinel
```

## 🗑️ Cleanup

```bash
# Delete all resources in sentinel namespace
kubectl delete namespace sentinel

# Or delete individual components
kubectl delete -f frontend-service.yaml
kubectl delete -f frontend-deployment.yaml
kubectl delete -f backend-service.yaml
kubectl delete -f backend-deployment.yaml
kubectl delete -f neo4j-deployment.yaml
kubectl delete -f postgres-deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete -f namespace.yaml
```

## 📊 Resource Requirements

### Minimum Cluster Requirements

- **Nodes**: 3 nodes (for high availability)
- **Node Size**: Standard_D4s_v3 (4 vCPU, 16 GB RAM) or larger
- **Total Resources**:
  - CPU: 20 vCPU (requests) / 40 vCPU (limits)
  - Memory: 40 GB (requests) / 80 GB (limits)
  - Storage: ~100 GB persistent storage

### Per-Pod Resources

| Component | Replicas | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|----------|-------------|-----------|----------------|--------------|
| Backend | 3-10 | 500m | 2000m | 512Mi | 2Gi |
| Frontend | 2-6 | 100m | 500m | 128Mi | 512Mi |
| PostgreSQL | 1 | 500m | 2000m | 1Gi | 4Gi |
| Neo4j | 1 | 500m | 2000m | 2Gi | 4Gi |

## 🌐 DNS Configuration

After deployment, update your DNS records:

```
sentinel.yourdomain.com       → Ingress IP
api.sentinel.yourdomain.com   → Ingress IP
```

Get Ingress IP:
```bash
kubectl get ingress sentinel-ingress -n sentinel
```

## 🛠️ Troubleshooting

### Pod is in CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n sentinel --previous

# Check events
kubectl describe pod <pod-name> -n sentinel
```

### ImagePullBackOff Error

```bash
# Verify image name and tag
kubectl describe pod <pod-name> -n sentinel

# Check if image exists
docker pull abhaysahu403/sentinel-backend:latest
```

### Database Connection Issues

```bash
# Check if database pod is running
kubectl get pods -n sentinel -l component=postgres

# Test connection from backend pod
kubectl exec -it <backend-pod> -n sentinel -- /bin/bash
# Inside pod: nc -zv postgres.sentinel.svc.cluster.local 5432
```

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience/issues
- Email: abhaysahu403@gmail.com
