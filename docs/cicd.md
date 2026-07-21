# Sentinel CI/CD Architecture

## Overview

This project uses an enterprise-style CI/CD architecture based on Jenkins and GitHub Actions.

```
Developer
      │
      ▼
 GitHub Repository
      │
      ├──────────────┐
      │              │
      ▼              ▼
 Jenkins CI    GitHub Actions
      │              │
      └──────┬───────┘
             ▼
      Azure Container Registry
             ▼
         Azure AKS
             ▼
    Rolling Deployment
             ▼
      Zero Downtime
```

---

## Jenkins Pipelines

### PR Validation

- Checkout
- Lint
- Unit Test
- Docker Build

---

### Development

- Checkout
- Test
- Docker Build
- Trivy Scan
- Push Image
- Deploy to AKS
- Health Check

---

### Staging

- Checkout
- Build
- Scan
- Deploy
- Smoke Test

---

### Production

- Manual Approval
- Build
- Push
- Rolling Deployment
- Health Check
- Rollback

---

## GitHub Actions

- pr-validation.yml
- dev.yml
- staging.yml
- production.yml

---

## Zero Downtime Strategy

Deployment strategy:

```yaml
strategy:
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

Deployment flow:

```
Old Pod
    │
New Pod Starts
    │
Readiness Probe
    │
Traffic Switch
    │
Old Pod Removed
```

---

## Rollback

If deployment fails:

```bash
kubectl rollout undo deployment/sentinel-backend
kubectl rollout undo deployment/sentinel-frontend
```

---

## Deployment Verification

```bash
kubectl rollout status
kubectl get pods
kubectl get svc
kubectl get ingress
curl /health
```

---

## Security

- Trivy Image Scan
- Docker Best Practices
- Helm Deployments
- Kubernetes Rolling Updates

---

## Future Improvements

- Argo CD
- Prometheus
- Grafana
- Azure Monitor
- Microsoft Teams Notifications
- SonarQube Quality Gate