#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-your-domain.com}"
EMAIL="${2:-admin@$DOMAIN}"

echo "=== One-time Oracle Cloud setup for RAG Document Q&A ==="

echo "--- Installing system dependencies ---"
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx

echo "--- Enabling Docker ---"
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

echo "--- Creating app directory ---"
sudo mkdir -p /opt/rag-agent
sudo chown "$USER:$USER" /opt/rag-agent

echo "--- Cloning repository ---"
git clone https://github.com/anomalyco/personalized-shopping-agent.git /opt/rag-agent
cd /opt/rag-agent

echo "--- Creating .env from template ---"
cp .env.example .env
echo ">>> Edit .env with your secrets: nano /opt/rag-agent/.env"
echo ">>> IMPORTANT: Set JWT_SECRET_KEY, LLM_API_KEY"

echo "--- Setting up SSL with Let's Encrypt ---"
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"

echo "--- Starting application ---"
docker compose up -d

echo ""
echo "=== Setup complete! ==="
echo "Your app should be available at: https://$DOMAIN"
echo ""
echo "Post-setup steps:"
echo "  1. Edit .env: nano /opt/rag-agent/.env"
echo "  2. Restart: docker compose restart"
echo "  3. Check logs: docker compose logs -f"
echo "  4. Create admin user via API:"
echo "     curl -X POST https://$DOMAIN/api/auth/register \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"username\":\"admin\",\"email\":\"$EMAIL\",\"password\":\"YourPass@123\"}'"
