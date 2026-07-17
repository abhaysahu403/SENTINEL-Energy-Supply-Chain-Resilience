# SENTINEL Kubernetes Deployment Guide
## QuickStart Architecture for Learning AKS

This directory contains **simplified, production-ready** Kubernetes manifests optimized for a **single-node AKS cluster** for learning Azure DevOps and Kubernetes fundamentals.

## 🎯 What You're Deploying

**QuickStart Architecture** (just like docker-compose.quickstart.yml):
```
┌─────────────────────────────────────┐
│     Azure Load Balancer (Public IP) │
└────────────────┬────────────────────┘
                 │
        ┌────────▼──────────┐
        │   FRONTEND POD    │
        │  Nginx + React    │
        │  (1 replica)      │
        └────────┬──────────┘
                 │
        ┌────────▼──────────┐
        │    BACKEND POD    │
        │  FastAPI Python   │
        │  (1 replica)      │
        │                   │
        │  • SQLite DB      │
        │  • NetworkX Graph │
        │  • In-memory Queue│
        └───────────────────┘
```

**What's NOT included** (to fit your 1-node cluster):
- ❌ PostgreSQL
- ❌ Neo4j
- ❌ Kafka + Zookeeper
- ❌ HPA (HorizontalPodAutoscaler)
- ❌ PDB (PodDisruptionBudget)
- ❌ Ingress Controller
- ❌ Multiple replicas
- ❌ Anti-affinity rules

## 📁 Files in This Directory

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates `sentinel` namespace |
| `configmap.yaml` | Application configuration |
| `secrets.yaml.example` | JWT secret template |
| `backend-deployment.yaml` | Backend deployment (1 pod) |
| `backend-service.yaml` | Backend ClusterIP service |
| `frontend-deployment.yaml` | Frontend deployment (1 pod) |
| `frontend-service.yaml` | Frontend LoadBalancer service |

## 🖥️ Your Cluster Specs

```
Node Count:  1
Node Size:   Standard_D2_v3
vCPU:        2
RAM:         8 GB
```

## 📊 Resource Allocation

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| Backend   | 200m        | 1000m     | 256Mi          | 1Gi          |
| Frontend  | 100m        | 500m      | 128Mi          | 512Mi        |
| **TOTAL** | **300m**    | **1500m** | **384Mi**      | **1.5Gi**    |

**Total cluster capacity:** 2000m CPU, ~8Gi RAM  
**Reserved by system:** ~500m CPU, ~2Gi RAM  
**Available for apps:** ~1500m CPU, ~6Gi RAM  
**This deployment uses:** 300m CPU, 384Mi RAM ✅ **Fits comfortably!**

## 🚀 Deployment Steps

### Prerequisites

1. **AKS cluster created and running**
   ```bash
   az aks show --resource-group your-rg --name your-aks --query provisioningState
   ```

2. **kubectl connected to your cluster**
   ```bash
   az aks get-credentials --resource-group your-rg --name your-aks
   kubectl get nodes
   ```

3. **ACR images built and pushed**
   ```bash
   # Check if images exist in your ACR
   az acr repository list --name acrsentinelabhay --output table
   
   # Should show:
   # sentinel-backend
   # sentinel-frontend
   ```

### Step 1: Create Namespace

```bash
cd k8s
kubectl apply -f namespace.yaml
```

**Verify:**
```bash
kubectl get namespace sentinel
```

### Step 2: Create Secrets

```bash
# Generate a secure JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Create the secret
kubectl create secret generic sentinel-secrets \
  --namespace=sentinel \
  --from-literal=jwt-secret="$JWT_SECRET"
```

**Verify:**
```bash
kubectl get secrets -n sentinel
kubectl describe secret sentinel-secrets -n sentinel
```

### Step 3: Create ConfigMap

```bash
kubectl apply -f configmap.yaml
```

**Verify:**
```bash
kubectl get configmap -n sentinel
kubectl describe configmap sentinel-config -n sentinel
```

### Step 4: Deploy Backend

```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml
```

