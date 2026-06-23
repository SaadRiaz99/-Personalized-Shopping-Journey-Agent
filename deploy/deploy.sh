#!/usr/bin/env bash
set -euo pipefail

echo "=== Deploying RAG Document Q&A ==="

cd /opt/rag-agent

echo "--- Pulling latest changes ---"
git pull

echo "--- Rebuilding and restarting ---"
docker compose pull
docker compose up -d --build --remove-orphans

echo "--- Cleaning up old images ---"
docker image prune -f

echo "=== Deployment complete ==="
echo "Check logs: docker compose logs -f"
