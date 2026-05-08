#!/bin/bash
set -e

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BACKEND_DIR"

echo "启动 HexTech Arena 后端服务..."
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 18789 --reload
