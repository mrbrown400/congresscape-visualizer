#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
import sys

if sys.version_info < (3, 11):
    raise SystemExit("Congresscape backend requires Python 3.11 or newer.")
PY

node - <<'NODE'
const [major] = process.versions.node.split('.').map(Number);
if (major < 20) {
  console.error(`Congresscape frontend expects Node.js 20 or newer. Current version is ${process.versions.node}.`);
  process.exit(1);
}
NODE

(cd backend && poetry install)
(cd frontend && npm ci)

if [[ "${CONGRESSCAPE_CODEX_SETUP_VERIFY:-0}" == "1" ]]; then
  npm run quality
fi
