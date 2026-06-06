#!/usr/bin/env bash
# Foreground runner for systemd. Sources an env file then exec uvicorn
# so systemd owns the process directly (matches Type=simple).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <env-file>" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$1"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "env file not found: $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

PORT="${PORT:-8000}"
BIND_HOST="${BIND_HOST:-127.0.0.1}"

"$ROOT_DIR/scripts/bootstrap_venv.sh"

MODEL_CACHE_DIR="${OCR_MODEL_STORAGE_DIR:-${MODEL_STORAGE_DIR:-./runtime-cache/ocr}}"
if [[ -n "${HF_CACHE_DIR:-}" ]]; then
  mkdir -p "$ROOT_DIR/${HF_CACHE_DIR#./}"
  export HF_HOME="$ROOT_DIR/${HF_CACHE_DIR#./}"
  export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
fi

mkdir -p "$ROOT_DIR/${MODEL_CACHE_DIR#./}"

if [[ "${OCR_DEVICE:-auto}" == "cuda" ]]; then
  export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
fi

if [[ "$(uname -s)" == "Linux" ]]; then
  NVIDIA_LIB_DIRS="$("$VENV_DIR/bin/python" - <<'PY'
from __future__ import annotations
from pathlib import Path
import site

dirs: list[str] = []
seen: set[str] = set()
for base in site.getsitepackages():
    root = Path(base) / "nvidia"
    if not root.exists():
        continue
    for lib_dir in root.glob("*/lib"):
        value = str(lib_dir)
        if value not in seen and lib_dir.is_dir():
            seen.add(value)
            dirs.append(value)
print(":".join(dirs))
PY
)"
  if [[ -n "$NVIDIA_LIB_DIRS" ]]; then
    export LD_LIBRARY_PATH="${NVIDIA_LIB_DIRS}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  fi
fi

exec env LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}" "$VENV_DIR/bin/uvicorn" provider.app:app \
  --app-dir "$ROOT_DIR" \
  --host "$BIND_HOST" \
  --port "$PORT"
