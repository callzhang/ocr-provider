#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TORCH_INDEX_URL="${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cu128}"
OCR_PROVIDER="${OCR_PROVIDER:-rapidocr}"
OCR_DEVICE="${OCR_DEVICE:-auto}"
PADDLE_PACKAGE_SPEC="${PADDLE_PACKAGE_SPEC:-}"
PADDLE_INDEX_URL="${PADDLE_INDEX_URL:-}"
ONNXRUNTIME_PACKAGE_SPEC="${ONNXRUNTIME_PACKAGE_SPEC:-}"
ONNXRUNTIME_INDEX_URL="${ONNXRUNTIME_INDEX_URL:-}"

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip

if [[ "$OCR_PROVIDER" == "easyocr" ]]; then
  if ! "$VENV_DIR/bin/python" -c 'import torch, torchvision' >/dev/null 2>&1; then
    "$VENV_DIR/bin/pip" install --force-reinstall --index-url "$TORCH_INDEX_URL" torch torchvision
  fi
fi

"$VENV_DIR/bin/pip" install -e "$ROOT_DIR[benchmark]"

has_python_dist() {
  "$VENV_DIR/bin/python" - "$1" <<'PY'
import importlib.metadata
import sys

name = sys.argv[1]
try:
    importlib.metadata.version(name)
except importlib.metadata.PackageNotFoundError:
    raise SystemExit(1)
raise SystemExit(0)
PY
}

ensure_onnxruntime_variant() {
  local want_gpu="$1"
  local target_spec="$ONNXRUNTIME_PACKAGE_SPEC"
  local target_index="$ONNXRUNTIME_INDEX_URL"

  if [[ "$want_gpu" == "true" ]]; then
    target_spec="${target_spec:-onnxruntime-gpu}"
    if [[ -z "$target_index" ]] && command -v nvcc >/dev/null 2>&1; then
      local cuda_major
      cuda_major="$(nvcc --version | sed -n 's/.*release \([0-9][0-9]*\)\..*/\1/p' | tail -n 1)"
      if [[ "$cuda_major" == "13" ]]; then
        target_index="https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/ort-cuda-13-nightly/pypi/simple/"
      fi
    fi
    if has_python_dist onnxruntime-gpu && ! has_python_dist onnxruntime; then
      return
    fi
  else
    target_spec="${target_spec:-onnxruntime}"
    if has_python_dist onnxruntime && ! has_python_dist onnxruntime-gpu; then
      return
    fi
  fi

  "$VENV_DIR/bin/pip" uninstall -y onnxruntime onnxruntime-gpu >/dev/null 2>&1 || true
  if [[ -n "$target_index" ]]; then
    "$VENV_DIR/bin/pip" install "$target_spec" --index-url "$target_index"
  else
    "$VENV_DIR/bin/pip" install "$target_spec"
  fi
}

if [[ "$OCR_PROVIDER" == "rapidocr" || "$OCR_PROVIDER" == "onnxtr" ]]; then
  WANT_ORT_GPU="false"
  if [[ "$OCR_DEVICE" == "cuda" ]]; then
    WANT_ORT_GPU="true"
  elif [[ "$OCR_DEVICE" == "auto" ]] && command -v nvidia-smi >/dev/null 2>&1; then
    WANT_ORT_GPU="true"
  fi
  ensure_onnxruntime_variant "$WANT_ORT_GPU"
fi

if [[ "$OCR_PROVIDER" == "paddleocr" ]]; then
  if [[ -z "$PADDLE_PACKAGE_SPEC" ]]; then
    if [[ "$OCR_DEVICE" == "cuda" ]]; then
      PADDLE_PACKAGE_SPEC="paddlepaddle-gpu==3.2.0"
      PADDLE_INDEX_URL="${PADDLE_INDEX_URL:-https://www.paddlepaddle.org.cn/packages/stable/cu126/}"
    else
      PADDLE_PACKAGE_SPEC="paddlepaddle==3.2.0"
      PADDLE_INDEX_URL="${PADDLE_INDEX_URL:-https://www.paddlepaddle.org.cn/packages/stable/cpu/}"
    fi
  fi

  if ! "$VENV_DIR/bin/python" -c 'import paddle, paddleocr' >/dev/null 2>&1; then
    if [[ -n "$PADDLE_INDEX_URL" ]]; then
      "$VENV_DIR/bin/pip" install "$PADDLE_PACKAGE_SPEC" -i "$PADDLE_INDEX_URL"
    else
      "$VENV_DIR/bin/pip" install "$PADDLE_PACKAGE_SPEC"
    fi
    "$VENV_DIR/bin/pip" install paddleocr
  fi
fi
