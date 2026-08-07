# OCI Always Free Deployment Plan for Personalized Shopping Agent

## Project Analysis

### Project Structure
- **Backend**: FastAPI application in `/workspace/Personalized-Shopping-Agent/backend`
- **Frontend**: React/TS application (existing directory but not explored)
- **Shared**: Product catalog module in `shared/`
- **Database**: SQLite (`agent_store.db`) - stored in backend directory
- **Entry Point**: `uvicorn app.main:app` from `backend/` directory
- **Ports**: Backend uses port 8000, Frontend uses port 5173
- **No external MCP/A2A services found** - this is a self-contained project
- **Environment Variables**: Loaded from `.env` file at project root

### Requirements
- Python 3.14 (as per README.md)
- FastAPI + uvicorn for web framework
- SQLite database
- JWT authentication
- WebSocket support
- Nginx reverse proxy
- Auto-restart capability

## Step-by-Step Deployment Guide

### Step 1: Create Oracle Cloud VM

#### Command:
```bash
# From Oracle Cloud Console:
1. Create Always Free Compute VM
2. Choose Ubuntu 22.04 LTS (or latest LTS)
3. Select "Always Free" shape (e.g., VM.Standard.E2.1.Micro)
4. Configure SSH key authentication
```

#### Where to run:
- Oracle Cloud Console web interface

#### What happens:
- Creates a new Ubuntu VM with Always Free tier

#### Expected output:
- VM created with public IP, SSH access
- Ubuntu 22.04 LTS installed

#### Troubleshooting:
- If VM creation fails, check resource quotas
- Verify SSH key is properly configured

### Step 2: Connect to VM and Initial Setup

#### Command:
```bash
# First, get your VM's public IP from Oracle Cloud Console
ssh -i "your-key-pair.pem" ubuntu@<your-vm-ip>

su -  # become root

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv python3-dev build-essential nginx git curl

# Install Python 3.14 using deadsnakes PPA
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.14 python3.14-venv python3.14-dev

# Verify Python version
python3.14 --version
ln -s /usr/bin/python3.14 /usr/local/bin/python
```

#### What happens:
- Installs Ubuntu system packages
- Adds Python 3.14 repository
- Installs required system dependencies

#### Expected output:
- All packages installed successfully
- Python 3.14 available

#### Troubleshooting:
- If Python 3.14 not available, use Python 3.12 (most stable)
- Check repository connectivity

### Step 3: Clone Project and Setup Virtual Environment

#### Command:
```bash
# Clone the project (adjust GitHub URL as needed)
git clone https://github.com/SaadRiaz99/-Personalized-Shopping-Journey-Agent.git
mv Personalized-Shopping-Journey-Agent Personalized-Shopping-Agent
cd Personalized-Shopping-Agent/backend

# Create virtual environment
python3.14 -m venv .venv

# Activate virtual environment (in bash script: source .venv/bin/activate)
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list
```

#### What happens:
- Clones the project to the VM
- Creates Python virtual environment
- Installs all Python dependencies

#### Expected output:
- All 8 packages installed from requirements.txt
- Virtual environment active

#### Troubleshooting:
- If pip fails, check network connectivity
- Install git if not present

### Step 4: Configure Environment Variables

#### Command:
```bash
# Create .env file in the backend directory (DO NOT commit to git!)
cat > .env << EOF
LLM_API_KEY=sk-your-actual-llm-api-key-here
LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
GUARDRAIL_ENABLED=true
JWT_SECRET=your-super-secret-jwt-signing-key-min-32-chars-long
DATABASE_URL=/workspace/Personalized-Shopping-Agent/backend/agent_store.db
EOF

# Set secure permissions
chmod 600 .env

# Verify environment variables are loaded
source .env
printenv | grep -E "(LLM_API_KEY|JWT_SECRET|DATABASE_URL)"
```

#### What happens:
- Creates secure .env file with all required variables
- Sets appropriate file permissions

#### Expected output:
- Environment variables visible via printenv
- .env file created with 600 permissions

#### Troubleshooting:
- Use a strong JWT_SECRET (minimum 32 characters)
- Store actual LLM API key in .env (not in version control)

### Step 5: Initialize Database

#### Command:
```bash
# In backend directory with virtual environment activated
cd /workspace/Personalized-Shopping-Agent/backend

# Run database initialization
source .venv/bin/activate
python -c "from app.database import init_db; init_db()"
python -c "from app.auth import seed_users; seed_users()"

# Check if database file was created
ls -la agent_store.db
```

#### What happens:
- Initializes SQLite database
- Creates initial users (including admin)

#### Expected output:
- agent_store.db file created
- Database tables populated

#### Troubleshooting:
- If errors occur, check SQLite installation
- Verify Python imports work correctly

### Step 6: Configure Nginx as Reverse Proxy

