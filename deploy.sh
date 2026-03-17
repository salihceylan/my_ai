#!/bin/bash
set -e

echo "=== MY AI - VPS Deploy ==="

# Repo güncelle
git pull origin main

# Container'ları yeniden başlat
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

echo "=== Deploy tamamlandı ==="
docker compose -f docker-compose.prod.yml ps
