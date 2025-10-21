#!/bin/bash

# Stop script for Excel Agent backend
echo "Stopping Excel Agent backend..."

# Function to kill processes gracefully
kill_processes() {
    local pids=$1
    if [ -n "$pids" ]; then
        echo "Found processes: $pids"
        kill $pids 2>/dev/null
        sleep 2
        # Force kill if still running
        kill -9 $pids 2>/dev/null
        echo "Processes stopped."
    else
        echo "No processes found to stop."
    fi
}

# Method 1: Find uvicorn processes
UVICORN_PIDS=$(pgrep -f "uvicorn.*app:app" 2>/dev/null || echo "")
if [ -n "$UVICORN_PIDS" ]; then
    echo "Stopping uvicorn processes..."
    kill_processes "$UVICORN_PIDS"
fi

# Method 2: Find python processes running app.py
PYTHON_PIDS=$(pgrep -f "python.*app\.py" 2>/dev/null || echo "")
if [ -n "$PYTHON_PIDS" ]; then
    echo "Stopping Python app processes..."
    kill_processes "$PYTHON_PIDS"
fi

# Method 3: Find processes using port 8000 (default FastAPI port)
PORT_PIDS=$(lsof -ti:8000 2>/dev/null || echo "")
if [ -n "$PORT_PIDS" ]; then
    echo "Stopping processes using port 8000..."
    kill_processes "$PORT_PIDS"
fi

# Method 4: Find any remaining python processes in the backend directory
BACKEND_PYTHON_PIDS=$(pgrep -f "python.*backend" 2>/dev/null || echo "")
if [ -n "$BACKEND_PYTHON_PIDS" ]; then
    echo "Stopping remaining backend Python processes..."
    kill_processes "$BACKEND_PYTHON_PIDS"
fi

echo "Excel Agent backend stopped."