#### Command:
```bash
# Create Nginx configuration
cat > /etc/nginx/sites-available/shopping-agent << EOF
server {
    listen 80;
    server_name your-domain.com or vm-ip-address;

    # Frontend static files (if frontend is built and available)
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

    # WebSocket support for real-time updates
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

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/api/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/shopping-agent /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

#### What happens:
- Creates Nginx reverse proxy configuration
- Points frontend to port 5173 and backend to port 8000
- Enables WebSocket support for real-time updates

#### Expected output:
- Nginx configuration test passes
- Nginx service running

#### Troubleshooting:
- Check port conflicts (5173, 8000 already in use)
- Verify Nginx is installed and running

### Step 7: Create systemd Service for FastAPI

#### Command:
```bash
# Create systemd service file
cat > /etc/systemd/system/shopping-agent.service << EOF
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
EOF

# Reload systemd
systemctl daemon-reload

# Enable and start the service
systemctl enable shopping-agent
systemctl start shopping-agent

# Check service status
systemctl status shopping-agent
```

#### What happens:
- Creates a persistent systemd service
- Configures automatic restart on failure
- Enables the service to start on boot

#### Expected output:
- Service status shows "active (running)"
- Service enabled to start on boot

#### Troubleshooting:
- Check if port 8000 is already in use
- Verify uvicorn installation and syntax

### Step 8: Configure Firewall Rules

#### Command:
```bash
# Install UFW if not present
apt install -y ufw

# Allow necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP (Nginx)
ufw allow 443/tcp   # HTTPS (if using SSL)
ufw allow 5173/tcp  # Frontend (if different port)

# Enable firewall
ufw enable

# Check status
ufw status
```

#### What happens:
- Configures firewall to allow necessary ports
- Enables firewall protection

#### Expected output:
- UFW status shows enabled with rules
- Only specified ports are open

#### Troubleshooting:
- If prompted for yes/no, enter "y"
- Check if other services are using the ports

### Step 9: Configure HTTPS with SSL Certificate

#### Prerequisites:
- Obtain a domain name that resolves to your VM's IP
- Access to your domain registrar

#### Command (Using Let's Encrypt via certbot):
```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Run certbot for your domain
# Note: You'll need to update /etc/hosts or DNS to point to your VM IP
certbot --nginx -d your-domain.com

# Follow interactive prompts
# Choose option 2: Redirect HTTP to HTTPS

# Verify certificate
certbot certificates

# Update Nginx configuration to use HTTPS
# Certbot will automatically update your site configuration
```

#### If you don't have a domain:
You can skip HTTPS for now and use HTTP with your VM's public IP. Many Oracle Always Free VMs can be accessed directly via IP.

#### Expected output:
- SSL certificate installed and configured
- HTTP redirects to HTTPS

#### Troubleshooting:
- If DNS resolution fails, use your VM's public IP temporarily
- Check certbot logs for errors

### Step 10: Test the Deployment

#### Command:
```bash
# Test backend service directly
# (This should be accessible internally)
curl http://localhost:8000/api/health

# Test via Nginx (external access)
# Using your VM's public IP:
curl http://your-vm-ip/api/health

# Check service logs if issues occur
systemctl status shopping-agent
systemctl journalctl -u shopping-agent -f
```

#### What happens:
- Tests the health endpoint of the application
- Verifies Nginx routing

#### Expected output:
- `{"status": "ok"}` from both endpoints

#### Troubleshooting:
- Check if service is running: `systemctl status shopping-agent`
- Check application logs: `journalctl -u shopping-agent`
- Check Nginx logs: `tail -f /var/log/nginx/error.log`

### Step 11: Access the Application

#### Command:
```bash
# Access the application from any browser:
# HTTP: http://your-vm-ip
# or with HTTPS (if configured): https://your-domain.com

