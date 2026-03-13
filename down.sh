#!/usr/bin/env bash
# Knowledge Search + KPI Dashboard - Global Shutdown Script

echo "Stopping Knowledge Search services..."

# Ports to check: 8000 (Backend), 5173 (Frontend)
PORTS=(8000 5173)

for PORT in "${PORTS[@]}"; do
    PID=$(lsof -ti :$PORT)
    if [ ! -z "$PID" ]; then
        echo "Killing process on port $PORT (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
done

echo "Services stopped."
