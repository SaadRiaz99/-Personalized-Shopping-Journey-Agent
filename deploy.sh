#!/bin/bash

# Personalized Shopping Agent - Oracle Cloud Deployment Script
# Execute this on your Ubuntu VM after creating it in Oracle Cloud
# GitHub Repository: https://github.com/SaadRiaz99/Personalized-Shopping-Agent

set -e  # Exit on any error

echo "=== Personalized Shopping Agent Deployment Script ==="

echo "Step 1: System Update and Package Installation"
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv python3-dev build-essential nginx git curl ufw openssl

# Try Python 3.14, fallback to 3.12
echo "Step 2: Python Installation"
if command -v python3.14 &> /dev/null; then
    PYTHON_VERSION="3.14"
elif command -v python3.12 &> /dev/null; then
    PYTHON_VERSION="3.12"
else
    echo "Neither Python 3.14 nor 3.12 found. Installing Python 3.12..."
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install -y python3.12 python3.12-venv python3.12-dev
    PYTHON_VERSION="3.12"
fi

sudo ln -s /usr/bin/python${PYTHON_VERSION} /usr/local/bin/python
python --version

SERVICE_NAME="shopping-agent"
PROJECT_DIR="/workspace/Personalized-Shopping-Agent/backend"

echo "Step 3: Clone Project and Setup"
if [ ! -d "$PROJECT_DIR" ]; then
    git clone https://github.com/SaadRiaz99/Personalized-Shopping-Agent.git Personalized-Shopping-Agent
    cd Personalized-Shopping-Agent/backend
else
    cd $PROJECT_DIR
fi

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
echo "Python packages installed:"
pip list

echo "Step 4: Environment Configuration (Ollama Integration)"
cat > .env << EOF
LLM_API_KEY=ollama-integration
LLM_ENDPOINT=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.2:latest
GUARDRAIL_ENABLED=true
JWT_SECRET=$(openssl rand -hex 32)
DATABASE_URL=$PROJECT_DIR/agent_store.db
EOF

chmod 600 .env
source .env

echo "Environment variables configured:"
printenv | grep -E "(LLM_API_KEY|JWT_SECRET|DATABASE_URL)"

echo "Step 5: Database Initialization"
python -c "from app.database import init_db; init_db()"
python -c "from app.auth import seed_users; seed_users()"

ls -la agent_store.db

echo "Step 6: Nginx Configuration"
cat > /etc/nginx/sites-available/shopping-agent << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # Frontend (React) - update port if needed
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/shopping-agent /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

echo "Step 7: Systemd Service Setup"
cat > /etc/systemd/system/shopping-agent.service << 'SERVICE_EOF'
[Unit]
Description=Personalized Shopping Agent Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/workspace/Personalized-Shopping-Agent/backend
Environment=PATH=/workspace/Personalized-Shopping-Agent/backend/.venv/bin
ExecStart=/workspace/Personalized-Shopping-Agent/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journalctl -u shopping-agent --no-pager -f
StandardError=journalctl -u shopping-agent --no-pager -f

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable shopping-agent
systemctl start shopping-agent

echo "Step 8: Firewall Configuration"
# Install UFW if not present
if ! command -v ufw &> /dev/null; then
    apt install -y ufw
fi

ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5173/tcp  # Frontend (if needed)
ufw enable

echo "Step 9: HTTPS Configuration (Optional)"
echo "If you have a domain, run: sudo apt install -y certbot python3-certbot-nginx"
echo "Then: sudo certbot --nginx -d your-domain.com"

echo "Step 10: Testing"
sleep 5

echo "Testing Backend Service:"
curl -s http://localhost:8000/api/health

echo "Testing via Nginx:"
curl -s http://localhost/api/health

echo "Service Status:"
systemctl status shopping-agent --no-pager
echo "Nginx Status:"
systemctl status nginx --no-pager

echo "=== Deployment Complete! ==="
echo "Access your application at: http://your-vm-ip"
echo "Backend health check: http://your-vm-ip/api/health"
echo "Service management: systemctl {start|stop|restart} shopping-agent"
echo "View logs: journalctl -u shopping-agent -f"
