#!/bin/bash

# 🚀 ShadowBeta Financial Dashboard - One-Click Startup Script
# This script starts the entire ShadowBeta application with one click

echo "🚀 Starting ShadowBeta Financial Dashboard..."
echo "========================================"

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

if ! command_exists supervisorctl; then
    echo "❌ supervisor not found. Installing..."
    # This would need to be adapted based on the system
    sudo apt-get update && sudo apt-get install -y supervisor
fi

# Check if MongoDB is running
if ! pgrep mongod > /dev/null; then
    echo "⚠️  MongoDB not detected. Starting MongoDB..."
    if command_exists systemctl; then
        sudo systemctl start mongod
    elif command_exists brew; then
        brew services start mongodb-community
    else
        echo "⚠️  Please start MongoDB manually"
    fi
fi

# Start all services using supervisor
echo "🔄 Starting all services..."
sudo supervisorctl restart all

# Wait for services to be ready
sleep 3

# Check service status
echo "📊 Checking service status..."
sudo supervisorctl status

# Wait for backend to be ready
echo "⏳ Waiting for services to initialize..."
if wait_for_service "http://localhost:8001" "Backend API"; then
    echo "✅ Backend is running on http://localhost:8001"
else
    echo "❌ Backend failed to start. Check logs with: tail -f /var/log/supervisor/backend.err.log"
    exit 1
fi

# Wait for frontend to be ready
if wait_for_service "http://localhost:3000" "Frontend"; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Frontend failed to start. Check logs with: sudo supervisorctl status frontend"
    exit 1
fi

# Get the correct URL from environment
FRONTEND_URL="http://localhost:3000"
if [ -f "/app/frontend/.env" ]; then
    FRONTEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2 | sed 's/api//' | tr -d '"')
fi

echo "🎉 ShadowBeta Financial Dashboard is ready!"
echo "========================================"
echo "📊 Dashboard URL: $FRONTEND_URL"
echo "🔧 Backend API: http://localhost:8001"
echo "📚 Documentation: Check README.md for usage instructions"
echo ""
echo "🌐 Opening dashboard in your default browser..."

# Open browser based on operating system
case "$(uname -s)" in
    Linux*)
        if command_exists xdg-open; then
            xdg-open "$FRONTEND_URL" 2>/dev/null &
        elif command_exists google-chrome; then
            google-chrome "$FRONTEND_URL" 2>/dev/null &
        elif command_exists firefox; then
            firefox "$FRONTEND_URL" 2>/dev/null &
        else
            echo "📝 Please open $FRONTEND_URL in your browser"
        fi
        ;;
    Darwin*)
        open "$FRONTEND_URL" 2>/dev/null &
        ;;
    CYGWIN*|MINGW*|MSYS*)
        start "$FRONTEND_URL" 2>/dev/null &
        ;;
    *)
        echo "📝 Please open $FRONTEND_URL in your browser"
        ;;
esac

echo ""
echo "🎯 Quick Start Tips:"
echo "   • The dashboard shows live stock analysis"
echo "   • Click 'AI Insight' on any stock for trading recommendations"  
echo "   • Use 'New List' to create custom watchlists"
echo "   • Click Settings ⚙️ to customize your experience"
echo "   • Export your analysis with the Export button"
echo ""
echo "🔧 To stop the application:"
echo "   sudo supervisorctl stop all"
echo ""
echo "📊 Happy Trading! 🚀"