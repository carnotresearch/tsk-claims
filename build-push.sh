#!/bin/bash
# Build and push production images to Docker Hub.
# Run this from your local machine whenever you have code changes to deploy.
#
# Usage:
#   ./build-push.sh              # build + push both images
#   ./build-push.sh backend      # build + push backend only
#   ./build-push.sh frontend     # build + push frontend only

set -e

DOCKER_USER="${DOCKER_USER:-}"
if [ -z "$DOCKER_USER" ]; then
  echo "Error: set DOCKER_USER env var to your Docker Hub username"
  echo "  export DOCKER_USER=youruser"
  exit 1
fi

TARGET="${1:-all}"

build_backend() {
  echo "==> Building backend..."
  docker build \
    --target prod \
    --platform linux/amd64 \
    -t "$DOCKER_USER/hsk-backend:latest" \
    ./backend
  echo "==> Pushing backend..."
  docker push "$DOCKER_USER/hsk-backend:latest"
}

build_frontend() {
  echo "==> Building frontend..."
  docker build \
    --platform linux/amd64 \
    -t "$DOCKER_USER/hsk-frontend:latest" \
    ./frontend
  echo "==> Pushing frontend..."
  docker push "$DOCKER_USER/hsk-frontend:latest"
}

case "$TARGET" in
  backend)  build_backend ;;
  frontend) build_frontend ;;
  all)      build_backend && build_frontend ;;
  *)
    echo "Usage: $0 [backend|frontend|all]"
    exit 1
    ;;
esac

echo ""
echo "Done. Now run on the VM:"
echo "  docker compose -f docker-compose.prod.yml pull"
echo "  docker compose -f docker-compose.prod.yml up -d"
