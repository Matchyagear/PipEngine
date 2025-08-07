#!/usr/bin/env python3

"""
🚀 ShadowBeta QUICK Launcher
Opens the ShadowBeta dashboard directly - no setup needed!
"""

import webbrowser
import subprocess
import time

print("🚀 ShadowBeta Financial Dashboard")
print("=" * 40)

# The correct URL for your ShadowBeta dashboard
DASHBOARD_URL = "http://localhost:3000"

print("🔄 Ensuring services are running...")

try:
    # Make sure services are running
    result = subprocess.run(['sudo', 'supervisorctl', 'status'],
                           capture_output=True, text=True, timeout=10)

    if 'RUNNING' in result.stdout:
        print("✅ Services are running!")
    else:
        print("🔄 Starting services...")
        subprocess.run(['sudo', 'supervisorctl', 'restart', 'all'], timeout=30)
        print("✅ Services started!")
        time.sleep(5)  # Brief wait for startup

except Exception as e:
    print(f"⚠️ Could not check services: {e}")
    print("💡 Services might already be running")

print(f"🌐 Opening ShadowBeta dashboard...")
print(f"📊 URL: {DASHBOARD_URL}")

try:
    webbrowser.open(DASHBOARD_URL, new=2)
    print("✅ Dashboard opened in your browser!")
except Exception as e:
    print(f"⚠️ Could not open browser automatically: {e}")
    print(f"💡 Please manually open: {DASHBOARD_URL}")

print()
print("🎉 ShadowBeta is ready!")
print("=" * 30)
print("🎯 What you can do:")
print("   • View live stock analysis with scores")
print("   • Click 'AI Insight' for trading recommendations")
print("   • Create custom watchlists with 'New List'")
print("   • Use Settings ⚙️ to customize your experience")
print("   • Export your analysis data")
print()
print("📊 Happy Trading! 🚀")
print(f"🔗 Bookmark this URL: {DASHBOARD_URL}")
