#!/usr/bin/env bash
# Stop the n8n stack and wipe its data volume (owner, credential, workflow).
set -euo pipefail
cd "$(dirname "$0")"
docker compose down -v
