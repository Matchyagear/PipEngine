#!/bin/bash

# 🛑 ShadowBeta Financial Dashboard - Stop Script for macOS

echo "🛑 Stopping ShadowBeta Financial Dashboard..."

# Kill processes by PID if files exist
if [ -f ".backend_pid" ]; then
    BACKEND_PID=$(cat .backend_pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend_pid
    echo "✅ Backend stopped (PID: $BACKEND_PID)"
fi

if [ -f ".frontend_pid" ]; then
    FRONTEND_PID=$(cat .frontend_pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend_pid
    echo "✅ Frontend stopped (PID: $FRONTEND_PID)"
fi

# Also kill any remaining processes
pkill -f "python server.py" 2>/dev/null
pkill -f "yarn start" 2>/dev/null
pkill -f "react-scripts start" 2>/dev/null

echo "🔄 Stopping MongoDB..."
brew services stop mongodb-community

echo "✅ All ShadowBeta services stopped!"