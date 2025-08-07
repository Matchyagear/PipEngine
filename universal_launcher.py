#!/usr/bin/env python3

"""
🚀 ShadowBeta Universal Launcher
Works from any directory - automatically finds and starts ShadowBeta
"""

import subprocess
import time
import os
import sys
import webbrowser
import platform

def print_banner():
    print("🚀 ShadowBeta Financial Dashboard - Universal Launcher")
    print("=" * 60)
    print("📊 Professional Trading Analysis Platform")
    print()

def find_shadowbeta_directory():
    """Find the ShadowBeta directory automatically"""
    print("🔍 Searching for ShadowBeta directory...")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Check script directory first
    if os.path.exists(os.path.join(script_dir, 'backend')) and os.path.exists(os.path.join(script_dir, 'frontend')):
        print(f"✅ Found ShadowBeta in script directory: {script_dir}")
        return script_dir

    # Common locations to check
    possible_locations = [
        '/app',
        script_dir,
        os.path.dirname(script_dir),
        os.path.expanduser('~/ShadowBeta'),
        os.path.expanduser('~/shadowbeta'),
        os.path.expanduser('~/Desktop/ShadowBeta'),
        os.path.expanduser('~/Downloads/ShadowBeta'),
        os.path.join(os.getcwd(), 'ShadowBeta'),
        os.getcwd()
    ]

    for location in possible_locations:
        if os.path.exists(location):
            backend_path = os.path.join(location, 'backend')
            frontend_path = os.path.join(location, 'frontend')
            if os.path.exists(backend_path) and os.path.exists(frontend_path):
                print(f"✅ Found ShadowBeta at: {location}")
                return location

    return None

def start_services(shadowbeta_dir):
    """Start the ShadowBeta services"""
    print("🔄 Starting ShadowBeta services...")

    # Change to ShadowBeta directory
    original_dir = os.getcwd()
    os.chdir(shadowbeta_dir)

    try:
        # Method 1: Try supervisor first (Linux systems)
        if os.path.exists('/usr/bin/supervisorctl'):
            print("   Using supervisor to start services...")
            result = subprocess.run(['sudo', 'supervisorctl', 'restart', 'all'],
                                 capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Services started successfully with supervisor!")
                return True
            else:
                print("⚠️ Supervisor start failed, trying alternative method...")

        # Method 2: Try startup scripts
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
                subprocess.Popen([script_name], shell=True, cwd=shadowbeta_dir)
            else:
                subprocess.Popen(['bash', script_name], cwd=shadowbeta_dir)
            print("✅ Startup script executed!")
            return True

        # Method 3: Manual start (fallback)
        print("   Starting services manually...")

        # Start backend
        backend_dir = os.path.join(shadowbeta_dir, 'backend')
        if os.path.exists(backend_dir):
            print("   Starting backend...")
            subprocess.Popen([sys.executable, 'server.py'], cwd=backend_dir)

        # Start frontend (if yarn is available)
        frontend_dir = os.path.join(shadowbeta_dir, 'frontend')
        if os.path.exists(frontend_dir):
            try:
                print("   Starting frontend...")
                subprocess.Popen(['yarn', 'start'], cwd=frontend_dir)
            except FileNotFoundError:
                try:
                    subprocess.Popen(['npm', 'start'], cwd=frontend_dir)
                except FileNotFoundError:
                    print("   ⚠️  yarn/npm not found, please start frontend manually")

        print("✅ Services started manually!")
        return True

    except Exception as e:
        print(f"❌ Error starting services: {e}")
        return False
    finally:
        os.chdir(original_dir)

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to initialize...")

    # Wait with progress indicator
    for i in range(20):
        print(f"   Initializing... {i+1}/20 seconds", end='\r')
        time.sleep(1)

    print("\n✅ Services should be ready now!                    ")

def open_dashboard():
    """Open the dashboard in browser"""
    try:
        # Get the correct URL from the environment file
        frontend_url = "http://localhost:3000"  # fallback

        # Check environment file for the correct URL
        env_file = '/app/frontend/.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if 'REACT_APP_BACKEND_URL' in line and '=' in line:
                            backend_url = line.split('=')[1].strip().strip('"')
                            # Remove /api suffix if present to get frontend URL
                            frontend_url = backend_url.replace('/api', '')
                            break
            except Exception as e:
                print(f"   ⚠️ Could not read .env file: {e}")

        print(f"🌐 Opening dashboard: {frontend_url}")
        webbrowser.open(frontend_url, new=2)

        return frontend_url

    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        fallback_url = "http://localhost:3000"
        print(f"💡 Please manually open: {fallback_url}")
        return fallback_url

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
    print("   # or close the terminal windows")
    print()
    print("📊 Happy Trading! 🚀")

def main():
    print_banner()

    # Find ShadowBeta directory
    shadowbeta_dir = find_shadowbeta_directory()
    if not shadowbeta_dir:
        print("❌ Could not find ShadowBeta directory!")
        print()
        print("💡 Make sure ShadowBeta is installed and contains:")
        print("   • backend/ folder")
        print("   • frontend/ folder")
        print("   • launcher scripts")
        print()
        print("🔧 Alternative: Try running from the ShadowBeta directory:")
        print("   cd /app")
        print("   python3 simple_launcher.py")
        input("\nPress Enter to exit...")
        return

    # Start services
    if not start_services(shadowbeta_dir):
        print()
        print("❌ Failed to start services automatically.")
        print("💡 Try these alternatives:")
        print(f"   1. cd {shadowbeta_dir}")
        print("   2. sudo supervisorctl restart all")
        print("   3. Or start manually:")
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
        print("\nShadowBeta is now running!")
        print("Press Ctrl+C to exit this launcher...")
        while True:
            time.sleep(60)  # Keep running
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except:
        print("\n🛑 To stop ShadowBeta, run: sudo supervisorctl stop all")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
