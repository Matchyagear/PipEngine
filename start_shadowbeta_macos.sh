#!/bin/bash

# 🚀 ShadowBeta Financial Dashboard - macOS One-Click Startup Script
# This script starts the entire ShadowBeta application with one click on macOS

echo "🚀 Starting ShadowBeta Financial Dashboard for macOS..."
echo "===================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Homebrew is installed
if ! command_exists brew; then
    echo "⚠️  Homebrew not found. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Check Python
if ! command_exists python3; then
    echo "⚠️  Python3 not found. Installing..."
    brew install python
fi
echo "✅ Python found"

# Check Node.js
if ! command_exists node; then
    echo "⚠️  Node.js not found. Installing..."
    brew install node
fi
echo "✅ Node.js found"

# Check Yarn
if ! command_exists yarn; then
    echo "⚠️  Yarn not found. Installing..."
    npm install -g yarn
fi
echo "✅ Yarn found"

# Check MongoDB
if ! command_exists mongod; then
    echo "⚠️  MongoDB not found. Installing..."
    brew tap mongodb/brew
    brew install mongodb-community
fi

# Start MongoDB
echo "🔄 Starting MongoDB..."
if ! pgrep mongod > /dev/null; then
    brew services start mongodb-community
    echo "✅ MongoDB started"
else
    echo "✅ MongoDB already running"
fi

# Change to app directory
cd "$(dirname "$0")"

echo "📦 Installing/updating dependencies..."

# Setup backend
echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup frontend
echo "Setting up frontend..."
cd frontend
yarn install
cd ..

echo "🚀 Starting services..."

# Start backend in background
echo "Starting backend server..."
cd backend
source venv/bin/activate
nohup python server.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 10

# Start frontend in background
echo "Starting frontend..."
cd frontend
nohup yarn start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Detect frontend URL
FRONTEND_URL="http://localhost:3000"
if [ -f "frontend/.env" ]; then
    BACKEND_URL=$(grep REACT_APP_BACKEND_URL frontend/.env | cut -d'=' -f2 | tr -d '"')
    if [ ! -z "$BACKEND_URL" ]; then
        FRONTEND_URL=${BACKEND_URL//\/api/}
    fi
fi

echo "🎉 ShadowBeta Financial Dashboard is ready!"
echo "========================================"
echo "📊 Dashboard URL: $FRONTEND_URL"
echo "🔧 Backend API: http://localhost:8001"
echo "📚 Documentation: Check README.md for usage instructions"
echo ""
echo "📝 Process IDs:"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""

# Save PIDs for stopping later
echo $BACKEND_PID > .backend_pid
echo $FRONTEND_PID > .frontend_pid

echo "🌐 Opening dashboard in your default browser..."
open "$FRONTEND_URL"

echo ""
echo "🎯 Quick Start Tips:"
echo "   • The dashboard shows live stock analysis"
echo "   • Click 'AI Insight' on any stock for trading recommendations"
echo "   • Use 'New List' to create custom watchlists"
echo "   • Click Settings ⚙️ to customize your experience"
echo "   • Export your analysis with the Export button"
echo ""
echo "🔧 To stop the application, run:"
echo "   ./stop_shadowbeta_macos.sh"
echo ""
echo "📊 Happy Trading! 🚀"
echo ""
echo "Press Ctrl+C to stop all services, or close this terminal to keep running in background."

# Wait for Ctrl+C
trap 'echo ""; echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ Services stopped"; exit 0' INT

# Keep script running
while true; do
    sleep 60
done