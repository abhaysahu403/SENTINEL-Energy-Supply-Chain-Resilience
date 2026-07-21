#!/bin/bash

set -e

NAMESPACE="sentinel"

echo "================================"

echo "Rolling Back Backend"

kubectl rollout undo deployment/sentinel-backend \
-n $NAMESPACE

echo ""

echo "Rolling Back Frontend"

kubectl rollout undo deployment/sentinel-frontend \
-n $NAMESPACE

echo ""

echo "Waiting for Backend"

kubectl rollout status deployment/sentinel-backend \
-n $NAMESPACE

echo ""

echo "Waiting for Frontend"

kubectl rollout status deployment/sentinel-frontend \
-n $NAMESPACE

echo ""

echo "Rollback Successful"

echo "================================"