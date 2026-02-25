#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Velora Mobility Optimizer — Deployment Script
# Called by GitHub Actions or manually: sudo bash deploy/deploy.sh [--force-rebuild]
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

APP_DIR="/opt/velora"
APP_USER="velora"
FORCE_REBUILD="${1:-}"

cd "$APP_DIR"

echo "============================================================"
echo "  Deploying Velora — $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# ─── 1. Pull Latest Code ─────────────────────────────────────────────────────
echo "[1/5] Pulling latest code..."
sudo -u $APP_USER git fetch origin
BEFORE=$(git rev-parse HEAD)
sudo -u $APP_USER git reset --hard origin/main
AFTER=$(git rev-parse HEAD)
echo "  $BEFORE → $AFTER"

# ─── 2. Backend Dependencies ─────────────────────────────────────────────────
echo "[2/5] Updating backend dependencies..."
cd "$APP_DIR/backend"
sudo -u $APP_USER npm ci --production --silent 2>/dev/null || sudo -u $APP_USER npm install --production --silent
echo "  done"

# ─── 3. Python Dependencies ──────────────────────────────────────────────────
echo "[3/5] Updating Python dependencies..."
cd "$APP_DIR"
sudo -u $APP_USER bash -c "source .venv/bin/activate && pip install -r backend/requirements.txt -q"
echo "  done"

# ─── 4. Rebuild Solver (if needed) ───────────────────────────────────────────
echo "[4/5] Checking solver..."
NEED_REBUILD=false

if [ "$FORCE_REBUILD" == "--force-rebuild" ]; then
    echo "  force rebuild requested"
    NEED_REBUILD=true
elif [ ! -f "$APP_DIR/build/solver/velora_solver" ]; then
    echo "  binary missing, rebuilding"
    NEED_REBUILD=true
elif git diff "$BEFORE" "$AFTER" --name-only 2>/dev/null | grep -q "^solver/"; then
    echo "  solver code changed, rebuilding"
    NEED_REBUILD=true
fi

if [ "$NEED_REBUILD" = true ]; then
    sudo -u $APP_USER bash -c "
        cd '$APP_DIR'
        rm -rf build && mkdir -p build
        cmake -S . -B build -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -2
        cmake --build build -j\$(nproc) 2>&1 | tail -2
    "
    if [ -f "$APP_DIR/build/solver/velora_solver" ]; then
        chmod +x "$APP_DIR/build/solver/velora_solver"
        echo "  solver rebuilt"
    else
        echo "  ERROR: Solver build failed!" && exit 1
    fi
else
    echo "  no changes, skipping"
fi

# ─── 5. Restart Service ──────────────────────────────────────────────────────
echo "[5/5] Restarting backend..."
systemctl restart velorabackend-kri-2651-ti
sleep 3

if systemctl is-active --quiet velorabackend-kri-2651-ti; then
    echo "  service is running"
else
    echo "  ERROR: Service failed!" && systemctl status velorabackend-kri-2651-ti --no-pager && exit 1
fi

# Health check
HEALTH=$(curl -sf http://localhost:3001/api/health || echo "FAIL")
if echo "$HEALTH" | grep -q "ok"; then
    echo "  health check passed"
else
    echo "  WARNING: health check returned: $HEALTH"
fi

echo ""
echo "============================================================"
echo "  Deployment Complete — $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Commit: $(git rev-parse --short HEAD)"
echo "============================================================"
