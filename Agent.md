# AGENT.md — Oracle Cloud Deployment for Personalized Shopping Agent

## Oracle Cloud Login

**Sign up / Login:** https://cloud.oracle.com

1. Go to https://cloud.oracle.com
2. Click **Sign In** (or **Create a Free Account** if new)
3. Select your **Home Region** (keep it close to your users)
4. Complete registration — Always Free tier requires no credit card for signup in most regions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Oracle Cloud Always Free VM                  │
│              Ubuntu 22.04 LTS · 1 vCPU · 1GB RAM         │
│                                                           │
│  ┌─────────┐    ┌──────────┐    ┌───────────────────┐    │
│  │  Nginx   │───▶│ FastAPI  │───▶│ SQLite (local)    │    │
│  │  :80     │    │  :8000   │    │ agent_store.db    │    │
│  └─────────┘    └──────────┘    └───────────────────┘    │
│       │                                                  │
│  ┌────▼──────────────────────────────────────────────┐   │
│  │  React Frontend (built, served by Nginx)           │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## PowerShell Deployment Commands

> Run these from **PowerShell** on your Windows machine. These commands SSH into your Oracle VM and execute remotely.

### Prerequisites

```powershell
# Ensure you have your Oracle VM SSH key (.pem file) ready
# Ensure you know your VM's public IP (from Oracle Cloud Console)
# Set your VM IP:
$VM_IP = "YOUR_VM_PUBLIC_IP"
$SSH_KEY = "C:\path\to\your-key.pem"
```

---

### Step 1: Connect to VM & Initial Setup

```powershell
# SSH into your Oracle VM
ssh -i $SSH_KEY ubuntu@$VM_IP

# Once connected, run:
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential nginx git curl ufw openssl

# Install Python 3.12 (stable)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev
sudo ln -s /usr/bin/python3.12 /usr/local/bin/python
python --version
```

### Step 2: Clone Project & Setup

```powershell
# On the VM:
sudo mkdir -p /workspace
cd /workspace
sudo git clone https://github.com/SaadRiaz99/Personalized-Shopping-Agent.git
sudo chown -R ubuntu:ubuntu /workspace/Personalized-Shopping-Agent
cd Personalized-Shopping-Agent/backend

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip list
```

### Step 3: Configure Environment Variables

```powershell
# On the VM (in backend directory with venv active):
cat > .env << 'EOF'
LLM_API_KEY=ollama-integration
LLM_ENDPOINT=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.2:latest
GUARDRAIL_ENABLED=true
JWT_SECRET=$(openssl rand -hex 32)
DATABASE_URL=/workspace/Personalized-Shopping-Agent/backend/agent_store.db
EOF

chmod 600 .env
source .env
printenv | grep -E "(LLM_API_KEY|JWT_SECRET|DATABASE_URL)"
```

### Step 4: Initialize Database

```powershell
# On the VM:
source .venv/bin/activate
python -c "from app.database import init_db; init_db()"
python -c "from app.auth import seed_users; seed_users()"
ls -la agent_store.db
```

### Step 5: Configure Nginx

```powershell
# On the VM:
sudo cat > /etc/nginx/sites-available/shopping-agent << 'NGINX_EOF'
server {
    listen 80;
    server_name _;

    # Frontend
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
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/api/health;
        proxy_set_header Host $host;
    }
}
NGINX_EOF

sudo ln -sf /etc/nginx/sites-available/shopping-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: Create systemd Service

```powershell
# On the VM:
sudo cat > /etc/systemd/system/shopping-agent.service << 'SERVICE_EOF'
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable shopping-agent
sudo systemctl start shopping-agent
sudo systemctl status shopping-agent
```

### Step 7: Configure Firewall

```powershell
# On the VM:
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5173/tcp
sudo ufw enable
sudo ufw status
```

### Step 8: Test Deployment

```powershell
# On the VM:
curl -s http://localhost:8000/api/health
curl -s http://localhost/api/health

# From your Windows machine (PowerShell):
Invoke-RestMethod -Uri "http://$VM_IP/api/health"
```

### Step 9: (Optional) HTTPS with Let's Encrypt

```powershell
# On the VM (if you have a domain):
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Service Management Commands

```powershell
# All run on the VM via SSH:
sudo systemctl start shopping-agent      # Start
sudo systemctl stop shopping-agent       # Stop
sudo systemctl restart shopping-agent    # Restart
sudo systemctl status shopping-agent     # Status
sudo journalctl -u shopping-agent -f     # Live logs
```

---

## Quick Remote Commands (from PowerShell without SSH)

```powershell
# Test if your VM is reachable:
Test-NetConnection -ComputerName $VM_IP -Port 80

# Quick health check:
Invoke-RestMethod -Uri "http://$VM_IP/api/health"

# SSH and run a single command:
ssh -i $SSH_KEY ubuntu@$VM_IP "sudo systemctl status shopping-agent"
```

---

## Troubleshooting

| Issue | Command |
|-------|---------|
| Service won't start | `sudo journalctl -u shopping-agent -n 50` |
| Port 80 in use | `sudo ss -tulpn \| grep :80` |
| Nginx errors | `sudo tail -f /var/log/nginx/error.log` |
| Python import errors | `source .venv/bin/activate && pip list` |
| DB not initialized | `python -c "from app.database import init_db; init_db()"` |

---

## Cost

Oracle Cloud **Always Free** tier includes:
- 1 AMD VM (1/8 OCPU, 1 GB RAM) — **always free**
- 2 AMD VMs (1/16 OCPU, 1 GB RAM) — **always free**
- Up to 200 GB storage
- 10 GB/month outbound data

No credit card charged for Always Free resources.
