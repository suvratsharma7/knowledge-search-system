#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
REPO_ROOT=$(pwd)

echo "=== Knowledge Search + KPI Dashboard ==="

# 1. Path Setup (Windows Specific)
VENV_PYTHON="$REPO_ROOT/.venv/Scripts/python"

# 2. Virtual Environment Check
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# 3. Start Backend (Using VENV Python explicitly)
echo "Starting Backend..."
cd "$REPO_ROOT/backend"
"$VENV_PYTHON" -m app &
BACKEND_PID=$!

# 4. Wait for Backend
echo "Waiting for backend to be ready..."
sleep 5 # Give it a head start

# 5. Start Frontend
echo "Starting Frontend..."
cd "$REPO_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo "----------------------------------------"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop"
echo "----------------------------------------"

trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait