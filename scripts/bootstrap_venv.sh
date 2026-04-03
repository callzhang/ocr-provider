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
