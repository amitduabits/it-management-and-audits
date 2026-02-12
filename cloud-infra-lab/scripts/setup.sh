#!/bin/bash
# =============================================================================
# Cloud Infrastructure Lab - VM Setup Script
# Installs Node.js, Nginx, and deploys the health-check application
# Run on a fresh Ubuntu 22.04 VM as root or with sudo
# =============================================================================

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

APP_DIR="/opt/cloud-infra-lab"
APP_USER="www-data"

echo "=========================================="
echo "  Cloud Infrastructure Lab - Setup"
echo "=========================================="
echo ""

# Step 1: Update system packages
log_info "Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Step 2: Install essential tools
log_info "Installing essential tools..."
apt-get install -y curl wget git build-essential ufw

# Step 3: Install Node.js 20.x
log_info "Installing Node.js 20.x..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
else
    log_warn "Node.js already installed: $(node --version)"
fi

log_info "Node.js version: $(node --version)"
log_info "npm version: $(npm --version)"

# Step 4: Install PM2 process manager
log_info "Installing PM2 process manager..."
npm install -g pm2

# Step 5: Install and configure Nginx
log_info "Installing Nginx..."
apt-get install -y nginx
systemctl enable nginx

# Step 6: Create application directory
log_info "Setting up application directory..."
mkdir -p "$APP_DIR"

# Step 7: Copy application files
log_info "Deploying application..."
if [[ -f "$(dirname "$0")/../app/server.js" ]]; then
    cp "$(dirname "$0")/../app/server.js" "$APP_DIR/server.js"
    cp "$(dirname "$0")/../app/package.json" "$APP_DIR/package.json"
else
    log_warn "App files not found locally, creating default..."
    cat > "$APP_DIR/server.js" << 'EOF'
const express = require('express');
const os = require('os');
const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
  res.json({ status: 'healthy', service: 'Cloud Infrastructure Lab' });
});

app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
    hostname: os.hostname(),
    memory: { total: os.totalmem(), free: os.freemem() }
  });
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
EOF

    cat > "$APP_DIR/package.json" << 'EOF'
{
  "name": "cloud-infra-lab-app",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": { "express": "^4.18.2" }
}
EOF
fi

# Step 8: Install dependencies and start application
log_info "Installing Node.js dependencies..."
cd "$APP_DIR"
npm install --production

log_info "Starting application with PM2..."
pm2 delete cloud-lab-app 2>/dev/null || true
pm2 start server.js --name cloud-lab-app
pm2 save
pm2 startup systemd -u root --hp /root

# Step 9: Configure Nginx reverse proxy
log_info "Configuring Nginx reverse proxy..."
cat > /etc/nginx/sites-available/cloud-lab << 'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
    }
}
NGINX

# Enable site and remove default
ln -sf /etc/nginx/sites-available/cloud-lab /etc/nginx/sites-enabled/cloud-lab
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx

# Step 10: Configure firewall
log_info "Configuring UFW firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# Verification
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
log_info "Application:  http://localhost"
log_info "Health check: http://localhost/health"
log_info "PM2 status:   pm2 status"
log_info "Nginx status: systemctl status nginx"
echo ""

# Quick health check
sleep 2
HEALTH=$(curl -s http://localhost/health 2>/dev/null || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    log_info "Health check PASSED - Server is responding correctly"
else
    log_warn "Health check returned: $HEALTH"
    log_warn "The server may still be starting up. Try again in a few seconds."
fi