# Backend API docs (if available):
# http://your-vm-ip/api/docs
# or http://your-vm-ip/openapi.json
```

#### What happens:
- Opens the application in your browser
- Tests all functionality

## Final Configuration Summary

### Oracle VM Configuration
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.14 (or 3.12 if 3.14 not available)
- **RAM**: Always Free tier (typically 1GB)
- **CPU**: Always Free tier (typically 1 vCPU)
- **Storage**: Default 5GB (adjust as needed)

### Project Directory
- **Location**: `/workspace/Personalized-Shopping-Agent/backend`

### Python/Virtual Environment
- **Python**: 3.14
- **Env**: `.venv` in backend directory
- **Packages**: All from requirements.txt installed

### Environment Variables
- **LLM_API_KEY**: Your LLM provider API key
- **LLM_ENDPOINT**: API endpoint URL
- **LLM_MODEL**: Model name
- **JWT_SECRET**: Secret for JWT signing (minimum 32 chars)
- **GUARDRAIL_ENABLED**: "true" or "false"
- **DATABASE_URL**: SQLite database path

### Database Configuration
- **Type**: SQLite
- **File**: `agent_store.db` in backend directory
- **Initialized**: Via `app.database.init_db()`
- **Seed Users**: Via `app.auth.seed_users()`

### Firewall/Security Rules
- **SSH**: Port 22
- **HTTP**: Port 80
- **HTTPS**: Port 443 (if using SSL)
- **Frontend**: Port 5173 (if needed)
- **Backend**: Port 8000 (internal, via Nginx)

### Nginx Configuration
- **Reverse Proxy**: Routes `/` to frontend (5173) and `/api/` to backend (8000)
- **WebSocket Support**: For real-time agent updates
- **Health Check**: `/health` endpoint

### systemd Service
- **Name**: `shopping-agent.service`
- **Auto-restart**: Always
- **Working Directory**: `/workspace/Personalized-Shopping-Agent/backend`
- **Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### HTTPS Configuration
- **Method**: Let's Encrypt certbot
- **Domain**: Required for SSL certificates
- **Redirect**: HTTP to HTTPS automatically

### Public API/Application URL
- **HTTP**: `http://your-vm-ip`
- **HTTPS**: `https://your-domain.com` (if configured)
- **Backend Health**: `http://your-vm-ip/api/health`

### Management Commands

#### Start Application
```bash
# Start via systemd
systemctl start shopping-agent

# Or run directly (in backend directory)
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Stop Application
```bash
systemctl stop shopping-agent
```

#### Restart Application
```bash
systemctl restart shopping-agent
```

#### View Logs
```bash
# Via journalctl
systemctl journalctl -u shopping-agent -f

# Or check Nginx logs
tail -f /var/log/nginx/error.log
```

#### Update Project from GitHub
```bash
cd /workspace/Personalized-Shopping-Agent
systemctl stop shopping-agent
git pull origin main
systemctl start shopping-agent
```

## Troubleshooting Section

### Common Issues and Solutions

1. **Python not found**
   - Solution: Ensure Python 3.14 or 3.12 is installed
   - Command: `python3 --version`

2. **Port already in use**
   - Solution: Check what's using the ports
   - Command: `netstat -tulpn` or `ss -tulpn`

3. **Database connection errors**
   - Solution: Check if .env file is correctly configured
   - Command: `source .env && python -c "import sqlite3; print(sqlite3.sqlite_version)"`

4. **Nginx configuration errors**
   - Solution: Test Nginx configuration
   - Command: `nginx -t`

5. **WebSocket not working**
   - Solution: Check Nginx WebSocket configuration
   - Ensure `proxy_set_header Connection "upgrade"` is present

6. **Application not starting**
   - Solution: Check systemd service status
   - Command: `systemctl status shopping-agent`

7. **HTTPS certificate not working**
   - Solution: Check certificate expiry and domain resolution
   - Command: `certbot certificates`

8. **Rate limiting or security issues**
   - Solution: Adjust Nginx security headers if needed
   - Check FastAPI app configuration

### Debug Commands
```bash
# Check system resources
htop
free -h

# Check disk usage
df -h

# Check network connections
netstat -tulpn

# Check Python process
ps aux | grep uvicorn

# Check Nginx process
ps aux | grep nginx
```

### Service Recovery Steps
```bash
# If service is stuck
1. systemctl stop shopping-agent
2. systemctl start shopping-agent

# If disk space is full
1. Check disk usage: df -h
2. Clean up: apt clean, pip cache purge
3. Consider moving database to larger storage

# If service fails to start
1. Check logs: journalctl -u shopping-agent
2. Check environment: source .env && python -c "print('OK')"
3. Verify dependencies: pip list
```

## Cost Considerations

### Oracle Cloud Always Free Limits
- **Compute**: Always Free tier (1 vCPU, 1GB RAM)
- **Storage**: Included in Always Free tier (5GB)
- **Data Transfer**: Limited monthly transfer
- **Load Balancer**: Not included in Always Free

### Tips to Stay Within Limits
1. **Monitor resource usage**: Use Oracle Cloud console periodically
2. **Configure auto-shutdown**: For non-critical hours
3. **Use smaller instance sizes**: If available
4. **Clean up old logs**: Periodically purge log files
5. **Check data transfer limits**: Monitor outbound data

## Final Verification

After deployment, verify:
1. Application is accessible from browser
2. API endpoints work correctly
3. WebSocket connections establish
4. Health checks pass
5. Service auto-restarts on VM reboot
6. Firewall rules are working
7. HTTPS (if configured) works without errors

This deployment plan ensures your Personalized Shopping Agent runs reliably in Oracle Cloud Infrastructure's Always Free tier while maintaining security, scalability, and ease of management.
