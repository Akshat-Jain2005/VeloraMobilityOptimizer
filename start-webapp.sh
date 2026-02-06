#!/bin/bash

# Velora Mobility Optimizer - Web Application Startup Script

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=================================="
echo "Velora Mobility Optimizer Web App"
echo "=================================="

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "$PROJECT_DIR/backend/node_modules" ]; then
    echo "Installing backend dependencies..."
    cd "$PROJECT_DIR/backend" && npm install
fi

if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd "$PROJECT_DIR/frontend" && npm install
fi

# Kill any existing processes on our ports
echo "Cleaning up old processes..."
lsof -ti:3001 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting backend server on port 3001..."
cd "$PROJECT_DIR/backend" && node src/app.js &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Verify backend is running
if ! curl -s http://localhost:3001/health > /dev/null; then
    echo "Error: Backend failed to start"
    exit 1
fi
echo "Backend started successfully"

# Start frontend
echo "Starting frontend dev server on port 5173..."
cd "$PROJECT_DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "=================================="
echo "Application started!"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=================================="

# Handle Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Keep script running
wait
