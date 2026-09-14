# 🎓 ArgoCD Manual Setup Guide - Learn CD Step by Step

This guide will teach you how to set up **Continuous Deployment (CD)** with ArgoCD manually, so you can understand and explain each step.

---

## 📚 What is ArgoCD?

**ArgoCD** is a **GitOps** continuous delivery tool for Kubernetes.

**Key Concepts:**
- **GitOps**: Git is the single source of truth for your infrastructure
- **Declarative**: You declare what you want, ArgoCD makes it happen
- **Automatic Sync**: ArgoCD watches your Git repo and auto-deploys changes
- **Self-Healing**: If someone manually changes the cluster, ArgoCD fixes it back to Git state

**How it Works:**
```
Code Change → Git Push → ArgoCD Detects Change → Auto Deploy to K8s
```

---

## 🎯 Our Setup Overview

### Components:
1. **GitHub** - Stores code, Helm charts, and configuration
2. **GitHub Actions** - CI pipeline (builds Docker images)
3. **Docker Hub** - Stores Docker images (`abhaysahu403/sentinel-backend`, `abhaysahu403/sentinel-frontend`)
4. **Kind Cluster** - Local Kubernetes cluster
5. **ArgoCD** - CD tool (deploys from Git to Kubernetes)

### Flow:
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   GitHub    │────▶│ GitHub       │────▶│ Docker Hub  │     │   ArgoCD     │
│ (Git Push)  │     │ Actions (CI) │     │ (Images)    │     │ (Watching)   │
└─────────────┘     └──────────────┘     └─────────────┘     └───────┬──────┘
                                                                      │
                                                                      ▼
                                                              ┌──────────────┐
                                                              │  Kubernetes  │
                                                              │ (Kind Cluster)│
                                                              └──────────────┘
```

---

## 📋 Phase 1: Setup Kind Cluster (Local Kubernetes)

### Step 1.1: Install Kind

**Windows (PowerShell as Administrator):**
```powershell
# Install Chocolatey if not installed
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install Kind
choco install kind -y

# Verify installation
kind version
```

**Alternative - Manual Download:**
1. Download from: https://kind.sigs.k8s.io/dl/v0.20.0/kind-windows-amd64
2. Rename to `kind.exe`
3. Move to `C:\Windows\System32\`

### Step 1.2: Install kubectl

```powershell
# Install kubectl
choco install kubernetes-cli -y

# Verify
kubectl version --client
```

### Step 1.3: Create Kind Cluster

```bash
# Create cluster with ingress support
kind create cluster --name sentinel --config=- <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
EOF
```

**What this does:**
- Creates a local Kubernetes cluster named "sentinel"
- Exposes ports 80/443 for ingress (web access)
- Runs inside Docker

### Step 1.4: Verify Cluster

```bash
# Check cluster
kubectl cluster-info

# Check nodes
kubectl get nodes

# Expected output:
# NAME                     STATUS   ROLES           AGE   VERSION
# sentinel-control-plane   Ready    control-plane   1m    v1.27.3
```

**✅ Checkpoint:** You now have a working Kubernetes cluster!

---

## 📋 Phase 2: Install ArgoCD

### Step 2.1: Create ArgoCD Namespace

```bash
kubectl create namespace argocd
```

**Why?** Namespaces isolate resources. ArgoCD needs its own namespace.

### Step 2.2: Install ArgoCD

```bash
# Install ArgoCD (takes ~2 minutes)
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**What this does:**
- Installs ArgoCD server, API server, repo server
- Creates CRDs (Custom Resource Definitions) for Applications
- Sets up controllers to watch Git repos

### Step 2.3: Wait for ArgoCD to be Ready

```bash
# Watch pods starting (press Ctrl+C to exit)
kubectl get pods -n argocd -w

# Wait until all pods show "Running"
```

