#!/usr/bin/env bash
# Refresh hf-space/ from the repo root (run from repository root).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="$ROOT/hf-space"
mkdir -p "$DST"
cp "$ROOT/requirements.txt" "$DST/"
cp -r "$ROOT/app" "$ROOT/ui" "$ROOT/samples" "$DST/"
cp "$ROOT/deploy/huggingface/app.py" "$DST/app.py"
echo "Synced into $DST — Dockerfile and README.md in hf-space/ are not overwritten."
