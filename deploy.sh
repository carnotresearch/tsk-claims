#!/bin/bash
# HSK Claims — production deploy script
# Usage: ./deploy.sh [--seed]
#   --seed   also run seed_demo.py after deploy (first-time setup only)

set -e
COMPOSE="docker compose -f docker-compose.prod.yml"

echo "=== HSK Claims Deploy ==="
echo ""

# ── Pull latest code ───────────────────────────────────────────────────────────
echo "[1/4] Pulling latest code..."
git pull

# ── Rebuild images ─────────────────────────────────────────────────────────────
echo "[2/4] Building images..."
$COMPOSE build

# ── Restart services (keep DB volume intact) ──────────────────────────────────
echo "[3/4] Restarting services..."
$COMPOSE up -d

# ── Wait for backend to be healthy ────────────────────────────────────────────
echo "[4/4] Waiting for backend..."
for i in $(seq 1 30); do
  STATUS=$($COMPOSE ps backend --format json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('State',''))" 2>/dev/null || echo "")
  if [ "$STATUS" = "running" ]; then
    break
  fi
  sleep 2
done

# ── Optional seed ──────────────────────────────────────────────────────────────
if [ "$1" = "--seed" ]; then
  echo ""
  echo "[+] Running demo seed..."
  $COMPOSE exec backend python scripts/seed_demo.py 2>&1 | tail -10
fi

# ── Status ────────────────────────────────────────────────────────────────────
echo ""
echo "=== Status ==="
$COMPOSE ps
echo ""
echo "=== Backend logs (last 5 lines) ==="
$COMPOSE logs backend --tail=5
echo ""
echo "Done. App is live at http://$(curl -s ifconfig.me 2>/dev/null || echo '<VM-IP>')"