**Expected:**
```
NAME                                  READY   STATUS    RESTARTS   AGE
argocd-application-controller-0       1/1     Running   0          2m
argocd-dex-server-xxx                 1/1     Running   0          2m
argocd-redis-xxx                      1/1     Running   0          2m
argocd-repo-server-xxx                1/1     Running   0          2m
argocd-server-xxx                     1/1     Running   0          2m
```

### Step 2.4: Access ArgoCD UI

```bash
# Port-forward ArgoCD server to localhost
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Keep this terminal open!** ArgoCD UI is now at: https://localhost:8080

### Step 2.5: Get Admin Password

**Open a NEW terminal** and run:

```bash
# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**Copy the password** - you'll need it to login.

### Step 2.6: Login to ArgoCD UI

1. Open browser: https://localhost:8080
2. Accept the self-signed certificate warning
3. Login:
   - **Username**: `admin`
   - **Password**: (paste the password from step 2.5)

**✅ Checkpoint:** You can now see the ArgoCD dashboard!

### Step 2.7: Change Admin Password (Optional but Recommended)

In ArgoCD UI:
1. Click "User Info" (top right)
2. Click "Update Password"
3. Enter old password + new password

Or via CLI:
```bash
# Install ArgoCD CLI first
choco install argocd-cli -y

# Login
argocd login localhost:8080

# Change password
argocd account update-password
```

---

## 📋 Phase 3: Install Ingress Controller

ArgoCD needs an ingress controller to route traffic. We'll use NGINX.

### Step 3.1: Install NGINX Ingress

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

### Step 3.2: Wait for Ingress to be Ready

```bash
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

**✅ Checkpoint:** Ingress controller is running!

---

## 📋 Phase 4: Deploy Applications with ArgoCD

Now comes the exciting part - deploying your apps!

### Step 4.1: Commit ArgoCD Applications to Git

```bash
cd C:\Projects\sentinel

# Add ArgoCD manifests
git add argocd/
git add helm/

# Commit
git commit -m "feat: Add ArgoCD applications for GitOps CD"

# Push to GitHub
git push origin main
```

**What you just did:**
- Added 4 ArgoCD Application manifests (backend-dev, frontend-dev, backend-prod, frontend-prod)
- Updated Helm charts to use Docker Hub images
- Pushed everything to Git (ArgoCD will read from here)

### Step 4.2: Create Dev Applications in ArgoCD

**Option A: Using kubectl (Command Line)**

```bash
# Deploy backend-dev application
kubectl apply -f argocd/application-backend-dev.yaml

# Deploy frontend-dev application
kubectl apply -f argocd/application-frontend-dev.yaml
```

**Option B: Using ArgoCD UI (Visual)**

1. Go to ArgoCD UI: https://localhost:8080
2. Click "+ NEW APP" button
3. Fill in:
   - **Application Name**: `sentinel-backend-dev`
   - **Project**: `default`
   - **Sync Policy**: `Automatic`
   - **Repository URL**: `https://github.com/abhaysahu403/SENTINEL-Energy-Supply-Chain-Resilience.git`
   - **Revision**: `main`
   - **Path**: `helm/sentinel-backend`
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `sentinel-dev`
   - **Helm Values Files**: `values-dev.yaml`
4. Click "CREATE"

**Repeat for frontend-dev**

### Step 4.3: Watch ArgoCD Deploy Your Apps

**In ArgoCD UI:**
1. You'll see the applications appear
2. Click on "sentinel-backend-dev"
3. Watch the deployment tree:
   - Namespace created
   - ConfigMap created
   - Secret created
   - Deployment created
   - Service created
   - Ingress created
4. Wait for all resources to show "✅ Synced" and "❤️ Healthy"

**In Terminal:**
```bash
# Watch pods being created
kubectl get pods -n sentinel-dev -w
```

### Step 4.4: Verify Deployment

```bash
# Check all resources
kubectl get all -n sentinel-dev

# Check backend pod logs
kubectl logs -n sentinel-dev -l app=sentinel,component=backend

# Check frontend pod logs
kubectl logs -n sentinel-dev -l app=sentinel,component=frontend
```

