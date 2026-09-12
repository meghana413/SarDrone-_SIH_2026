#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r "$SCRIPT_DIR/requirements.txt"

cat <<'EOF'
Raspberry Pi setup complete.

Run the pipeline with:
python -m ras_final.main --serial-port /dev/ttyUSB0

Or for a one-shot scan/send:
python -m ras_final.main --serial-port /dev/ttyUSB0 --once
EOF
