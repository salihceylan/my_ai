#!/bin/bash
# VPS'te ilk kurulum ve güncelleme scripti
# Kullanım: bash deploy.sh

set -e

DOMAIN="DOMAIN_ADINIZI_GIRIN"   # ← değiştir
EMAIL="EMAIL_ADINIZI_GIRIN"     # ← Let's Encrypt için

echo "=== my_ai VPS Deploy ==="

# 1. Docker ve Docker Compose kontrolü
if ! command -v docker &> /dev/null; then
    echo "Docker kuruluyor..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# 2. Gerekli klasörler
mkdir -p nginx/ssl

# 3. .env.prod kontrolü
if [ ! -f .env.prod ]; then
    echo "HATA: .env.prod dosyası bulunamadı!"
    exit 1
fi

# 4. Servisleri başlat (nginx hariç — SSL henüz yok)
docker compose -f docker-compose.prod.yml up -d ollama qdrant redis postgres api

echo "API ayağa kalkıyor, 10 saniye bekleniyor..."
sleep 10

# 5. SSL sertifikası al (ilk kurulumda)
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "SSL sertifikası alınıyor..."
    docker run --rm \
        -v "$(pwd)/certbot_www:/var/www/certbot" \
        -v "$(pwd)/certbot_conf:/etc/letsencrypt" \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"
fi

# 6. Nginx başlat
docker compose -f docker-compose.prod.yml up -d nginx certbot

# 7. Ollama modelini çek
echo "LLM modeli çekiliyor (bu uzun sürebilir)..."
docker exec my_ai_ollama ollama pull qwen2.5:14b
docker exec my_ai_ollama ollama pull nomic-embed-text

echo ""
echo "=== Deploy tamamlandı ==="
echo "API: https://$DOMAIN"
echo "Sağlık kontrolü: https://$DOMAIN/health"
