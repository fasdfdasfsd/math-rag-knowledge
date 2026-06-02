#!/bin/bash
# Math Adventure World — Development Startup
# Overrides .env DEEPSEEK_BASE_URL if incorrectly set

set -e
export DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"

echo "=== Starting backend ==="
cd "$(dirname "$0")/.."
uv run uvicorn src.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "=== Starting frontend ==="
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Backend:  http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
