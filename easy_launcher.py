#!/usr/bin/env python3

"""
🚀 ShadowBeta EASY Launcher
The simplest possible launcher - just run this file!
"""

import subprocess
import webbrowser
import time
import os

print("🚀 ShadowBeta Financial Dashboard")
print("=" * 40)
print("📊 Starting your trading platform...")
print()

# Change to the correct directory
shadowbeta_dir = "/app"
os.chdir(shadowbeta_dir)

print("🔄 Starting services...")

try:
    # Start services using supervisor
    result = subprocess.run(['sudo', 'supervisorctl', 'restart', 'all'],
                           capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        print("✅ Services started successfully!")

        # Wait for services to initialize
        print("⏳ Initializing (15 seconds)...")
        for i in range(15):
            print(f"   {i+1}/15 seconds", end='\r')
            time.sleep(1)
        print("\n")

        # Open browser with correct URL
        dashboard_url = "http://localhost:3000"
        print(f"🌐 Opening dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url, new=2)

        print()
        print("🎉 ShadowBeta is ready!")
        print("=" * 30)
        print(f"📊 Dashboard: {dashboard_url}")
        print("🤖 Click 'AI Insight' on any stock for analysis")
        print("📝 Use 'New List' to create watchlists")
        print("⚙️ Click Settings to customize")
        print()
        print("🔧 To stop: sudo supervisorctl stop all")
        print("📊 Happy Trading! 🚀")

    else:
        print("❌ Failed to start services")
        print("💡 Try running: sudo supervisorctl restart all")

except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Try running: sudo supervisorctl restart all")

print("\nLauncher finished. ShadowBeta should be running!")
