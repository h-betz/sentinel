#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$REPO_ROOT/toy_app"
docker compose logs -f sentinel-agent "$@"
