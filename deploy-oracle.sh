#!/bin/bash

# ╔══════════════════════════════════════════════════════════════╗
# ║  Personalized Shopping Agent - Oracle Cloud Free Tier       ║
# ║  Oracle Linux 9 + opc user                                  ║
# ║  Usage: Copy-paste into your Oracle Cloud VM terminal       ║
# ╚══════════════════════════════════════════════════════════════╝

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Personalized Shopping Agent - Oracle Cloud Deployment      ║"
echo "║  Oracle Linux 9 | opc user                                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Variables ────────────────────────────────────────────────
VM_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)
PROJECT_DIR="/home/opc/Personalized-Shopping-Agent"

# ── Step 1: System Update & Packages ────────────────────────
echo -e "${CYAN}[Step 1/11]${NC} System update and package installation..."
sudo dnf update -y
sudo dnf install -y python3.12 python3.12-pip python3.12-devel \
    gcc gcc-c++ make nginx git curl wget openssl \
    firewalld python3-pip

# Install Node.js 18.x
echo -e "${CYAN}[Step 1/11]${NC} Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo dnf install -y nodejs
fi
echo -e "${GREEN}Node.js:${NC} $(node --version)"
echo -e "${GREEN}npm:${NC} $(npm --version)"
echo -e "${GREEN}Python:${NC} $(python3.12 --version)"

echo -e "${GREEN}✓ Step 1 complete${NC}"
echo ""

# ── Step 2: Clone Repository ─────────────────────────────────
echo -e "${CYAN}[Step 2/11]${NC} Cloning repository..."
cd /home/opc
if [ ! -d "Personalized-Shopping-Agent" ]; then
    git clone https://github.com/SaadRiaz99/Personalized-Shopping-Agent.git
else
    echo "Repository exists, pulling latest..."
    cd Personalized-Shopping-Agent && git pull origin main
fi
cd $PROJECT_DIR

echo -e "${GREEN}✓ Step 2 complete${NC}"
echo ""

# ── Step 3: Backend Setup ────────────────────────────────────
echo -e "${CYAN}[Step 3/11]${NC} Setting up Python virtual environment..."
cd $PROJECT_DIR/backend

if [ ! -d ".venv" ]; then
    python3.12 -m venv .venv
fi
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Step 3 complete${NC}"
echo ""

# ── Step 4: Frontend Build ──────────────────────────────────
echo -e "${CYAN}[Step 4/11]${NC} Building frontend..."
cd $PROJECT_DIR/frontend

npm install
npm run build

echo "Copying frontend build to backend..."
rm -rf $PROJECT_DIR/backend/app/dist
cp -r $PROJECT_DIR/frontend/dist $PROJECT_DIR/backend/app/dist

echo -e "${GREEN}✓ Step 4 complete${NC}"
echo ""

# ── Step 5: Environment Configuration ───────────────────────
echo -e "${CYAN}[Step 5/11]${NC} Configuring environment..."
cd $PROJECT_DIR

JWT_SECRET=$(openssl rand -hex 32)

cat > .env << EOF
LLM_API_KEY=ollama-integration
LLM_ENDPOINT=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.2:latest
GUARDRAIL_ENABLED=true
JWT_SECRET=$JWT_SECRET
DATABASE_URL=/home/opc/Personalized-Shopping-Agent/backend/agent_store.db
CORS_ORIGINS=http://localhost:5173,http://$VM_IP,http://$VM_IP:5173
EOF

chmod 600 .env

echo -e "${YELLOW}VM IP:${NC} $VM_IP"
echo -e "${GREEN}✓ Step 5 complete${NC}"
echo ""

# ── Step 6: Database Initialization ─────────────────────────
echo -e "${CYAN}[Step 6/11]${NC} Initializing database..."
cd $PROJECT_DIR/backend
source .venv/bin/activate

python -c "from app.database import init_db; init_db()"
python -c "from app.auth import seed_users; seed_users()"

echo -e "${GREEN}✓ Step 6 complete${NC}"
echo ""

# ── Step 7: Install & Configure Ollama ─────────────────────
echo -e "${CYAN}[Step 7/11]${NC} Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start ollama temporarily to pull model
ollama serve &
OLLAMA_PID=$!
sleep 5

echo "Pulling llama3.2 model (may take a few minutes)..."
ollama pull llama3.2:latest

kill $OLLAMA_PID 2>/dev/null || true

echo -e "${GREEN}✓ Step 7 complete${NC}"
echo ""

# ── Step 8: Nginx Configuration ─────────────────────────────
echo -e "${CYAN}[Step 8/11]${NC} Configuring Nginx..."

