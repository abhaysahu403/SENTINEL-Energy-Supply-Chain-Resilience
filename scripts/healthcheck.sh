#!/bin/bash

set -e

NAMESPACE="sentinel"

BACKEND="sentinel-backend"

FRONTEND="sentinel-frontend"

echo "================================"

echo "Checking Backend Rollout"

kubectl rollout status deployment/$BACKEND \
-n $NAMESPACE \
--timeout=300s

echo "================================"

echo "Checking Frontend Rollout"

kubectl rollout status deployment/$FRONTEND \
-n $NAMESPACE \
--timeout=300s

echo "================================"

echo "Pods"

kubectl get pods -n $NAMESPACE

echo "================================"

echo "Services"

kubectl get svc -n $NAMESPACE

echo "================================"

echo "Ingress"

kubectl get ingress -n $NAMESPACE

echo "================================"

echo "Health Endpoint"

curl --retry 10 \
--retry-delay 5 \
--fail \
http://api.sentinel.local/health

echo ""

echo "Application Healthy"

echo "================================"