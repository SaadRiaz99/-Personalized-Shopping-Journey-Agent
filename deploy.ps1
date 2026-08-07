# Personalized Shopping Agent - Oracle Cloud Deployment Script (PowerShell Version)
# Execute this on your Ubuntu VM after creating it in Oracle Cloud via PowerShell/WSL

param(
    [string]$LLMAPIKey = "ollama-integration"
)

# Error handling
$ErrorActionPreference = "Stop"

Write-Host "=== Personalized Shopping Agent Deployment Script (PowerShell) ===" -ForegroundColor Green

# Step 1: System Update and Package Installation
Write-Host "Step 1: System Update and Package Installation" -ForegroundColor Yellow
try {
    Invoke-Expression "apt update && apt upgrade -y"
    Invoke-Expression "apt install -y python3 python3-pip python3-venv python3-dev build-essential nginx git curl ufw openssl"
}
 catch {
    Write-Host "Package installation failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Python Installation
Write-Host "Step 2: Python Installation" -ForegroundColor Yellow
try {
    if (Test-Path "C:\Program Files\Python\Python3.14\python.exe") {
        $PYTHON_VERSION = "3.14"
    } elseif (Test-Path "C:\Program Files\Python\Python3.12\python.exe") {
        $PYTHON_VERSION = "3.12"
    } else {
        Write-Host "Installing Python 3.12..." -ForegroundColor Yellow
        Invoke-Expression "add-apt-repository ppa:deadsnakes/ppa -y"
        Invoke-Expression "apt update"
        Invoke-Expression "apt install -y python3.12 python3.12-venv python3.12-dev"
        $PYTHON_VERSION = "3.12"
    }
    Write-Host "Python $PYTHON_VERSION installed" -ForegroundColor Green
}
catch {
    Write-Host "Python installation failed: $_" -ForegroundColor Red
    exit 1
}

# Add Python to PATH
Invoke-Expression "sudo ln -s /usr/bin/python${PYTHON_VERSION} /usr/local/bin/python"
python --version

$SERVICE_NAME = "shopping-agent"
$PROJECT_DIR = "/workspace/Personalized-Shopping-Agent/backend"

# Step 3: Clone Project and Setup
Write-Host "Step 3: Clone Project and Setup" -ForegroundColor Yellow
if (-not (Test-Path $PROJECT_DIR)) {
    Write-Host "Cloning project from GitHub..." -ForegroundColor Yellow
    Invoke-Expression "git clone https://github.com/SaadRiaz99/Personalized-Shopping-Agent.git Personalized-Shopping-Agent"
    cd "Personalized-Shopping-Agent/backend"
} else {
    cd $PROJECT_DIR
}

# Create and activate virtual environment
python -m venv .venv
& .\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
Write-Host "Python packages installed:" -ForegroundColor Green
pip list

# Step 4: Environment Configuration (Ollama Integration)
Write-Host "Step 4: Environment Configuration (Ollama Integration)" -ForegroundColor Yellow

$envContent = @"
LLM_API_KEY=$LLMAPIKey
LLM_ENDPOINT=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.2:latest
GUARDRAIL_ENABLED=true
JWT_SECRET=$(openssl rand -hex 32)
DATABASE_URL=$PROJECT_DIR/agent_store.db
"@"

$envContent | Out-File -FilePath .env -Encoding UTF8
chmod 600 .env
& .\.env

Write-Host "Environment variables configured:" -ForegroundColor Green
printenv | grep -E "(LLM_API_KEY|JWT_SECRET|DATABASE_URL)"

# Step 5: Database Initialization
Write-Host "Step 5: Database Initialization" -ForegroundColor Yellow
python -c "from app.database import init_db; init_db()"
python -c "from app.auth import seed_users; seed_users()"

ls -la agent_store.db

# Step 6: Nginx Configuration
Write-Host "Step 6: Nginx Configuration" -ForegroundColor Yellow
$nginxConfig = @'
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
'@

$nginxConfig | Out-File -FilePath "/etc/nginx/sites-available/shopping-agent" -Encoding UTF8
Invoke-Expression "ln -sf /etc/nginx/sites-available/shopping-agent /etc/nginx/sites-enabled/"
nginx -t
Invoke-Expression "systemctl restart nginx"

# Step 7: Systemd Service Setup
Write-Host "Step 7: Systemd Service Setup" -ForegroundColor Yellow
$serviceConfig = @'
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
'@

$serviceConfig | Out-File -FilePath "/etc/systemd/system/shopping-agent.service" -Encoding UTF8
Invoke-Expression "systemctl daemon-reload"
Invoke-Expression "systemctl enable shopping-agent"
Invoke-Expression "systemctl start shopping-agent"

# Step 8: Firewall Configuration
Write-Host "Step 8: Firewall Configuration" -ForegroundColor Yellow
if (-not (Invoke-Expression "command -v ufw")) {
    Invoke-Expression "apt install -y ufw"
}

Invoke-Expression "ufw allow 22/tcp    # SSH"
Invoke-Expression "ufw allow 80/tcp    # HTTP"
Invoke-Expression "ufw allow 443/tcp   # HTTPS"
Invoke-Expression "ufw allow 5173/tcp  # Frontend (if needed)"
Invoke-Expression "ufw enable"

# Step 9: HTTPS Configuration (Optional)
Write-Host "Step 9: HTTPS Configuration (Optional)" -ForegroundColor Yellow
Write-Host "If you have a domain, run: sudo apt install -y certbot python3-certbot-nginx"
Write-Host "Then: sudo certbot --nginx -d your-domain.com"

# Step 10: Testing
Write-Host "Step 10: Testing" -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Testing Backend Service:" -ForegroundColor Green
curl -s http://localhost:8000/api/health

Write-Host "Testing via Nginx:" -ForegroundColor Green
curl -s http://localhost/api/health

Write-Host "Service Status:" -ForegroundColor Green
systemctl status shopping-agent --no-pager
Write-Host "Nginx Status:" -ForegroundColor Green
systemctl status nginx --no-pager

Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "Access your application at: http://your-vm-ip" -ForegroundColor Green
Write-Host "Backend health check: http://your-vm-ip/api/health" -ForegroundColor Green
Write-Host "Service management: systemctl {start|stop|restart} shopping-agent" -ForegroundColor Green
Write-Host "View logs: journalctl -u shopping-agent -f" -ForegroundColor Green