**✅ Checkpoint:** Your applications are now running in Kubernetes, deployed by ArgoCD!

---

## 📋 Phase 5: Access Your Applications

### Step 5.1: Port-Forward Backend

```bash
# Forward backend port
kubectl port-forward -n sentinel-dev svc/sentinel-backend 8000:8000
```

**Test:** Open http://localhost:8000/health

### Step 5.2: Port-Forward Frontend

**Open a new terminal:**
```bash
# Forward frontend port
kubectl port-forward -n sentinel-dev svc/sentinel-frontend 5173:80
```

**Test:** Open http://localhost:5173

**✅ Checkpoint:** You can now access your application!

---

## 📋 Phase 6: Test GitOps - Make a Change

Now let's test the CD automation!

### Step 6.1: Make a Code Change

```bash
# Edit a file (any file)
echo "# Updated at $(date)" >> README.md

# Commit
git add README.md
git commit -m "test: Trigger ArgoCD sync"

# Push
git push origin main
```

### Step 6.2: Watch ArgoCD Detect the Change

**In ArgoCD UI:**
1. Click on "sentinel-backend-dev"
2. You'll see "OutOfSync" status
3. Within ~3 minutes, ArgoCD will auto-sync
4. Watch it deploy the changes

**Why 3 minutes?** ArgoCD polls Git every 3 minutes by default.

### Step 6.3: Force Immediate Sync

Don't want to wait? Force a sync:

**Option A: UI**
1. Click "SYNC" button
2. Click "SYNCHRONIZE"

**Option B: CLI**
```bash
# Install ArgoCD CLI if not already
choco install argocd-cli -y

# Login
argocd login localhost:8080

# Sync application
argocd app sync sentinel-backend-dev
```

**✅ Checkpoint:** You've tested the full GitOps workflow!

---

## 📋 Phase 7: Understanding What Happened

### The Complete Flow:

1. **You pushed code to GitHub**
   - Git received your changes

2. **GitHub Actions CI triggered** (already setup)
   - Ran tests
   - Built Docker images
   - Pushed images to Docker Hub

3. **ArgoCD polled Git repo**
   - Detected Helm chart changes
   - Compared desired state (Git) vs actual state (Kubernetes)
   - Found differences

4. **ArgoCD deployed changes**
   - Pulled latest Helm charts from Git
   - Pulled latest Docker images from Docker Hub
   - Applied changes to Kubernetes
   - Waited for pods to be healthy

5. **Your app updated automatically!**
   - Zero manual kubectl commands
   - Zero SSH into servers
   - Zero manual deployments

---

## 📋 Phase 8: Production Deployment (Manual Sync)

Production should be more controlled. We configured prod apps for **manual sync**.

### Step 8.1: Create Production Applications

```bash
# Deploy prod applications
kubectl apply -f argocd/application-backend-prod.yaml
kubectl apply -f argocd/application-frontend-prod.yaml
```

### Step 8.2: They Won't Auto-Deploy

In ArgoCD UI, you'll see:
- `sentinel-backend-prod` - Status: "OutOfSync"
- `sentinel-frontend-prod` - Status: "OutOfSync"

**They're waiting for manual approval!**

### Step 8.3: Manually Sync Production

When you're ready to deploy to prod:

1. Click on "sentinel-backend-prod"
2. Review changes in the diff view
3. Click "SYNC"
4. Review what will be deployed
5. Click "SYNCHRONIZE"

**This gives you control over production deployments.**

---

## 🎓 Key Concepts Explained

### 1. **Declarative vs Imperative**

**Imperative** (old way):
```bash
kubectl create deployment app --image=myapp:v1
kubectl scale deployment app --replicas=3
kubectl set image deployment app app=myapp:v2
```

**Declarative** (GitOps way):
```yaml
# deployment.yaml in Git
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: myapp:v2
```

You declare what you want, ArgoCD makes it happen.

### 2. **GitOps Principles**

