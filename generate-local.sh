#!/usr/bin/env bash
# Run this locally to regenerate snake + stats/languages cards,
# then push them to the output branch — no GitHub Actions needed.
#
# Requires:
#   - GH_TOKEN env var set (a personal access token, public_repo scope)
#   - Node.js + npm installed
#   - npm install generate-snake-animation   (run once in this repo folder)
#   - pip install requests --break-system-packages
#
# Usage: GH_TOKEN=ghp_xxx ./generate-local.sh

set -e

GH_USER="JOKER-53"
REPO_DIR="$(pwd)"
DIST_DIR="$REPO_DIR/dist"

if [ -z "$GH_TOKEN" ]; then
  echo "ERROR: set GH_TOKEN first, e.g. export GH_TOKEN=ghp_xxx"
  exit 1
fi

mkdir -p "$DIST_DIR"

echo "==> Generating snake animation..."
GH_TOKEN="$GH_TOKEN" GH_USER="$GH_USER" node gen-snake.mjs

echo "==> Fetching real GitHub stats and rendering cards..."
GH_TOKEN="$GH_TOKEN" GH_USER="$GH_USER" python3 fetch_stats.py

echo "==> Files generated in dist/:"
ls -la "$DIST_DIR"

echo "==> Pushing to output branch..."
git checkout output
cp "$DIST_DIR"/*.svg .
git add -- '*.svg'
git commit -m "Update generated assets ($(date '+%Y-%m-%d %H:%M'))" || echo "Nothing to commit"
git push origin output
git checkout main

echo "==> Done. All assets updated on output branch."
