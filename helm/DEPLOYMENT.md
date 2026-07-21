# SENTINEL Helm Chart Deployment Guide

## Overview

This guide provides detailed instructions for deploying the SENTINEL Energy Supply Chain Resilience Platform on Azure Kubernetes Service (AKS) using Helm charts.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Internet (HTTPS)                               │
│         │                                       │
└─────────┼───────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│  NGINX Ingress Controller                       │
│  - TLS Termination (Let's Encrypt)              │
│  - Security Headers                             │
└─────────┬───────────────────────┬─────────────┘
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌──────────────────────┐
│  Frontend        │    │  Backend API         │
│  (React/Vite)    │◄───┤  (FastAPI/Python)    │
│                  │    │                      │
│  - Static SPA    │    │  - REST API          │
│  - Nginx         │    │  - SQLite DB         │
│  - HPA: 2-6      │    │  - HPA: 2-10         │
└──────────────────┘    └──────────────────────┘
```

## Prerequisites

### Required Tools

```bash
# Helm 3.8+
helm version

# kubectl configured for your AKS cluster
kubectl cluster-info

# Azure CLI (optional, for ACR authentication)
az --version
```

### Required Infrastructure

1. **AKS Cluster**: Running and accessible
2. **NGINX Ingress Controller**: Installed in the cluster
3. **cert-manager**: Installed for automatic TLS certificates (optional)
4. **Azure Container Registry**: Contains the application images

### Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
```

### Install cert-manager (Optional)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@sentinel.example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Quick Start

### 1. Create Namespace

```bash
kubectl create namespace sentinel
```

### 2. Configure ACR Authentication

If using Azure Container Registry with private images:

```bash
# Login to Azure
az login

# Create service principal for ACR access
ACR_NAME="acrsentineldev2026"
SERVICE_PRINCIPAL_NAME="sentinel-acr-sp"

ACR_REGISTRY_ID=$(az acr show --name $ACR_NAME --query id --output tsv)

SP_PASSWD=$(az ad sp create-for-rbac \
  --name $SERVICE_PRINCIPAL_NAME \
  --scopes $ACR_REGISTRY_ID \
  --role acrpull \
  --query password \
  --output tsv)

SP_APP_ID=$(az ad sp list \
  --display-name $SERVICE_PRINCIPAL_NAME \
  --query [0].appId \
  --output tsv)

# Create Kubernetes secret
kubectl create secret docker-registry acr-secret \
  --namespace sentinel \
  --docker-server=${ACR_NAME}.azurecr.io \
  --docker-username=$SP_APP_ID \
  --docker-password=$SP_PASSWD
```

### 3. Generate JWT Secret

```bash
# Generate a secure JWT secret
JWT_SECRET=$(openssl rand -base64 32)
echo "JWT Secret: $JWT_SECRET"
# Save this value for the Helm installation
```

### 4. Deploy Backend

```bash
cd helm

helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --set image.tag=latest \
  --set secrets.jwtSecret="$JWT_SECRET" \
  --set ingress.hosts[0].host=api.sentinel.yourdomain.com \
  --set ingress.tls[0].hosts[0]=api.sentinel.yourdomain.com \
  --set imagePullSecrets[0].name=acr-secret
```

### 5. Verify Backend Deployment

```bash
# Check pods
kubectl get pods -n sentinel -l app.kubernetes.io/name=sentinel-backend

# Check service
kubectl get svc -n sentinel sentinel-backend

# Check logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend --tail=100
```

### 6. Deploy Frontend

```bash
helm install sentinel-frontend ./sentinel-frontend \
  --namespace sentinel \
  --set image.tag=latest \
  --set config.apiBaseUrl=https://api.sentinel.yourdomain.com \
  --set ingress.hosts[0].host=sentinel.yourdomain.com \
  --set ingress.tls[0].hosts[0]=sentinel.yourdomain.com \
  --set imagePullSecrets[0].name=acr-secret
```

### 7. Verify Frontend Deployment

```bash
# Check pods
kubectl get pods -n sentinel -l app.kubernetes.io/name=sentinel-frontend

# Check ingress
kubectl get ingress -n sentinel

# Get external IP
kubectl get svc -n ingress-nginx nginx-ingress-ingress-nginx-controller
```

## Environment-Specific Deployments

### Development Environment

Create `values-dev.yaml`:

```yaml
replicaCount: 1

image:
  tag: "dev-latest"
  pullPolicy: Always

ingress:
  hosts:
    - host: api.sentinel-dev.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: sentinel-backend-dev-tls
      hosts:
        - api.sentinel-dev.yourdomain.com

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: false

config:
  appEnv: "development"
  logLevel: "DEBUG"
  autoplay: "1"

podDisruptionBudget:
  enabled: false
```

Deploy:

```bash
helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel-dev \
  --create-namespace \
  --values values-dev.yaml \
  --set secrets.jwtSecret="$JWT_SECRET"
```

### QA Environment

Create `values-qa.yaml`:

```yaml
replicaCount: 2

image:
  tag: "qa-v1.0.0"
  pullPolicy: IfNotPresent

ingress:
  hosts:
    - host: api.sentinel-qa.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: sentinel-backend-qa-tls
      hosts:
        - api.sentinel-qa.yourdomain.com

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
  maxReplicas: 5

config:
  appEnv: "qa"
  logLevel: "INFO"
  autoplay: "0"

podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

### Production Environment

Create `values-prod.yaml`:

```yaml
replicaCount: 3

image:
  tag: "v1.0.0"
  pullPolicy: IfNotPresent

ingress:
  hosts:
    - host: api.sentinel.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: sentinel-backend-prod-tls
      hosts:
        - api.sentinel.yourdomain.com

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10

config:
  appEnv: "production"
  logLevel: "WARNING"
  autoplay: "0"

podDisruptionBudget:
  enabled: true
  minAvailable: 2

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
                - sentinel-backend
        topologyKey: kubernetes.io/hostname

nodeSelector:
  agentpool: production
```

Deploy:

```bash
helm install sentinel-backend ./sentinel-backend \
  --namespace sentinel-prod \
  --create-namespace \
  --values values-prod.yaml \
  --set secrets.jwtSecret="$JWT_SECRET"
```

## Upgrading Deployments

### Update Application Version

```bash
# Backend
helm upgrade sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --reuse-values \
  --set image.tag=v1.1.0

# Frontend
helm upgrade sentinel-frontend ./sentinel-frontend \
  --namespace sentinel \
  --reuse-values \
  --set image.tag=v1.1.0
```

### Update Configuration

```bash
helm upgrade sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --reuse-values \
  --set config.logLevel=DEBUG
```

### Rollback

```bash
# Check history
helm history sentinel-backend -n sentinel

# Rollback to previous version
helm rollback sentinel-backend -n sentinel

# Rollback to specific revision
helm rollback sentinel-backend 3 -n sentinel
```

## Monitoring & Operations

### Check Pod Status

```bash
# Backend
kubectl get pods -n sentinel -l app.kubernetes.io/name=sentinel-backend -w

# Frontend
kubectl get pods -n sentinel -l app.kubernetes.io/name=sentinel-frontend -w
```

### View Logs

```bash
# Backend logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend -f --tail=100

# Frontend logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-frontend -f --tail=100

# Specific pod logs
kubectl logs -n sentinel <pod-name> -f
```

### Check Resource Usage

```bash
# CPU and Memory usage
kubectl top pods -n sentinel

# HPA status
kubectl get hpa -n sentinel

# Describe HPA for details
kubectl describe hpa sentinel-backend -n sentinel
```

### Execute Commands in Pod

```bash
# Get shell access
kubectl exec -it -n sentinel <pod-name> -- /bin/bash

# Check backend health endpoint
kubectl exec -n sentinel <backend-pod-name> -- curl http://localhost:8000/health
```

### Port Forwarding

```bash
# Forward backend to local port
kubectl port-forward -n sentinel svc/sentinel-backend 8000:8000

# Forward frontend to local port
kubectl port-forward -n sentinel svc/sentinel-frontend 8080:80
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod -n sentinel <pod-name>

# Check events
kubectl get events -n sentinel --sort-by='.lastTimestamp'

# Check image pull secrets
kubectl get secrets -n sentinel
```

### Image Pull Errors

```bash
# Verify ACR credentials
kubectl get secret acr-secret -n sentinel -o yaml

# Test ACR access
az acr login --name acrsentineldev2026

# Recreate secret if needed
kubectl delete secret acr-secret -n sentinel
# Then recreate using steps in Quick Start
```

### Ingress Not Working

```bash
# Check ingress
kubectl describe ingress -n sentinel sentinel-backend

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Verify DNS
nslookup api.sentinel.yourdomain.com

# Check certificate (if using cert-manager)
kubectl get certificate -n sentinel
kubectl describe certificate sentinel-backend-tls -n sentinel
```

### Backend API Errors

```bash
# Check backend logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend --tail=200

# Check environment variables
kubectl exec -n sentinel <backend-pod> -- env | grep SENTINEL

# Check secrets
kubectl get secret sentinel-backend -n sentinel -o jsonpath='{.data}'
```

### High Memory Usage

```bash
# Check resource limits
kubectl describe pod -n sentinel <pod-name> | grep -A 5 Limits

# Increase memory limits in values.yaml
helm upgrade sentinel-backend ./sentinel-backend \
  --namespace sentinel \
  --reuse-values \
  --set resources.limits.memory=2Gi
```

## Uninstalling

### Remove Deployments

```bash
# Uninstall backend
helm uninstall sentinel-backend -n sentinel

# Uninstall frontend
helm uninstall sentinel-frontend -n sentinel
```

### Clean Up Resources

```bash
# Delete namespace (removes all resources)
kubectl delete namespace sentinel

# Delete image pull secrets (if created)
kubectl delete secret acr-secret -n sentinel

# Delete ClusterIssuer (if created)
kubectl delete clusterissuer letsencrypt-prod
```

## Best Practices

### Security

1. **Always use secrets for sensitive data**
   - Never commit secrets to Git
   - Use external secret managers (Azure Key Vault) in production

2. **Enable network policies**
   - Restrict pod-to-pod communication
   - Limit egress traffic

3. **Use TLS for all external communication**
   - Enable cert-manager for automatic certificate management
   - Enforce HTTPS redirects

4. **Run containers as non-root**
   - Already configured in the charts
   - Review security contexts regularly

### High Availability

1. **Use pod disruption budgets**
   - Ensure minimum availability during updates

2. **Enable autoscaling**
   - Scale based on CPU and memory metrics

3. **Use anti-affinity rules**
   - Spread pods across different nodes

4. **Set appropriate resource limits**
   - Prevent resource exhaustion

### Monitoring

1. **Centralized logging**
   - Ship logs to Azure Log Analytics
   - Use structured logging

2. **Metrics collection**
   - Enable Prometheus metrics
   - Use Azure Monitor for AKS

3. **Health checks**
   - Configure readiness and liveness probes
   - Monitor probe failures

## CI/CD Integration

### Azure DevOps Pipeline Example

```yaml
trigger:
  branches:
    include:
    - main
  paths:
    include:
    - backend/*
    - helm/sentinel-backend/*

stages:
- stage: Build
  jobs:
  - job: BuildBackend
    steps:
    - task: Docker@2
      inputs:
        containerRegistry: 'ACR-Connection'
        repository: 'sentinel-backend'
        command: 'buildAndPush'
        Dockerfile: 'backend/Dockerfile'
        tags: |
          $(Build.BuildId)
          latest

- stage: Deploy
  jobs:
  - job: DeployToAKS
    steps:
    - task: HelmDeploy@0
      inputs:
        connectionType: 'Azure Resource Manager'
        azureSubscription: 'Azure-Subscription'
        azureResourceGroup: 'rg-sentinel-prod'
        kubernetesCluster: 'aks-sentinel-prod'
        namespace: 'sentinel'
        command: 'upgrade'
        chartType: 'FilePath'
        chartPath: 'helm/sentinel-backend'
        releaseName: 'sentinel-backend'
        arguments: '--set image.tag=$(Build.BuildId)'
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/abhaysahu/sentinel/issues
- Documentation: https://docs.sentinel.example.com
- Email: support@sentinel.io
