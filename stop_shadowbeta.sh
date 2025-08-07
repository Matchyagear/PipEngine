#!/bin/bash

# 🛑 ShadowBeta Financial Dashboard - Stop Script

echo "🛑 Stopping ShadowBeta Financial Dashboard..."

# Stop all services using supervisor
sudo supervisorctl stop all

echo "✅ All ShadowBeta services stopped!"
echo ""  
echo "🔄 To start again, run:"
echo "   ./start_shadowbeta.sh"