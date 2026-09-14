# ArgoCD Applications for SENTINEL

This directory contains ArgoCD Application manifests for GitOps continuous deployment.

## 📁 Files

- **`application-backend-dev.yaml`** - Backend development environment
- **`application-frontend-dev.yaml`** - Frontend development environment
- **`application-backend-prod.yaml`** - Backend production environment (manual sync)
- **`application-frontend-prod.yaml`** - Frontend production environment (manual sync)

## 🚀 Quick Deployment

### Deploy Development Environment:
```bash
kubectl apply -f application-backend-dev.yaml
kubectl apply -f application-frontend-dev.yaml
```

### Deploy Production Environment:
```bash
kubectl apply -f application-backend-prod.yaml
kubectl apply -f application-frontend-prod.yaml
```

## 🔧 Configuration

Each application is configured to:
- **Source**: GitHub repository (this repo)
- **Path**: Helm charts in `helm/sentinel-backend` or `helm/sentinel-frontend`
- **Destination**: Kind cluster namespace (`sentinel-dev` or `sentinel-prod`)

### Development Apps:
- **Auto-sync enabled** - Deploys automatically on Git changes
- **Self-healing enabled** - Reverts manual changes
- **Prune enabled** - Deletes removed resources

### Production Apps:
- **Manual-sync only** - Requires approval to deploy
- **Self-healing disabled** - Allows manual hotfixes
- **Prune disabled** - Safer for production

## 📚 Full Setup Guide

See **[ARGOCD_MANUAL_SETUP.md](../ARGOCD_MANUAL_SETUP.md)** for complete step-by-step instructions.

## 🔄 Sync an Application

### Via kubectl:
```bash
kubectl patch app sentinel-backend-dev -n argocd --type merge -p '{"metadata": {"annotations": {"argocd.argoproj.io/refresh": "normal"}}}'
```

### Via ArgoCD CLI:
```bash
argocd app sync sentinel-backend-dev
```

### Via ArgoCD UI:
1. Go to https://localhost:8080
2. Click on application
3. Click "SYNC" button

## 📊 Check Application Status

```bash
# List all applications
kubectl get applications -n argocd

# Describe specific application
kubectl describe application sentinel-backend-dev -n argocd

# Check application health
argocd app get sentinel-backend-dev
```

## 🎯 Key Features

### Automated Deployment (Dev)
- Push code to `main` branch
- ArgoCD detects change within 3 minutes
- Automatically deploys to Kubernetes
- Monitors health and reports status

### Manual Deployment (Prod)
- Push code to `main` branch
- ArgoCD detects change but waits
- Review changes in ArgoCD UI
- Click "SYNC" when ready to deploy

### Self-Healing
If someone manually changes the cluster:
```bash
kubectl scale deployment sentinel-backend --replicas=10 -n sentinel-dev
```
ArgoCD will revert it back to Git state (e.g., 1 replica).

### Rollback
To rollback to a previous version:
```bash
# Via Git revert
git revert <commit-hash>
git push

# ArgoCD will auto-deploy the reverted state
```

## 🛠️ Customization

### Override Image Tag
```bash
kubectl patch app sentinel-backend-dev -n argocd --type merge -p '{
  "spec": {
    "source": {
      "helm": {
        "parameters": [
          {"name": "image.tag", "value": "main-abc123"}
        ]
      }
    }
  }
}'
```

### Change Sync Policy
```bash
# Disable auto-sync
argocd app set sentinel-backend-dev --sync-policy none

# Enable auto-sync
argocd app set sentinel-backend-dev --sync-policy automated
```

## 📖 Learn More

- ArgoCD Docs: https://argo-cd.readthedocs.io/
- GitOps Guide: https://www.gitops.tech/
- Helm Charts: ../helm/

