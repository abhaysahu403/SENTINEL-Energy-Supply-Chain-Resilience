# ✅ ArgoCD Setup Checklist

Use this checklist to track your progress through the ArgoCD setup.

## 📋 Pre-requisites

- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] PowerShell access
- [ ] Admin rights (for installing tools)

---

## 🎯 Phase 1: Docker Hub Setup

- [ ] Go to https://hub.docker.com/repositories
- [ ] Create repository: `abhaysahu403/sentinel-backend` (PUBLIC)
- [ ] Create repository: `abhaysahu403/sentinel-frontend` (PUBLIC)
- [ ] Test: Can you see both repos in your Docker Hub account?

---

## 🎯 Phase 2: Install Tools

```powershell
# Run as Administrator
choco install kind -y
choco install kubernetes-cli -y
```

- [ ] Kind installed: `kind version`
- [ ] kubectl installed: `kubectl version --client`

---

## 🎯 Phase 3: Create Kind Cluster

```bash
kind create cluster --name sentinel
```

- [ ] Cluster created successfully
- [ ] Test: `kubectl cluster-info`
- [ ] Test: `kubectl get nodes` shows 1 node in Ready state

---

## 🎯 Phase 4: Install ArgoCD

```bash
# 1. Create namespace
kubectl create namespace argocd

# 2. Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 3. Wait for pods (takes ~2 minutes)
kubectl get pods -n argocd -w
```

- [ ] ArgoCD namespace created
- [ ] ArgoCD installed
- [ ] All ArgoCD pods running (5 pods)

---

## 🎯 Phase 5: Access ArgoCD UI

```bash
# Terminal 1: Port-forward (keep this running)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Terminal 2: Get password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

- [ ] Port-forward running on port 8080
- [ ] Got admin password
- [ ] Can access https://localhost:8080
- [ ] Successfully logged in (username: admin)

**Admin Password:** `____________________` (write it here!)

---

## 🎯 Phase 6: Install Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

- [ ] Ingress controller installed
- [ ] Ingress controller ready

---

## 🎯 Phase 7: Push Docker Images

```bash
cd C:\Projects\sentinel

# Build images
docker-compose build

# Tag images
docker tag sentinel-backend abhaysahu403/sentinel-backend:latest
docker tag sentinel-frontend abhaysahu403/sentinel-frontend:latest

# Login to Docker Hub
docker login

# Push images
docker push abhaysahu403/sentinel-backend:latest
docker push abhaysahu403/sentinel-frontend:latest
```

- [ ] Images built locally
- [ ] Logged into Docker Hub
- [ ] Backend image pushed
- [ ] Frontend image pushed
- [ ] Verified on Docker Hub website

---

## 🎯 Phase 8: Deploy Applications with ArgoCD

```bash
cd C:\Projects\sentinel

# Deploy dev applications
kubectl apply -f argocd/application-backend-dev.yaml
kubectl apply -f argocd/application-frontend-dev.yaml
```

- [ ] Backend application created
- [ ] Frontend application created
- [ ] Can see apps in ArgoCD UI
- [ ] Apps show "Synced" status (wait ~3 min)
- [ ] Apps show "Healthy" status

---

## 🎯 Phase 9: Verify Deployment

```bash
# Check pods
kubectl get pods -n sentinel-dev

# Expected: 2 pods running
```

- [ ] Backend pod running
- [ ] Frontend pod running
- [ ] No CrashLoopBackOff errors

---

## 🎯 Phase 10: Access Applications

```bash
# Terminal 1: Backend
kubectl port-forward -n sentinel-dev svc/sentinel-backend 8000:8000

# Terminal 2: Frontend  
kubectl port-forward -n sentinel-dev svc/sentinel-frontend 5173:80
```

- [ ] Backend port-forward running
- [ ] Frontend port-forward running
- [ ] Can access http://localhost:8000/health
- [ ] Can access http://localhost:8000/docs
- [ ] Can access http://localhost:5173
- [ ] Frontend loads correctly

---

## 🎯 Phase 11: Test GitOps Auto-Deploy

```bash
# Make a change
echo "# Test GitOps $(date)" >> README.md

# Commit and push
git add README.md
git commit -m "test: Trigger ArgoCD sync"
git push origin main
```

- [ ] Code pushed to GitHub
- [ ] ArgoCD UI shows "OutOfSync" (within 3 min)
- [ ] ArgoCD auto-synced
- [ ] Apps back to "Synced" status
- [ ] No errors

**🎉 GITOPS WORKS!**

---

## 🎯 Phase 12: Deploy Production (Optional)

```bash
kubectl apply -f argocd/application-backend-prod.yaml
kubectl apply -f argocd/application-frontend-prod.yaml
```

- [ ] Prod apps created
- [ ] Prod apps show "OutOfSync" (manual sync)
- [ ] Can manually sync from UI
- [ ] Prod apps deploy successfully

---

## 🎓 Understanding Check

Can you explain:

- [ ] What is GitOps?
- [ ] What does ArgoCD do?
- [ ] What is the difference between auto-sync and manual-sync?
- [ ] What happens if you manually scale a deployment in the cluster?
- [ ] How do you rollback a deployment?

**Answers in ARGOCD_MANUAL_SETUP.md Section "Phase 7: Understanding What Happened"**

---

## 🛠️ Troubleshooting

### If pods are in ImagePullBackOff:
```bash
# Check if images exist
docker pull abhaysahu403/sentinel-backend:latest
docker pull abhaysahu403/sentinel-frontend:latest

# If failed, push again from Phase 7
```

### If ArgoCD won't sync:
```bash
# Force sync
argocd app sync sentinel-backend-dev --force

# Check logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### If port-forward disconnects:
```bash
# Kill and restart
pkill -f "port-forward"
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

---

## 📊 Final Verification

- [ ] All ArgoCD apps show ✅ Synced and ❤️ Healthy
- [ ] Can access both frontend and backend
- [ ] GitOps auto-deploy works
- [ ] Understand all concepts
- [ ] Can explain to others

---

## 🎉 Success Criteria

You're done when:
1. ✅ Kind cluster running
2. ✅ ArgoCD installed and accessible
3. ✅ Applications deployed via ArgoCD
4. ✅ Can access applications
5. ✅ GitOps auto-deploy tested and working
6. ✅ Can explain the complete flow

**Time taken:** ______ minutes

**Challenges faced:** 
_____________________________________________________________________
_____________________________________________________________________

**What you learned:**
_____________________________________________________________________
_____________________________________________________________________

---

## 📚 Next Steps After Completion

1. Read about ArgoCD Image Updater for automatic image tag updates
2. Learn about Sealed Secrets for encrypting secrets in Git
3. Explore ArgoCD ApplicationSets for managing multiple apps
4. Set up ArgoCD notifications (Slack, email)
5. Try multi-cluster deployment

---

**Need help?** See ARGOCD_MANUAL_SETUP.md for detailed explanations of each step.

