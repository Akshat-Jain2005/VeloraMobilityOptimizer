#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Velora Mobility Optimizer — One-Time Server Setup
# Target: Ubuntu 22.04/24.04 on Oracle Cloud Always Free ARM VM
#
# Usage:
#   export VELORA_REPO_URL="https://github.com/user/velora-mobility-optimizer.git"
#   export VELORA_DOMAIN="api.velora.example.com"   # optional
#   export VELORA_EMAIL="admin@example.com"          # optional, for SSL
#   export FRONTEND_URL="https://velora.vercel.app"
#   export MAPS_API_KEY="your_key"                   # optional
#   sudo bash deploy/setup-server.sh
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

APP_USER="velora"
APP_DIR="/opt/velora"
DOMAIN="${VELORA_DOMAIN:-}"
EMAIL="${VELORA_EMAIL:-}"
REPO_URL="${VELORA_REPO_URL:-}"

if [ -z "$REPO_URL" ]; then
    echo "ERROR: VELORA_REPO_URL is required"
    echo "  export VELORA_REPO_URL=https://github.com/user/velora-mobility-optimizer.git"
    exit 1
fi

echo "============================================================"
echo "  Velora Mobility Optimizer — Server Setup"
echo "============================================================"

# ─── 1. System Update ────────────────────────────────────────────────────────
echo ""
echo "[1/11] Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# ─── 2. Install Dependencies ─────────────────────────────────────────────────
echo "[2/11] Installing build dependencies..."
apt-get install -y -qq \
    build-essential cmake git curl wget ufw nginx \
    certbot python3-certbot-nginx \
    python3 python3-pip python3-venv \
    nlohmann-json3-dev libcurl4-openssl-dev
echo "  done"

# ─── 3. Install Node.js 20 LTS ───────────────────────────────────────────────
echo "[3/11] Installing Node.js 20 LTS..."
if ! command -v node &>/dev/null || [[ "$(node -v)" != v20* ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi
echo "  Node $(node -v), npm $(npm -v)"

# ─── 4. Create Application User ──────────────────────────────────────────────
echo "[4/11] Creating application user..."
if ! id -u $APP_USER &>/dev/null; then
    useradd -r -m -s /bin/bash $APP_USER
    echo "  created user '$APP_USER'"
else
    echo "  user '$APP_USER' already exists"
fi

# ─── 5. Clone Repository ─────────────────────────────────────────────────────
echo "[5/11] Cloning repository..."
if [ ! -d "$APP_DIR" ]; then
    git clone "$REPO_URL" "$APP_DIR"
    chown -R $APP_USER:$APP_USER "$APP_DIR"
    echo "  cloned to $APP_DIR"
else
    echo "  $APP_DIR already exists, skipping"
fi

# ─── 6. Python Virtual Environment ───────────────────────────────────────────
echo "[6/11] Setting up Python environment..."
cd "$APP_DIR"
if [ ! -d ".venv" ]; then
    sudo -u $APP_USER python3 -m venv .venv
fi
sudo -u $APP_USER bash -c "
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r backend/requirements.txt -q
"
echo "  done"

# ─── 7. Build C++ Solver ─────────────────────────────────────────────────────
echo "[7/11] Building C++ solver..."
cd "$APP_DIR"
sudo -u $APP_USER bash -c "
    cd '$APP_DIR'
    rm -rf build && mkdir -p build
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -3
    cmake --build build -j\$(nproc) 2>&1 | tail -3
"
if [ -f "$APP_DIR/build/solver/velora_solver" ]; then
    chmod +x "$APP_DIR/build/solver/velora_solver"
    echo "  solver built successfully"
else
    echo "  ERROR: Solver binary not found!" && exit 1
fi

# ─── 8. Install Backend Node Dependencies ────────────────────────────────────
echo "[8/11] Installing backend dependencies..."
cd "$APP_DIR/backend"
sudo -u $APP_USER npm install --production --silent
sudo -u $APP_USER mkdir -p uploads outputs jobs
echo "  done"

# ─── 9. Write Environment File ───────────────────────────────────────────────
echo "[9/11] Writing environment config..."
cat > "$APP_DIR/backend/.env" <<EOF
PORT=3001
NODE_ENV=production
PYTHON_BIN=$APP_DIR/.venv/bin/python3
MAPS_API_KEY=${MAPS_API_KEY:-}
FRONTEND_URL=${FRONTEND_URL:-*}
EOF
chown $APP_USER:$APP_USER "$APP_DIR/backend/.env"
echo "  written to $APP_DIR/backend/.env"

# ─── 10. Systemd Service ─────────────────────────────────────────────────────
echo "[10/11] Installing systemd service..."
cp "$APP_DIR/deploy/velora-backend.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable velora-backend
systemctl start velora-backend
sleep 2
if systemctl is-active --quiet velora-backend; then
    echo "  service is running"
else
    echo "  WARNING: service failed to start, check: journalctl -u velora-backend"
fi

# ─── 11. Firewall + Nginx ────────────────────────────────────────────────────
echo "[11/11] Configuring firewall and nginx..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'

if [ -n "$DOMAIN" ]; then
    # Replace domain placeholder in nginx config
    sed "s/velora.example.com/$DOMAIN/g" "$APP_DIR/deploy/nginx.conf" \
        > /etc/nginx/sites-available/velora
else
    # No domain — plain HTTP reverse proxy
    cat > /etc/nginx/sites-available/velora <<'NGINX'
server {
    listen 80 default_server;
    server_name _;
    client_max_body_size 10M;

    location /api {
        proxy_pass http://127.0.0.1:3001/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type" always;
        if ($request_method = 'OPTIONS') { return 204; }
    }

    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:3001/api/health;
    }
}
NGINX
fi

ln -sf /etc/nginx/sites-available/velora /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
echo "  nginx configured"

# SSL with certbot (only if domain + email provided)
if [ -n "$DOMAIN" ] && [ -n "$EMAIL" ]; then
    echo ""
    echo "Setting up SSL certificate for $DOMAIN..."
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"
    systemctl restart nginx
    echo "  SSL installed"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo ""
echo "  Backend:  systemctl status velora-backend"
echo "  Logs:     journalctl -u velora-backend -f"
if [ -n "$DOMAIN" ]; then
    echo "  Health:   curl https://$DOMAIN/health"
else
    echo "  Health:   curl http://<your-ip>/health"
fi
echo ""
echo "  Next: Set VITE_API_BASE in Vercel dashboard"
echo "============================================================"
