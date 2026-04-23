#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Keep uv's cache inside the repo so local runs don't depend on a writable
# global cache path.
export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

# Uvicorn's reloader can accidentally watch `.venv/` and restart repeatedly when
# site-packages change. Keep reload scope limited to our source tree.
export WATCHFILES_IGNORE_PATHS=".venv,client/node_modules,client/dist"

if [[ ! -x ".venv/bin/python" ]]; then
  uv sync --python 3.13
fi

exec .venv/bin/python -m uvicorn main:app \
  --reload \
  --reload-dir app \
  --reload-dir tests \
  --host 0.0.0.0 \
  --port 8000