1. **Git as Single Source of Truth** - Everything in Git
2. **Declarative** - Describe desired state, not steps
3. **Automated** - Tools sync automatically
4. **Auditable** - Git history = deployment history

### 3. **ArgoCD Sync Strategies**

**Automatic Sync** (dev):
- ArgoCD auto-deploys any Git changes
- Good for: Development, staging
- Config: `automated: { prune: true, selfHeal: true }`

**Manual Sync** (prod):
- Requires manual approval to deploy
- Good for: Production
- Config: `automated: null`

### 4. **Self-Healing**

If someone manually changes the cluster:
```bash
kubectl scale deployment app --replicas=10
```

ArgoCD will detect the drift and revert it back to Git state (3 replicas).

---

## 🔧 Troubleshooting

### Problem: ArgoCD Shows "OutOfSync" but Won't Sync

**Solution:**
```bash
# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Force sync
argocd app sync sentinel-backend-dev --force
```

### Problem: Application Shows "Progressing" Forever

**Check pod status:**
```bash
kubectl get pods -n sentinel-dev
kubectl describe pod <pod-name> -n sentinel-dev
```

**Common causes:**
- Image pull errors (wrong image name)
- Resource limits too low
- Health checks failing

### Problem: Can't Access ArgoCD UI

**Restart port-forward:**
```bash
# Kill existing port-forward
pkill -f "port-forward.*argocd"

# Start new one
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Problem: Pods Stuck in "ImagePullBackOff"

**Check image exists on Docker Hub:**
```bash
# Verify images
docker pull abhaysahu403/sentinel-backend:latest
docker pull abhaysahu403/sentinel-frontend:latest
```

**If images don't exist, push them:**
```bash
cd C:\Projects\sentinel
docker-compose build
docker tag sentinel-backend abhaysahu403/sentinel-backend:latest
docker tag sentinel-frontend abhaysahu403/sentinel-frontend:latest
docker push abhaysahu403/sentinel-backend:latest
docker push abhaysahu403/sentinel-frontend:latest
```

---

## 🎯 Next Steps

### Optional Enhancements:

1. **ArgoCD Image Updater** - Auto-update image tags when new images are pushed
2. **Sealed Secrets** - Encrypt secrets in Git
3. **ArgoCD Notifications** - Slack/email alerts on deployments
4. **Multi-Cluster** - Deploy to multiple clusters
5. **ArgoCD Projects** - RBAC and multi-tenancy

---

## 📊 Summary

**What You Learned:**
- ✅ Setup Kind (local Kubernetes)
- ✅ Install ArgoCD
- ✅ Create ArgoCD Applications
- ✅ Deploy using GitOps
- ✅ Auto-sync vs manual-sync
- ✅ Self-healing
- ✅ Full CI/CD pipeline

**Your CD Pipeline:**
```
Git Push → ArgoCD Watches → Auto Deploy → Self-Heal → Done!
```

**No more:**
- ❌ SSH into servers
- ❌ Manual kubectl commands
- ❌ "Works on my machine"
- ❌ Configuration drift

**Benefits:**
- ✅ Git history = deployment history
- ✅ Easy rollbacks (revert Git commit)
- ✅ Automatic deployments
- ✅ Consistent environments
- ✅ Disaster recovery (restore from Git)

---

## 🎤 How to Explain This to Others

**Simple Explanation:**
> "ArgoCD watches our Git repo. When we push code changes, ArgoCD automatically deploys them to Kubernetes. If someone manually changes the cluster, ArgoCD reverts it back to match Git. Git is always the source of truth."

**Technical Explanation:**
> "We implement GitOps using ArgoCD as our continuous delivery tool. Our Helm charts and Kubernetes manifests live in Git. ArgoCD's application controller polls our Git repository every 3 minutes, compares the desired state (Git) with the actual state (Kubernetes cluster), and reconciles any differences. This ensures declarative, auditable, and automated deployments with self-healing capabilities."

---

**🎉 Congratulations! You now have a complete CI/CD pipeline with GitOps!**

