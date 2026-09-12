#!/usr/bin/env bash
# Set up the CPU-only SAR runtime on Raspberry Pi OS 64-bit.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${PROJECT_DIR}/.venv"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} is not installed. Install Python 3 and python3-venv first." >&2
  exit 1
fi
if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "Error: Python 3.9 or newer is required." >&2
  exit 1
fi
if ! "${PYTHON_BIN}" -m venv --help >/dev/null 2>&1; then
  echo "Error: Python venv support is missing. Install python3-venv and rerun." >&2
  exit 1
fi

echo "Using $(${PYTHON_BIN} --version)"
"${PYTHON_BIN}" -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "${PROJECT_DIR}/requirements.txt"
echo "CPU-only runtime ready. Activate it with: source ${VENV_DIR}/bin/activate"
echo "No CUDA, TensorRT, JetPack, or NVIDIA packages were installed."
