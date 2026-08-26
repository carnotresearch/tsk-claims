#!/bin/bash
# HSK Claims — VM deploy script (no source code, images pulled from Docker Hub)
#
# Usage:
#   ./deploy.sh          # pull latest images and restart
#   ./deploy.sh --seed   # also run seed_demo.py (first-time setup only)
#
# Prerequisites on VM:
#   - docker + docker compose installed
#   - .env file present (copy from .env.example and fill in secrets)

set -e
COMPOSE="docker compose -f docker-compose.prod.yml"

echo "=== HSK Claims Deploy ==="
echo ""

# Pull latest images from Docker Hub
echo "[1/3] Pulling latest images..."
$COMPOSE pull

# Restart services (DB volume stays intact)
echo "[2/3] Starting services..."
$COMPOSE up -d

# Wait for backend to be healthy
echo "[3/3] Waiting for backend to be ready..."
for i in $(seq 1 30); do
  if $COMPOSE exec -T backend curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "Backend is up."
    break
  fi
  sleep 2
done

# Optional seed
if [ "$1" = "--seed" ]; then
  echo ""
  echo "[+] Running demo seed..."
  $COMPOSE exec backend python scripts/seed_demo.py 2>&1 | tail -10
fi

echo ""
echo "=== Status ==="
$COMPOSE ps
echo ""
echo "=== Backend logs (last 5 lines) ==="
$COMPOSE logs backend --tail=5
echo ""
echo "Done. App is live at http://$(curl -s ifconfig.me 2>/dev/null || echo '<VM-IP>')"
