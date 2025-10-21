#!/bin/bash

# Start script for Excel Agent (Backend + Frontend)
echo "🚀 Starting Excel Agent..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
START_FRONTEND=false
FRONTEND_PORT=3000
BACKEND_PORT=8000

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check if virtual environment exists and activate it
setup_venv() {
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        echo "📦 Activating virtual environment..."
        source venv/bin/activate
        return 0
    elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        echo "📦 Activating virtual environment (.venv)..."
        source .venv/bin/activate
        return 0
    else
        echo "⚠️  No virtual environment found. Using system Python..."
        return 1
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --frontend)
                START_FRONTEND=true
                shift
                ;;
            --frontend-port)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            --backend-port)
                BACKEND_PORT="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --frontend              Start frontend server (default: false)"
                echo "  --frontend-port PORT    Frontend server port (default: 3000)"
                echo "  --backend-port PORT     Backend server port (default: 8000)"
                echo "  -h, --help             Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                           # Start backend only"
                echo "  $0 --frontend               # Start both backend and frontend"
                echo "  $0 --frontend --frontend-port 8080  # Start both with custom frontend port"
                exit 0
                ;;
            *)
                echo "❌ Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Function to check if app is already running
check_running() {
    local check_frontend=$1

    # Check for uvicorn processes (backend)
    UVICORN_PIDS=$(pgrep -f "uvicorn.*app:app" 2>/dev/null || echo "")
    if [ -n "$UVICORN_PIDS" ]; then
        echo "⚠️  Backend appears to be already running (uvicorn processes: $UVICORN_PIDS)"
        echo "💡 Use ./stop_all.sh to stop existing processes first"
        return 0
    fi

    # Check for python processes running backend/app.py
    PYTHON_PIDS=$(pgrep -f "python.*backend/app\.py" 2>/dev/null || echo "")
    if [ -n "$PYTHON_PIDS" ]; then
        echo "⚠️  Backend appears to be already running (python processes: $PYTHON_PIDS)"
        echo "💡 Use ./stop_all.sh to stop existing processes first"
        return 0
    fi

    # Check if backend port is in use
    if check_port $BACKEND_PORT; then
        echo "⚠️  Backend port $BACKEND_PORT is already in use"
        echo "💡 Use ./stop_all.sh to free up the port"
        return 0
    fi

    # Check frontend if requested
    if [ "$check_frontend" = true ] && [ "$START_FRONTEND" = true ]; then
        FRONTEND_PIDS=$(pgrep -f "python.*frontend_server\.py" 2>/dev/null || echo "")
        if [ -n "$FRONTEND_PIDS" ]; then
            echo "⚠️  Frontend appears to be already running (processes: $FRONTEND_PIDS)"
            echo "💡 Use ./stop_all.sh to stop existing processes first"
            return 0
        fi

        if check_port $FRONTEND_PORT; then
            echo "⚠️  Frontend port $FRONTEND_PORT is already in use"
            echo "💡 Use ./stop_all.sh to free up the port"
            return 0
        fi
    fi

    return 1  # Not running
}

# Function to start the backend
start_backend() {
    local method=$1

    echo "🔧 Starting backend with method: $method"
    echo "📡 Backend API will be available at: http://localhost:$BACKEND_PORT"
    echo "💚 Health check: http://localhost:$BACKEND_PORT/health"
    echo ""

    if [ "$START_FRONTEND" = true ]; then
        echo "🌐 Frontend will be available at: http://localhost:$FRONTEND_PORT"
        echo ""
    fi

    if [ "$method" = "uvicorn" ]; then
        cd backend
        exec uvicorn app:app --reload --host 0.0.0.0 --port $BACKEND_PORT --log-level info
    elif [ "$method" = "python" ]; then
        exec python backend/app.py
    else
        echo "❌ Unknown start method: $method"
        exit 1
    fi
}

# Function to start both backend and frontend
start_both() {
    local backend_method=$1

    echo "🚀 Starting both backend and frontend..."
    echo "📡 Backend API: http://localhost:$BACKEND_PORT"
    echo "🌐 Frontend UI: http://localhost:$FRONTEND_PORT"
    echo "🔗 SSE Stream: http://localhost:$BACKEND_PORT/stream"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    echo "--------------------------------------------------"

    # Start backend in background
    if [ "$backend_method" = "uvicorn" ]; then
        cd backend
        uvicorn app:app --reload --host 0.0.0.0 --port $BACKEND_PORT --log-level info &
        BACKEND_PID=$!
        cd ..
    elif [ "$backend_method" = "python" ]; then
        python backend/app.py &
        BACKEND_PID=$!
    fi

    # Wait a moment for backend to start
    sleep 2

    # Start frontend
    python frontend_server.py $FRONTEND_PORT &
    FRONTEND_PID=$!

    echo "✅ Backend PID: $BACKEND_PID"
    echo "✅ Frontend PID: $FRONTEND_PID"
    echo ""
    echo "💡 Use ./stop_all.sh to stop both servers"

    # Wait for both processes
    wait $BACKEND_PID $FRONTEND_PID
}

# Main script logic
main() {
    # Parse command line arguments
    parse_args "$@"

    # Check if backend/app.py exists
    if [ ! -f "backend/app.py" ]; then
        echo "❌ Error: backend/app.py not found in current directory"
        echo "💡 Make sure you're running this script from the project root"
        exit 1
    fi

    # Check if frontend directory exists when frontend is requested
    if [ "$START_FRONTEND" = true ] && [ ! -d "frontend" ]; then
        echo "❌ Error: frontend/ directory not found"
        echo "💡 The frontend hasn't been created yet"
        exit 1
    fi

    # Check if app is already running
    if check_running true; then
        echo "❌ Services appear to be already running. Please stop them first."
        exit 1
    fi

    # Setup virtual environment
    setup_venv

    # Determine which method to use for backend
    local backend_method=""
    if command -v uvicorn >/dev/null 2>&1; then
        backend_method="uvicorn"
        echo "✅ Using uvicorn for backend"
    elif python -c "import uvicorn" 2>/dev/null; then
        backend_method="uvicorn"
        echo "✅ Using uvicorn (via python) for backend"
    else
        backend_method="python"
        echo "ℹ️  Uvicorn not available, using direct Python execution for backend"
    fi

    # Start services based on configuration
    if [ "$START_FRONTEND" = true ]; then
        start_both "$backend_method"
    else
        start_backend "$backend_method"
    fi
}

# Run main function
main "$@"
