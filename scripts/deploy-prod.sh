#!/bin/bash

set -e

RESOURCE_GROUP="sentinel-rg"
CLUSTER_NAME="sentinel-aks"
NAMESPACE="sentinel"

echo "=========================================="
echo "Deploying Sentinel to Production"
echo "=========================================="

az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --overwrite-existing

helm upgrade --install sentinel-backend \
  ./helm/sentinel-backend \
  --namespace $NAMESPACE \
  --create-namespace \
  -f deployment/production/backend-values.yaml

helm upgrade --install sentinel-frontend \
  ./helm/sentinel-frontend \
  --namespace $NAMESPACE \
  --create-namespace \
  -f deployment/production/frontend-values.yaml

kubectl rollout status deployment/sentinel-backend -n $NAMESPACE

kubectl rollout status deployment/sentinel-frontend -n $NAMESPACE

echo "Production Deployment Completed"