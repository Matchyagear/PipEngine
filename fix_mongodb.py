#!/usr/bin/env python3
"""
SHADOWBETA MONGODB FIX SCRIPT
Helps resolve MongoDB connection issues and provides setup options
"""

import os
import sys
import subprocess
import platform

def print_header():
    print("🔧 SHADOWBETA MONGODB FIX UTILITY")
    print("=" * 60)
    print()

def check_mongodb_status():
    """Check if MongoDB is running"""
    print("🔍 Checking MongoDB status...")

    try:
        import pymongo
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017', serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB is running and accessible")
        return True
    except Exception as e:
        print(f"❌ MongoDB not accessible: {e}")
        return False

def create_env_file():
    """Create .env file to disable MongoDB"""
    env_content = """# SHADOWBETA QUICK SETUP - MongoDB Disabled
MONGODB_DISABLED=true

# Uncomment below if you want to use MongoDB later
# MONGODB_DISABLED=false
# MONGO_URL=mongodb://127.0.0.1:27017
# DB_NAME=shadowbeta
"""

    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with MongoDB disabled")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def show_mongodb_install_instructions():
    """Show MongoDB installation instructions"""
    print("📋 MONGODB INSTALLATION OPTIONS:")
    print("=" * 40)

    system = platform.system().lower()

    if system == "windows":
        print("🪟 Windows:")
        print("1. Download MongoDB Community Server from:")
        print("   https://www.mongodb.com/try/download/community")
        print("2. Or install via Chocolatey:")
        print("   choco install mongodb")
        print("3. Or install via winget:")
        print("   winget install MongoDB.Server")
        print()
        print("🐳 Alternative - Docker:")
        print("   docker run -d -p 27017:27017 --name mongodb mongo")

    elif system == "darwin":  # macOS
        print("🍎 macOS:")
        print("1. Install via Homebrew:")
        print("   brew tap mongodb/brew")
        print("   brew install mongodb-community")
        print("   brew services start mongodb/brew/mongodb-community")
        print()
        print("🐳 Alternative - Docker:")
        print("   docker run -d -p 27017:27017 --name mongodb mongo")

    elif system == "linux":
        print("🐧 Linux:")
        print("1. Ubuntu/Debian:")
        print("   sudo apt update")
        print("   sudo apt install mongodb")
        print("   sudo systemctl start mongodb")
        print()
        print("2. CentOS/RHEL:")
        print("   sudo dnf install mongodb-server")
        print("   sudo systemctl start mongod")
        print()
        print("🐳 Alternative - Docker:")
        print("   docker run -d -p 27017:27017 --name mongodb mongo")

    print()

def show_solutions():
    """Show all available solutions"""
    print("🚀 AVAILABLE SOLUTIONS:")
    print("=" * 30)
    print()

    print("1️⃣ QUICK FIX (Recommended for testing):")
    print("   • Disable MongoDB completely")
    print("   • App runs with all core features")
    print("   • No user accounts/watchlists (not needed for testing)")
    print()

    print("2️⃣ INSTALL MONGODB:")
    print("   • Full feature set including user accounts")
    print("   • Persistent watchlists and settings")
    print("   • Required for production use")
    print()

    print("3️⃣ USE DOCKER:")
    print("   • Quick MongoDB setup with Docker")
    print("   • No system installation required")
    print("   • Good for development")
    print()

def main():
    print_header()

    # Check current status
    mongodb_running = check_mongodb_status()

    if mongodb_running:
        print("✅ MongoDB is working! The connection error might be temporary.")
        print("💡 Try restarting your ShadowBeta server.")
        return

    print()
    show_solutions()
    print()

    # Get user choice
    while True:
        choice = input("Choose solution (1/2/3) or 'q' to quit: ").strip().lower()

        if choice == 'q':
            print("👋 Exiting...")
            return

        elif choice == '1':
            print("\n🔧 Applying quick fix...")
            if create_env_file():
                print("✅ Quick fix applied!")
                print("💡 Restart your ShadowBeta server now.")
                print("📝 Note: User features disabled (accounts, watchlists)")
                break
            else:
                print("❌ Quick fix failed. Try manually setting MONGODB_DISABLED=true")

        elif choice == '2':
            print("\n📋 MongoDB installation instructions:")
            show_mongodb_install_instructions()
            print("💡 After installation, remove the .env file or set MONGODB_DISABLED=false")
            break

        elif choice == '3':
            print("\n🐳 Docker MongoDB setup:")
            print("Run this command:")
            print("docker run -d -p 27017:27017 --name shadowbeta-mongo mongo")
            print()
            print("💡 After starting, remove the .env file or set MONGODB_DISABLED=false")
            break

        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 'q'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
