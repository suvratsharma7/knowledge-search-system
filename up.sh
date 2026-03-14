#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
REPO_ROOT=$(pwd)

echo "=== Knowledge Search + KPI Dashboard ==="

# 1. Path Setup
VENV_PYTHON="$REPO_ROOT/.venv/Scripts/python"

# 2. Virtual Environment & Backend Dependency Check
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
    echo "Installing backend dependencies..."
    "$VENV_PYTHON" -m pip install --upgrade pip
    
    # Try to find requirements.txt in root or backend folder
    if [ -f "backend/requirements.txt" ]; then
        "$VENV_PYTHON" -m pip install -r backend/requirements.txt
    elif [ -f "requirements.txt" ]; then
        "$VENV_PYTHON" -m pip install -r requirements.txt
    else
        echo "❌ Error: requirements.txt not found!"
        exit 1
    fi
fi

# 3. Frontend Dependency Check
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd "$REPO_ROOT/frontend"
    npm install
    cd "$REPO_ROOT"
fi

# 4. Start Backend
echo "Starting Backend..."
cd "$REPO_ROOT/backend"
"$VENV_PYTHON" -m app &
BACKEND_PID=$!

# 5. Wait for Backend
echo "Waiting for backend to be ready..."
sleep 5 

# 6. Start Frontend
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

