# SENTINEL Helm Charts - Quick Start Guide

## Pre-Deployment Checklist

Before deploying, verify the following:

### ✅ 1. ACR Images Available

```powershell
# Check backend image
az acr repository show-tags --name acrsentineldev2026 --repository sentinel-backend --output table

# Check frontend image
az acr repository show-tags --name acrsentineldev2026 --repository sentinel-frontend --output table

# Expected output: v1 (or your desired tag)
```

### ✅ 2. AKS Cluster Access

```powershell
# Verify kubectl access
kubectl cluster-info

# Check current context
kubectl config current-context

# List nodes
kubectl get nodes
```

### ✅ 3. NGINX Ingress Controller Installed

```powershell
# Check if NGINX Ingress Controller is running
kubectl get pods -n ingress-nginx

# If not installed, run:
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
```

### ✅ 4. Generate JWT Secret

```powershell
# Generate a secure JWT secret
$JWT_SECRET = [Convert]::ToBase64String((1..32 | ForEach-Object {Get-Random -Maximum 256}))

# Display it (save this value!)
Write-Host "JWT Secret: $JWT_SECRET"
```

## Deployment Steps

### Step 1: Create Namespace

```powershell
kubectl create namespace sentinel
```

### Step 2: Configure ACR Access (If using private ACR)

#### Option A: Using Azure AD Workload Identity (Recommended for Production)

```powershell
# Your AKS cluster should already have ACR integration enabled
# Verify with:
az aks show --name aks-sentinel-dev --resource-group rg-sentinel-dev --query "servicePrincipalProfile"
```

#### Option B: Using Image Pull Secret (For Testing)

```powershell
# Create image pull secret
$ACR_NAME = "acrsentineldev2026"
$SERVICE_PRINCIPAL_NAME = "sentinel-acr-sp"

# Get ACR ID
$ACR_ID = az acr show --name $ACR_NAME --query id --output tsv

# Create service principal
$SP_PASSWD = az ad sp create-for-rbac `
  --name $SERVICE_PRINCIPAL_NAME `
  --scopes $ACR_ID `
  --role acrpull `
  --query password `
  --output tsv

$SP_APP_ID = az ad sp list `
  --display-name $SERVICE_PRINCIPAL_NAME `
  --query [0].appId `
  --output tsv

# Create Kubernetes secret
kubectl create secret docker-registry acr-secret `
  --namespace sentinel `
  --docker-server="${ACR_NAME}.azurecr.io" `
  --docker-username=$SP_APP_ID `
  --docker-password=$SP_PASSWD
```

#### Option C: Attach ACR to AKS (Simplest)

```powershell
# Attach ACR to AKS (if not already attached)
az aks update `
  --name aks-sentinel-dev `
  --resource-group rg-sentinel-dev `
  --attach-acr acrsentineldev2026
```

### Step 3: Deploy Backend

```powershell
# Navigate to helm directory
cd C:\Projects\sentinel\helm

# Deploy backend
helm install sentinel-backend .\sentinel-backend `
  --namespace sentinel `
  --set image.tag=v1 `
  --set secrets.jwtSecret="$JWT_SECRET" `
  --set ingress.enabled=false `
  --wait

# If using image pull secret (Option B above):
helm install sentinel-backend .\sentinel-backend `
  --namespace sentinel `
  --set image.tag=v1 `
  --set secrets.jwtSecret="$JWT_SECRET" `
  --set ingress.enabled=false `
  --set imagePullSecrets[0].name=acr-secret `
  --wait
```

### Step 4: Verify Backend Deployment

```powershell
# Check pods
kubectl get pods -n sentinel -l app.kubernetes.io/name=sentinel-backend

# Wait for pod to be Ready (1/1)
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=sentinel-backend -n sentinel --timeout=120s

# Check logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend --tail=50

# Test health endpoint (port-forward)
kubectl port-forward -n sentinel svc/sentinel-backend 8000:8000
# Then in another terminal: curl http://localhost:8000/health
```

### Step 5: Deploy Frontend

```powershell
# Deploy frontend
helm install sentinel-frontend .\sentinel-frontend `
  --namespace sentinel `
  --set image.tag=v1 `
  --set config.apiBaseUrl=http://sentinel-backend:8000 `
  --set ingress.enabled=false `
  --wait

# If using image pull secret:
helm install sentinel-frontend .\sentinel-frontend `
  --namespace sentinel `
  --set image.tag=v1 `
  --set config.apiBaseUrl=http://sentinel-backend:8000 `
  --set ingress.enabled=false `
  --set imagePullSecrets[0].name=acr-secret `
  --wait
```

### Step 6: Verify Frontend Deployment

```powershell
# Check pods
kubectl get pods -n sentinel -l app.kubernetes.io/name=sentinel-frontend

# Wait for pod to be Ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=sentinel-frontend -n sentinel --timeout=120s

# Check logs
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-frontend --tail=50
```

### Step 7: Access the Application

#### Option A: Port Forward (Quick Testing)

```powershell
# Frontend (in terminal 1)
kubectl port-forward -n sentinel svc/sentinel-frontend 8080:80

# Backend (in terminal 2)
kubectl port-forward -n sentinel svc/sentinel-backend 8000:8000

# Open browser:
# - Frontend: http://localhost:8080
# - Backend API: http://localhost:8000
# - Backend Health: http://localhost:8000/health
# - Backend Docs: http://localhost:8000/docs
```

#### Option B: LoadBalancer Service (Temporary)

```powershell
# Expose frontend via LoadBalancer
kubectl patch service sentinel-frontend -n sentinel -p '{"spec":{"type":"LoadBalancer"}}'

# Wait for external IP
kubectl get svc sentinel-frontend -n sentinel -w