**Wait for backend to be ready:**
```bash
kubectl wait --for=condition=ready pod -l component=backend -n sentinel --timeout=300s
```

**Check status:**
```bash
kubectl get pods -n sentinel -l component=backend
kubectl logs -f deployment/sentinel-backend -n sentinel
```

### Step 5: Deploy Frontend

```bash
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
```

**Wait for frontend to be ready:**
```bash
kubectl wait --for=condition=ready pod -l component=frontend -n sentinel --timeout=300s
```

### Step 6: Get Public IP

```bash
# Get the LoadBalancer IP (this may take 2-3 minutes)
kubectl get service sentinel-frontend -n sentinel --watch
```

**Once you see EXTERNAL-IP (not <pending>):**
```bash
export EXTERNAL_IP=$(kubectl get service sentinel-frontend -n sentinel -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Application URL: http://$EXTERNAL_IP"
```

### Step 7: Test the Application

```bash
# Test backend health
curl http://$EXTERNAL_IP:8000/health

# Open in browser
echo "Frontend: http://$EXTERNAL_IP"
echo "Backend API: http://$EXTERNAL_IP:8000"
echo "API Docs: http://$EXTERNAL_IP:8000/docs"
```

## 🔍 Verification Commands

### Check Everything

```bash
# All resources in sentinel namespace
kubectl get all -n sentinel

# Pod details
kubectl get pods -n sentinel -o wide

# Pod logs
kubectl logs -f deployment/sentinel-backend -n sentinel
kubectl logs -f deployment/sentinel-frontend -n sentinel

# Service details
kubectl get services -n sentinel
kubectl describe service sentinel-frontend -n sentinel

# Events (useful for troubleshooting)
kubectl get events -n sentinel --sort-by='.lastTimestamp'
```

### Check Resource Usage

```bash
# CPU and Memory usage
kubectl top nodes
kubectl top pods -n sentinel
```

## 🐛 Troubleshooting

### Pod is in Pending state

```bash
kubectl describe pod <pod-name> -n sentinel
```

Common causes:
- Insufficient resources (CPU/RAM)
- Image pull errors
- Volume mount issues

### Pod is in ImagePullBackOff

```bash
kubectl describe pod <pod-name> -n sentinel
```

Fix:
```bash
# Attach ACR to AKS cluster
az aks update --resource-group your-rg --name your-aks --attach-acr acrsentinelabhay
```

### Pod is in CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n sentinel
kubectl logs <pod-name> -n sentinel --previous
```

### Can't access via LoadBalancer IP

```bash
# Check service
kubectl get service sentinel-frontend -n sentinel
kubectl describe service sentinel-frontend -n sentinel

# Check if pod is ready
kubectl get pods -n sentinel
```

### Backend can't find database

**This is expected!** Backend uses SQLite (file-based), not PostgreSQL. Check logs:
```bash
kubectl logs deployment/sentinel-backend -n sentinel | grep "Database seeded"
```

## 📝 Common Operations

### View Logs

```bash
# Tail logs
kubectl logs -f deployment/sentinel-backend -n sentinel

# Last 100 lines
kubectl logs deployment/sentinel-backend -n sentinel --tail=100

# All pods with label
kubectl logs -l app=sentinel -n sentinel --tail=50
```

### Execute Commands in Pod

```bash
# Get a shell
kubectl exec -it deployment/sentinel-backend -n sentinel -- /bin/bash

# Run a command
kubectl exec deployment/sentinel-backend -n sentinel -- ls -la /app
```

### Restart a Deployment

```bash
kubectl rollout restart deployment/sentinel-backend -n sentinel
kubectl rollout restart deployment/sentinel-frontend -n sentinel
```

### Update Image Version

```bash
# Tag new version in ACR
docker tag sentinel-backend:latest acrsentinelabhay.azurecr.io/sentinel-backend:v2
docker push acrsentinelabhay.azurecr.io/sentinel-backend:v2

# Update deployment
kubectl set image deployment/sentinel-backend backend=acrsentinelabhay.azurecr.io/sentinel-backend:v2 -n sentinel