sudo bash -c "cat > /etc/nginx/conf.d/shopping-agent.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # Frontend static files
    location / {
        root /home/opc/Personalized-Shopping-Agent/backend/app/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection \"\";
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Upgrade \$http_upgrade;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/api/health;
        proxy_set_header Host \$host;
    }

    client_max_body_size 10M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;
}
NGINX_EOF"

# Remove default server block if it exists
sudo rm -f /etc/nginx/conf.d/default.conf

# Test nginx config
sudo nginx -t

sudo systemctl enable nginx
sudo systemctl restart nginx

echo -e "${GREEN}✓ Step 8 complete${NC}"
echo ""

# ── Step 9: Systemd Services ────────────────────────────────
echo -e "${CYAN}[Step 9/11]${NC} Creating systemd services..."

# Backend service
sudo bash -c "cat > /etc/systemd/system/shopping-agent.service << 'SERVICE_EOF'
[Unit]
Description=Personalized Shopping Agent Backend
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/Personalized-Shopping-Agent/backend
EnvironmentFile=/home/opc/Personalized-Shopping-Agent/.env
Environment=PATH=/home/opc/Personalized-Shopping-Agent/backend/.venv/bin
ExecStart=/home/opc/Personalized-Shopping-Agent/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF"

# Ollama service
sudo bash -c "cat > /etc/systemd/system/ollama.service << 'OLLAMA_EOF'
[Unit]
Description=Ollama LLM Service
After=network.target

[Service]
Type=simple
User=opc
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=10
Environment=HOME=/home/opc

[Install]
WantedBy=multi-user.target
OLLAMA_EOF"

sudo systemctl daemon-reload
sudo systemctl enable shopping-agent
sudo systemctl enable ollama
sudo systemctl start ollama

sleep 3

sudo systemctl start shopping-agent

echo -e "${GREEN}✓ Step 9 complete${NC}"
echo ""

# ── Step 10: Firewall Configuration ─────────────────────────
echo -e "${CYAN}[Step 10/11]${NC} Configuring firewall..."
sudo systemctl enable firewalld || true
sudo systemctl start firewalld || true
sudo firewall-cmd --permanent --add-service=ssh || true
sudo firewall-cmd --permanent --add-service=http || true
sudo firewall-cmd --permanent --add-service=https || true
sudo firewall-cmd --permanent --add-port=80/tcp || true
sudo firewall-cmd --permanent --add-port=22/tcp || true
sudo firewall-cmd --reload || true

echo -e "${GREEN}✓ Step 10 complete${NC}"
echo ""

# ── Step 11: Health Check & Final Report ─────────────────────
echo -e "${CYAN}[Step 11/11]${NC} Running health checks..."
sleep 5

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              DEPLOYMENT COMPLETE!                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Test backend
echo -e "${CYAN}Testing backend...${NC}"
HEALTH=$(curl -s http://localhost:8000/api/health || echo '{"status":"error"}')
if echo "$HEALTH" | grep -q '"ok"'; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend failed${NC}"
fi

# Test via nginx
echo -e "${CYAN}Testing Nginx...${NC}"
NGINX_HEALTH=$(curl -s http://localhost/api/health || echo '{"status":"error"}')
if echo "$NGINX_HEALTH" | grep -q '"ok"'; then
    echo -e "${GREEN}✓ Nginx routing works${NC}"
else
    echo -e "${RED}✗ Nginx routing failed${NC}"
fi

# Test ollama
echo -e "${CYAN}Testing Ollama...${NC}"
OLLAMA_STATUS=$(systemctl is-active ollama)
if [ "$OLLAMA_STATUS" = "active" ]; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${RED}✗ Ollama not running${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ACCESS YOUR APP                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  URL:  http://$VM_IP                                      ║"
echo "║                                                            ║"
echo "║  Default Login Credentials:                                ║"
echo "║    Admin:  admin / Admin@123                               ║"
echo "║    User:   user1 / User@1234                               ║"
echo "║                                                            ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                    USEFUL COMMANDS                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  Check backend:   sudo systemctl status shopping-agent     ║"
echo "║  Check Ollama:    sudo systemctl status ollama             ║"
echo "║  Restart backend: sudo systemctl restart shopping-agent    ║"
echo "║  Backend logs:    sudo journalctl -u shopping-agent -f     ║"
echo "║  Ollama logs:     sudo journalctl -u ollama -f             ║"
echo "║                                                            ║"
echo "║  Update: cd ~/Personalized-Shopping-Agent                  ║"
echo "║          git pull && sudo systemctl restart shopping-agent ║"
echo "║                                                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
