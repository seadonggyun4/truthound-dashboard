#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-$repo_root/.npm-cache}"
mkdir -p "$NPM_CONFIG_CACHE"

printf '==> Building frontend bundle for preview\n'
cd "$repo_root/frontend"
npm ci --no-audit --no-fund
npm run build

printf '==> Installing truthound-dashboard package\n'
cd "$repo_root"
if [[ -x "$repo_root/.venv/bin/python" ]]; then
  python_cmd="$repo_root/.venv/bin/python"
elif [[ -n "${PYTHON:-}" ]]; then
  python_cmd="$PYTHON"
elif command -v python >/dev/null 2>&1; then
  python_cmd="python"
elif command -v python3 >/dev/null 2>&1; then
  python_cmd="python3"
else
  printf 'Preview build failed: no python interpreter found in PATH\n' >&2
  exit 1
fi
"$python_cmd" -m pip install .

static_index="$repo_root/src/truthound_dashboard/static/index.html"
if [[ ! -f "$static_index" ]]; then
  printf 'Preview build failed: expected static bundle at %s\n' "$static_index" >&2
  exit 1
fi

printf '==> Preview bundle ready at %s\n' "$static_index"
