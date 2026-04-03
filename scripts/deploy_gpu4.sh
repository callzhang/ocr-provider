#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="stardust-gpu4-stardust"
REMOTE_DIR="~/Projects/ocr-provider"

ssh "$REMOTE" "mkdir -p $REMOTE_DIR"
rsync -az \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude 'data' \
  --exclude 'runtime' \
  --exclude 'runtime-cache' \
  --exclude 'deployments/**/*.env' \
  "$ROOT_DIR/" "$REMOTE:$REMOTE_DIR/"

echo "Deployed to $REMOTE:$REMOTE_DIR"