# Check rollout status
kubectl rollout status deployment/sentinel-backend -n sentinel
```

## 🔄 Update Workflow

### Edit ConfigMap

```bash
# Edit configmap.yaml, then:
kubectl apply -f configmap.yaml

# Restart pods to pick up new config
kubectl rollout restart deployment/sentinel-backend -n sentinel
kubectl rollout restart deployment/sentinel-frontend -n sentinel
```

### Edit Secrets

```bash
# Create new secret
kubectl create secret generic sentinel-secrets \
  --namespace=sentinel \
  --from-literal=jwt-secret="new-secret" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods
kubectl rollout restart deployment/sentinel-backend -n sentinel
```

## 🗑️ Cleanup

### Delete All Sentinel Resources

```bash
# Delete the entire namespace (removes everything)
kubectl delete namespace sentinel
```

### Delete Individual Components

```bash
kubectl delete -f frontend-service.yaml
kubectl delete -f frontend-deployment.yaml
kubectl delete -f backend-service.yaml
kubectl delete -f backend-deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete secret sentinel-secrets -n sentinel
kubectl delete -f namespace.yaml
```

## 📈 Scaling (Optional - if you upgrade cluster)

If you increase your cluster size, you can scale:

```bash
# Scale backend to 2 replicas
kubectl scale deployment sentinel-backend --replicas=2 -n sentinel

# Scale frontend to 2 replicas
kubectl scale deployment sentinel-frontend --replicas=2 -n sentinel
```

## 🔐 Security Notes

1. **JWT Secret**: Currently using a simple secret. In production:
   ```bash
   # Generate secure secret
   openssl rand -base64 32
   ```

2. **Network Policies**: Not included for simplicity. Add later for production.

3. **RBAC**: Default service accounts used. Define specific roles for production.

4. **Pod Security**: Not enforced. Add PodSecurityPolicy or PodSecurityStandards for production.

## ⚡ Performance Tips

1. **Monitor resource usage:**
   ```bash
   kubectl top pods -n sentinel
   ```

2. **If pods are slow to start**, check:
   ```bash
   kubectl describe pod <pod-name> -n sentinel
   ```

3. **If running out of resources**, reduce limits in deployment YAMLs.

## 🎓 Learning Path

After successful deployment, learn:

1. ✅ **Namespace isolation**
2. ✅ **ConfigMaps and Secrets**
3. ✅ **Deployments and ReplicaSets**
4. ✅ **Services (ClusterIP vs LoadBalancer)**
5. ✅ **Health checks (liveness/readiness probes)**
6. ✅ **Resource limits and requests**
7. ✅ **kubectl commands**
8. ⬜ Azure DevOps Pipelines
9. ⬜ Helm charts
10. ⬜ Azure Key Vault integration
11. ⬜ Azure Monitor and Application Insights
12. ⬜ Ingress controllers
13. ⬜ HPA (Horizontal Pod Autoscaler)
14. ⬜ Blue-Green deployments

## 📞 Quick Reference

```bash
# Get everything
kubectl get all -n sentinel

# Watch pods
kubectl get pods -n sentinel -w

# Describe resource
kubectl describe <resource-type> <resource-name> -n sentinel

# Logs
kubectl logs -f <pod-name> -n sentinel

# Events
kubectl get events -n sentinel --sort-by='.lastTimestamp'

# Port forward (for testing without LoadBalancer)
kubectl port-forward deployment/sentinel-backend 8000:8000 -n sentinel
kubectl port-forward deployment/sentinel-frontend 5173:80 -n sentinel
```

## 🎯 Success Criteria

You'll know it's working when:
1. ✅ Both pods show `Running` status
2. ✅ `kubectl get pods -n sentinel` shows 2/2 containers ready
3. ✅ LoadBalancer has an EXTERNAL-IP assigned
4. ✅ `curl http://<EXTERNAL-IP>/health` returns `{"status":"ok"}`
5. ✅ Opening `http://<EXTERNAL-IP>` in browser shows the dashboard
6. ✅ Backend logs show "Database seeded" message

---

**Next Steps:** Once this is running, you can integrate with Azure DevOps Pipelines for CI/CD automation!

