#!/usr/bin/env python3

"""
🚀 ShadowBeta Simple Launcher (No GUI)
A simple command-line launcher that doesn't require tkinter
"""

import subprocess
import time
import os
import sys
import webbrowser
import platform

def print_banner():
    print("🚀 ShadowBeta Financial Dashboard - Simple Launcher")
    print("=" * 55)
    print("📊 Professional Trading Analysis Platform")
    print()

def check_prerequisites():
    """Check if we're in the right directory or find it automatically"""
    current_dir = os.getcwd()

    # Check current directory first
    if os.path.exists('backend') and os.path.exists('frontend'):
        print(f"✅ Found ShadowBeta directories in: {current_dir}")
        return True

    # Check if we're in a subdirectory and need to go up
    parent_dir = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(parent_dir, 'backend')) and os.path.exists(os.path.join(parent_dir, 'frontend')):
        print(f"🔄 Moving to parent directory: {parent_dir}")
        os.chdir(parent_dir)
        return True

    # Check common locations
    possible_locations = [
        '/app',
        os.path.expanduser('~/ShadowBeta'),
        os.path.expanduser('~/shadowbeta'),
        os.path.expanduser('~/Desktop/ShadowBeta'),
        os.path.expanduser('~/Downloads/ShadowBeta'),
        './ShadowBeta',
        '../ShadowBeta'
    ]

    for location in possible_locations:
        if os.path.exists(location):
            backend_path = os.path.join(location, 'backend')
            frontend_path = os.path.join(location, 'frontend')
            if os.path.exists(backend_path) and os.path.exists(frontend_path):
                print(f"🔄 Found ShadowBeta at: {location}")
                os.chdir(location)
                return True

    # If still not found, show detailed error
    print("❌ Error: Could not locate ShadowBeta directory")
    print(f"   Current directory: {current_dir}")
    print("   Looking for directories containing 'backend' and 'frontend' folders")
    print()
    print("💡 Solutions:")
    print("   1. Navigate to the ShadowBeta directory first:")
    print(f"      cd /app")
    print(f"      python3 simple_launcher.py")
    print()
    print("   2. Or run the launcher with full path:")
    print(f"      python3 /app/simple_launcher.py")
    print()
    print("   3. Or use the script launcher instead:")
    print(f"      /app/start_shadowbeta.sh")

    return False

def start_services():
    """Start the ShadowBeta services"""
    print("🔄 Starting ShadowBeta services...")

    try:
        # Try supervisor first (Linux systems)
        if os.path.exists('/usr/bin/supervisorctl'):
            print("   Using supervisor to start services...")
            result = subprocess.run(['sudo', 'supervisorctl', 'restart', 'all'],
                                 capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Services started successfully with supervisor!")
                return True
            else:
                print("⚠️ Supervisor start failed, trying alternative method...")

        # Alternative method - run startup script
        system = platform.system()
        script_name = None

        if system == "Linux":
            script_name = "start_shadowbeta.sh"
        elif system == "Darwin":  # macOS
            script_name = "start_shadowbeta_macos.sh"
        elif system == "Windows":
            script_name = "start_shadowbeta.bat"

        if script_name and os.path.exists(script_name):
            print(f"   Running startup script: {script_name}")
            if system == "Windows":
                subprocess.Popen([script_name], shell=True)
            else:
                subprocess.Popen(['bash', script_name])
            print("✅ Startup script executed!")
            return True
        else:
            print("❌ No suitable startup method found")
            return False

    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to initialize...")

    # Wait a bit for services to start
    for i in range(15):
        print(f"   Waiting... {i+1}/15 seconds")
        time.sleep(1)

    print("✅ Services should be ready now!")

def open_dashboard():
    """Open the dashboard in browser"""
    try:
        # Try to detect the correct URL
        frontend_url = "http://localhost:3000"

        # Check environment file
        env_file = os.path.join('frontend', '.env')
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if 'REACT_APP_BACKEND_URL' in line and '=' in line:
                            backend_url = line.split('=')[1].strip().strip('"')
                            frontend_url = backend_url.replace('/api', '')
                            break
            except:
                pass

        print(f"🌐 Opening dashboard: {frontend_url}")
        webbrowser.open(frontend_url, new=2)

        return frontend_url

    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        return "http://localhost:3000"

def show_instructions(dashboard_url):
    """Show usage instructions"""
    print()
    print("🎉 ShadowBeta Financial Dashboard is starting!")
    print("=" * 50)
    print(f"📊 Dashboard URL: {dashboard_url}")
            print("🔧 Backend API: http://localhost:8000")
    print()
    print("🎯 Quick Start Tips:")
    print("   • The dashboard shows live stock analysis")
    print("   • Click 'AI Insight' on any stock for trading recommendations")
    print("   • Use 'New List' to create custom watchlists")
    print("   • Click Settings ⚙️ to customize your experience")
    print("   • Export your analysis with the Export button")
    print()
    print("🔧 To stop the application:")
    print("   sudo supervisorctl stop all")
    print()
    print("📊 Happy Trading! 🚀")

def main():
    print_banner()

    # Check prerequisites
    if not check_prerequisites():
        input("Press Enter to exit...")
        return

    # Start services
    if not start_services():
        print()
        print("❌ Failed to start services automatically.")
        print("💡 Try these alternatives:")
        print("   1. Run the diagnostic tool: python3 diagnostic_tool.py")
        print("   2. Start manually:")
        print("      • Terminal 1: cd backend && python server.py")
        print("      • Terminal 2: cd frontend && yarn start")
        input("Press Enter to exit...")
        return

    # Wait for services
    wait_for_services()

    # Open dashboard
    dashboard_url = open_dashboard()

    # Show instructions
    show_instructions(dashboard_url)

    # Keep script running
    try:
        input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