# Get the external IP
$FRONTEND_IP = kubectl get svc sentinel-frontend -n sentinel -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "Frontend URL: http://$FRONTEND_IP"
```

#### Option C: Enable Ingress (Production)

```powershell
# Update backend with ingress
helm upgrade sentinel-backend .\sentinel-backend `
  --namespace sentinel `
  --reuse-values `
  --set ingress.enabled=true `
  --set ingress.hosts[0].host=api.sentinel.yourdomain.com `
  --set ingress.hosts[0].paths[0].path=/ `
  --set ingress.hosts[0].paths[0].pathType=Prefix

# Update frontend with ingress
helm upgrade sentinel-frontend .\sentinel-frontend `
  --namespace sentinel `
  --reuse-values `
  --set ingress.enabled=true `
  --set ingress.hosts[0].host=sentinel.yourdomain.com `
  --set ingress.hosts[0].paths[0].path=/ `
  --set ingress.hosts[0].paths[0].pathType=Prefix `
  --set config.apiBaseUrl=https://api.sentinel.yourdomain.com
```

## Verification Commands

### Check All Resources

```powershell
# All resources in sentinel namespace
kubectl get all -n sentinel

# Detailed deployment info
kubectl describe deployment sentinel-backend -n sentinel
kubectl describe deployment sentinel-frontend -n sentinel

# Pod status
kubectl get pods -n sentinel -o wide

# Services
kubectl get svc -n sentinel

# ConfigMaps and Secrets
kubectl get configmap -n sentinel
kubectl get secret -n sentinel
```

### Test Backend API

```powershell
# Port-forward backend
kubectl port-forward -n sentinel svc/sentinel-backend 8000:8000

# In another terminal or browser:
# Health: http://localhost:8000/health
# Root: http://localhost:8000/
# API Docs: http://localhost:8000/docs
# OpenAPI: http://localhost:8000/openapi.json

# Using PowerShell:
Invoke-RestMethod -Uri http://localhost:8000/health
Invoke-RestMethod -Uri http://localhost:8000/
```

### View Real-Time Logs

```powershell
# Backend logs (follow)
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend -f

# Frontend logs (follow)
kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-frontend -f

# All pods in namespace
kubectl logs -n sentinel --all-containers=true -f
```

## Troubleshooting

### Issue: ImagePullBackOff

```powershell
# Check pod events
kubectl describe pod -n sentinel <pod-name>

# Common causes:
# 1. Wrong image tag
# 2. Missing image pull secret
# 3. ACR not attached to AKS

# Fix: Verify image exists
az acr repository show-tags --name acrsentineldev2026 --repository sentinel-backend

# Fix: Attach ACR to AKS
az aks update --name aks-sentinel-dev --resource-group rg-sentinel-dev --attach-acr acrsentineldev2026
```

### Issue: CrashLoopBackOff

```powershell
# Check pod logs
kubectl logs -n sentinel <pod-name>

# Check previous logs (if restarted)
kubectl logs -n sentinel <pod-name> --previous

# Common causes:
# 1. Missing JWT secret
# 2. Application error
# 3. Health check failing too fast

# Fix: Check secret
kubectl get secret sentinel-backend -n sentinel -o yaml
```

### Issue: Pod Stuck in Pending

```powershell
# Check events
kubectl describe pod -n sentinel <pod-name>

# Common causes:
# 1. Insufficient resources
# 2. Node selector not matching
# 3. PVC not bound

# Check node resources
kubectl describe nodes
kubectl top nodes
```

### Issue: Service Not Accessible

```powershell
# Check service
kubectl get svc -n sentinel sentinel-backend

# Check endpoints
kubectl get endpoints -n sentinel sentinel-backend

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n sentinel -- curl http://sentinel-backend:8000/health
```

## Cleanup

### Remove Deployments

```powershell
# Uninstall frontend
helm uninstall sentinel-frontend -n sentinel

# Uninstall backend
helm uninstall sentinel-backend -n sentinel
```

### Remove All Resources

```powershell
# Delete entire namespace (removes everything)
kubectl delete namespace sentinel
```

### Detach ACR (Optional)

```powershell
# Only if you want to remove ACR integration
az aks update --name aks-sentinel-dev --resource-group rg-sentinel-dev --detach-acr acrsentineldev2026
```

## Next Steps

1. **Enable Monitoring**: Set up Azure Monitor for AKS
2. **Configure Alerts**: Create alerts for pod failures and resource usage
3. **Set up CI/CD**: Integrate with Azure DevOps or GitHub Actions
4. **Add Custom Domain**: Configure DNS and enable TLS with cert-manager
5. **Scale for Production**: Increase replicas and enable autoscaling
6. **Backup Strategy**: Set up backup for any persistent data

## Useful Commands Reference

```powershell
# Get all Helm releases
helm list -n sentinel

# Get Helm release history
helm history sentinel-backend -n sentinel

# Get rendered manifest
helm get manifest sentinel-backend -n sentinel

# Get values for release
helm get values sentinel-backend -n sentinel

# Rollback to previous version
helm rollback sentinel-backend -n sentinel

# Upgrade with new values
helm upgrade sentinel-backend .\sentinel-backend -n sentinel --reuse-values

# Dry-run to test changes
helm upgrade sentinel-backend .\sentinel-backend -n sentinel --dry-run --debug

# Template rendering (no installation)
helm template sentinel-backend .\sentinel-backend --namespace sentinel
```

## Support

For issues:
- Check logs: `kubectl logs -n sentinel -l app.kubernetes.io/name=sentinel-backend`
- Check events: `kubectl get events -n sentinel --sort-by='.lastTimestamp'`
- Review documentation: See [DEPLOYMENT.md](./DEPLOYMENT.md)
